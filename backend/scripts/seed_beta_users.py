"""
Seed Beta Users for Osool Phase 1 Launch
-----------------------------------------
Creates 14 beta accounts for testing and investor demos.

Usage:
    cd backend
    python scripts/seed_beta_users.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal, engine
from app.models import User, Base
from app.auth import get_password_hash
from sqlalchemy import select

BETA_USERS = [
    # Core Team (4)
    {
        "email": "mustafa@osool.eg",
        "full_name": "Mustafa",
        "password": "Osool2025",
        "role": "admin"
    },
    {
        "email": "hani@osool.eg",
        "full_name": "Hani",
        "password": "Osool2025",
        "role": "admin"
    },
    {
        "email": "abady@osool.eg",
        "full_name": "Abady",
        "password": "Osool2025",
        "role": "admin"
    },
    {
        "email": "sama@osool.eg",
        "full_name": "Sama",
        "password": "Osool2025",
        "role": "admin"
    },

    # Beta Testers (10)
    {
        "email": "tester1@osool.eg",
        "full_name": "Beta Tester 1",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester2@osool.eg",
        "full_name": "Beta Tester 2",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester3@osool.eg",
        "full_name": "Beta Tester 3",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester4@osool.eg",
        "full_name": "Beta Tester 4",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester5@osool.eg",
        "full_name": "Beta Tester 5",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester6@osool.eg",
        "full_name": "Beta Tester 6",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester7@osool.eg",
        "full_name": "Beta Tester 7",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester8@osool.eg",
        "full_name": "Beta Tester 8",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester9@osool.eg",
        "full_name": "Beta Tester 9",
        "password": "Osool2025",
        "role": "investor"
    },
    {
        "email": "tester10@osool.eg",
        "full_name": "Beta Tester 10",
        "password": "Osool2025",
        "role": "investor"
    },
]

async def seed_beta_users():
    """Create all beta user accounts."""
    print("=" * 60)
    print("Osool Phase 1: Beta User Seeding")
    print("=" * 60)
    print()

    # Create tables if they don't exist
    print("📋 Checking database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database schema ready")
    print()

    async with AsyncSessionLocal() as db:
        created_count = 0
        skipped_count = 0

        for user_data in BETA_USERS:
            # Check if user already exists
            result = await db.execute(
                select(User).filter(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"⚠️  {user_data['email']} already exists, skipping")
                skipped_count += 1
                continue

            # Create user
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_verified=True,  # Pre-verified for beta
                email_verified=True
            )

            db.add(user)
            print(f"✅ Created: {user_data['email']} ({user_data['role']})")
            created_count += 1

        await db.commit()
        print()
        print("=" * 60)
        print(f"✅ Beta user seeding complete!")
        print(f"   Created: {created_count} users")
        print(f"   Skipped: {skipped_count} users (already exist)")
        print("=" * 60)
        print()
        print("📝 Credentials saved to: BETA_CREDENTIALS.md")
        print()


if __name__ == "__main__":
    print()
    print("🚀 Starting beta user seeding...")
    print()

    try:
        asyncio.run(seed_beta_users())
        print("✅ Seeding successful!")
        print()
        print("You can now use these credentials to login:")
        print("   - mustafa@osool.eg / Osool2025")
        print("   - hani@osool.eg / Osool2025")
        print("   - tester1@osool.eg / Osool2025")
        print("   - ... (see BETA_CREDENTIALS.md for all accounts)")
        print()
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
