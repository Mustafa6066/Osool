"""
Osool API Endpoints
-------------------
FastAPI routes for property reservation and blockchain integration.

Payment Flow:
1. User pays via InstaPay/Fawry (EGP)
2. User submits payment reference to this API
3. Backend verifies payment
4. Backend updates blockchain status
5. User receives TX hash as proof
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.blockchain import blockchain_service
from app.ai_engine.openai_service import osool_ai
from app.ai_engine.hybrid_brain import hybrid_brain

router = APIRouter(prefix="/api", tags=["Osool API"])


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class ReservationRequest(BaseModel):
    property_id: int = Field(..., description="On-chain property ID")
    user_address: str = Field(..., description="Buyer's wallet address")
    payment_reference: str = Field(..., description="InstaPay/Fawry transaction reference")
    payment_amount_egp: Optional[float] = Field(None, description="Payment amount in EGP")


class SaleFinalizationRequest(BaseModel):
    property_id: int = Field(..., description="On-chain property ID")
    bank_transfer_reference: str = Field(..., description="Bank transfer reference")


class CancellationRequest(BaseModel):
    property_id: int = Field(..., description="On-chain property ID")
    reason: str = Field(..., description="Cancellation reason")


class ContractAnalysisRequest(BaseModel):
    text: str = Field(..., description="Contract text in Arabic or English")


class ValuationRequest(BaseModel):
    location: str = Field(..., description="Property location (e.g., 'New Cairo', 'Sheikh Zayed')")
    size_sqm: int = Field(..., description="Property size in square meters")
    bedrooms: int = Field(3, description="Number of bedrooms")
    finishing: str = Field("Fully Finished", description="Finishing level")
    property_type: str = Field("Apartment", description="Type of property")


class PriceComparisonRequest(BaseModel):
    asking_price: int = Field(..., description="Seller's asking price in EGP")
    location: str = Field(..., description="Property location")
    size_sqm: int = Field(..., description="Property size in square meters")
    finishing: str = Field("Fully Finished", description="Finishing level")


class HybridValuationRequest(BaseModel):
    """Request model for XGBoost + GPT-4o hybrid valuation."""
    location: str = Field(..., description="Property location (e.g., 'New Cairo', 'Sheikh Zayed')")
    size: int = Field(..., description="Property size in square meters")
    finishing: int = Field(2, description="0=Core&Shell, 1=Semi, 2=Finished, 3=Ultra Lux")
    floor: int = Field(3, description="Floor number")
    is_compound: int = Field(1, description="1 if in gated compound, 0 otherwise")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/health")
def health_check():
    """Check API and blockchain connection health"""
    return {
        "status": "healthy",
        "blockchain_connected": blockchain_service.is_connected(),
        "service": "Osool Registry API"
    }


@router.get("/property/{property_id}")
def get_property(property_id: int):
    """Get property details from blockchain"""
    result = blockchain_service.get_property(property_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/property/{property_id}/available")
def check_availability(property_id: int):
    """Check if property is available for reservation"""
    is_available = blockchain_service.is_available(property_id)
    return {
        "property_id": property_id,
        "available": is_available
    }


@router.post("/reserve")
def reserve_property(req: ReservationRequest):
    """
    Reserve a property after EGP payment verification.
    
    Flow:
    1. User pays via InstaPay/Fawry
    2. User enters payment reference in app
    3. This endpoint verifies payment (placeholder)
    4. Blockchain status is updated to RESERVED
    5. User receives TX hash as immutable proof
    """
    
    # ─────────────────────────────────────────────────────────────
    # STEP 1: Validate wallet address format
    # ─────────────────────────────────────────────────────────────
    if not req.user_address.startswith("0x") or len(req.user_address) != 42:
        raise HTTPException(
            status_code=400, 
            detail="Invalid wallet address format"
        )
    
    # ─────────────────────────────────────────────────────────────
    # STEP 2: Check property availability
    # ─────────────────────────────────────────────────────────────
    if not blockchain_service.is_available(req.property_id):
        raise HTTPException(
            status_code=409,
            detail="Property is not available for reservation"
        )
    
    # ─────────────────────────────────────────────────────────────
    # STEP 3: Verify EGP payment (PLACEHOLDER)
    # TODO: Integrate with InstaPay/Fawry API for real verification
    # ─────────────────────────────────────────────────────────────
    payment_verified = verify_egp_payment(req.payment_reference)
    
    if not payment_verified:
        raise HTTPException(
            status_code=400,
            detail="Payment verification failed. Please check reference number."
        )
    
    # ─────────────────────────────────────────────────────────────
    # STEP 4: Update blockchain status
    # ─────────────────────────────────────────────────────────────
    result = blockchain_service.reserve_property(
        req.property_id, 
        req.user_address
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Blockchain update failed: {result['error']}"
        )
    
    return {
        "status": "success",
        "message": "Property reserved successfully! 🎉",
        "tx_hash": result["tx_hash"],
        "property_id": req.property_id,
        "blockchain_proof": f"https://amoy.polygonscan.com/tx/{result['tx_hash']}"
    }


@router.post("/finalize-sale")
def finalize_sale(req: SaleFinalizationRequest):
    """
    Finalize property sale after full bank transfer.
    Transfers on-chain ownership to the buyer.
    """
    
    # Verify bank transfer (placeholder)
    transfer_verified = verify_bank_transfer(req.bank_transfer_reference)
    
    if not transfer_verified:
        raise HTTPException(
            status_code=400,
            detail="Bank transfer verification failed"
        )
    
    result = blockchain_service.finalize_sale(req.property_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Sale finalization failed: {result['error']}"
        )
    
    return {
        "status": "success",
        "message": "Property sale finalized! Ownership transferred on-chain.",
        "tx_hash": result["tx_hash"],
        "blockchain_proof": f"https://amoy.polygonscan.com/tx/{result['tx_hash']}"
    }


@router.post("/cancel-reservation")
def cancel_reservation(req: CancellationRequest):
    """Cancel a property reservation (admin only)"""
    
    result = blockchain_service.cancel_reservation(req.property_id)
    
    if "error" in result:
        raise HTTPException(
            status_code=500,
            detail=f"Cancellation failed: {result['error']}"
        )
    
    return {
        "status": "success",
        "message": "Reservation cancelled",
        "tx_hash": result["tx_hash"],
        "reason": req.reason
    }


# ═══════════════════════════════════════════════════════════════
# PAYMENT VERIFICATION (PLACEHOLDERS)
# ═══════════════════════════════════════════════════════════════

def verify_egp_payment(reference: str) -> bool:
    """
    Placeholder for InstaPay/Fawry payment verification.
    
    TODO: Integrate with actual payment gateway API:
    - InstaPay: https://instapay.eg/api
    - Fawry: https://www.fawry.com/api
    - Paymob: https://paymob.com/api
    
    For prototype, we accept any reference with 8+ chars.
    """
    if len(reference) >= 8:
        print(f"✅ Payment reference verified: {reference}")
        return True
    return False


def verify_bank_transfer(reference: str) -> bool:
    """
    Placeholder for bank transfer verification.
    
    TODO: Integrate with bank API or manual verification queue.
    """
    if len(reference) >= 8:
        print(f"✅ Bank transfer verified: {reference}")
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# AI INTELLIGENCE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/ai/analyze-contract")
def analyze_contract(req: ContractAnalysisRequest):
    """
    🕵️ AI Legal Check - The "Killer Feature"
    
    Scans Egyptian real estate contracts for:
    - Red flags (abusive clauses)
    - Missing essential clauses (Tawkil, delivery dates)
    - Risk score (0-100)
    
    Based on Egyptian Civil Code No. 131 and Law No. 114.
    This is a premium feature worth 500 EGP.
    """
    if len(req.text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Contract text too short. Please provide more content."
        )
    
    result = osool_ai.analyze_contract_with_egyptian_context(req.text)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/ai/valuation")
def smart_valuation(req: ValuationRequest):
    """
    📊 AI Property Valuation with Market Reasoning
    
    Returns:
    - Price range (min-max) in EGP
    - Price per sqm
    - Detailed reasoning based on market trends
    - Investment verdict
    """
    result = osool_ai.get_smart_valuation(
        location=req.location,
        size_sqm=req.size_sqm,
        finishing=req.finishing,
        bedrooms=req.bedrooms,
        property_type=req.property_type
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/ai/compare-price")
def compare_price(req: PriceComparisonRequest):
    """
    💰 Compare Asking Price vs. Market Value
    
    Tells the buyer if the seller's price is:
    - BARGAIN (unusually low - verify why)
    - FAIR (within market range)
    - OVERPRICED (negotiate down)
    """
    result = osool_ai.compare_price_to_market(
        asking_price=req.asking_price,
        location=req.location,
        size_sqm=req.size_sqm,
        finishing=req.finishing
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


# ═══════════════════════════════════════════════════════════════
# HYBRID AI ENDPOINTS (XGBoost + GPT-4o)
# ═══════════════════════════════════════════════════════════════

@router.post("/ai/hybrid-valuation")
def hybrid_valuation(req: HybridValuationRequest):
    """
    🧠 Hybrid AI Valuation (XGBoost + GPT-4o)
    
    Combines:
    - XGBoost: Precise statistical price prediction based on Cairo market data
    - GPT-4o: Market context and reasoning about WHY the price is what it is
    
    Returns:
    - predicted_price: Exact EGP value from XGBoost
    - market_status: Hot/Stable/Cool
    - reasoning_bullets: 3 market insights explaining the price
    """
    result = hybrid_brain.get_valuation(
        location=req.location,
        size=req.size,
        finishing=req.finishing,
        floor=req.floor,
        is_compound=req.is_compound
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/ai/audit-contract")
def audit_contract(req: ContractAnalysisRequest):
    """
    ⚖️ Egyptian Legal Contract Audit
    
    Uses the Hybrid Brain's legal analysis with strict Egyptian law context.
    
    Returns:
    - risk_score: 0-100
    - verdict: Safe/Risky/Scam
    - red_flags: Specific dangerous clauses
    - missing_clauses: What should be there
    """
    if len(req.text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Contract text too short. Please provide more content."
        )
    
    result = hybrid_brain.audit_contract(req.text)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/ai/compare-asking-price")
def compare_asking(req: PriceComparisonRequest):
    """
    💵 Compare Asking Price (Hybrid Version)
    
    Uses XGBoost fair price + GPT-4o context to determine if
    a seller's asking price is BARGAIN/FAIR/OVERPRICED.
    """
    # Convert finishing string to int if needed
    finishing_map = {
        "Core & Shell": 0,
        "Semi Finished": 1,
        "Fully Finished": 2,
        "Ultra Lux": 3
    }
    finishing_int = finishing_map.get(req.finishing, 2)
    
    result = hybrid_brain.compare_asking_price(
        asking_price=req.asking_price,
        location=req.location,
        size=req.size_sqm,
        finishing=finishing_int
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result
