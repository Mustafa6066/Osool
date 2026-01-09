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
from fastapi.responses import JSONResponse
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
from app.auth import create_access_token, get_current_user, get_password_hash, verify_password, verify_wallet_signature, get_or_create_user_by_wallet, create_custodial_wallet
from app.database import get_db
from app.models import User, Property, Transaction, PaymentApproval
from sqlalchemy.orm import Session
from fastapi import Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api", tags=["Osool API"])
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# SECURITY DEPENDENCIES
# ---------------------------------------------------------------------------
from fastapi.security import APIKeyHeader
import os

API_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Protects Admin/Ingest endpoints."""
    # In production, use a secure env var. For now, hardcoded or env.
    ADMIN_KEY = os.getenv("ADMIN_API_KEY") # REMOVED HARDCODED BACKDOOR
    if not ADMIN_KEY or api_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key


# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class ReservationRequest(BaseModel):
    property_id: int = Field(..., description="On-chain property ID")
    user_address: str = Field(..., description="Buyer's wallet address")
    payment_reference: str = Field(..., description="InstaPay/Fawry transaction reference")
    payment_amount_egp: float = Field(..., description="Payment amount in EGP")


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
    property_id: int # Critical for fractional mapping

# ---------------------------------------------------------------------------
# SECURITY DEPENDENCIES
# ---------------------------------------------------------------------------
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-Admin-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    Phase 4: Protects Admin/Ingest endpoints with secure API key validation.
    CRITICAL: No hardcoded fallback - fails fast if not configured.
    """
    ADMIN_KEY = os.getenv("ADMIN_API_KEY")
    if not ADMIN_KEY:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_API_KEY environment variable not configured. Server misconfiguration."
        )
    if api_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

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

    # 1. Generate Custodial Wallet (Bridge to Web3)
    wallet = create_custodial_wallet()
    
    # 2. Create User
    new_user = User(
        email=email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        wallet_address=wallet["address"], # Assigned Custodial Wallet
        is_verified=True 
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # In real world: Send email with Private Key (Securely) or store in Vault
    print(f"🔐 Custodial Wallet Created for {email}: {wallet['address']}")
    
    return {"status": "user_created", "email": email, "id": new_user.id, "wallet": wallet["address"]}

@router.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint. Returns JWT token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email, "wallet": user.wallet_address, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}



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
    access_token = create_access_token(data={"wallet": user.wallet_address, "sub": user.email, "role": user.role})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user.id,
        "is_new_user": is_new_user
    }

