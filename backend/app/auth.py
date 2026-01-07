"""
Osool Authentication Module
---------------------------
Handles JWT generation, password hashing, and Web3 Wallet Verification (SIWE).
"""

import os
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

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200 # 30 Days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    # Ensure role is in payload if passed in data, otherwise it's handled by caller
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
    Generates an Ethereum wallet for an email-based user.
    Returns: {"address": str, "private_key": str}
    ⚠️ In Production: Encrypt the private key before identifying it!
    """
    acct = Account.create()
    return {"address": acct.address, "private_key": acct.key.hex()}

def verify_otp(phone_number: str, otp_code: str) -> bool:
    """
    MOCK: Verifies OTP Code for high-value transactions.
    Integration: Twilio / Vonage.
    """
    print(f"📱 Validating OTP '{otp_code}' for {phone_number}")
    if otp_code == "123456": # Mock backdoor
        return True
    return False

