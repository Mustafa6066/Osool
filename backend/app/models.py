"""
Osool Database Models
---------------------
Defines the schema for Users, Properties, and Transactions.
Includes pgvector support for AI semantic search.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # KYC Fields - Required for Egyptian FRA compliance
    # Note: nullable=True for backward compatibility with existing users
    # New signups enforce these at application level
    national_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)

    # Authentication Fields
    wallet_address: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="investor") # investor, admin

    # Phase 1: Encrypted wallet private key storage (custodial wallets only)
    # Stores Fernet-encrypted private keys for email-based users
    # NULL for wallet-only users (non-custodial accounts)
    encrypted_private_key: Mapped[str] = mapped_column(Text, nullable=True)

    # Verification Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # Master verification flag
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str] = mapped_column(String, nullable=True)

    # KYC Status Tracking (Phase 7)
    kyc_status: Mapped[str] = mapped_column(String, default="pending")  # pending, verified, rejected
    kyc_verified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship("Transaction", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Basic Info
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=True) # Apartment, Villa, Townhouse, etc.
    location: Mapped[str] = mapped_column(String, index=True)
    compound: Mapped[str] = mapped_column(String, nullable=True)
    developer: Mapped[str] = mapped_column(String, nullable=True)

    # Pricing
    price: Mapped[float] = mapped_column(Float)
    price_per_sqm: Mapped[float] = mapped_column(Float, nullable=True)

    # Size & Layout
    size_sqm: Mapped[int] = mapped_column(Integer)
    bedrooms: Mapped[int] = mapped_column(Integer)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=True)
    finishing: Mapped[str] = mapped_column(String, nullable=True) # e.g., "Fully Finished"

    # Payment Plan
    delivery_date: Mapped[str] = mapped_column(String, nullable=True)
    down_payment: Mapped[int] = mapped_column(Integer, nullable=True) # Percentage
    installment_years: Mapped[int] = mapped_column(Integer, nullable=True)
    monthly_installment: Mapped[float] = mapped_column(Float, nullable=True)

    # External Links
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    nawy_url: Mapped[str] = mapped_column(Text, nullable=True)
    sale_type: Mapped[str] = mapped_column(String, nullable=True) # Resale, Developer

    # Vector Embedding for Semantic Search (1536 dim for OpenAI text-embedding-ada-002)
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=True)

    # Blockchain Integration
    blockchain_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True) # ID on Smart Contract
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="EGP")
    
    # Status
    status: Mapped[str] = mapped_column(String, default="pending") # pending, paid, blockchain_confirmed, failed
    
    # External References
    paymob_order_id: Mapped[str] = mapped_column(String, nullable=True)
    blockchain_tx_hash: Mapped[str] = mapped_column(String, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")
    property = relationship("Property")

class PaymentApproval(Base):
    """
    Manual Bank Transfer Approvals.
    Admins must verify these before blockchain transfer.
    """
    __tablename__ = "payment_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))

    reference_number: Mapped[str] = mapped_column(String, unique=True, index=True) # Bank Ref
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="pending") # pending, approved, rejected

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    """
    Phase 3: Persistent Chat History
    Stores all user-AI conversations for session continuity and cross-device sync.
    """
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String, index=True) # UUID for session tracking
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True) # Null for anonymous users
    role: Mapped[str] = mapped_column(String) # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text) # Message content
    properties_json: Mapped[str] = mapped_column(Text, nullable=True) # JSON array of recommended properties
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_messages")


class RefreshToken(Base):
    """
    Phase 6: Refresh Token System for Secure Session Extension
    Allows users to refresh access tokens without re-authentication.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)  # Hashed refresh token
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class LiquidityPool(Base):
    """
    Phase 6: AMM Liquidity Pools for Property Token Trading
    Each property can have a liquidity pool for instant token trading.
    """
    __tablename__ = "liquidity_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), unique=True, index=True)
    pool_address: Mapped[str] = mapped_column(String, unique=True)  # Smart contract address
    token_reserve: Mapped[float] = mapped_column(Float, default=0)  # Property tokens in pool
    egp_reserve: Mapped[float] = mapped_column(Float, default=0)  # EGP in pool (OEGP stablecoin)
    total_lp_tokens: Mapped[float] = mapped_column(Float, default=0)  # Total LP tokens issued
    total_volume_24h: Mapped[float] = mapped_column(Float, default=0)  # 24h trading volume
    total_fees_earned: Mapped[float] = mapped_column(Float, default=0)  # Total fees accumulated
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property")


class Trade(Base):
    """
    Phase 6: Trading History for AMM Swaps
    Records all property token swaps through liquidity pools.
    """
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("liquidity_pools.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    trade_type: Mapped[str] = mapped_column(String)  # 'BUY' or 'SELL'
    token_amount: Mapped[float] = mapped_column(Float)  # Amount of property tokens
    egp_amount: Mapped[float] = mapped_column(Float)  # Amount of EGP
    execution_price: Mapped[float] = mapped_column(Float)  # Price at execution (EGP per token)
    slippage_percent: Mapped[float] = mapped_column(Float)  # Actual slippage
    fee_amount: Mapped[float] = mapped_column(Float)  # Fee paid (0.3%)
    tx_hash: Mapped[str] = mapped_column(String, nullable=True)  # Blockchain transaction hash
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, completed, failed
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pool = relationship("LiquidityPool")
    user = relationship("User")


class LiquidityPosition(Base):
    """
    Phase 6: Liquidity Provider Positions
    Tracks user LP token holdings and their value.
    """
    __tablename__ = "liquidity_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("liquidity_pools.id"), index=True)
    lp_tokens: Mapped[float] = mapped_column(Float)  # Amount of LP tokens owned
    initial_token_amount: Mapped[float] = mapped_column(Float)  # Tokens deposited initially
    initial_egp_amount: Mapped[float] = mapped_column(Float)  # EGP deposited initially
    fees_earned: Mapped[float] = mapped_column(Float, default=0)  # Accumulated fees
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User")
    pool = relationship("LiquidityPool")
