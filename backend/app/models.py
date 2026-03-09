"""
Osool Database Models
---------------------
Defines the schema for Users, Properties, Transactions, and Dual-Engine models
(Developers, Areas, Projects, Intents, Leads, SEO Pages, Campaigns, Email Events).
Includes pgvector support for AI semantic search (when available).
"""

import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base


# ═══════════════════════════════════════════════════════════════
# DUAL-ENGINE ENUMS
# ═══════════════════════════════════════════════════════════════

class ProjectType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    RESORT = "resort"


class ProjectStatus(str, enum.Enum):
    PRE_LAUNCH = "pre_launch"
    UNDER_CONSTRUCTION = "under_construction"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"


class IntentType(str, enum.Enum):
    COMPARISON = "comparison"
    PRICE_CHECK = "price_check"
    ROI_FORECAST = "roi_forecast"
    DEVELOPER_REVIEW = "developer_review"
    AREA_ANALYSIS = "area_analysis"
    PAYMENT_PLAN = "payment_plan"
    GENERAL_ADVICE = "general_advice"
    DELIVERY_STATUS = "delivery_status"


class EmailStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"


class SEOPageType(str, enum.Enum):
    COMPARISON = "comparison"
    ROI_TRACKER = "roi_tracker"
    PROJECT_DEEPDIVE = "project_deepdive"
    PILLAR_GUIDE = "pillar_guide"


class PageStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    PUBLISHED = "published"
    ARCHIVED = "archived"

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
    Phase 2: Will add national_id, phone_number for KYC
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Phase 1: Core Authentication Fields
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="investor") # investor, admin

    # Phase 2: KYC Fields (kept for database compatibility, not used in Phase 1)
    national_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    # wallet_address and encrypted_private_key columns removed (deprecated)

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
    sale_type: Mapped[str] = mapped_column(String, nullable=True) # Resale, Developer, Nawy Now

    # Resale / Delivery Fields (v2)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    is_cash_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    land_area: Mapped[int] = mapped_column(Integer, nullable=True)  # Land area (separate from BUA size_sqm)
    nawy_reference: Mapped[str] = mapped_column(String, nullable=True)  # Nawy property ID
    is_nawy_now: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)  # Nawy mortgage product
    scraped_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Vector Embedding for Semantic Search (1536 dim for OpenAI text-embedding-3-small)
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=True)

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Transaction(Base):
    """Payment transaction tracking"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="EGP")
    
    # Status
    status: Mapped[str] = mapped_column(String, default="pending") # pending, paid, confirmed, failed
    
    # External References
    paymob_order_id: Mapped[str] = mapped_column(String, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")
    property = relationship("Property")

class PaymentApproval(Base):
    """
    Phase 2: Manual Bank Transfer Approvals
    Admins must verify these before confirming the transaction.
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


# ═══════════════════════════════════════════════════════════════
# GAMIFICATION MODELS (Phase 9: Professional Investor Gamification)
# ═══════════════════════════════════════════════════════════════

class InvestorProfile(Base):
    """
    Investor Progression & Gamification Profile
    --------------------------------------------
    Tracks XP, level, streaks, and investment readiness.
    Levels: curious -> informed -> analyst -> strategist -> mogul
    """
    __tablename__ = "investor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    # Progression
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(20), default="curious")
    investment_readiness_score: Mapped[int] = mapped_column(Integer, default=0)

    # Streaks
    login_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Activity tracking (JSON via Text)
    areas_explored: Mapped[str] = mapped_column(Text, default="{}")
    tools_used: Mapped[str] = mapped_column(Text, default="{}")
    properties_analyzed: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


# ═══════════════════════════════════════════════════════════════
# TICKETING SYSTEM MODELS
# ═══════════════════════════════════════════════════════════════