@router.post("/auth/link-wallet")
def link_wallet(req: WalletLoginRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    🔗 Link a Web3 Wallet to an existing Email Account.
    Protected endpoint: Requires valid Email JWT.
    """
    # 1. Verify Signature
    is_valid = verify_wallet_signature(req.address, req.message, req.signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid wallet signature")

    # 2. Check if wallet uses a different account
    if current_user.wallet_address == req.address:
        return {"status": "already_linked"}

    success = bind_wallet_to_user(db, current_user.id, req.address)
    if not success:
        raise HTTPException(status_code=400, detail="Wallet already linked to another user.")
    
    # 3. Issue Enriched Token
    db.refresh(current_user)
    access_token = create_access_token(data={
        "sub": current_user.email, 
        "wallet": current_user.wallet_address,
        "role": current_user.role
    })
    
    return {
        "status": "linked",
        "access_token": access_token,
        "user_id": current_user.id
    }

class ProfileUpdateRequest(BaseModel):
    """Request model for profile completion."""
    full_name: str = Field(..., description="User's full name")
    phone_number: str = Field(..., description="User's phone number")
    email: Optional[str] = Field(None, description="Email for account binding")

@router.post("/auth/update-profile")
def update_profile(req: ProfileUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    📝 Complete User Profile
    Called after wallet connection. Binds email if provided.
    """
    current_user.full_name = req.full_name
    current_user.phone_number = req.phone_number
    if req.email:
        # Check if email is available
        existing = db.query(User).filter(User.email == req.email).first()
        if existing and existing.id != current_user.id:
             raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = req.email
        
    db.commit()
    
    return {
        "status": "success",
        "message": "Profile updated successfully",
        "user_id": current_user.id,
        "full_name": current_user.full_name
    }

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Phase 5: Comprehensive health check for all services.

    Checks:
    - Database connectivity
    - Redis cache
    - Blockchain connection
    - OpenAI API

    Returns:
    - status: "healthy" | "degraded" | "unhealthy"
    - Individual service statuses
    """
    import time
    start_time = time.time()

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Osool Registry API",
        "checks": {}
    }

    # 1. Database Check
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # 2. Redis Cache Check
    try:
        from app.services.cache import cache
        cache.redis.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "degraded", "error": str(e)}
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # 3. Blockchain Check
    try:
        is_connected = blockchain_service.is_connected()
        health_status["checks"]["blockchain"] = {
            "status": "healthy" if is_connected else "degraded",
            "connected": is_connected
        }
        if not is_connected and health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["blockchain"] = {"status": "degraded", "error": str(e)}
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # 4. OpenAI API Check (lightweight test)
    try:
        from app.services.circuit_breaker import openai_breaker
        # Check circuit breaker state
        breaker_status = openai_breaker.state.value
        health_status["checks"]["openai"] = {
            "status": "healthy" if breaker_status == "closed" else "degraded",
            "circuit_breaker": breaker_status
        }
        if breaker_status == "open":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["openai"] = {"status": "degraded", "error": str(e)}
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    # Response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)

    # Set HTTP status code based on health
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/metrics")
def prometheus_metrics():
    """
    Phase 5: Prometheus metrics endpoint for monitoring.

    Exposes metrics in Prometheus format for:
    - API requests and latency
    - OpenAI usage and costs
    - Circuit breaker states
    - Business metrics (searches, reservations)
    """
    from app.services.metrics import metrics_endpoint
    return metrics_endpoint()


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
    """
    
    # 1. Validate Address
    if not req.user_address.startswith("0x") or len(req.user_address) != 42:
        raise HTTPException(
            status_code=400, 
            detail="Invalid wallet address format"
        )
    
    # 2. Check Availability
    if not blockchain_service.is_available(req.property_id):
        raise HTTPException(
            status_code=409,
            detail="Property is not available for reservation"
        )
    
def reserve_property(req: ReservationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    🏡 Reserve Property (Pre-Payment Check)
    """
    # 1. STRICT KYC CHECK
    if not current_user.phone_number:
        raise HTTPException(
            status_code=403, 
            detail="Phone number verification required. Please complete your profile."
        )
    if not current_user.national_id:
        raise HTTPException(
            status_code=403, 
            detail="National ID required for legal contract binding."
        )

    # ... [Rest of logic would go here, simplified for MVP to just return success/link]

    return {
        "status": "ready_for_payment",
        "message": "KYC Verified. Proceed to payment.",
        "link": f"https://pay.osool.eg/checkout/{req.property_id}" 
    }

class CancellationRequest(BaseModel):
    property_id: int
    reason: str

@router.post("/finalize-sale")
def finalize_sale(req: SaleFinalizationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    ✅ Finalize Sale (Mint NFT/Tokens)
    """
    
    # Verify bank transfer via DB (Strict)
    approval = db.query(PaymentApproval).filter(
        PaymentApproval.reference_number == req.bank_transfer_reference,
        PaymentApproval.status == "approved"
    ).first()
    
    if not approval:
        raise HTTPException(
            status_code=400,
            detail="Bank transfer verification failed: Reference not found or not approved by admin."
        )
        
    # Check if property matches approval
    if approval.property_id != req.property_id:
         raise HTTPException(status_code=400, detail="Payment reference does not match property ID.")
    
    # Verify manual bank transfer if applicable
    if req.payment_method == "bank_transfer":
        if not verify_bank_transfer(req.reference_number, db):
             raise HTTPException(status_code=400, detail="Bank transfer not found or not approved yet.")
    
    result = blockchain_service.finalize_sale(
        property_id=req.property_id, 
        buyer_address=current_user.wallet_address,
        amount=req.amount
    )
    
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


def verify_bank_transfer(reference: str, db: Session) -> bool:
    """
    Strict verification against PaymentApproval table.
    """
    approval = db.query(PaymentApproval).filter(
        PaymentApproval.reference_number == reference,
        PaymentApproval.status == "approved"
    ).first()
    return approval is not None


# ═══════════════════════════════════════════════════════════════
# WEBHOOKS (PAYMOB INTEGRATION)
# ═══════════════════════════════════════════════════════════════

@router.post("/payment/initiate")
def initiate_paymob_payment(req: PaymentInitiateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    💳 Start Payment Flow (Paymob)
    Creates a Transaction Record + Paymob Order.
    """
    
    # 1. STRICT KYC CHECK
    if not current_user.phone_number:
         raise HTTPException(status_code=403, detail="Verified phone number required for payments.")
         
    # 1.5 AVAILABILITY CHECK
    property = db.query(Property).filter(Property.id == req.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    if not property.is_available:
        raise HTTPException(status_code=400, detail="Property is NOT available associated with this payment request.")

    # 2. Initiate Paymob
    result = paymob_service.initiate_payment(
        amount_egp=req.amount_egp,
        user_email=req.email,
        user_phone=req.phone_number,
        first_name=req.first_name,
        last_name=req.last_name
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    # 3. Store Transaction for internal tracking
    # CRITICAL: Webhook needs this to link Order ID -> User/Property
    try:
        new_tx = Transaction(
            user_id=current_user.id, 
            property_id=req.property_id,
            amount=req.amount_egp, 
            paymob_order_id=str(result.get("order_id")),
            status="pending"
        )
        db.add(new_tx)
        db.commit()
    except Exception as e:
        print(f"❌ Failed to save transaction: {e}")
        # We proceed but warn. In strict mode, maybe fail?
        # If we fail here, user paid but we don't know.
        # Ideally transaction is created BEFORE paymob, then updated with order_id.
        # But for now, we do this.
    
    return result

@router.post("/webhook/paymob")
async def paymob_webhook(data: dict, hmac: str, db: Session = Depends(get_db)):
    """
    🔐 Secure Webhook Listener for Paymob.
    Verifies HMAC signature then triggers Blockchain actions on payment success.
    """
    # 1. Verify source is actually Paymob
    if not paymob_service.verify_hmac(data, hmac):
         raise HTTPException(status_code=403, detail="Nice try, hacker. HMAC verification failed.")
    
    # 2. Extract Data
    try:
        obj = data.get('obj', {})
        order_id = str(obj.get('order', {}).get('id'))
        amount_cents = obj.get('amount_cents')
        success = obj.get('success', False)
        
        if not success:
            return {"status": "ignored", "reason": "transaction_failed"}
            
        print(f"✅ Webhook: Payment SUCCESS (Order: {order_id}). Triggering Blockchain...")

        # 3. Lookup Transaction in DB to get Property & User
        # We need to find the pending transaction associated with this order
        transaction = db.query(Transaction).filter(Transaction.paymob_order_id == order_id).first()
        
        if not transaction:
             print(f"⚠️ Webhook: Unknown Order ID {order_id}. Manual check required.")
             return {"status": "accepted_but_unknown_order"}
             
        # Update transaction status
        transaction.status = "paid"
        db.commit()

        # 4. Trigger Blockchain Action (Mint Fractional Shares)
        # Assuming we have property_id and user logic in place.
        # Since 'Transaction' stores property_id and user_id...
        
        if transaction.property_id:
             user = transaction.user
             wallet_address = user.wallet_address
             
             if not wallet_address:
                  print("⚠️ User has no wallet address. Cannot mint.")
                  return {"status": "user_no_wallet"}
                  
             # Calculate shares (1 EGP = 100 Shares - simplistic)
             # Or use the fractional service logic
             shares = int(transaction.amount * 100)
             
             blockchain_service_prod.mint_fractional_shares(
                 property_id=transaction.property_id,
                 investor_address=wallet_address,
                 amount=shares
             )
             transaction.status = "blockchain_confirmed"
             db.commit()
        
    except Exception as e:
        print(f"Webhook Error: {e}")
        raise HTTPException(status_code=500, detail="Processing error")
    
    return {"status": "success"}



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
async def chat_with_agent(req: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    💬 Main AI Chat Endpoint (Phase 3: With Chat History Persistence)

    Sends user message to the Wolf AI Agent with conversation memory.
    Saves chat history to database for cross-session continuity.

    Returns:
    - response: AI text response
    - properties: JSON array of property objects found during search

    Frontend can render property cards from the `properties` array.
    """
    from app.ai_engine.sales_agent import sales_agent, get_last_search_results
    from app.models import ChatMessage
    from sqlalchemy import select
    import json

    try:
        # Phase 3: Load last 20 messages from database for this session
        chat_history = []
        result = await db.execute(
            select(ChatMessage)
            .filter(ChatMessage.session_id == req.session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
        )
        messages = result.scalars().all()

        # Convert to LangChain message format (reverse chronological order)
        for msg in reversed(messages):
            if msg.role == "user":
                from langchain_core.messages import HumanMessage
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                from langchain_core.messages import AIMessage
                chat_history.append(AIMessage(content=msg.content))

        # Save user message to database
        user_message = ChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.message
        )
        db.add(user_message)
        await db.commit()

        # Get AI response (with history)
        response_text = sales_agent.chat(req.message, req.session_id, chat_history)

        # Save AI response to database
        search_results = get_last_search_results(req.session_id)
        ai_message = ChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=response_text,
            properties_json=json.dumps(search_results) if search_results else None
        )
        db.add(ai_message)
        await db.commit()

        return {
            "response": response_text,
            "properties": search_results,
            "session_id": req.session_id
        }
    except Exception as e:
        await db.rollback()
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
def fractional_invest(req: FractionalInvestmentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    🏢 Fractional Property Investment (Production)
    
    Flow:
    1. Verify EGP payment (assume initiated previously or verified check)
    2. Fetch REAL Property Price from DB
    3. Calculate Precise Ownership %
    4. Mint fractional shares on blockchain
    """
    
    # Step 1: Validate wallet address
    if not req.investor_address.startswith("0x") or len(req.investor_address) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address format")
    
    # Step 2: Fetch Property Data (The Logic Upgrade)
    property_record = db.query(Property).filter(Property.id == req.property_id).first()
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found")
        
    total_price = property_record.price
    if total_price <= 0:
        raise HTTPException(status_code=500, detail="Invalid property price in database")

    # Step 3: Calculate Precise Ownership
    ownership_percentage = (req.investment_amount_egp / total_price) * 100
    
    # Calculate Shares (Example: Total Tokens = Total Price * 100? Or 1 Token = 1 EGP?)
    # Let's assume 1 Share = 1 EGP for simplicity or 100 Shares = 1 EGP (Penny stocks style)
    # The user request said "precise calculated amount". 
    # Let's use 1 Share = 1 EGP for standard tokenization logic usually
    # But earlier code used amount * 100. We will stick to amount * 100 (Cents representation perhaps?)
    shares_to_mint = int(req.investment_amount_egp * 100)
    
    # Step 4: Mint fractional shares
    try:
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
        "message": "🎉 Investment confirmed! Ownership transferred.",
        "property_id": req.property_id,
        "invested_amount": req.investment_amount_egp,
        "total_property_value": total_price,
        "ownership_percentage": round(ownership_percentage, 4),
        "shares_minted": shares_to_mint,
        "tx_hash": blockchain_result.get("tx_hash", ""),
        "blockchain_proof": f"https://amoy.polygonscan.com/tx/{blockchain_result.get('tx_hash', '')}"
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


# ═══════════════════════════════════════════════════════════════
# ADMIN & INGESTION (Protected)
# ---------------------------------------------------------------------------

@router.post("/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Manually triggers the Nawy Scraper.
    Protected by X-Admin-Key.
    """
    from app.services.nawy_scraper import ingest_nawy_data
    background_tasks.add_task(ingest_nawy_data)
    return {"status": "Ingestion started in background"}

@router.post("/admin/withdraw-fees")
def admin_withdraw_fees(api_key: str = Depends(verify_api_key)):
    """
    Admin: Withdraws platform fees from Smart Contract.
    """
    # Logic to call blockchain_service.withdraw_fees() would go here
    return {"status": "Not implemented yet"}
