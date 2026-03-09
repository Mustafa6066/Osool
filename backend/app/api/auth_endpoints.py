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
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User, Invitation
from app.auth import (
    verify_google_token,
    get_or_create_user_by_email,
    get_or_create_user_by_email_async,
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    create_refresh_token_async,
    verify_refresh_token_async,
    revoke_refresh_token_async,
)
from app.services.sms_service import sms_service
from app.services.email_service import email_service, create_verification_token, is_verification_token_valid, consume_verification_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


# ═══════════════════════════════════════════════════════════════
# DISPLAY NAME MAPPING (Phase 1 - Specific User Mapping)
# ═══════════════════════════════════════════════════════════════
DISPLAY_NAME_MAPPING = {
    "hani@osool.eg": "Hani",
    "mustafa@osool.eg": "Mustafa",
    "abady@osool.eg": "Abady",
    "sama@osool.eg": "Mrs. Mustafa",
}


def get_display_name(user: User) -> str:
    """
    Get the display name for a user based on specific mapping rules.

    Rules:
    - Hani → Display: "Hani"
    - Mustafa → Display: "Mustafa"
    - Abady → Display: "Abady"
    - Sama → Display: "Mrs. Mustafa"
    - Others → Use full_name or email username
    """
    if user.email and user.email.lower() in DISPLAY_NAME_MAPPING:
        return DISPLAY_NAME_MAPPING[user.email.lower()]

    if user.full_name:
        return user.full_name

    # Fallback to email username
    if user.email:
        return user.email.split("@")[0].capitalize()

    return "User"


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure token using OpenSSL-equivalent method.
    Uses os.urandom which is backed by the OS's cryptographic PRNG.

    Args:
        length: Number of random bytes (will be base64 encoded, resulting in longer string)

    Returns:
        URL-safe base64 encoded token string
    """
    import base64
    # os.urandom uses the OS's cryptographic random number generator
    # On Linux/Mac this is /dev/urandom, on Windows it's CryptGenRandom
    random_bytes = os.urandom(length)
    # URL-safe base64 encoding without padding
    return base64.urlsafe_b64encode(random_bytes).rstrip(b'=').decode('ascii')


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


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


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

# @router.post("/signup")
# async def signup_with_kyc(req: SignupRequest, db: Session = Depends(get_db)):
#     """
#     DISABLED FOR PHASE 1 - INVITATION ONLY
#     """
#     raise HTTPException(
#         status_code=status.HTTP_403_FORBIDDEN,
#         detail="Public signup is currently disabled. Please use an invitation link."
#     )
    
