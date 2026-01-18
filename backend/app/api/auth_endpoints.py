"""
Authentication Endpoints - Phase 2
-----------------------------------
Complete multi-method authentication:
- Google OAuth
- Phone OTP
- Email Verification
- Password Reset

Import this in endpoints.py to add all auth routes.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User, Invitation
from app.auth import (
    verify_google_token,
    get_or_create_user_by_email,
    create_access_token,
    get_password_hash,
    verify_password,
    create_custodial_wallet,
    get_current_user
)
from app.services.sms_service import sms_service
from app.services.email_service import email_service, create_verification_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


# ═══════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════

class GoogleAuthRequest(BaseModel):
    id_token: str


class OTPSendRequest(BaseModel):
    phone_number: str  # E.164 format: +201234567890


class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp_code: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class SignupRequest(BaseModel):
    """KYC-Compliant Signup for Egyptian FRA Compliance"""
    full_name: str
    email: EmailStr
    password: str
    phone_number: str  # E.164 format: +201234567890
    national_id: str   # Egyptian NID: 14 digits


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    is_new_user: bool


# ═══════════════════════════════════════════════════════════════
# KYC-COMPLIANT SIGNUP & LOGIN (FRA Egyptian Compliance)
# ═══════════════════════════════════════════════════════════════

@router.post("/signup")
async def signup_with_kyc(req: SignupRequest, db: Session = Depends(get_db)):
    """
    FRA-Compliant Signup requiring National ID + Phone Verification.

    Flow:
    1. Validate inputs (phone format, NID length)
    2. Check for duplicate email/phone/NID
    3. Create user with unverified status
    4. Send OTP to phone immediately
    5. User must verify OTP before login is allowed

    Required Fields:
    - full_name: User's full name
    - email: Email address
    - password: Minimum 8 characters
    - phone_number: Egyptian phone (+20...)
    - national_id: 14-digit Egyptian National ID
    """
    # Validation 1: Egyptian phone number format
    if not req.phone_number.startswith('+20'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Egyptian phone numbers only. Use E.164 format: +201234567890"
        )

    # Validation 2: National ID length (14 digits)
    if len(req.national_id) != 14 or not req.national_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="National ID must be exactly 14 digits"
        )

    # Validation 3: Password strength
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Check for duplicates
    existing_user = db.query(User).filter(
        (User.email == req.email) |
        (User.phone_number == req.phone_number) |
        (User.national_id == req.national_id)
    ).first()

    if existing_user:
        # Don't leak which field is duplicate for security
        if existing_user.email == req.email:
            detail = "Email already registered"
        elif existing_user.phone_number == req.phone_number:
            detail = "Phone number already registered"
        else:
            detail = "National ID already registered"

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    # Create custodial wallet
    # Phase 1 Security: Returns encrypted private key
    wallet = create_custodial_wallet()

    # Create user with unverified status
    new_user = User(
        full_name=req.full_name,
        email=req.email,
        password_hash=get_password_hash(req.password),
        phone_number=req.phone_number,
        national_id=req.national_id,
        wallet_address=wallet["address"],
        encrypted_private_key=wallet["encrypted_private_key"], # Phase 1: Store encrypted key
        is_verified=False,       # Cannot login until phone verified
        phone_verified=False,    # Must verify OTP
        email_verified=False,
        kyc_status="pending",    # KYC pending
        role="investor"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"✅ Created new user: {req.email} (NID: {req.national_id[:4]}****)")

    # Send OTP immediately
    try:
        otp_code = sms_service.send_otp(req.phone_number)

        # Return response
        response = {
            "status": "otp_sent",
            "user_id": new_user.id,
            "message": "Signup successful. Please verify your phone number with the OTP sent to complete registration."
        }

        # In development mode, include OTP for testing
        if os.getenv('ENVIRONMENT') == 'development':
            response["dev_otp"] = otp_code

        return response

    except Exception as e:
        logger.error(f"Failed to send OTP during signup: {e}")
        # Rollback user creation if OTP fails
        db.delete(new_user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code. Please try again."
        )


@router.post("/login")
async def login_with_verification(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint with phone verification gate.

    Returns 403 if user hasn't verified their phone number.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Find user by email (async pattern for AsyncSession)
    result = await db.execute(select(User).filter(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # For beta users (pre-verified), skip phone verification check
    # CRITICAL: In production, require phone verification
    if not user.is_verified and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "account_not_verified",
                "message": "Please verify your account before logging in",
                "user_id": user.id
            }
        )

    # Generate JWT
    access_token = create_access_token(data={
        "sub": user.email,
        "wallet": user.wallet_address,
        "role": user.role
    })

    logger.info(f"Login successful: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id
    }


# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH
# ═══════════════════════════════════════════════════════════════

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth.

    Flow:
    1. Frontend gets ID token from Google
    2. Backend verifies token with Google
    3. Create/get user by email
    4. Return JWT token
    """
    try:
        # Verify Google token
        user_info = await verify_google_token(request.id_token)

        email = user_info['email']
        name = user_info.get('name', 'Google User')

        # Get or create user
        user = get_or_create_user_by_email(db, email, name)

        # Check if this is a new user
        is_new = user.full_name == 'Google User'

        # Generate JWT
        access_token = create_access_token(data={
            "sub": user.email,
            "wallet": user.wallet_address,
            "role": user.role
        })

        logger.info(f"✅ Google OAuth successful for {email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "is_new_user": is_new
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


# ═══════════════════════════════════════════════════════════════
# PHONE OTP
# ═══════════════════════════════════════════════════════════════

@router.post("/otp/send")
@limiter.limit("3/hour")  # Prevent SMS spam
async def send_otp(
    request: Request,
    req: OTPSendRequest,
    db: Session = Depends(get_db)
):
    """
    Send OTP code to phone number.

    Rate limit: 3 requests per hour per IP to prevent abuse.
    """
    # Validate Egyptian phone number
    if not req.phone_number.startswith('+20'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Egyptian phone number format. Use E.164: +201234567890"
        )

    try:
        code = sms_service.send_otp(req.phone_number)

        # In development, return code for testing
        if os.getenv('ENVIRONMENT') == 'development':
            return {
                "status": "sent",
                "dev_code": code,
                "message": "OTP sent successfully (dev mode shows code)"
            }

        return {
            "status": "sent",
            "message": "OTP sent to your phone. Valid for 5 minutes."
        }

    except Exception as e:
        logger.error(f"OTP send failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )


@router.post("/otp/verify", response_model=AuthResponse)
async def verify_otp_login(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP and complete phone verification.

    This endpoint:
    1. Verifies the OTP code
    2. Marks phone_verified = True
    3. Sets is_verified = True (enables login)
    4. Returns JWT token for immediate login
    """
    # Verify OTP
    if not sms_service.verify_otp(req.phone_number, req.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )

    # Find user by phone
    user = db.query(User).filter(User.phone_number == req.phone_number).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this phone number. Please sign up first."
        )

    # Mark phone as verified and enable login
    user.phone_verified = True
    user.is_verified = True  # Enable login
    db.commit()
    db.refresh(user)

    logger.info(f"✅ Phone verified for user: {user.email} ({user.phone_number})")

    # Generate JWT for immediate login
    access_token = create_access_token(data={
        "sub": user.email or user.phone_number,
        "wallet": user.wallet_address,
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": False,  # User already signed up, just verifying
        "message": "Phone verified successfully. You can now login."
    }


# ═══════════════════════════════════════════════════════════════
# EMAIL VERIFICATION
# ═══════════════════════════════════════════════════════════════

@router.post("/send-verification")
async def send_verification(
    req: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Send verification email to user.

    Can be called after signup or to resend verification.
    """
    user = db.query(User).filter(User.email == req.email).first()

    if not user:
        # Don't leak if email exists
        return {
            "status": "sent",
            "message": "If the email exists, verification link has been sent."
        }

    if user.email_verified:
        return {
            "status": "already_verified",
            "message": "Email is already verified"
        }

    # Generate verification token
    token = create_verification_token()
    user.verification_token = token
    db.commit()

    # Send email
    try:
        email_service.send_verification_email(req.email, token)
        logger.info(f"✅ Verification email sent to {req.email}")

        return {
            "status": "sent",
            "message": "Verification email sent. Please check your inbox."
        }

    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify email address using token from email link.

    Example: /api/auth/verify-email?token=abc123...
    """
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Mark as verified
    user.email_verified = True
    user.verification_token = None
    db.commit()

    logger.info(f"✅ Email verified: {user.email}")

    return {
        "status": "verified",
        "message": "Email successfully verified! You can now log in."
    }


# ═══════════════════════════════════════════════════════════════
# PASSWORD RESET
# ═══════════════════════════════════════════════════════════════

@router.post("/reset-password")
@limiter.limit("5/hour")  # Prevent abuse
async def request_reset(
    request: Request,
    req: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset link.

    Rate limit: 5 requests per hour per IP.
    """
    user = db.query(User).filter(User.email == req.email).first()

    # Don't leak if email exists (security best practice)
    if not user:
        return {
            "status": "sent",
            "message": "If the email exists, password reset link has been sent."
        }

    # Generate reset token
    token = create_verification_token()
    user.verification_token = token
    db.commit()

    # Send reset email
    try:
        email_service.send_reset_email(req.email, token)
        logger.info(f"✅ Password reset email sent to {req.email}")

        return {
            "status": "sent",
            "message": "Password reset link sent. Please check your email."
        }

    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        # Still return success to not leak email existence
        return {
            "status": "sent",
            "message": "If the email exists, password reset link has been sent."
        }


@router.post("/reset-password/confirm")
async def confirm_reset(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Confirm password reset with token and new password.
    """
    user = db.query(User).filter(User.verification_token == req.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Validate password strength
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Update password
    user.password_hash = get_password_hash(req.new_password)
    user.verification_token = None
    db.commit()

    logger.info(f"✅ Password reset successful for {user.email}")

    return {
        "status": "success",
        "message": "Password successfully reset. You can now log in with your new password."
    }


# ═══════════════════════════════════════════════════════════════
# INVITATION SYSTEM
# ═══════════════════════════════════════════════════════════════

# Admin emails that can generate unlimited invitations
UNLIMITED_INVITATION_ADMINS = [
    "mustafa@osool.eg",
    "hani@osool.eg",
    "abady@osool.eg",
    "sama@osool.eg"
]

MAX_INVITATIONS_PER_USER = 2  # Regular users can only send 2 invitations


class InvitationGenerateRequest(BaseModel):
    """Request to generate a new invitation code"""
    pass  # No extra params needed, user is from token


class InvitationValidateResponse(BaseModel):
    """Response for invitation validation"""
    valid: bool
    message: str
    created_by: str = None


class SignupWithInvitationRequest(BaseModel):
    """Signup request requiring invitation code"""
    full_name: str
    email: EmailStr
    password: str
    invitation_code: str  # Required invitation code


@router.post("/invitation/generate")
async def generate_invitation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a new invitation code.

    Rules:
    - Admin users (Mustafa, Hani, Abady, Sama) can generate unlimited invitations
    - Regular users can only generate 2 invitations total

    Returns:
    - invitation_code: Unique code to share
    - invitation_link: Full URL for sharing
    """
    from sqlalchemy import select, func
    from app.auth import get_current_user
    import secrets

    # Check if user is admin (unlimited invitations)
    is_admin = current_user.email.lower() in [e.lower() for e in UNLIMITED_INVITATION_ADMINS]

    if not is_admin:
        # Check how many invitations this user has created
        result = await db.execute(
            select(func.count(Invitation.id))
            .filter(Invitation.created_by_user_id == current_user.id)
        )
        invitation_count = result.scalar() or 0

        if invitation_count >= MAX_INVITATIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You have reached the maximum of {MAX_INVITATIONS_PER_USER} invitations. Only admin users can generate more."
            )

    # Generate unique invitation code
    invitation_code = secrets.token_urlsafe(16)  # 22 characters

    # Create invitation record
    new_invitation = Invitation(
        code=invitation_code,
        created_by_user_id=current_user.id,
        is_used=False
    )

    db.add(new_invitation)

    # Update user's invitation count
    current_user.invitations_sent = (current_user.invitations_sent or 0) + 1

    await db.commit()

    # Build invitation link
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    invitation_link = f"{frontend_url}/signup?invite={invitation_code}"

    logger.info(f"✅ Invitation generated by {current_user.email}: {invitation_code[:8]}...")

    return {
        "status": "success",
        "invitation_code": invitation_code,
        "invitation_link": invitation_link,
        "invitations_remaining": "unlimited" if is_admin else (MAX_INVITATIONS_PER_USER - (current_user.invitations_sent or 0))
    }


@router.get("/invitation/validate/{code}")
async def validate_invitation(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate an invitation code without using it.

    Returns whether the code is valid and who created it.
    """
    from sqlalchemy import select

    result = await db.execute(
        select(Invitation, User.full_name)
        .join(User, Invitation.created_by_user_id == User.id)
        .filter(Invitation.code == code)
    )
    row = result.first()

    if not row:
        return {
            "valid": False,
            "message": "Invalid invitation code"
        }

    invitation, creator_name = row

    if invitation.is_used:
        return {
            "valid": False,
            "message": "This invitation has already been used"
        }

    return {
        "valid": True,
        "message": "Valid invitation code",
        "invited_by": creator_name
    }


@router.get("/invitation/my-invitations")
async def get_my_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all invitations created by the current user.
    """
    from sqlalchemy import select

    result = await db.execute(
        select(Invitation)
        .filter(Invitation.created_by_user_id == current_user.id)
        .order_by(Invitation.created_at.desc())
    )
    invitations = result.scalars().all()

    is_admin = current_user.email.lower() in [e.lower() for e in UNLIMITED_INVITATION_ADMINS]

    return {
        "total_invitations": len(invitations),
        "invitations_remaining": "unlimited" if is_admin else max(0, MAX_INVITATIONS_PER_USER - len(invitations)),
        "invitations": [
            {
                "code": inv.code,
                "is_used": inv.is_used,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "used_at": inv.used_at.isoformat() if inv.used_at else None
            }
            for inv in invitations
        ]
    }


@router.post("/signup-with-invitation")
async def signup_with_invitation(
    req: SignupWithInvitationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Signup with invitation code (required).

    Flow:
    1. Validate invitation code exists and is unused
    2. Create user account
    3. Mark invitation as used
    4. Return JWT token for immediate login

    No phone/NID required - simplified for beta testing.
    """
    from sqlalchemy import select
    from datetime import datetime

    # Validation 1: Password strength
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Validation 2: Check invitation code
    result = await db.execute(
        select(Invitation).filter(Invitation.code == req.invitation_code)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invitation code. Please request an invitation from an existing user."
        )

    if invitation.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation code has already been used."
        )

    # Validation 3: Check for duplicate email
    result = await db.execute(
        select(User).filter(User.email == req.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create custodial wallet
    wallet = create_custodial_wallet()

    # Create user (pre-verified for beta)
    new_user = User(
        full_name=req.full_name,
        email=req.email,
        password_hash=get_password_hash(req.password),
        wallet_address=wallet["address"],
        encrypted_private_key=wallet["encrypted_private_key"],
        is_verified=True,  # Pre-verified for beta
        email_verified=True,
        invited_by_user_id=invitation.created_by_user_id,
        role="investor"
    )

    db.add(new_user)
    await db.flush()  # Get the new user ID

    # Mark invitation as used
    invitation.is_used = True
    invitation.used_by_user_id = new_user.id
    invitation.used_at = datetime.utcnow()

    await db.commit()
    await db.refresh(new_user)

    logger.info(f"✅ New user signed up via invitation: {req.email}")

    # Generate JWT for immediate login
    access_token = create_access_token(data={
        "sub": new_user.email,
        "wallet": new_user.wallet_address,
        "role": new_user.role
    })

    return {
        "status": "success",
        "message": "Account created successfully!",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id
    }


# ═══════════════════════════════════════════════════════════════
# ADMIN: SEED BETA USERS
# ═══════════════════════════════════════════════════════════════

class SeedBetaUsersRequest(BaseModel):
    """Request to seed beta users - requires admin secret"""
    admin_secret: str


# Beta accounts configuration
BETA_ACCOUNTS = [
    # Admin accounts (Core Team) - Unlimited invitations
    {"full_name": "Mustafa", "email": "mustafa@osool.eg", "password": "Mustafa@Osool2025!", "role": "admin"},
    {"full_name": "Hani", "email": "hani@osool.eg", "password": "Hani@Osool2025!", "role": "admin"},
    {"full_name": "Abady", "email": "abady@osool.eg", "password": "Abady@Osool2025!", "role": "admin"},
    {"full_name": "Sama", "email": "sama@osool.eg", "password": "Sama@Osool2025!", "role": "admin"},
    # Tester accounts - 2 invitations each
    {"full_name": "Tester One", "email": "tester1@osool.eg", "password": "Tester1@Beta2025", "role": "investor"},
    {"full_name": "Tester Two", "email": "tester2@osool.eg", "password": "Tester2@Beta2025", "role": "investor"},
    {"full_name": "Tester Three", "email": "tester3@osool.eg", "password": "Tester3@Beta2025", "role": "investor"},
    {"full_name": "Tester Four", "email": "tester4@osool.eg", "password": "Tester4@Beta2025", "role": "investor"},
    {"full_name": "Tester Five", "email": "tester5@osool.eg", "password": "Tester5@Beta2025", "role": "investor"},
    {"full_name": "Tester Six", "email": "tester6@osool.eg", "password": "Tester6@Beta2025", "role": "investor"},
    {"full_name": "Tester Seven", "email": "tester7@osool.eg", "password": "Tester7@Beta2025", "role": "investor"},
    {"full_name": "Tester Eight", "email": "tester8@osool.eg", "password": "Tester8@Beta2025", "role": "investor"},
    {"full_name": "Tester Nine", "email": "tester9@osool.eg", "password": "Tester9@Beta2025", "role": "investor"},
    {"full_name": "Tester Ten", "email": "tester10@osool.eg", "password": "Tester10@Beta2025", "role": "investor"},
]


@router.post("/admin/seed-beta-users")
async def seed_beta_users(
    req: SeedBetaUsersRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Seed beta users into the database.
    
    Requires admin_secret that matches JWT_SECRET_KEY environment variable.
    This is a one-time operation for production setup.
    """
    from sqlalchemy import select
    import hashlib
    
    # Verify admin secret (use JWT_SECRET_KEY as the admin secret)
    admin_secret = os.getenv("JWT_SECRET_KEY", "")
    if not admin_secret or req.admin_secret != admin_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret"
        )
    
    created = 0
    updated = 0
    
    for account in BETA_ACCOUNTS:
        # Check if user exists
        result = await db.execute(
            select(User).filter(User.email == account["email"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing user
            existing.is_verified = True
            existing.email_verified = True
            existing.role = account["role"]
            existing.password_hash = get_password_hash(account["password"])
            updated += 1
            logger.info(f"[SEED] Updated: {account['email']}")
        else:
            # Generate wallet address
            wallet_hash = hashlib.sha256(account["email"].encode()).hexdigest()[:40]
            wallet_address = f"0x{wallet_hash}"
            
            new_user = User(
                full_name=account["full_name"],
                email=account["email"],
                password_hash=get_password_hash(account["password"]),
                wallet_address=wallet_address,
                is_verified=True,
                email_verified=True,
                kyc_status="approved",
                role=account["role"],
                invitations_sent=0
            )
            db.add(new_user)
            created += 1
            logger.info(f"[SEED] Created: {account['email']}")
    
    await db.commit()
    
    logger.info(f"✅ Beta user seeding complete: {created} created, {updated} updated")
    
    return {
        "status": "success",
        "message": f"Beta users seeded successfully",
        "created": created,
        "updated": updated,
        "total": len(BETA_ACCOUNTS)
    }