class Ticket(Base):
    """
    Support Ticket System
    ---------------------
    Users create tickets for support inquiries.
    Only admins can see all tickets; users see only their own.
    """
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general")  # general, payment, property, technical, account
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high, urgent
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open, in_progress, resolved, closed

    assigned_to: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    closed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="tickets")
    assigned_admin = relationship("User", foreign_keys=[assigned_to])
    replies = relationship("TicketReply", back_populates="ticket", order_by="TicketReply.created_at")


class TicketReply(Base):
    """
    Ticket Reply / Message Thread
    Each reply belongs to a ticket, from either the user or an admin.
    """
    __tablename__ = "ticket_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_admin_reply: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="replies")
    user = relationship("User")


class Achievement(Base):
    """Achievement badge definitions. Seeded on startup."""
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title_en: Mapped[str] = mapped_column(String(100))
    title_ar: Mapped[str] = mapped_column(String(100))
    description_en: Mapped[str] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="award")
    category: Mapped[str] = mapped_column(String(30))
    xp_reward: Mapped[int] = mapped_column(Integer, default=50)
    requirement_type: Mapped[str] = mapped_column(String(30))
    requirement_value: Mapped[int] = mapped_column(Integer, default=1)
    tier: Mapped[str] = mapped_column(String(10), default="bronze")


class UserAchievement(Base):
    """Tracks which achievements a user has unlocked."""
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"), index=True)
    unlocked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    achievement = relationship("Achievement")


class UserFavorite(Base):
    """Property shortlist / favorites."""
    __tablename__ = "user_favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    added_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    property = relationship("Property")


class SavedSearch(Base):
    """Background search agents that notify on matching properties."""
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    filters_json: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    match_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


# ═══════════════════════════════════════════════════════════════
# GEOPOLITICAL & MACROECONOMIC AWARENESS LAYER
# ═══════════════════════════════════════════════════════════════

class GeopoliticalEvent(Base):
    """
    Geopolitical & Macroeconomic Events
    ------------------------------------
    Stores curated geopolitical and macro-economic events that affect
    Egyptian real estate investment decisions. Fed by the geopolitical
    scraper and consumed by the GeopoliticalLayer in the AI engine.

    Impact mapping examples:
    - Red Sea tensions → construction materials cost ↑ → off-plan advantage
    - CBE rate decisions → mortgage affordability shifts
    - USD/EGP movements → foreign investment inflow / capital preservation plays
    - Oil price spikes → cement/rebar cost → developer price adjustments
    """
    __tablename__ = "geopolitical_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Core Event Data
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=True)  # e.g., "Reuters", "CBE", "Trading Economics"
    source_url: Mapped[str] = mapped_column(Text, nullable=True)
    event_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Classification
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Categories: conflict, monetary_policy, currency, oil_energy, trade, inflation,
    #             fiscal_policy, foreign_investment, construction_costs, regulation

    region: Mapped[str] = mapped_column(String(50), default="middle_east")
    # Regions: egypt, middle_east, global

    impact_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Impact: high, medium, low

    # Real Estate Impact Tags (JSON array stored as text)
    # e.g. '["inflation_hedge", "construction_costs", "currency_devaluation", "supply_chain"]'
    impact_tags: Mapped[str] = mapped_column(Text, nullable=True)

    # AI-generated real estate advisory based on this event
    real_estate_impact: Mapped[str] = mapped_column(Text, nullable=True)

    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)


# ═══════════════════════════════════════════════════════════════
# DUAL-ENGINE: MARKETING & SEO PLATFORM MODELS
# ═══════════════════════════════════════════════════════════════

class Developer(Base):
    """
    Real estate developer profiles for programmatic SEO comparison pages.
    Stores scores, Arabic names, and aggregated metrics.
    """
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    logo: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str] = mapped_column(Text, nullable=True)
    founded_year: Mapped[int] = mapped_column(Integer, nullable=True)
    total_projects: Mapped[int] = mapped_column(Integer, default=0)
    avg_delivery_score: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    avg_finish_quality: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    avg_resale_retention: Mapped[float] = mapped_column(Float, default=0)  # percentage
    payment_flexibility: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    overall_score: Mapped[float] = mapped_column(Float, default=0)  # composite 0-100
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    seo_projects = relationship("SEOProject", back_populates="developer")


