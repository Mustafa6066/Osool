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
            self.amm_contract = None
            self.oegp_contract = None
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self.account = self.w3.eth.account.from_key(self.private_key)

            # Load contract ABIs and addresses
            self.amm_address = os.getenv("OSOOL_AMM_ADDRESS")
            self.oegp_address = os.getenv("OSOOL_OEGP_ADDRESS")

            # Load contract ABIs from compiled artifacts
            self.amm_contract = None
            self.oegp_contract = None
            self._load_contract_abis()

            if self.amm_contract and self.oegp_contract:
                logger.info(f"✅ Liquidity Service initialized (Chain: {self.chain_id}, AMM: {self.amm_address})")
            else:
                logger.warning(f"⚠️ Contract ABIs not loaded. Run 'npx hardhat compile' first.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Web3: {e}")
            self.w3 = None
            self.amm_contract = None
            self.oegp_contract = None

    def _load_contract_abis(self):
        """
        Load contract ABIs from Hardhat compilation artifacts.

        This function reads the compiled contract JSON files from:
        - contracts/artifacts/contracts/OsoolLiquidityAMM.sol/OsoolLiquidityAMM.json
        - contracts/artifacts/contracts/OsoolEGPStablecoin.sol/OsoolEGPStablecoin.json

        Prerequisites:
        1. Run 'npx hardhat compile' to generate artifacts
        2. Set OSOOL_AMM_ADDRESS and OSOOL_OEGP_ADDRESS in .env
        """
        import json
        from pathlib import Path

        try:
            # Get project root (assuming this file is in backend/app/services/)
            project_root = Path(__file__).parent.parent.parent.parent
            artifacts_dir = project_root / "contracts" / "artifacts" / "contracts"

            # Load AMM contract ABI
            amm_artifact_path = artifacts_dir / "OsoolLiquidityAMM.sol" / "OsoolLiquidityAMM.json"
            if amm_artifact_path.exists() and self.amm_address:
                with open(amm_artifact_path, 'r') as f:
                    amm_artifact = json.load(f)
                    self.amm_contract = self.w3.eth.contract(
                        address=self.w3.to_checksum_address(self.amm_address),
                        abi=amm_artifact['abi']
                    )
                    logger.info(f"✅ AMM contract loaded: {self.amm_address}")
            else:
                logger.warning(f"⚠️ AMM artifact not found at {amm_artifact_path}")

            # Load OEGP stablecoin contract ABI
            oegp_artifact_path = artifacts_dir / "OsoolEGPStablecoin.sol" / "OsoolEGPStablecoin.json"
            if oegp_artifact_path.exists() and self.oegp_address:
                with open(oegp_artifact_path, 'r') as f:
                    oegp_artifact = json.load(f)
                    self.oegp_contract = self.w3.eth.contract(
                        address=self.w3.to_checksum_address(self.oegp_address),
                        abi=oegp_artifact['abi']
                    )
                    logger.info(f"✅ OEGP contract loaded: {self.oegp_address}")
            else:
                logger.warning(f"⚠️ OEGP artifact not found at {oegp_artifact_path}")

        except Exception as e:
            logger.error(f"❌ Failed to load contract ABIs: {e}")
            logger.info("💡 Solution: Run 'npx hardhat compile' in project root")

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

            # ═══════════════════════════════════════════════════════════════
            # TWO-PHASE COMMIT: Blockchain FIRST, then Database
            # ═══════════════════════════════════════════════════════════════
            # This ensures database and blockchain stay synchronized.
            # If blockchain fails, we don't update the database.
            # ═══════════════════════════════════════════════════════════════

            tx_hash = None
            tx_confirmed = False

            if self.w3 and self.amm_contract:
                # Get user's wallet address (you'll need to fetch this from User model)
                # For now, using admin account as relayer
                user_address = self.account.address

                try:
                    # PHASE 1: Verify user has sufficient balance on-chain
                    if trade_type.upper() == "SELL":
                        # User is selling property tokens for OEGP
                        balance_ok, balance_msg = await self._verify_user_balance(
                            user_address,
                            "PROPERTY_TOKEN",
                            amount_in,
                            property_id
                        )
                        if not balance_ok:
                            return {"success": False, "error": f"Insufficient balance: {balance_msg}"}

                        # Execute swap on blockchain
                        tx_hash = await self._execute_token_to_egp_swap(
                            property_id,
                            amount_in,
                            min_amount_out,
                            user_address
                        )
                    else:
                        # User is buying property tokens with OEGP
                        balance_ok, balance_msg = await self._verify_user_balance(
                            user_address,
                            "OEGP",
                            amount_in
                        )
                        if not balance_ok:
                            return {"success": False, "error": f"Insufficient balance: {balance_msg}"}

                        # Execute swap on blockchain
                        tx_hash = await self._execute_egp_to_token_swap(
                            property_id,
                            amount_in,
                            min_amount_out,
                            user_address
                        )

                    if not tx_hash:
                        return {"success": False, "error": "Blockchain transaction failed"}

                    # PHASE 2: Wait for transaction confirmation
                    logger.info(f"⏳ Waiting for confirmation: {tx_hash}")
                    tx_confirmed, receipt = await self._monitor_transaction(tx_hash, timeout=180)

                    if not tx_confirmed:
                        return {
                            "success": False,
                            "error": "Transaction failed or timed out",
                            "tx_hash": tx_hash
                        }

                    logger.info(f"✅ Transaction confirmed in block {receipt['blockNumber']}")

                except ContractLogicError as e:
                    return {"success": False, "error": f"Smart contract error: {str(e)}"}
                except Exception as e:
                    logger.error(f"❌ Blockchain execution failed: {e}")
                    return {"success": False, "error": f"Blockchain error: {str(e)}"}
            else:
                # Blockchain not configured - simulation mode for development
                logger.warning("⚠️ Blockchain not configured. Running in SIMULATION mode.")
                tx_hash = "simulated_tx_" + str(datetime.utcnow().timestamp())
                tx_confirmed = True  # Simulate success for development

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

    # ═══════════════════════════════════════════════════════════════
    # BLOCKCHAIN INTEGRATION (Phase 2: Production Readiness)
    # ═══════════════════════════════════════════════════════════════

    async def _verify_user_balance(
        self,
        user_address: str,
        token_type: str,
        amount: float,
        property_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Verify user has sufficient balance on-chain before executing swap.

        This is a CRITICAL security function from the walkthrough requirements:
        "verify user token balance on-chain before allowing a swap"

        Args:
            user_address: User's wallet address
            token_type: "OEGP" or "PROPERTY_TOKEN"
            amount: Amount to verify (in human-readable units)
            property_id: Required if token_type is "PROPERTY_TOKEN"

        Returns:
            Tuple of (success: bool, message: str)

        Raises:
            None - Returns error message instead
        """
        if not self.w3 or not self.oegp_contract or not self.amm_contract:
            return False, "Blockchain not initialized. Run 'npx hardhat compile' first."

        try:
            checksum_address = self.w3.to_checksum_address(user_address)

            if token_type.upper() == "OEGP":
                # Check OEGP stablecoin balance
                balance_wei = self.oegp_contract.functions.balanceOf(checksum_address).call()
                balance = self.w3.from_wei(balance_wei, 'ether')

                if balance >= amount:
                    logger.info(f"✅ User {user_address[:10]}... has {balance} OEGP (needs {amount})")
                    return True, f"Sufficient balance: {balance} OEGP"
                else:
                    logger.warning(f"⚠️ Insufficient OEGP: User has {balance}, needs {amount}")
                    return False, f"Insufficient OEGP balance. Have: {balance}, Need: {amount}"

            elif token_type.upper() == "PROPERTY_TOKEN":
                if not property_id:
                    return False, "Property ID required for property token balance check"

                # Check property token balance (ERC1155)
                # Note: Property tokens use ERC1155, so we need to call balanceOf with tokenId
                balance = self.amm_contract.functions.balanceOf(checksum_address, property_id).call()

                if balance >= amount:
                    logger.info(f"✅ User {user_address[:10]}... has {balance} tokens for property {property_id}")
                    return True, f"Sufficient balance: {balance} tokens"
                else:
                    logger.warning(f"⚠️ Insufficient tokens: User has {balance}, needs {amount}")
                    return False, f"Insufficient property token balance. Have: {balance}, Need: {amount}"

            else:
                return False, f"Invalid token type: {token_type}. Must be 'OEGP' or 'PROPERTY_TOKEN'"

        except Exception as e:
            logger.error(f"❌ Balance verification failed: {e}")
            return False, f"Balance check error: {str(e)}"

    async def _execute_token_to_egp_swap(
        self,
        property_id: int,
        token_amount: float,
        min_egp_out: float,
        user_address: str
    ) -> Optional[str]:
        """
        Execute swapTokensForEGP transaction on blockchain.

        Calls the smart contract function:
        swapTokensForEGP(uint256 propertyId, uint256 tokenAmount, uint256 minEGPOut)

        Args:
            property_id: Property token ID
            token_amount: Amount of property tokens to swap
            min_egp_out: Minimum OEGP to receive (slippage protection)
            user_address: User's wallet address

        Returns:
            Transaction hash (str) if successful, None if failed

        Raises:
            ContractLogicError: If smart contract reverts
        """
        if not self.w3 or not self.amm_contract:
            raise ValueError("Blockchain not initialized")

        try:
            # Convert amounts to wei (assuming 18 decimals)
            token_amount_wei = self.w3.to_wei(token_amount, 'ether')
            min_egp_out_wei = self.w3.to_wei(min_egp_out, 'ether')

            # Build transaction
            tx = self.amm_contract.functions.swapTokensForEGP(
                property_id,
                token_amount_wei,
                min_egp_out_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300000,  # Estimated gas limit
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.chain_id
            })

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = self.w3.to_hex(tx_hash)

            logger.info(f"✅ Swap transaction sent: {tx_hash_hex}")
            return tx_hash_hex

        except ContractLogicError as e:
            logger.error(f"❌ Smart contract reverted: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Swap execution failed: {e}")
            return None

    async def _execute_egp_to_token_swap(
        self,
        property_id: int,
        egp_amount: float,
        min_tokens_out: float,
        user_address: str
    ) -> Optional[str]:
        """
        Execute swapEGPForTokens transaction on blockchain.

        Calls the smart contract function:
        swapEGPForTokens(uint256 propertyId, uint256 egpAmount, uint256 minTokensOut)

        Args:
            property_id: Property token ID
            egp_amount: Amount of OEGP to swap
            min_tokens_out: Minimum property tokens to receive (slippage protection)
            user_address: User's wallet address

        Returns:
            Transaction hash (str) if successful, None if failed

        Raises:
            ContractLogicError: If smart contract reverts
        """
        if not self.w3 or not self.amm_contract:
            raise ValueError("Blockchain not initialized")

        try:
            # Convert amounts to wei
            egp_amount_wei = self.w3.to_wei(egp_amount, 'ether')
            min_tokens_out_wei = self.w3.to_wei(min_tokens_out, 'ether')

            # Build transaction
            tx = self.amm_contract.functions.swapEGPForTokens(
                property_id,
                egp_amount_wei,
                min_tokens_out_wei
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.chain_id
            })

            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = self.w3.to_hex(tx_hash)

            logger.info(f"✅ Swap transaction sent: {tx_hash_hex}")
            return tx_hash_hex

        except ContractLogicError as e:
            logger.error(f"❌ Smart contract reverted: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Swap execution failed: {e}")
            return None

    async def _monitor_transaction(
        self,
        tx_hash: str,
        timeout: int = 120
    ) -> Tuple[bool, Optional[dict]]:
        """
        Monitor blockchain transaction until confirmed or timeout.

        Polls for transaction receipt every 2 seconds.
        Handles stuck transactions (low gas) and network issues.

        Args:
            tx_hash: Transaction hash to monitor
            timeout: Maximum wait time in seconds (default: 120s = 2 minutes)

        Returns:
            Tuple of (success: bool, receipt: dict or None)

        Example:
            success, receipt = await self._monitor_transaction(tx_hash, timeout=180)
            if success:
                print(f"Confirmed in block {receipt['blockNumber']}")
            else:
                print("Transaction failed or timed out")
        """
        if not self.w3:
            return False, None

        import asyncio
        from datetime import datetime, timedelta

        try:
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(seconds=timeout)

            logger.info(f"⏳ Monitoring transaction: {tx_hash}")

            while datetime.utcnow() < end_time:
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx_hash)

                    if receipt:
                        # Transaction confirmed
                        if receipt['status'] == 1:
                            elapsed = (datetime.utcnow() - start_time).total_seconds()
                            logger.info(f"✅ Transaction confirmed in {elapsed:.1f}s (Block: {receipt['blockNumber']})")
                            return True, receipt
                        else:
                            logger.error(f"❌ Transaction reverted: {tx_hash}")
                            return False, receipt

                except Exception:
                    # Receipt not yet available, continue polling
                    pass

                # Wait 2 seconds before next poll
                await asyncio.sleep(2)

            # Timeout reached
            logger.warning(f"⚠️ Transaction monitoring timed out after {timeout}s: {tx_hash}")
            return False, None

        except Exception as e:
            logger.error(f"❌ Transaction monitoring error: {e}")
            return False, None


# Singleton instance
liquidity_service = LiquidityService()
