"""
Seed Beta Users for Osool Phase 1 Launch (Standalone Version)
--------------------------------------------------------------
Creates 14 beta accounts for testing and investor demos.
This version is designed to run locally with Railway environment variables.

Usage:
    railway run -s Osool python backend/scripts/seed_beta_users_standalone.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import only what's needed
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, Column, String, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase


# Password hashing using bcrypt directly
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


# Minimal models for seeding (matching production schema)
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    invitations_sent = Column(Integer, default=0)
    invited_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Invitation(Base):
    """Invitation table for controlled user registration"""
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    created_by_user_id = Column(Integer, nullable=False)
    used_by_user_id = Column(Integer, nullable=True)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)


BETA_USERS = [
    # Core Team (4) - Each has unique password - CAN GENERATE UNLIMITED INVITATIONS
    {"email": "mustafa@osool.eg", "full_name": "Mustafa", "password": "Mustafa@Osool2025!", "role": "admin"},
    {"email": "hani@osool.eg", "full_name": "Hani", "password": "Hani@Osool2025!", "role": "admin"},
    {"email": "abady@osool.eg", "full_name": "Abady", "password": "Abady@Osool2025!", "role": "admin"},
    {"email": "sama@osool.eg", "full_name": "Sama", "password": "Sama@Osool2025!", "role": "admin"},

    # Beta Testers (10) - Each has unique password - CAN GENERATE 2 INVITATIONS EACH
    {"email": "tester1@osool.eg", "full_name": "Beta Tester 1", "password": "Tester1@Beta2025", "role": "investor"},
    {"email": "tester2@osool.eg", "full_name": "Beta Tester 2", "password": "Tester2@Beta2025", "role": "investor"},
    {"email": "tester3@osool.eg", "full_name": "Beta Tester 3", "password": "Tester3@Beta2025", "role": "investor"},
    {"email": "tester4@osool.eg", "full_name": "Beta Tester 4", "password": "Tester4@Beta2025", "role": "investor"},
    {"email": "tester5@osool.eg", "full_name": "Beta Tester 5", "password": "Tester5@Beta2025", "role": "investor"},
    {"email": "tester6@osool.eg", "full_name": "Beta Tester 6", "password": "Tester6@Beta2025", "role": "investor"},
    {"email": "tester7@osool.eg", "full_name": "Beta Tester 7", "password": "Tester7@Beta2025", "role": "investor"},
    {"email": "tester8@osool.eg", "full_name": "Beta Tester 8", "password": "Tester8@Beta2025", "role": "investor"},
    {"email": "tester9@osool.eg", "full_name": "Beta Tester 9", "password": "Tester9@Beta2025", "role": "investor"},
    {"email": "tester10@osool.eg", "full_name": "Beta Tester 10", "password": "Tester10@Beta2025", "role": "investor"},
]


async def seed_beta_users():
    """Create all beta user accounts."""
    print("=" * 60)
    print("Osool Phase 1: Beta User Seeding (Standalone)")
    print("=" * 60)
    print()

    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL environment variable not set!")
        print("   Make sure to run with: railway run -s Osool python ...")
        sys.exit(1)

    # Convert postgres:// to postgresql+asyncpg://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"[DB] Database URL: {database_url[:50]}...")
    print()

    # Create engine and session
    engine = create_async_engine(database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables if they don't exist
    print("[INFO] Checking database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database schema ready (including invitations table)")
    print()

    async with AsyncSessionLocal() as db:
        created_count = 0
        updated_count = 0

        for user_data in BETA_USERS:
            # Check if user already exists
            result = await db.execute(
                select(User).filter(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Update existing user with new password and ensure verified
                existing_user.password_hash = get_password_hash(user_data["password"])
                existing_user.is_verified = True
                existing_user.email_verified = True
                existing_user.role = user_data["role"]
                print(f"[UPDATE] {user_data['email']} - updated password and verified")
                updated_count += 1
                continue

            # Create user
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_verified=True,  # Pre-verified for beta
                email_verified=True,
                invitations_sent=0
            )

            db.add(user)
            print(f"[CREATE] {user_data['email']} ({user_data['role']})")
            created_count += 1

        await db.commit()
        print()
        print("=" * 60)
        print(f"[SUCCESS] Beta user seeding complete!")
        print(f"   Created: {created_count} new users")
        print(f"   Updated: {updated_count} existing users")
        print("=" * 60)
        print()

    await engine.dispose()


if __name__ == "__main__":
    print()
    print("[START] Starting beta user seeding (standalone)...")
    print()

    try:
        asyncio.run(seed_beta_users())
        print("[SUCCESS] Seeding successful!")
        print()
        print("=" * 60)
        print("BETA USER CREDENTIALS")
        print("=" * 60)
        print()
        print("ADMIN ACCOUNTS (Unlimited Invitations):")
        print("  mustafa@osool.eg  | Mustafa@Osool2025!")
        print("  hani@osool.eg     | Hani@Osool2025!")
        print("  abady@osool.eg    | Abady@Osool2025!")
        print("  sama@osool.eg     | Sama@Osool2025!")
        print()
        print("TESTER ACCOUNTS (2 Invitations Each):")
        for i in range(1, 11):
            print(f"  tester{i}@osool.eg  | Tester{i}@Beta2025")
        print()
        print("=" * 60)
        print()
    except Exception as e:
        print(f"[ERROR] Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
