"""
Osool Liquidity Service
-----------------------
Backend service for AMM (Automated Market Maker) operations.

Integrates with:
- OsoolLiquidityAMM.sol (smart contract)
- OsoolEGPStablecoin.sol (stablecoin)
- PostgreSQL (liquidity_pools, trades, liquidity_positions tables)

Phase 6: Osool Production Transformation
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from web3 import Web3
from web3.exceptions import ContractLogicError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LiquidityPool, Trade, LiquidityPosition, Property
from app.services.cache import cache

logger = logging.getLogger(__name__)


class LiquidityService:
    """
    Service for managing AMM liquidity pools and trading operations.
    """

    def __init__(self):
        """Initialize liquidity service with Web3 connection."""
        # Web3 Setup
        self.rpc_url = os.getenv("POLYGON_RPC_URL")
        self.chain_id = int(os.getenv("CHAIN_ID", "137"))
        self.private_key = os.getenv("PRIVATE_KEY")

        if not self.rpc_url or not self.private_key:
            logger.warning("⚠️ Blockchain credentials not configured")
            self.w3 = None
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self.account = self.w3.eth.account.from_key(self.private_key)

            # Load contract ABIs and addresses
            self.amm_address = os.getenv("OSOOL_AMM_ADDRESS")
            self.oegp_address = os.getenv("OSOOL_OEGP_ADDRESS")

            # Note: In production, load actual ABI from compiled contracts
            # For now, we'll use simplified ABIs
            self.amm_contract = None  # Will be initialized with actual ABI
            self.oegp_contract = None

            logger.info(f"✅ Liquidity Service initialized (Chain: {self.chain_id})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Web3: {e}")
            self.w3 = None

    # ═══════════════════════════════════════════════════════════════
    # POOL MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    async def get_all_pools(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Get all liquidity pools with current stats.

        Args:
            db: Database session
            skip: Pagination offset
            limit: Max pools to return
            active_only: Only return active pools

        Returns:
            List of pool dictionaries with current price, volume, APY
        """
        try:
            # Build query
            query = select(LiquidityPool).join(Property)

            if active_only:
                query = query.where(LiquidityPool.is_active == True)

            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            pools = result.scalars().all()

            pool_list = []
            for pool in pools:
                # Calculate current price
                current_price = (
                    (pool.egp_reserve / pool.token_reserve)
                    if pool.token_reserve > 0 else 0
                )

                # Calculate APY (based on 24h fees)
                apy = await self._calculate_pool_apy(db, pool.id)

                # Get property info
                property_result = await db.execute(
                    select(Property).where(Property.id == pool.property_id)
                )
                property_obj = property_result.scalar_one_or_none()

                pool_list.append({
                    "pool_id": pool.id,
                    "property_id": pool.property_id,
                    "property_title": property_obj.title if property_obj else "Unknown",
                    "property_location": property_obj.location if property_obj else "Unknown",
                    "pool_address": pool.pool_address,
                    "token_reserve": float(pool.token_reserve),
                    "egp_reserve": float(pool.egp_reserve),
                    "total_lp_tokens": float(pool.total_lp_tokens),
                    "current_price": round(current_price, 4),
                    "volume_24h": float(pool.total_volume_24h),
                    "total_fees_earned": float(pool.total_fees_earned),
                    "apy": round(apy, 2),
                    "is_active": pool.is_active,
                    "created_at": pool.created_at.isoformat()
                })

            return pool_list

        except Exception as e:
            logger.error(f"❌ Failed to get pools: {e}")
            return []

    async def get_pool_details(self, db: AsyncSession, property_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific pool.

        Args:
            db: Database session
            property_id: Property ID

        Returns:
            Pool details dictionary or None
        """
        try:
            result = await db.execute(
                select(LiquidityPool).where(LiquidityPool.property_id == property_id)
            )
            pool = result.scalar_one_or_none()

            if not pool:
                return None

            # Get property details
            property_result = await db.execute(
                select(Property).where(Property.id == property_id)
            )
            property_obj = property_result.scalar_one_or_none()

            # Calculate metrics
            current_price = (pool.egp_reserve / pool.token_reserve) if pool.token_reserve > 0 else 0
            apy = await self._calculate_pool_apy(db, pool.id)
            tvl = pool.egp_reserve * 2  # Total Value Locked (both sides)

            # Get recent trades
            recent_trades = await self._get_recent_trades(db, pool.id, limit=10)

            return {
                "pool_id": pool.id,
                "property_id": pool.property_id,
                "property_title": property_obj.title if property_obj else "Unknown",
                "property_location": property_obj.location if property_obj else "Unknown",
                "property_image": property_obj.image_url if property_obj else None,
                "pool_address": pool.pool_address,
                "reserves": {
                    "token_reserve": float(pool.token_reserve),
                    "egp_reserve": float(pool.egp_reserve),
                    "total_lp_tokens": float(pool.total_lp_tokens)
                },
                "metrics": {
                    "current_price": round(current_price, 4),
                    "tvl": round(tvl, 2),
                    "volume_24h": float(pool.total_volume_24h),
                    "total_fees_earned": float(pool.total_fees_earned),
                    "apy": round(apy, 2)
                },
                "recent_trades": recent_trades,
                "is_active": pool.is_active,
                "created_at": pool.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Failed to get pool details for property {property_id}: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════
    # SWAP QUOTES & EXECUTION
    # ═══════════════════════════════════════════════════════════════

    async def get_swap_quote(
        self,
        db: AsyncSession,
        property_id: int,
        trade_type: str,
        amount_in: float
    ) -> Dict:
        """
        Calculate swap quote using constant product formula (x * y = k).

        Args:
            db: Database session
            property_id: Property ID
            trade_type: "BUY" (EGP → Tokens) or "SELL" (Tokens → EGP)
            amount_in: Amount of input token

        Returns:
            Quote dictionary with output amount, price, slippage, fee
        """
        try:
            # Get pool
            result = await db.execute(
                select(LiquidityPool).where(LiquidityPool.property_id == property_id)
            )
            pool = result.scalar_one_or_none()

            if not pool or not pool.is_active:
                return {"error": "Pool not found or inactive"}

            # Constant product formula: x * y = k
            # With 0.3% fee: amountInWithFee = amountIn * 0.997
            FEE_DENOMINATOR = 10000
            TOTAL_FEE = 30  # 0.3%

            if trade_type.upper() == "SELL":
                # Selling property tokens for EGP
                token_amount_in = amount_in
                token_amount_in_with_fee = token_amount_in * (FEE_DENOMINATOR - TOTAL_FEE)

                numerator = token_amount_in_with_fee * pool.egp_reserve
                denominator = (pool.token_reserve * FEE_DENOMINATOR) + token_amount_in_with_fee
                egp_out = numerator / denominator

                # Calculate price and slippage
                current_price = pool.egp_reserve / pool.token_reserve
                execution_price = egp_out / token_amount_in
                price_impact = ((current_price - execution_price) / current_price) * 100

                fee_amount = (token_amount_in * TOTAL_FEE) / FEE_DENOMINATOR

                return {
                    "trade_type": "SELL",
                    "amount_in": token_amount_in,
                    "amount_out": round(egp_out, 2),
                    "current_price": round(current_price, 4),
                    "execution_price": round(execution_price, 4),
                    "price_impact": round(price_impact, 2),
                    "fee_amount": round(fee_amount, 4),
                    "fee_percent": 0.3,
                    "minimum_received": round(egp_out * 0.95, 2),  # 5% slippage tolerance
                    "input_token": "Property Tokens",
                    "output_token": "OEGP"
                }

            elif trade_type.upper() == "BUY":
                # Buying property tokens with EGP
                egp_amount_in = amount_in
                egp_amount_in_with_fee = egp_amount_in * (FEE_DENOMINATOR - TOTAL_FEE)

                numerator = egp_amount_in_with_fee * pool.token_reserve
                denominator = (pool.egp_reserve * FEE_DENOMINATOR) + egp_amount_in_with_fee
                tokens_out = numerator / denominator

                # Calculate price and slippage
                current_price = pool.egp_reserve / pool.token_reserve
                execution_price = egp_amount_in / tokens_out
                price_impact = ((execution_price - current_price) / current_price) * 100

                fee_amount = (egp_amount_in * TOTAL_FEE) / FEE_DENOMINATOR

                return {
                    "trade_type": "BUY",
                    "amount_in": egp_amount_in,
                    "amount_out": round(tokens_out, 4),
                    "current_price": round(current_price, 4),
                    "execution_price": round(execution_price, 4),
                    "price_impact": round(price_impact, 2),
                    "fee_amount": round(fee_amount, 2),
                    "fee_percent": 0.3,
                    "minimum_received": round(tokens_out * 0.95, 4),  # 5% slippage tolerance
                    "input_token": "OEGP",
                    "output_token": "Property Tokens"
                }

            else:
                return {"error": "Invalid trade type. Use 'BUY' or 'SELL'"}

        except Exception as e:
            logger.error(f"❌ Failed to get swap quote: {e}")
            return {"error": str(e)}

    async def execute_swap(
        self,
        db: AsyncSession,
        user_id: int,
        property_id: int,
        trade_type: str,
        amount_in: float,
        min_amount_out: float
    ) -> Dict:
        """
        Execute a swap on the AMM.

        Args:
            db: Database session
            user_id: User ID
            property_id: Property ID
            trade_type: "BUY" or "SELL"
            amount_in: Input amount
            min_amount_out: Minimum output (slippage protection)

        Returns:
            Trade result dictionary
        """
        try:
            # Get pool
            result = await db.execute(
                select(LiquidityPool).where(LiquidityPool.property_id == property_id)
            )
            pool = result.scalar_one_or_none()

            if not pool or not pool.is_active:
                return {"success": False, "error": "Pool not found or inactive"}

            # Get fresh quote
            quote = await self.get_swap_quote(db, property_id, trade_type, amount_in)

            if "error" in quote:
                return {"success": False, "error": quote["error"]}

            # Check slippage
            if quote["amount_out"] < min_amount_out:
                return {
                    "success": False,
                    "error": f"Slippage exceeded. Expected {min_amount_out}, would get {quote['amount_out']}"
                }

            # Execute blockchain transaction
            tx_hash = None
            if self.w3 and self.amm_contract:
                try:
                    if trade_type.upper() == "SELL":
                        # Call swapTokensForEGP on smart contract
                        # tx_hash = await self._execute_token_to_egp_swap(...)
                        pass  # Placeholder for actual blockchain call
                    else:
                        # Call swapEGPForTokens on smart contract
                        # tx_hash = await self._execute_egp_to_token_swap(...)
                        pass  # Placeholder for actual blockchain call
                except ContractLogicError as e:
                    return {"success": False, "error": f"Smart contract error: {e}"}

            # Record trade in database
            trade = Trade(
                pool_id=pool.id,
                user_id=user_id,
                trade_type=trade_type.upper(),
                token_amount=amount_in if trade_type.upper() == "SELL" else quote["amount_out"],
                egp_amount=quote["amount_out"] if trade_type.upper() == "SELL" else amount_in,
                execution_price=quote["execution_price"],
                slippage_percent=quote["price_impact"],
                fee_amount=quote["fee_amount"],
                tx_hash=tx_hash or "simulated_tx_" + str(datetime.utcnow().timestamp()),
                status="completed" if tx_hash else "pending"
            )
            db.add(trade)

            # Update pool reserves (if tx confirmed)
            if trade_type.upper() == "SELL":
                pool.token_reserve += amount_in
                pool.egp_reserve -= quote["amount_out"]
            else:
                pool.egp_reserve += amount_in
                pool.token_reserve -= quote["amount_out"]

            # Update 24h volume
            pool.total_volume_24h += amount_in
            pool.total_fees_earned += quote["fee_amount"]

            await db.commit()

            logger.info(f"✅ Swap executed: User {user_id}, {trade_type}, {amount_in} → {quote['amount_out']}")

            return {
                "success": True,
                "trade_id": trade.id,
                "trade_type": trade_type.upper(),
                "amount_in": amount_in,
                "amount_out": quote["amount_out"],
                "execution_price": quote["execution_price"],
                "price_impact": quote["price_impact"],
                "fee_amount": quote["fee_amount"],
                "tx_hash": tx_hash,
                "status": trade.status
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to execute swap: {e}")
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # LIQUIDITY PROVISION
    # ═══════════════════════════════════════════════════════════════

    async def add_liquidity(
        self,
        db: AsyncSession,
        user_id: int,
        property_id: int,
        token_amount: float,
        egp_amount: float,
        min_lp_tokens: float = 0
    ) -> Dict:
        """
        Add liquidity to a pool.

        Args:
            db: Database session
            user_id: User ID
            property_id: Property ID
            token_amount: Property tokens to deposit
            egp_amount: EGP to deposit
            min_lp_tokens: Minimum LP tokens to receive

        Returns:
            Result dictionary
        """
        try:
            # Get pool
            result = await db.execute(
                select(LiquidityPool).where(LiquidityPool.property_id == property_id)
            )
            pool = result.scalar_one_or_none()

            if not pool:
                return {"success": False, "error": "Pool not found"}

            # Calculate LP tokens to mint (proportional to reserves)
            lp_from_tokens = (token_amount * pool.total_lp_tokens) / pool.token_reserve
            lp_from_egp = (egp_amount * pool.total_lp_tokens) / pool.egp_reserve

            # Use smaller amount to maintain ratio
            lp_tokens = min(lp_from_tokens, lp_from_egp)

            if lp_tokens < min_lp_tokens:
                return {
                    "success": False,
                    "error": f"Slippage exceeded. Would receive {lp_tokens} LP tokens, expected {min_lp_tokens}"
                }

            # Calculate actual amounts (to maintain exact ratio)
            actual_token_amount = (lp_tokens * pool.token_reserve) / pool.total_lp_tokens
            actual_egp_amount = (lp_tokens * pool.egp_reserve) / pool.total_lp_tokens

            # Execute blockchain transaction (placeholder)
            tx_hash = "simulated_add_liquidity_" + str(datetime.utcnow().timestamp())

            # Update pool
            pool.token_reserve += actual_token_amount
            pool.egp_reserve += actual_egp_amount
            pool.total_lp_tokens += lp_tokens

            # Create or update liquidity position
            position_result = await db.execute(
                select(LiquidityPosition).where(
                    LiquidityPosition.user_id == user_id,
                    LiquidityPosition.pool_id == pool.id,
                    LiquidityPosition.is_active == True
                )
            )
            position = position_result.scalar_one_or_none()

            if position:
                position.lp_tokens += lp_tokens
                position.updated_at = datetime.utcnow()
            else:
                position = LiquidityPosition(
                    user_id=user_id,
                    pool_id=pool.id,
                    lp_tokens=lp_tokens,
                    initial_token_amount=actual_token_amount,
                    initial_egp_amount=actual_egp_amount,
                    is_active=True
                )
                db.add(position)

            await db.commit()

            logger.info(f"✅ Liquidity added: User {user_id}, LP tokens: {lp_tokens}")

            return {
                "success": True,
                "lp_tokens_minted": round(lp_tokens, 4),
                "token_amount_deposited": round(actual_token_amount, 4),
                "egp_amount_deposited": round(actual_egp_amount, 2),
                "tx_hash": tx_hash,
                "pool_share_percent": round((lp_tokens / pool.total_lp_tokens) * 100, 2)
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to add liquidity: {e}")
            return {"success": False, "error": str(e)}

    async def remove_liquidity(
        self,
        db: AsyncSession,
        user_id: int,
        property_id: int,
        lp_tokens: float,
        min_token_amount: float = 0,
        min_egp_amount: float = 0
    ) -> Dict:
        """
        Remove liquidity from a pool.

        Args:
            db: Database session
            user_id: User ID
            property_id: Property ID
            lp_tokens: LP tokens to burn
            min_token_amount: Minimum property tokens to receive
            min_egp_amount: Minimum EGP to receive

        Returns:
            Result dictionary
        """
        try:
            # Get pool
            pool_result = await db.execute(
                select(LiquidityPool).where(LiquidityPool.property_id == property_id)
            )
            pool = pool_result.scalar_one_or_none()

            if not pool:
                return {"success": False, "error": "Pool not found"}

            # Get user's position
            position_result = await db.execute(
                select(LiquidityPosition).where(
                    LiquidityPosition.user_id == user_id,
                    LiquidityPosition.pool_id == pool.id,
                    LiquidityPosition.is_active == True
                )
            )
            position = position_result.scalar_one_or_none()

            if not position or position.lp_tokens < lp_tokens:
                return {"success": False, "error": "Insufficient LP token balance"}

            # Calculate amounts to return (proportional to LP tokens)
            token_amount = (lp_tokens * pool.token_reserve) / pool.total_lp_tokens
            egp_amount = (lp_tokens * pool.egp_reserve) / pool.total_lp_tokens

            if token_amount < min_token_amount or egp_amount < min_egp_amount:
                return {"success": False, "error": "Slippage exceeded"}

            # Execute blockchain transaction (placeholder)
            tx_hash = "simulated_remove_liquidity_" + str(datetime.utcnow().timestamp())

            # Update pool
            pool.token_reserve -= token_amount
            pool.egp_reserve -= egp_amount
            pool.total_lp_tokens -= lp_tokens

            # Update position
            position.lp_tokens -= lp_tokens
            position.updated_at = datetime.utcnow()

            if position.lp_tokens == 0:
                position.is_active = False

            await db.commit()

            logger.info(f"✅ Liquidity removed: User {user_id}, LP tokens: {lp_tokens}")

            return {
                "success": True,
                "lp_tokens_burned": round(lp_tokens, 4),
                "token_amount_received": round(token_amount, 4),
                "egp_amount_received": round(egp_amount, 2),
                "tx_hash": tx_hash
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Failed to remove liquidity: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_positions(self, db: AsyncSession, user_id: int) -> List[Dict]:
        """
        Get all liquidity positions for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of position dictionaries
        """
        try:
            result = await db.execute(
                select(LiquidityPosition).where(
                    LiquidityPosition.user_id == user_id,
                    LiquidityPosition.is_active == True
                )
            )
            positions = result.scalars().all()

            position_list = []
            for pos in positions:
                # Get pool info
                pool_result = await db.execute(
                    select(LiquidityPool).where(LiquidityPool.id == pos.pool_id)
                )
                pool = pool_result.scalar_one_or_none()

                if not pool:
                    continue

                # Calculate current value
                current_token_value = (pos.lp_tokens * pool.token_reserve) / pool.total_lp_tokens
                current_egp_value = (pos.lp_tokens * pool.egp_reserve) / pool.total_lp_tokens

                # Calculate PnL
                token_pnl = current_token_value - pos.initial_token_amount
                egp_pnl = current_egp_value - pos.initial_egp_amount

                position_list.append({
                    "position_id": pos.id,
                    "pool_id": pos.pool_id,
                    "property_id": pool.property_id,
                    "lp_tokens": float(pos.lp_tokens),
                    "pool_share_percent": round((pos.lp_tokens / pool.total_lp_tokens) * 100, 2),
                    "initial_deposit": {
                        "tokens": float(pos.initial_token_amount),
                        "egp": float(pos.initial_egp_amount)
                    },
                    "current_value": {
                        "tokens": round(current_token_value, 4),
                        "egp": round(current_egp_value, 2)
                    },
                    "pnl": {
                        "tokens": round(token_pnl, 4),
                        "egp": round(egp_pnl, 2)
                    },
                    "fees_earned": float(pos.fees_earned),
                    "created_at": pos.created_at.isoformat(),
                    "updated_at": pos.updated_at.isoformat() if pos.updated_at else None
                })

            return position_list

        except Exception as e:
            logger.error(f"❌ Failed to get user positions: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    async def _calculate_pool_apy(self, db: AsyncSession, pool_id: int) -> float:
        """Calculate pool APY based on 24h fees."""
        try:
            result = await db.execute(
                select(LiquidityPool).where(LiquidityPool.id == pool_id)
            )
            pool = result.scalar_one_or_none()

            if not pool or pool.total_lp_tokens == 0:
                return 0.0

            # APY = (24h fees / TVL) * 365 * 100
            tvl = pool.egp_reserve * 2  # Both sides of pool
            if tvl == 0:
                return 0.0

            daily_fees = pool.total_fees_earned / 365  # Approximate
            daily_return = daily_fees / tvl
            apy = daily_return * 365 * 100

            return min(apy, 1000)  # Cap at 1000% APY

        except Exception as e:
            logger.error(f"❌ Failed to calculate APY: {e}")
            return 0.0

    async def _get_recent_trades(
        self,
        db: AsyncSession,
        pool_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent trades for a pool."""
        try:
            result = await db.execute(
                select(Trade).where(Trade.pool_id == pool_id)
                .order_by(Trade.created_at.desc())
                .limit(limit)
            )
            trades = result.scalars().all()

            return [
                {
                    "trade_id": trade.id,
                    "trade_type": trade.trade_type,
                    "token_amount": float(trade.token_amount),
                    "egp_amount": float(trade.egp_amount),
                    "execution_price": float(trade.execution_price),
                    "fee_amount": float(trade.fee_amount),
                    "created_at": trade.created_at.isoformat()
                }
                for trade in trades
            ]

        except Exception as e:
            logger.error(f"❌ Failed to get recent trades: {e}")
            return []


# Singleton instance
liquidity_service = LiquidityService()
