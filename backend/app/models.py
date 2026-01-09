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
    national_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True) # KYC
    wallet_address: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=True) # For Auth
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)  # For profile completion
    role: Mapped[str] = mapped_column(String, default="investor") # investor, admin
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Phase 2: Email and Phone Verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str] = mapped_column(String, nullable=True)

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
