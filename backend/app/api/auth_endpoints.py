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
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User
from app.auth import (
    verify_google_token,
    get_or_create_user_by_email,
    create_access_token,
    get_password_hash,
    verify_password,
    create_custodial_wallet
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


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    is_new_user: bool


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
    Verify OTP and login/signup user.

    Creates new user if phone number doesn't exist.
    """
    # Verify OTP
    if not sms_service.verify_otp(req.phone_number, req.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )

    # Get or create user by phone
    user = db.query(User).filter(User.phone_number == req.phone_number).first()

    is_new = False
    if not user:
        # Create new user
        wallet = create_custodial_wallet()
        user = User(
            phone_number=req.phone_number,
            full_name="Phone User",
            wallet_address=wallet['address'],
            phone_verified=True,
            is_verified=True,
            role='investor'
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        is_new = True
        logger.info(f"✅ Created new user via phone: {req.phone_number}")
    else:
        # Mark phone as verified
        user.phone_verified = True
        db.commit()

    # Generate JWT
    access_token = create_access_token(data={
        "sub": user.email or user.phone_number,
        "wallet": user.wallet_address,
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": is_new
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
