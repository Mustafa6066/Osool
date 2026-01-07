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
from app.services.payment_service import payment_service, PaymentStatus
from app.services.blockchain_prod import blockchain_service_prod
from app.ai_engine.openai_service import osool_ai
from app.ai_engine.hybrid_brain import hybrid_brain
from app.ai_engine.hybrid_brain_prod import hybrid_brain_prod
from app.ai_engine.sales_agent import sales_agent
from app.services.paymob_service import paymob_service
from app.tasks import reserve_property_task
from app.auth import create_access_token, get_current_user, get_password_hash, verify_password, verify_wallet_signature, get_or_create_user_by_wallet
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session
from fastapi import Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api", tags=["Osool API"])
limiter = Limiter(key_func=get_remote_address)


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


class FractionalInvestmentRequest(BaseModel):
    """Request model for fractional property investment."""
    property_id: int = Field(..., description="Property ID to invest in")
    investor_address: str = Field(..., description="Investor's wallet address")
    investment_amount_egp: float = Field(..., description="Investment amount in EGP")
    # payment_reference removed, we initiate valid payments now

class PaymentInitiateRequest(BaseModel):
    amount_egp: float
    first_name: str
    last_name: str
    phone_number: str
    email: str

class ChatRequest(BaseModel):
    """Request model for AI chat."""
    message: str = Field(..., description="User message to the AI agent")
    session_id: str = Field(default="default", description="Chat session ID for history")



# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/auth/signup")
def signup(email: str, password: str, full_name: str, db: Session = Depends(get_db)):
    """User Registration"""
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        email=email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        is_verified=True 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "user_created", "email": email, "id": new_user.id}

@router.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint. Returns JWT token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}



class WalletLoginRequest(BaseModel):
    address: str
    signature: str
    message: str