@router.post("/signup_disabled_public") # Renamed to avoid route conflict if enabled later
async def signup_with_kyc_disabled(req: SignupRequest):
    """
    PUBLIC SIGNUP — PERMANENTLY DISABLED.
    Registration is by invitation only.
    Returns 410 Gone so callers know this endpoint will not be re-enabled.
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Public registration is not available. Please use an invitation link."
    )


@router.post("/login")
@limiter.limit("10/minute")
async def login_with_verification(
    request: Request,
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

    if getattr(user, 'role', '') == 'blocked':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended. Contact support."
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

    # Get the proper display name using mapping rules
    display_name = get_display_name(user)

    # Security Fix M3: Only include essential claims in JWT
    access_token = create_access_token(data={
        "sub": user.email,
        "role": user.role,
    })

    refresh_token = None
    try:
        refresh_token = await create_refresh_token_async(db, user.id)
    except Exception as token_err:
        logger.warning(f"Failed to create refresh token for {user.email}: {token_err}")

    logger.info(f"Login successful: {user.email} (Display: {display_name})")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
        "display_name": display_name  # Return display name to frontend
    }


@router.post("/refresh")
async def refresh_access_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token from request body.
    Rotates refresh token on every use.
    """
    if not req.refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    user_id = await verify_refresh_token_async(db, req.refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Revoke old token and issue a new one
    await revoke_refresh_token_async(db, req.refresh_token)

    from sqlalchemy import select
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(data={
        "sub": user.email,
        "role": user.role,
    })
    new_refresh_token = await create_refresh_token_async(db, user.id)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(req: LogoutRequest, db: AsyncSession = Depends(get_db)):
    """
    Revoke refresh token on logout (best-effort).
    """
    if req.refresh_token:
        try:
            await revoke_refresh_token_async(db, req.refresh_token)
        except Exception as err:
            logger.warning(f"Failed to revoke refresh token on logout: {err}")

    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH
# ═══════════════════════════════════════════════════════════════

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
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

        # SECURITY: Reject Google accounts whose email has not been verified by Google.
        # Without this, an attacker can create a Google account with an unverified email
        # and gain access to the platform under that address.
        if not user_info.get('email_verified'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email is not verified. Please verify your Google account first."
            )

        email = user_info['email']
        name = user_info.get('name', 'Google User')

        # Get or create user
        user = await get_or_create_user_by_email_async(db, email, name)

        # Check if this is a new user
        is_new = user.full_name == 'Google User'

        # Generate JWT
        access_token = create_access_token(data={
            "sub": user.email,
            "role": user.role
        })

        refresh_token = None
        try:
            refresh_token = await create_refresh_token_async(db, user.id)
        except Exception as token_err:
            logger.warning(f"Failed to create refresh token for Google user {email}: {token_err}")

        logger.info(f"Google OAuth successful for {email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
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
    db: AsyncSession = Depends(get_db)
):
    """
    Send OTP code to phone number.

    Rate limit: 3 requests per hour per IP to prevent abuse.
    """
    from app.utils.input_sanitization import validate_egyptian_phone

    # SECURITY FIX V10: Strict Egyptian phone validation
    if not validate_egyptian_phone(req.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Egyptian mobile number. Use E.164 format: +201XXXXXXXXX (Vodafone/Orange/Etisalat/WE)"
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
async def verify_otp_login(req: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP and complete phone verification.
    """
    from sqlalchemy import select

    if not sms_service.verify_otp(req.phone_number, req.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )

    result = await db.execute(select(User).filter(User.phone_number == req.phone_number))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this phone number. Please sign up first."
        )

    user.phone_verified = True
    user.is_verified = True
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ Phone verified for user: {user.email} ({user.phone_number})")

    access_token = create_access_token(data={
        "sub": user.email or user.phone_number,
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": False,
    }


# ═══════════════════════════════════════════════════════════════
# EMAIL VERIFICATION
# ═══════════════════════════════════════════════════════════════

@router.post("/send-verification")
async def send_verification(
    req: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send verification email to user.
    """
    from sqlalchemy import select

    result = await db.execute(select(User).filter(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user:
        return {
            "status": "sent",
            "message": "If the email exists, verification link has been sent."
        }

    if user.email_verified:
        return {
            "status": "already_verified",
            "message": "Email is already verified"
        }

    token = create_verification_token()
    user.verification_token = token
    await db.commit()

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
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify email address using token from email link.
    """
    from sqlalchemy import select

    if not is_verification_token_valid(token, purpose="verify"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one."
        )

    result = await db.execute(select(User).filter(User.verification_token == token))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    user.email_verified = True
    user.verification_token = None
    await db.commit()

    consume_verification_token(token, purpose="verify")
    logger.info(f"✅ Email verified: {user.email}")

    return {
        "status": "verified",
        "message": "Email successfully verified! You can now log in."
    }


# ═══════════════════════════════════════════════════════════════
# PASSWORD RESET
# ═══════════════════════════════════════════════════════════════

@router.post("/reset-password")
@limiter.limit("5/hour")
async def request_reset(
    request: Request,
    req: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset link.
    """
    from sqlalchemy import select

    result = await db.execute(select(User).filter(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user:
        return {
            "status": "sent",
            "message": "If the email exists, password reset link has been sent."
        }

    token = create_verification_token(purpose="reset", ttl_seconds=3600)
    user.verification_token = token
    await db.commit()

    try:
        email_service.send_reset_email(req.email, token)
        logger.info(f"✅ Password reset email sent to {req.email}")

        return {
            "status": "sent",
            "message": "Password reset link sent. Please check your email."
        }

    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        return {
            "status": "sent",
            "message": "If the email exists, password reset link has been sent."
        }


@router.post("/reset-password/confirm")
async def confirm_reset(req: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """
    Confirm password reset with token and new password.
    """
    from sqlalchemy import select

    if not is_verification_token_valid(req.token, purpose="reset"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    result = await db.execute(select(User).filter(User.verification_token == req.token))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    user.password_hash = get_password_hash(req.new_password)
    user.verification_token = None
    await db.commit()

    consume_verification_token(req.token, purpose="reset")
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
    request: Request,
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

    # Generate cryptographically secure invitation code using OpenSSL-equivalent method
    invitation_code = generate_secure_token(24)  # 32 character URL-safe token

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

    # Build invitation link — use the request Origin/Referer so the link
    # always matches the domain the user is actually on (works for both
    # localhost dev and any Vercel/production deployment).
    origin = request.headers.get("origin") or request.headers.get("referer", "").rstrip("/")
    if origin:
        # Strip any path from referer (e.g. https://osool-ten.vercel.app/dashboard → https://osool-ten.vercel.app)
        from urllib.parse import urlparse
        parsed = urlparse(origin)
        frontend_url = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else origin
    else:
        frontend_url = os.getenv("FRONTEND_URL", "https://osool-ten.vercel.app")
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
            detail="An account with these details already exists"
        )

    # Create user (pre-verified via invitation, email verification sent separately)
    verification_token = create_verification_token()
    new_user = User(
        full_name=req.full_name,
        email=req.email,
        password_hash=get_password_hash(req.password),
        is_verified=True,   # Can login immediately (invited user)
        email_verified=False,  # Must verify email separately
        verification_token=verification_token,
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

    # Send verification email (non-blocking — don't fail signup if email fails)
    try:
        email_service.send_verification_email(req.email, verification_token)
        logger.info(f"📧 Verification email sent to {req.email}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to send verification email to {req.email}: {e}")

    # Award referral XP to the inviter
    try:
        from app.services.gamification import GamificationEngine
        gamification = GamificationEngine()
        if invitation.created_by_user_id:
            xp_result = await gamification.award_xp(
                user_id=invitation.created_by_user_id,
                action="referral",
                session=db
            )
            logger.info(f"🎮 Awarded {xp_result.get('xp_awarded', 0)} referral XP to user {invitation.created_by_user_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to award referral XP: {e}")

    # Get the proper display name using mapping rules
    display_name = get_display_name(new_user)

    logger.info(f"✅ New user signed up via invitation: {req.email} (Display: {display_name})")

    # Security Fix M3: Only include essential claims in JWT
    access_token = create_access_token(data={
        "sub": new_user.email,
        "role": new_user.role,
    })

    return {
        "status": "success",
        "message": "Account created successfully!",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "full_name": new_user.full_name,
        "display_name": display_name
    }


# ═══════════════════════════════════════════════════════════════
# USER PROFILE
# ═══════════════════════════════════════════════════════════════

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile with proper display name mapping.

    Returns:
    - email: User's email
    - full_name: Original full name from database
    - display_name: Mapped display name (e.g., Sama → "Mrs. Mustafa")
    - role: User role (investor, admin)
    - is_admin: Whether user has admin privileges
    """
    display_name = get_display_name(current_user)
    is_admin = current_user.email.lower() in [e.lower() for e in UNLIMITED_INVITATION_ADMINS]

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "display_name": display_name,
        "role": current_user.role,
        "is_admin": is_admin,
        "invitations_sent": current_user.invitations_sent or 0,
        "invitations_remaining": "unlimited" if is_admin else max(0, MAX_INVITATIONS_PER_USER - (current_user.invitations_sent or 0))
    }


# ═══════════════════════════════════════════════════════════════
# ADMIN: SEED BETA USERS
# ═══════════════════════════════════════════════════════════════

class SeedBetaUsersRequest(BaseModel):
    """Request to seed beta users - requires admin secret"""
    admin_secret: str


# Security Fix C2: Beta accounts loaded from env var instead of hardcoded passwords.
# Set BETA_ACCOUNTS_JSON env var with base64-encoded JSON array of account objects.
# Each object: {"full_name": "...", "email": "...", "password": "...", "role": "admin|investor"}
import json as _json
import secrets as _secrets

def _load_beta_accounts() -> list:
    """Load beta accounts from BETA_ACCOUNTS_JSON env var (base64-encoded JSON)."""
    import base64
    raw = os.getenv("BETA_ACCOUNTS_JSON")
    if not raw:
        logger.info("BETA_ACCOUNTS_JSON not set — no beta accounts configured")
        return []
    try:
        return _json.loads(base64.b64decode(raw))
    except Exception as e:
        logger.error(f"Failed to parse BETA_ACCOUNTS_JSON: {e}")
        return []

BETA_ACCOUNTS = _load_beta_accounts()


@router.post("/admin/seed-beta-users")
async def seed_beta_users(
    req: SeedBetaUsersRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Seed beta users into the database.
    
    Requires admin_secret that matches ADMIN_API_KEY environment variable.
    This is a one-time operation for production setup.
    """
    from sqlalchemy import select
    import hashlib
    
    # Security Fix C3: Use ADMIN_API_KEY with timing-safe comparison
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_API_KEY not configured"
        )
    if not _secrets.compare_digest(req.admin_secret, admin_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret"
        )
    
    if not BETA_ACCOUNTS:
        return {
            "status": "skipped",
            "message": "No beta accounts configured. Set BETA_ACCOUNTS_JSON env var.",
            "created": 0,
            "updated": 0,
            "total": 0
        }
    
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
            new_user = User(
                full_name=account["full_name"],
                email=account["email"],
                password_hash=get_password_hash(account["password"]),
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
        "message": "Beta users seeded successfully",
        "created": created,
        "updated": updated,
        "total": len(BETA_ACCOUNTS)
    }
