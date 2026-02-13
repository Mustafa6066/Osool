"""
Osool Database Models
---------------------
Defines the schema for Users, Properties, and Transactions.
Includes pgvector support for AI semantic search (when available).
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base

# Try to import pgvector, fallback to Text if not available
PGVECTOR_AVAILABLE = False
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    # Fallback: Use Text column to store JSON representation of embeddings
    Vector = lambda dim: Text

class User(Base):
    """
    User Model - Phase 1: Simplified for email/password auth

    Phase 1: Email, password, full_name (required)
    Phase 2: Will add back wallet_address, national_id, phone_number for KYC
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Phase 1: Core Authentication Fields
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="investor") # investor, admin

    # Phase 2: KYC & Web3 Fields (kept for database compatibility, not used in Phase 1)
    national_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    wallet_address: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
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

    # Invitation tracking
    invitations_sent: Mapped[int] = mapped_column(Integer, default=0)  # Count of invitations sent
    invited_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)  # Who invited this user

    transactions = relationship("Transaction", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    invitations_created = relationship("Invitation", back_populates="created_by_user", foreign_keys="Invitation.created_by_user_id")


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
    price: Mapped[float] = mapped_column(Float, index=True)
    price_per_sqm: Mapped[float] = mapped_column(Float, nullable=True)

    # Size & Layout
    size_sqm: Mapped[int] = mapped_column(Integer, index=True)
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
    """Phase 2: Blockchain transaction tracking"""
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
    Phase 2: Manual Bank Transfer Approvals
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
    Phase 2: AMM Liquidity Pools for Property Token Trading
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
    Phase 2: Trading History for AMM Swaps
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
    Phase 2: Liquidity Provider Positions
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



class MarketIndicator(Base):
    """
    Dynamic Economic Indicators
    Stores key market rates like inflation, bank interest, gold appreciation, etc.
    Updated via Admin Dashboard or Cron Job.

    Key indicators:
    - inflation_rate: Egyptian inflation rate (e.g., 0.136 for 13.6%)
    - bank_cd_rate: Bank certificate of deposit rate (e.g., 0.22 for 22%)
    - property_appreciation: Real estate appreciation rate (e.g., 0.145 for 14.5%)
    - rental_yield_avg: Average rental yield (e.g., 0.075 for 7.5%)
    - gold_appreciation: Gold price appreciation rate
    """
    __tablename__ = "market_indicators"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(200), nullable=True)  # Data source (e.g., "Central Bank of Egypt")
    last_updated: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ConversationAnalytics(Base):
    """
    Phase 3: AI Conversation Analytics
    Tracks AI agent performance for optimization and conversion analysis.
    Used for: lead scoring, conversion tracking, A/B testing, performance metrics.
    """
    __tablename__ = "conversation_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)  # NULL for anonymous users

    # Segmentation (from customer_profiles.py)
    customer_segment: Mapped[str] = mapped_column(String, nullable=True)  # luxury, first_time, savvy, unknown
    lead_temperature: Mapped[str] = mapped_column(String, nullable=True)  # hot, warm, cold
    lead_score: Mapped[int] = mapped_column(Integer, default=0)

    # Behavior Tracking
    properties_viewed: Mapped[int] = mapped_column(Integer, default=0)
    tools_used: Mapped[dict] = mapped_column(String, nullable=True)  # JSON list of tool usage
    objections_raised: Mapped[dict] = mapped_column(String, nullable=True)  # JSON list of objections

    # Outcome Metrics
    conversion_status: Mapped[str] = mapped_column(String, default="browsing")  # browsing, reserved, abandoned, viewing_scheduled
    reservation_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    viewing_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Engagement Metrics
    session_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Additional Context
    user_intent: Mapped[str] = mapped_column(String, nullable=True)  # residential, investment, resale, unknown
    budget_mentioned: Mapped[int] = mapped_column(Integer, nullable=True)  # Budget in EGP
    preferred_locations: Mapped[str] = mapped_column(String, nullable=True)  # JSON list of locations

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class Invitation(Base):
    """
    Invitation System for Controlled User Registration
    ---------------------------------------------------
    - Each invitation code can only be used once
    - Regular users can generate max 2 invitations
    - Admin users (Mustafa, Hani, Abady, Sama) can generate unlimited invitations
    """
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)  # Unique invitation code

    # Creator info
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Usage info
    used_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)  # Who used this invitation
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    used_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)  # Optional expiration

    # Relationships
    created_by_user = relationship("User", back_populates="invitations_created", foreign_keys=[created_by_user_id])


class UserMemory(Base):
    """
    Cross-Session Memory Persistence
    ---------------------------------
    Stores key customer facts (budget, preferences, deal-breakers) so the AI 
    can recall them across sessions. Creates the "family consultant" experience.
    
    Example: Session 1 user says "wife hates open kitchens" → stored.
             Session 2 user looks at unit with American kitchen → AI warns them.
    """
    __tablename__ = "user_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    
    # Core memory fields (JSON serialized)
    memory_json: Mapped[str] = mapped_column(Text, nullable=True)  # Full ConversationMemory dict
    
    # Quick-access fields for common lookups
    budget_min: Mapped[int] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int] = mapped_column(Integer, nullable=True)
    preferred_areas: Mapped[str] = mapped_column(String, nullable=True)  # Comma-separated
    investment_vs_living: Mapped[str] = mapped_column(String, nullable=True)
    
    # Free-text preferences (e.g., "wife hates open kitchens", "needs garden")
    preferences_text: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