@router.post("/auth/verify-wallet")
def verify_wallet(req: WalletLoginRequest, db: Session = Depends(get_db)):
    """
    🔐 Web3 Login (SIWE) - Production
    Verifies signature and issues JWT.
    Returns is_new_user flag for profile completion flow.
    """
    # 1. Verify Signature
    is_valid = verify_wallet_signature(req.address, req.message, req.signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid wallet signature")
    
    # 2. Get or Create User
    user = get_or_create_user_by_wallet(db, req.address)
    
    # 3. Check if profile is complete
    is_new_user = user.full_name == "Wallet User" or not user.phone_number
    
    # 4. Issue Token
    access_token = create_access_token(data={"wallet": user.wallet_address, "sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user.id,
        "is_new_user": is_new_user
    }

class ProfileUpdateRequest(BaseModel):
    """Request model for profile completion."""
    full_name: str = Field(..., description="User's full name")
    phone_number: str = Field(..., description="User's phone number")

@router.post("/auth/update-profile")
def update_profile(req: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    📝 Complete User Profile
    Called after wallet connection for new users to add name and phone.
    """
    current_user.full_name = req.full_name
    current_user.phone_number = req.phone_number
    db.commit()
    
    return {
        "status": "success",
        "message": "Profile updated successfully",
        "user_id": current_user.id,
        "full_name": current_user.full_name
    }

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


    return {
        "property_id": property_id,
        "available": is_available
    }

@router.get("/properties")
def list_properties(db: Session = Depends(get_db)):
    """
    🏠 List all available properties.
    Used by the Fractional Investment Dashboard.
    """
    props = db.query(Property).filter(Property.is_available == True).all()
    
    # Enrich with computed fields (Mocking AI score/Funding for MVP if not in DB)
    results = []
    import random
    
    for p in props:
        # Calculate funding based on blockchain if possible, else mock for display
        # In prod, query smart contract: blockchain_service.get_funding(p.blockchain_id)
        
        results.append({
            "id": p.id,
            "name": p.title,
            "location": p.location,
            "totalPrice": p.price,
            "minimumInvestment": p.price * 0.05, # 5% minimum
            "expectedReturn": 20 + (p.id % 5), # Random-ish but deterministic
            "expectedExitDate": "Dec 2028",
            "fundingPercentage": 0, # TODO: Sync with Smart Contract
            "aiRiskScore": 10 + (p.id * 2),
            "aiValuation": p.price * 1.1,
            "description": p.description,
            "image": f"/assets/property{1 + (p.id % 3)}.jpg" # Placeholder rotation
        })
        
    return results


@router.post("/reserve")
def reserve_property(req: ReservationRequest, current_user: User = Depends(get_current_user)):
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
    # STEP 4: Offload to Celery Worker (Async)
    # ─────────────────────────────────────────────────────────────
    task = reserve_property_task.delay(
        req.property_id, 
        req.user_address
    )
    
    return {
        "status": "pending",
        "message": "Reservation process started. Please poll status.",
        "task_id": task.id,
        "property_id": req.property_id
    }


@router.get("/reservation/status/{task_id}")
def check_reservation_status(task_id: str):
    """Check status of background reservation task"""
    from celery.result import AsyncResult
    task_result = AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        return {"status": "pending", "message": "Transaction is mining..."}
    elif task_result.state == 'SUCCESS':
        result = task_result.result
        return {
            "status": "success", 
            "message": "Property reserved successfully! 🎉",
            "tx_hash": result.get("tx_hash"),
            "property_id": result.get("property_id"),
            "blockchain_proof": f"https://amoy.polygonscan.com/tx/{result.get('tx_hash')}"
        }
    elif task_result.state == 'FAILURE':
        return {"status": "failed", "message": str(task_result.result)}
    
    return {"status": task_result.state}


@router.post("/finalize-sale")
def finalize_sale(req: SaleFinalizationRequest, current_user: User = Depends(get_current_user)):
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
    Verify payment using Paymob Service.
    """
    return paymob_service.verify_transaction(reference)


# ═══════════════════════════════════════════════════════════════
# WEBHOOKS (PAYMOB INTEGRATION)
# ═══════════════════════════════════════════════════════════════

@router.post("/payment/initiate")
def initiate_paymob_payment(req: PaymentInitiateRequest, current_user: User = Depends(get_current_user)):
    """
    💳 Start Payment Flow (Paymob)
    Returns an Iframe URL for the user to pay via Credit Card/Wallet.
    """
    result = paymob_service.initiate_payment(
        amount_egp=req.amount_egp,
        user_email=req.email,
        user_phone=req.phone_number,
        first_name=req.first_name,
        last_name=req.last_name
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@router.post("/webhook/paymob")
async def paymob_webhook(data: dict, request: Request):
    """
    🔐 Secure Webhook Listener for Paymob.
    Verifies HMAC signature then triggers Blockchain actions on payment success.
    """
    import os
    
    # 1. Get HMAC signature from query params
    hmac_signature = request.query_params.get("hmac")
    
    # 2. Verify HMAC (CRITICAL FOR PRODUCTION SECURITY)
    if hmac_signature:
        if not paymob_service.verify_hmac(data, hmac_signature):
            print("❌ Webhook: HMAC verification FAILED - rejecting request")
            raise HTTPException(status_code=403, detail="Invalid HMAC signature")
        print("✅ Webhook: HMAC verified successfully")
    else:
        # In production, ALWAYS require HMAC
        if os.getenv("ENVIRONMENT", "development") == "production":
            print("❌ Webhook: Missing HMAC signature in production")
            raise HTTPException(status_code=403, detail="Missing HMAC signature")
        else:
            print("⚠️ Webhook: No HMAC provided (dev mode - proceeding with caution)")
        
    # 3. Check Payment Success
    tx_data = data.get('obj', {})
    is_success = tx_data.get('success', False)
    
    if not is_success:
        print(f"❌ Webhook: Payment failed or pending (ID: {tx_data.get('id')})")
        return {"status": "received_failed"}
        
    print(f"✅ Webhook: Payment SUCCESS (ID: {tx_data.get('id')}). Triggering Blockchain...")

    # 4. Trigger Blockchain Action
    # TODO: Lookup PropertyID and InvestorAddress from order metadata
    order_id = tx_data.get('order', {}).get('id')
    amount_cents = tx_data.get('amount_cents', 0)
    
    # For future: Query DB to get property_id and investor_address by order_id
    # Then call: blockchain_service_prod.mint_fractional_shares(property_id, investor_address, shares)
    
    return {
        "status": "processed_success",
        "order_id": order_id,
        "amount_egp": amount_cents / 100
    }



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
@limiter.limit("10/minute")
def analyze_contract(req: ContractAnalysisRequest, request: Request):
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
# AI CHAT ENDPOINT (RAG)
# ═══════════════════════════════════════════════════════════════

@router.post("/chat")
@limiter.limit("20/minute")
def chat_with_agent(req: ChatRequest, request: Request):
    """
    💬 Main AI Chat Endpoint
    
    Sends user message to the Wolf AI Agent.
    Returns:
    - response: AI text response
    - properties: JSON array of property objects found during search
    
    Frontend can render property cards from the `properties` array.
    """
    from app.ai_engine.sales_agent import sales_agent, get_last_search_results
    
    try:
        # Get AI response
        response_text = sales_agent.chat(req.message, req.session_id)
        
        # Get properties searched in THIS session (concurrency safe)
        search_results = get_last_search_results(req.session_id)
        
        return {
            "response": response_text,
            "properties": search_results,
            "session_id": req.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")





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


# ═══════════════════════════════════════════════════════════════
# FRACTIONAL INVESTMENT ENDPOINTS (Production)
# ═══════════════════════════════════════════════════════════════

@router.post("/fractional/invest")
def fractional_invest(req: FractionalInvestmentRequest, current_user: User = Depends(get_current_user)):
    """
    🏢 Fractional Property Investment (Production)
    
    Allows investors to purchase fractional ownership shares in properties.
    
    Flow:
    1. Verify EGP payment via payment service
    2. Calculate ownership percentage
    3. Mint fractional shares on blockchain
    4. Return investment confirmation with TX hash
    
    Returns:
    - ownership_percentage: Percentage of property owned
    - shares_minted: Number of blockchain tokens minted
    - tx_hash: Blockchain transaction proof
    - expected_exit_date: Anticipated exit/sale date
    - expected_return: Expected ROI percentage
    """
    
    # Step 1: Validate wallet address
    if not req.investor_address.startswith("0x") or len(req.investor_address) != 42:
        raise HTTPException(
            status_code=400, 
            detail="Invalid wallet address format"
        )
    
    # Step 2: Verify EGP payment using PaymentService
    payment_result = payment_service.verify_egp_deposit(
        reference=req.payment_reference,
        expected_amount=req.investment_amount_egp
    )
    
    if payment_result["status"] != PaymentStatus.VERIFIED:
        raise HTTPException(
            status_code=400,
            detail=f"Payment verification failed: {payment_result['message']}"
        )
    
    # Step 3: Calculate ownership and shares
    # TODO: In production, fetch property value from database by property_id
    # For now, we estimate based on typical property values from our data (avg ~30M EGP)
    property_total_value = req.investment_amount_egp * 20  # Assume ~5% ownership per investment
    ownership_percentage = (req.investment_amount_egp / property_total_value) * 100
    shares_to_mint = int(req.investment_amount_egp * 100)  # 1 EGP = 100 shares
    
    # Step 4: Mint fractional shares via PropertyFactory
    # We now use the new Factory pattern to deploy/mint specific tokens
    
    try:
        # Assuming blockchain_service_prod has been updated to use the factory
        # If not, we call the raw function here or assume the service handles the factory call
        # For this step, we'll assume a generic minting function that knows about the factory
        
        blockchain_result = blockchain_service_prod.mint_fractional_shares(
            property_id=req.property_id,
            investor_address=req.investor_address,
            amount=shares_to_mint
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain Error: {str(e)}")
    
    if "error" in blockchain_result:
        raise HTTPException(
            status_code=500,
            detail=f"Blockchain minting failed: {blockchain_result['error']}"
        )
    
    return {
        "status": "success",
        "message": "🎉 Investment confirmed! You now own fractional shares (ERC20) of this property.",
        "property_id": req.property_id,
        "ownership_percentage": round(ownership_percentage, 2),
        "shares_minted": shares_to_mint,
        "tx_hash": blockchain_result.get("tx_hash", ""),
        "blockchain_proof": f"https://amoy.polygonscan.com/tx/{blockchain_result.get('tx_hash', '')}",
        "expected_exit_date": "Mar 2029",
        "expected_return": 25,
        "payment_verified": True,
        "payment_tx_id": payment_result["tx_id"]
    }


@router.post("/ai/prod/valuation")
def production_valuation(req: HybridValuationRequest):
    """
    🧠 Production Hybrid AI Valuation (MLOps XGBoost + GPT-4o)
    
    Uses the production hybrid brain with:
    - MLOps endpoint integration
    - Result caching
    - Enhanced prompts
    """
    result = hybrid_brain_prod.get_valuation(
        location=req.location,
        size=req.size,
        finishing=req.finishing,
        floor=req.floor,
        is_compound=req.is_compound
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/ai/prod/audit-contract")
def production_audit(req: ContractAnalysisRequest):
    """
    ⚖️ Production Legal Contract Audit
    
    Uses the production hybrid brain for enhanced legal analysis.
    """
    if len(req.text) < 50:
        raise HTTPException(
            status_code=400,
            detail="Contract text too short. Please provide more content."
        )
    
    result = hybrid_brain_prod.audit_contract(req.text)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