class Area(Base):
    """
    Neighborhood/area profiles for ROI tracker SEO pages.
    Stores price metrics, growth data, and Arabic translations.
    """
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)  # Cairo, Alexandria, North Coast
    description: Mapped[str] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str] = mapped_column(Text, nullable=True)
    avg_price_per_meter: Mapped[float] = mapped_column(Float, default=0)
    price_growth_ytd: Mapped[float] = mapped_column(Float, default=0)
    predicted_roi_5y: Mapped[float] = mapped_column(Float, default=0)
    rental_yield: Mapped[float] = mapped_column(Float, default=0)
    liquidity_score: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    demand_score: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    seo_projects = relationship("SEOProject", back_populates="area")
    price_history = relationship("PriceHistory", back_populates="area")


class SEOProject(Base):
    """
    Curated project records for programmatic SEO deep-dive pages.
    Named SEOProject to avoid collision with existing Property model.
    Links to Developer and Area for relational queries.
    """
    __tablename__ = "seo_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    developer_id: Mapped[int] = mapped_column(ForeignKey("developers.id"), nullable=False, index=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str] = mapped_column(Text, nullable=True)
    project_type: Mapped[str] = mapped_column(String(30), default=ProjectType.RESIDENTIAL.value)
    status: Mapped[str] = mapped_column(String(30), default=ProjectStatus.UNDER_CONSTRUCTION.value)
    launch_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_delivery: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_delivery: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    min_price_per_meter: Mapped[float] = mapped_column(Float, default=0)
    max_price_per_meter: Mapped[float] = mapped_column(Float, default=0)
    avg_price_per_meter: Mapped[float] = mapped_column(Float, default=0)
    min_unit_size: Mapped[float] = mapped_column(Float, nullable=True)  # sqm
    max_unit_size: Mapped[float] = mapped_column(Float, nullable=True)
    down_payment_min: Mapped[float] = mapped_column(Float, nullable=True)  # percentage
    installment_years: Mapped[int] = mapped_column(Integer, nullable=True)
    predicted_roi_1y: Mapped[float] = mapped_column(Float, default=0)
    predicted_roi_3y: Mapped[float] = mapped_column(Float, default=0)
    predicted_roi_5y: Mapped[float] = mapped_column(Float, default=0)
    resale_value_retention: Mapped[float] = mapped_column(Float, default=0)
    construction_progress: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    unit_types: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array string
    amenities: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array string
    images: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array string
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lng: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    developer = relationship("Developer", back_populates="seo_projects")
    area = relationship("Area", back_populates="seo_projects")
    price_history = relationship("PriceHistory", back_populates="project")


class PriceHistory(Base):
    """
    Historical price/m² data for projects and areas.
    Used for trend charts on ROI and project pages.
    """
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("seo_projects.id"), nullable=True, index=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), nullable=True, index=True)
    price_per_m2: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("SEOProject", back_populates="price_history")
    area = relationship("Area", back_populates="price_history")


