"""
Osool Liquidity Marketplace API Endpoints
------------------------------------------
REST API for AMM trading and liquidity provision.

Phase 6: Osool Production Transformation
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services.liquidity_service import liquidity_service

router = APIRouter(prefix="/api/liquidity", tags=["Liquidity Marketplace"])
limiter = Limiter(key_func=get_remote_address)


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class SwapQuoteRequest(BaseModel):
    """Request model for swap quote."""
    property_id: int = Field(..., description="Property ID")
    trade_type: str = Field(..., description="'BUY' or 'SELL'")
    amount_in: float = Field(..., gt=0, description="Amount of input token")


class SwapExecuteRequest(BaseModel):
    """Request model for executing a swap."""
    property_id: int = Field(..., description="Property ID")
    trade_type: str = Field(..., description="'BUY' or 'SELL'")
    amount_in: float = Field(..., gt=0, description="Amount of input token")
    min_amount_out: float = Field(..., gt=0, description="Minimum output (slippage protection)")


class AddLiquidityRequest(BaseModel):
    """Request model for adding liquidity."""
    property_id: int = Field(..., description="Property ID")
    token_amount: float = Field(..., gt=0, description="Property tokens to deposit")
    egp_amount: float = Field(..., gt=0, description="EGP to deposit")
    min_lp_tokens: float = Field(default=0, ge=0, description="Minimum LP tokens to receive")


class RemoveLiquidityRequest(BaseModel):
    """Request model for removing liquidity."""
    property_id: int = Field(..., description="Property ID")
    lp_tokens: float = Field(..., gt=0, description="LP tokens to burn")
    min_token_amount: float = Field(default=0, ge=0, description="Minimum tokens to receive")
    min_egp_amount: float = Field(default=0, ge=0, description="Minimum EGP to receive")


# ═══════════════════════════════════════════════════════════════
# POOL ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/pools")
async def get_all_pools(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all liquidity pools.

    Returns:
        List of pools with current price, volume, APY
    """
    try:
        pools = await liquidity_service.get_all_pools(db, skip, limit, active_only)
        return {
            "success": True,
            "count": len(pools),
            "pools": pools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pools/{property_id}")
async def get_pool_details(
    property_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific pool.

    Args:
        property_id: Property ID

    Returns:
        Pool details with reserves, metrics, recent trades
    """
    try:
        pool_details = await liquidity_service.get_pool_details(db, property_id)

        if not pool_details:
            raise HTTPException(status_code=404, detail="Pool not found")

        return {
            "success": True,
            "pool": pool_details
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# SWAP ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/quote")
@limiter.limit("60/minute")  # Generous limit for quotes
async def get_swap_quote(
    request: Request,
    quote_request: SwapQuoteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a quote for swapping tokens.

    No authentication required (public quotes).

    Request Body:
        - property_id: Property ID
        - trade_type: "BUY" (EGP → Tokens) or "SELL" (Tokens → EGP)
        - amount_in: Amount of input token

    Returns:
        Quote with output amount, price, slippage, fee
    """
    try:
        quote = await liquidity_service.get_swap_quote(
            db,
            quote_request.property_id,
            quote_request.trade_type,
            quote_request.amount_in
        )

        if "error" in quote:
            raise HTTPException(status_code=400, detail=quote["error"])

        return {
            "success": True,
            "quote": quote
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/swap")
@limiter.limit("10/minute")  # Stricter limit for actual swaps
async def execute_swap(
    request: Request,
    swap_request: SwapExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a swap on the AMM.

    Requires authentication.

    Request Body:
        - property_id: Property ID
        - trade_type: "BUY" or "SELL"
        - amount_in: Input amount
        - min_amount_out: Minimum output (slippage protection)

    Returns:
        Trade result with execution details and transaction hash

    Flow:
        1. Validate user has sufficient balance (OEGP or property tokens)
        2. Get fresh quote
        3. Check slippage protection
        4. Execute blockchain transaction
        5. Record trade in database
        6. Return result
    """
    try:
        result = await liquidity_service.execute_swap(
            db,
            current_user.id,
            swap_request.property_id,
            swap_request.trade_type,
            swap_request.amount_in,
            swap_request.min_amount_out
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Swap failed"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# LIQUIDITY PROVISION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/add")
@limiter.limit("10/minute")
async def add_liquidity(
    request: Request,
    add_request: AddLiquidityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add liquidity to a pool.

    Requires authentication.

    Request Body:
        - property_id: Property ID
        - token_amount: Property tokens to deposit
        - egp_amount: OEGP to deposit
        - min_lp_tokens: Minimum LP tokens to receive (optional)

    Returns:
        Result with LP tokens minted and pool share

    Important:
        - Amounts must maintain pool ratio
        - User receives LP tokens representing their share
        - LP tokens earn 0.25% of all trading fees
    """
    try:
        result = await liquidity_service.add_liquidity(
            db,
            current_user.id,
            add_request.property_id,
            add_request.token_amount,
            add_request.egp_amount,
            add_request.min_lp_tokens
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to add liquidity"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove")
@limiter.limit("10/minute")
async def remove_liquidity(
    request: Request,
    remove_request: RemoveLiquidityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove liquidity from a pool.

    Requires authentication.

    Request Body:
        - property_id: Property ID
        - lp_tokens: LP tokens to burn
        - min_token_amount: Minimum tokens to receive (optional)
        - min_egp_amount: Minimum EGP to receive (optional)

    Returns:
        Result with tokens and EGP received

    Important:
        - Burns LP tokens proportionally
        - Returns both property tokens and EGP
        - Fees earned are included in returned amounts
    """
    try:
        result = await liquidity_service.remove_liquidity(
            db,
            current_user.id,
            remove_request.property_id,
            remove_request.lp_tokens,
            remove_request.min_token_amount,
            remove_request.min_egp_amount
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to remove liquidity"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_user_positions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's liquidity positions.

    Requires authentication.

    Returns:
        List of user's LP positions with:
        - Pool information
        - LP tokens held
        - Current value
        - PnL (Profit and Loss)
        - Fees earned
    """
    try:
        positions = await liquidity_service.get_user_positions(db, current_user.id)

        return {
            "success": True,
            "count": len(positions),
            "positions": positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/stats")
async def get_marketplace_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overall marketplace statistics.

    Returns:
        - Total pools
        - Total TVL (Total Value Locked)
        - 24h volume across all pools
        - Total fees earned
    """
    try:
        pools = await liquidity_service.get_all_pools(db, skip=0, limit=1000, active_only=True)

        total_tvl = sum(pool["egp_reserve"] * 2 for pool in pools)
        total_volume_24h = sum(pool["volume_24h"] for pool in pools)
        total_fees = sum(pool["total_fees_earned"] for pool in pools)
        avg_apy = sum(pool["apy"] for pool in pools) / len(pools) if pools else 0

        return {
            "success": True,
            "stats": {
                "total_pools": len(pools),
                "total_tvl": round(total_tvl, 2),
                "volume_24h": round(total_volume_24h, 2),
                "total_fees_earned": round(total_fees, 2),
                "average_apy": round(avg_apy, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-pools")
async def get_hot_pools(
    limit: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """
    Get hottest (highest volume) pools.

    Args:
        limit: Number of pools to return (default 5)

    Returns:
        List of top pools by 24h volume
    """
    try:
        pools = await liquidity_service.get_all_pools(db, skip=0, limit=100, active_only=True)

        # Sort by 24h volume
        hot_pools = sorted(pools, key=lambda p: p["volume_24h"], reverse=True)[:limit]

        return {
            "success": True,
            "count": len(hot_pools),
            "pools": hot_pools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
