"""
Osool Authentication Module
---------------------------
Handles JWT generation, password hashing, and Web3 Wallet Verification (SIWE).
Phase 2: Enhanced with Google OAuth, Email Verification, Password Reset.
Phase 4: Security hardening - no hardcoded fallbacks.
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from eth_account import Account
from eth_account.messages import encode_defunct
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

# Configuration - Phase 4: No fallback secrets (will raise error if not set)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("❌ JWT_SECRET_KEY environment variable must be set for production")

# DEBUG: Log JWT_SECRET_KEY info for Railway troubleshooting
print(f"🔍 [DEBUG] JWT_SECRET_KEY length: {len(SECRET_KEY)}")
print(f"🔍 [DEBUG] JWT_SECRET_KEY first 10 chars: {SECRET_KEY[:10]}...")
print(f"🔍 [DEBUG] JWT_SECRET_KEY last 10 chars: ...{SECRET_KEY[-10:]}")

# Validate secret key strength (minimum 32 characters)
if len(SECRET_KEY) < 32:
    raise ValueError(f"❌ JWT_SECRET_KEY must be at least 32 characters long for security (got {len(SECRET_KEY)} characters)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 Hours (Phase 6: Reduced from 30 days)
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 Days for refresh tokens

# Token blacklist (for logout functionality)
# In production, use Redis for distributed blacklist
_token_blacklist = set()  # Stores invalidated token JTI (JWT ID)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    """
    OPTIONAL authentication.
    Returns User object if token is valid, None if not provided or invalid.
    Does NOT raise 401.
    """
    if not token:
        return None
        
    try:
        # Re-use logic from get_current_user but verify token manually since we can't call get_current_user directly 
        # (it relies on strict oauth2_scheme which might conflict in dependency injection if we nest them awkwardly)
        # Actually, we can just decode here.
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        wallet: str = payload.get("wallet")
        
        if username is None and wallet is None:
            return None
            
        if username:
            user = db.query(User).filter(User.email == username).first()
        elif wallet:
            user = db.query(User).filter(User.wallet_address == wallet).first()
        else:
            return None
            
        return user
    except JWTError:
        return None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token with enhanced security.

    Includes:
    - Expiration time (exp)
    - Issued at time (iat)
    - JWT ID (jti) for blacklisting
    """
    import uuid

    to_encode = data.copy()
    now = datetime.utcnow()

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add security claims
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())  # Unique token ID for blacklisting
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def invalidate_token(token: str):
    """
    Add token to blacklist (logout functionality).

    In production, use Redis with TTL matching token expiration.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")

        if jti:
            _token_blacklist.add(jti)
            logger.info(f"Token {jti[:8]}... invalidated")
            return True
        return False
    except JWTError as e:
        logger.warning(f"Failed to invalidate token: {e}")
        return False


def is_token_blacklisted(jti: str) -> bool:
    """
    Check if token is blacklisted.

    Args:
        jti: JWT ID from token payload

    Returns:
        True if token is blacklisted (invalidated)
    """
    return jti in _token_blacklist

# ═══════════════════════════════════════════════════════════════
# WEB3 AUTHENTICATION (SIWE)
# ═══════════════════════════════════════════════════════════════

def verify_wallet_signature(address: str, message: str, signature: str) -> bool:
    """
    Verifies that a message was signed by the owner of the address.
    Uses EIP-191 standard (eth_account).
    """
    try:
        # Encode message as "defunct" (Ethereum standard prefix)
        encoded_msg = encode_defunct(text=message)
        
        # Recover address from signature
        recovered_address = Account.recover_message(encoded_msg, signature=signature)
        
        # Case-insensitive comparison
        return recovered_address.lower() == address.lower()
    except Exception as e:
        print(f"Signature Verification Failed: {e}")
        return False

def get_or_create_user_by_wallet(db: Session, wallet_address: str, email: Optional[str] = None):
    """
    Finds a user by wallet. If not found, creates one.
    If email is provided, links it.
    """
    user = db.query(User).filter(User.wallet_address == wallet_address).first()
    
    if not user:
        # Check if email exists (Linking scenario)
        if email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.wallet_address = wallet_address
                db.commit()
                return user

        # Create new anonymous wallet user
        user = User(
            wallet_address=wallet_address,
            email=email, # Might be None
            full_name="Wallet User",
            role="investor",
            is_verified=True # Wallet ownership proves identity effectively
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Blacklisted token attempted: {jti[:8]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Token can contain 'sub' (email) or 'wallet' (address)
        username: str = payload.get("sub")
        wallet: str = payload.get("wallet")
        # role: str = payload.get("role") # Optionally validate role here

        if username is None and wallet is None:
            raise credentials_exception

        token_data = {"sub": username, "wallet": wallet}
    except JWTError:
        raise credentials_exception
        
    # Find user by either metric
    if token_data["sub"]:
        user = db.query(User).filter(User.email == token_data["sub"]).first()
    elif token_data["wallet"]:
        user = db.query(User).filter(User.wallet_address == token_data["wallet"]).first()
    else:
        user = None
        
    if user is None:
        raise credentials_exception
    return user

def bind_wallet_to_user(db: Session, user_id: int, wallet_address: str) -> bool:
    """
    Binds a wallet address to an existing user (for KYC).
    Returns True if successful, False if wallet already bound to another user.
    """
    # Check if wallet already bound to another user
    existing = db.query(User).filter(User.wallet_address == wallet_address).first()
    if existing and existing.id != user_id:
        return False  # Wallet belongs to someone else
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.wallet_address = wallet_address
        db.commit()
        return True
    return False

# ═══════════════════════════════════════════════════════════════
# CUSTODIAL WALLETS (Email Users)
# ═══════════════════════════════════════════════════════════════

def create_custodial_wallet() -> dict:
    """
    Create encrypted custodial wallet for new users.
    Private keys are encrypted using Fernet (AES-128-CBC) before storage.

    Returns:
        dict: {
            "address": str - Ethereum address (0x...)
            "encrypted_private_key": str - Fernet-encrypted private key
        }

    Security Implementation:
        - Uses Fernet symmetric encryption (NIST approved AES-128-CBC)
        - Encryption key stored in WALLET_ENCRYPTION_KEY environment variable
        - Compliant with CBE Law 194 of 2020 Article 8 (Data Protection)
        - Keys never logged or exposed in plaintext

    Raises:
        ValueError: If WALLET_ENCRYPTION_KEY is not set

    Production Notes:
        - Store WALLET_ENCRYPTION_KEY in AWS KMS / Azure Key Vault / GCP Secret Manager
        - Never commit encryption keys to version control
        - Rotate encryption keys periodically
    """
    acct = Account.create()

    # Encrypt private key before returning
    encrypted_pk = encrypt_private_key(acct.key.hex())

    return {
        "address": acct.address,
        "encrypted_private_key": encrypted_pk
    }

def encrypt_private_key(private_key: str) -> str:
    """
    Encrypt wallet private key before database storage using Fernet (AES-128-CBC).

    Args:
        private_key: Unencrypted private key (hex string)

    Returns:
        Encrypted private key as base64 string

    Raises:
        ValueError: If WALLET_ENCRYPTION_KEY is not set in environment

    Security Notes:
        - Uses Fernet symmetric encryption (AES-128 in CBC mode)
        - Encryption key MUST be stored securely (AWS KMS, Azure Key Vault, etc.)
        - Never commit encryption keys to version control
        - Rotate encryption keys periodically in production
    """
    from cryptography.fernet import Fernet

    encryption_key = os.getenv("WALLET_ENCRYPTION_KEY")
    if not encryption_key:
        raise ValueError(
            "WALLET_ENCRYPTION_KEY environment variable must be set for production. "
            "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )

    try:
        fernet = Fernet(encryption_key.encode())
        encrypted = fernet.encrypt(private_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Wallet encryption failed: {e}")
        raise ValueError(f"Failed to encrypt private key: {str(e)}")

def decrypt_private_key(encrypted_key: str) -> str:
    """
    Decrypt wallet private key for transaction signing.

    Args:
        encrypted_key: Encrypted private key (base64 string from database)

    Returns:
        Decrypted private key as hex string

    Raises:
        ValueError: If WALLET_ENCRYPTION_KEY is not set or decryption fails

    Security Notes:
        - Only decrypt in-memory when needed for transaction signing
        - Never log or return decrypted keys in API responses
        - Clear decrypted key from memory immediately after use
    """
    from cryptography.fernet import Fernet

    encryption_key = os.getenv("WALLET_ENCRYPTION_KEY")
    if not encryption_key:
        raise ValueError("WALLET_ENCRYPTION_KEY environment variable must be set")

    try:
        fernet = Fernet(encryption_key.encode())
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Wallet decryption failed: {e}")
        raise ValueError(f"Failed to decrypt private key: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH (Phase 2)
# ═══════════════════════════════════════════════════════════════

async def verify_google_token(id_token: str) -> dict:
    """
    Verify Google ID token and extract user info.

    Args:
        id_token: Google ID token from OAuth flow

    Returns:
        Dictionary with user info: {email, name, picture}

    Raises:
        HTTPException if token is invalid
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Google token"
                )

            user_info = response.json()

            # Verify token is for our app (if GOOGLE_CLIENT_ID is set)
            expected_client_id = os.getenv('GOOGLE_CLIENT_ID')
            if expected_client_id and user_info.get('aud') != expected_client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token not issued for this application"
                )

            return {
                'email': user_info.get('email'),
                'name': user_info.get('name', 'Google User'),
                'picture': user_info.get('picture'),
                'email_verified': user_info.get('email_verified', False)
            }

    except httpx.RequestError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not verify Google token"
        )