class ChatIntent(Base):
    """
    Structured intent extracted from chat messages.
    Fed by the intent extractor after each user message.
    Consumed by the intent aggregator cron and admin heatmap.
    """
    __tablename__ = "chat_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    intent_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entities: Mapped[str] = mapped_column(Text, nullable=True)  # JSON: {developers, areas, projects, priceRange}
    segment: Mapped[str] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    raw_query: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class LeadProfile(Base):
    """
    Lead scoring and segmentation profile.
    One per user, updated after each chat interaction.
    Drives email drip sequences and retargeting.
    """
    __tablename__ = "lead_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=0)  # 0-100
    stage: Mapped[str] = mapped_column(String(30), default="new")  # new, engaged, hot, qualified, converted, lost
    segment: Mapped[str] = mapped_column(String(50), nullable=True)  # expat_investor, domestic_hnw, first_time, institutional
    budget_min: Mapped[float] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float] = mapped_column(Float, nullable=True)
    preferred_areas: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    preferred_types: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array
    timeline: Mapped[str] = mapped_column(String(50), nullable=True)  # immediate, 3months, 6months, 1year
    risk_appetite: Mapped[str] = mapped_column(String(50), nullable=True)  # conservative, moderate, aggressive
    investment_goal: Mapped[str] = mapped_column(String(50), nullable=True)  # primary_residence, investment, retirement, rental
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    email_sequence_step: Mapped[int] = mapped_column(Integer, default=0)
    converted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class EmailEvent(Base):
    """
    Tracks all email events for drip sequence management.
    Updated via Resend webhooks (delivery, open, click, bounce).
    """
    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    email_type: Mapped[str] = mapped_column(String(100), nullable=True)  # welcome, drip_1, drip_2, drip_3, price_alert, report, custom
    subject: Mapped[str] = mapped_column(String(500), nullable=True)
    resend_id: Mapped[str] = mapped_column(String(200), nullable=True, index=True)  # Resend API message ID
    status: Mapped[str] = mapped_column(String(20), default=EmailStatus.QUEUED.value)
    sent_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=True)  # JSON for extra data
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class SEOPage(Base):
    """
    Tracks programmatic SEO pages: generation source, status, and performance.
    Pages are auto-generated from intent aggregation or manually created.
    """
    __tablename__ = "seo_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(500), nullable=True)
    meta_desc: Mapped[str] = mapped_column(Text, nullable=False)
    meta_desc_ar: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=PageStatus.DRAFT.value, index=True)
    generated_from: Mapped[str] = mapped_column(String(50), nullable=True)  # intent_aggregation, manual, seed
    source_intents: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of intent IDs
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    chat_conv_rate: Mapped[float] = mapped_column(Float, default=0)  # % of viewers who engaged chat
    content_json: Mapped[str] = mapped_column(Text, nullable=True)  # JSON: generated page content
    last_built: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AdCampaign(Base):
    """
    Ad campaign performance tracker for Meta, Google, LinkedIn.
    Updated by the weekly ad optimizer cron and manual input.
    """
    __tablename__ = "ad_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    platform: Mapped[str] = mapped_column(String(30), nullable=False)  # meta, google, linkedin
    campaign_id: Mapped[str] = mapped_column(String(200), nullable=False)  # external platform ID
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")
    target_segment: Mapped[str] = mapped_column(String(100), nullable=True)
    budget: Mapped[float] = mapped_column(Float, nullable=True)
    spend: Mapped[float] = mapped_column(Float, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    roas: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RetargetingRule(Base):
    """
    Behavior-based retargeting rules that map user actions to ad audiences.
    E.g., visited comparison page but no chat → audience:comparison_browsers
    """
    __tablename__ = "retargeting_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # page_visit, chat_drop, chat_topic, repeat_visit
    trigger_config: Mapped[str] = mapped_column(Text, nullable=True)  # JSON: {page, minVisits, topic}
    ad_template: Mapped[str] = mapped_column(String(200), nullable=True)
    audience: Mapped[str] = mapped_column(String(200), nullable=True)  # Meta/Google audience ID
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WaitlistEntry(Base):
    """Premium waitlist signups from marketing pages."""
    __tablename__ = "waitlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    segment: Mapped[str] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(200), nullable=True)  # utm_source or referral
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    """Generated personalized ROI reports for users."""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # roi_comparison, area_analysis, developer_audit
    content: Mapped[str] = mapped_column(Text, nullable=True)  # JSON structured report data
    pdf_url: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
