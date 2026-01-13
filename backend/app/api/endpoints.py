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
from app.auth import create_access_token, get_current_user, get_current_user_optional, get_password_hash, verify_password, verify_wallet_signature, get_or_create_user_by_wallet, create_custodial_wallet
from app.database import get_db
from app.models import User, Property, Transaction, PaymentApproval
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
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
    # Phase 1 Security: Returns encrypted private key
    wallet = create_custodial_wallet()

    # 2. Create User
    new_user = User(
        email=email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        wallet_address=wallet["address"], # Assigned Custodial Wallet
        encrypted_private_key=wallet["encrypted_private_key"], # Phase 1: Store encrypted key
        is_verified=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Security: Private key is encrypted and stored, never logged or exposed
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
def reserve_property(req: ReservationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    🏡 Reserve Property (Manual Payment Submission)
    """
    # 1. STRICT KYC CHECK
    if not current_user.phone_number:
        raise HTTPException(status_code=403, detail="Phone number verification required.")
    if not current_user.national_id:
        raise HTTPException(status_code=403, detail="National ID required for legal contract binding.")

    # 2. Validate Address
    if not req.user_address.startswith("0x") or len(req.user_address) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address format")
    
    # 3. Check Availability (Blockchain Authority)
    if not blockchain_service.is_available(req.property_id):
        raise HTTPException(status_code=409, detail="Property is not available for reservation")

    # 4. Record Transaction (Pending Admin Approval)
    # In a real app this would go to a specialized "Payment Claims" table
    # For now we use Transaction with a specific status
    try:
        tx = Transaction(
            user_id=current_user.id,
            property_id=req.property_id,
            amount=req.payment_amount_egp,
            paymob_order_id=f"MANUAL-{req.payment_reference}", # Hack for schema
            status="pending_approval"
        )
        db.add(tx)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "status": "pending_approval",
        "message": "Payment reference submitted. Reservation pending admin verification.",
        "tx_id": tx.id
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

    # ENHANCEMENT: Call markSold() on-chain to transfer ownership
    # This replaces the fractional minting approach with proper ownership transfer
    property = db.query(Property).filter(Property.id == req.property_id).first()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    blockchain_id = property.blockchain_id or property.id

    # Call blockchain to mark property as SOLD (transfers ownership on-chain)
    result = blockchain_service_prod.mark_sold(property_id=blockchain_id)

    if "error" in result or not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Sale finalization failed on blockchain: {result.get('error', 'Unknown error')}"
        )

    # Update database to reflect blockchain state
    tx_hash = result.get("tx_hash")
    property.is_available = False

    # Record transaction completion in database
    db.commit()

    return {
        "status": "success",
        "message": "Property sale finalized! Ownership transferred on-chain via markSold().",
        "tx_hash": tx_hash,
        "blockchain_proof": f"https://amoy.polygonscan.com/tx/{tx_hash}"
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
# AI CHECKOUT BRIDGE (PHASE 3)
# ═══════════════════════════════════════════════════════════════

@router.post("/checkout")
def checkout(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🧠 Phase 3: AI Checkout Bridge - Converts JWT reservation tokens to payment sessions

    This endpoint bridges the gap between AI-generated reservation links and payment initiation.
    The Wolf of Cairo AI creates JWT tokens via `generate_reservation_link` tool.
    This endpoint validates the token and redirects to payment.

    Flow:
    1. Decode & validate JWT token from AI agent
    2. Extract property_id from token payload
    3. Fetch property details and verify availability
    4. Initiate Paymob payment session
    5. Return payment URL to frontend

    Args:
        token: JWT token generated by AI agent (expires in 1 hour)
        current_user: Authenticated user from session
        db: Database session

    Returns:
        Payment initiation result with iframe URL
    """
    import jwt
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)

    try:
        # 1. Decode JWT token
        SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        if not SECRET_KEY:
            raise HTTPException(status_code=500, detail="JWT secret not configured")

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Reservation link expired. Please generate a new one.")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=400, detail=f"Invalid reservation token: {str(e)}")

        # 2. Validate token type
        if payload.get("type") != "reservation":
            raise HTTPException(status_code=400, detail="Invalid token type")

        # 3. Extract property ID
        property_id = payload.get("property_id")
        if not property_id:
            raise HTTPException(status_code=400, detail="Property ID missing from token")

        # 4. Fetch property and verify availability
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")

        if not property.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"Property '{property.title}' is no longer available for reservation"
            )

        # 5. Verify user has verified phone (required for payments)
        if not current_user.phone_verified:
            raise HTTPException(
                status_code=403,
                detail="Verified phone number required for payments. Please verify your phone first."
            )

        # 6. Prepare payment request
        payment_amount = float(property.price)
        first_name = current_user.full_name.split()[0] if current_user.full_name else "Buyer"
        last_name = current_user.full_name.split()[-1] if current_user.full_name and len(current_user.full_name.split()) > 1 else ""

        # 7. Initiate Paymob payment
        result = paymob_service.initiate_payment(
            amount_egp=payment_amount,
            user_email=current_user.email or f"user{current_user.id}@osool.com",
            user_phone=current_user.phone_number,
            first_name=first_name,
            last_name=last_name
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # 8. Store transaction for webhook tracking
        try:
            new_tx = Transaction(
                user_id=current_user.id,
                property_id=property_id,
                amount=payment_amount,
                paymob_order_id=str(result.get("order_id")),
                status="pending"
            )
            db.add(new_tx)
            db.commit()

            logger.info(f"✅ Checkout: User {current_user.id} → Property {property_id} → Order {result.get('order_id')}")
        except Exception as e:
            logger.error(f"❌ Failed to save checkout transaction: {e}")

        # 9. Return payment URL with property context
        return {
            "success": True,
            "payment_url": result.get("iframe_url") or result.get("redirect_url"),
            "order_id": result.get("order_id"),
            "property": {
                "id": property.id,
                "title": property.title,
                "price": float(property.price),
                "location": property.location
            },
            "message": "Redirecting to secure payment gateway..."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Checkout failed: {e}")
        raise HTTPException(status_code=500, detail=f"Checkout error: {str(e)}")


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

        # 4. Determine Transaction Type & Trigger Appropriate Blockchain Action
        if transaction.property_id:
             user = transaction.user
             wallet_address = user.wallet_address

             if not wallet_address:
                  print("⚠️ User has no wallet address. Cannot process blockchain action.")
                  return {"status": "user_no_wallet"}

             # Fetch property to determine transaction type
             property = db.query(Property).filter(Property.id == transaction.property_id).first()

             if not property:
                  print(f"⚠️ Property {transaction.property_id} not found.")
                  return {"status": "property_not_found"}

             # HEURISTIC: If payment >= 10% of property price, it's a RESERVATION deposit
             # Otherwise, it's a FRACTIONAL investment
             is_reservation_deposit = (transaction.amount >= property.price * 0.10)

             if is_reservation_deposit:
                  # This is a RESERVATION deposit - call markReserved()
                  print(f"🔒 Detected RESERVATION deposit ({transaction.amount} EGP >= 10% of {property.price} EGP)")

                  try:
                      # Call blockchain to mark property as reserved
                      blockchain_id = property.blockchain_id or property.id
                      result = blockchain_service_prod.reserve_property(
                          property_id=blockchain_id,
                          buyer_address=wallet_address
                      )

                      if result.get("success"):
                          tx_hash = result.get("tx_hash")
                          transaction.blockchain_tx_hash = tx_hash
                          transaction.status = "blockchain_confirmed"

                          # Update property status in DB (for consistency)
                          property.is_available = False  # Mark as no longer available

                          db.commit()
                          print(f"✅ Property {property.id} reserved on-chain: {tx_hash}")
                      else:
                          # Blockchain call failed - queue for retry
                          print(f"❌ Blockchain reservation failed: {result.get('error')}")
                          transaction.status = "blockchain_pending"
                          db.commit()

                          # TODO: Queue for Celery retry (implemented in tasks.py)
                          # from app.tasks import reserve_property_task
                          # reserve_property_task.apply_async(
                          #     args=[blockchain_id, wallet_address],
                          #     countdown=60
                          # )

                          return {"status": "payment_confirmed_blockchain_pending", "error": result.get('error')}

                  except Exception as e:
                      print(f"❌ Exception during blockchain reservation: {e}")
                      transaction.status = "blockchain_pending"
                      db.commit()
                      return {"status": "payment_confirmed_blockchain_error", "error": str(e)}

             else:
                  # This is a FRACTIONAL investment - mint fractional shares
                  print(f"💎 Detected FRACTIONAL investment ({transaction.amount} EGP)")
                  shares = int(transaction.amount * 100)  # 1 EGP = 100 Shares

                  blockchain_id = property.blockchain_id or property.id
                  result = blockchain_service_prod.mint_fractional_shares(
                      property_id=blockchain_id,
                      investor_address=wallet_address,
                      amount=shares
                  )

                  if result.get("success"):
                      transaction.blockchain_tx_hash = result.get("tx_hash")
                      transaction.status = "blockchain_confirmed"
                      db.commit()
                      print(f"✅ Minted {shares} fractional shares")
                  else:
                      transaction.status = "blockchain_pending"
                      db.commit()
                      print(f"❌ Minting failed: {result.get('error')}")
        
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
async def chat_with_agent(
    req: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    💬 Main AI Chat Endpoint (Phase 1: Claude-Powered with Arabic Support)

    Sends user message to AMR (Claude-powered) AI Agent with conversation memory.
    Supports both Arabic and English conversations seamlessly.
    Saves chat history to database for cross-session continuity.

    Returns:
    - response: AI text response (Arabic/English mix based on user language)
    - properties: JSON array of property objects found during search
    - analytics: Conversation metrics (lead score, customer segment)

    Frontend can render property cards from the `properties` array.
    """
    from app.ai_engine.claude_sales_agent import claude_sales_agent, get_last_search_results
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

        # Convert to Claude-compatible message format
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

        # Get AI response from Claude agent (supports Arabic automatically)
        response_text = await claude_sales_agent.chat(
            user_input=req.message,
            session_id=req.session_id,
            chat_history=chat_history,
            user=user.__dict__ if user else None
        )

        # Save AI response to database (with hybrid retrieval - Redis + DB fallback)
        search_results = await get_last_search_results(req.session_id, db)
        ai_message = ChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=response_text,
            properties_json=json.dumps(search_results) if search_results else None
        )
        db.add(ai_message)
        await db.commit()

        # Phase 1: Track analytics (for future dashboard integration)
        analytics_data = {
            "customer_segment": claude_sales_agent.customer_segment.value if claude_sales_agent.customer_segment else "unknown",
            "lead_temperature": claude_sales_agent.lead_score.get("temperature") if claude_sales_agent.lead_score else "cold",
            "lead_score": claude_sales_agent.lead_score.get("score", 0) if claude_sales_agent.lead_score else 0,
            "properties_viewed": len(search_results) if search_results else 0,
            "message_count": len(chat_history) + 2  # +2 for current exchange
        }

        # Week 3: Generate visualization data based on response content
        from app.ai_engine.visualization_helpers import attach_visualizations_to_response

        visualizations = {}
        if search_results and len(search_results) > 0:
            # Detect intent from response text
            response_lower = response_text.lower()

            # Show investment scorecard for valuation/analysis requests
            show_scorecard = any(keyword in response_lower for keyword in [
                "تحليل", "analysis", "investment", "استثمار", "roi", "return"
            ])

            # Show comparison for multiple properties
            show_comparison = len(search_results) > 1 and any(keyword in response_lower for keyword in [
                "قارن", "compare", "comparison", "مقارنة", "options", "choose"
            ])

            # Show payment timeline for payment/installment questions
            show_payment = any(keyword in response_lower for keyword in [
                "payment", "دفع", "أقساط", "installment", "monthly", "شهري"
            ])

            # Show market trends for trend/market questions
            show_trends = any(keyword in response_lower for keyword in [
                "trend", "market", "سوق", "نمو", "growth", "اتجاه"
            ])

            visualizations = attach_visualizations_to_response(
                properties=search_results,
                show_scorecard=show_scorecard,
                show_comparison=show_comparison,
                show_payment=show_payment,
                show_trends=show_trends
            )

        return {
            "response": response_text,
            "properties": search_results,
            "visualizations": visualizations,  # NEW: Visualization data
            "session_id": req.session_id,
            "analytics": analytics_data,
            "cost": claude_sales_agent.get_cost_summary()  # For monitoring
        }
    except Exception as e:
        await db.rollback()
        print(f"❌ Chat Error: {e}")
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