def get_or_create_user_by_email(db: Session, email: str, full_name: str) -> User:
    """
    Get existing user by email or create new one.
    Used for Google OAuth and email signup.

    Args:
        db: Database session
        email: User email address
        full_name: User's full name

    Returns:
        User object
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create custodial wallet for email users
        # Phase 1 Security: Returns encrypted private key
        wallet = create_custodial_wallet()

        user = User(
            email=email,
            full_name=full_name,
            wallet_address=wallet['address'],
            encrypted_private_key=wallet['encrypted_private_key'], # Phase 1: Store encrypted key
            email_verified=True,  # Google/OAuth users are pre-verified
            is_verified=True,
            role='investor'
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"✅ Created new user via email: {email}")

    return user


# ═══════════════════════════════════════════════════════════════
# REFRESH TOKEN SYSTEM (Phase 6)
# ═══════════════════════════════════════════════════════════════

import secrets
import hashlib
from datetime import datetime, timedelta
from app.models import RefreshToken

def create_refresh_token(db: Session, user_id: int) -> str:
    """
    Create a new refresh token for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Raw refresh token (only time it's available unhashed)
    """
    # Generate secure random token
    raw_token = secrets.token_urlsafe(32)

    # Hash token for storage (like passwords)
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Store hashed token in database
    refresh_token = RefreshToken(
        user_id=user_id,
        token=hashed_token,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()

    logger.info(f"✅ Created refresh token for user {user_id}")
    return raw_token


def verify_refresh_token(db: Session, raw_token: str) -> Optional[int]:
    """
    Verify a refresh token and return the user ID if valid.

    Args:
        db: Database session
        raw_token: The raw refresh token from client

    Returns:
        User ID if token is valid, None otherwise
    """
    # Hash the provided token
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    # Find token in database
    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == hashed_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if token_record:
        return token_record.user_id
    return None


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """
    Revoke a refresh token (logout).

    Args:
        db: Database session
        raw_token: The raw refresh token from client

    Returns:
        True if token was revoked, False if not found
    """
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

    token_record = db.query(RefreshToken).filter(
        RefreshToken.token == hashed_token
    ).first()

    if token_record:
        token_record.is_revoked = True
        db.commit()
        logger.info(f"🔒 Revoked refresh token for user {token_record.user_id}")
        return True
    return False


def revoke_all_user_tokens(db: Session, user_id: int):
    """
    Revoke all refresh tokens for a user (e.g., password change, security incident).

    Args:
        db: Database session
        user_id: User ID
    """
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()
    logger.info(f"🔒 Revoked all refresh tokens for user {user_id}")

