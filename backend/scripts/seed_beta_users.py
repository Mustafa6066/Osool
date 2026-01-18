"""
Osool Beta User Seeding Script
------------------------------
Creates 14 pre-verified beta accounts for Phase One testing.

Usage:
    cd backend
    python scripts/seed_beta_users.py

Accounts Created:
    - 4 Admin accounts: Mustafa, Hani, Abady, Sama
    - 10 Tester accounts: tester1-10@osool.eg
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Use synchronous SQLAlchemy for seeding script
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

# Database URL modification for sync driver
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./osool_dev.db")

# Convert async drivers to sync for this script
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
elif "aiosqlite" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "")
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

print(f"[INFO] Using database: {DATABASE_URL[:50]}...")

# Create sync engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Import models after engine is set up
from app.models import User, Base

# Password hashing using bcrypt directly
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Beta accounts configuration with UNIQUE passwords
BETA_ACCOUNTS = [
    # Admin accounts (Core Team) - Each has unique password
    {"full_name": "Mustafa", "email": "mustafa@osool.eg", "password": "Mustafa@Osool2025!", "role": "admin"},
    {"full_name": "Hani", "email": "hani@osool.eg", "password": "Hani@Osool2025!", "role": "admin"},
    {"full_name": "Abady", "email": "abady@osool.eg", "password": "Abady@Osool2025!", "role": "admin"},
    {"full_name": "Sama", "email": "sama@osool.eg", "password": "Sama@Osool2025!", "role": "admin"},

    # Tester accounts - Each has unique password
    {"full_name": "Tester One", "email": "tester1@osool.eg", "password": "Tester1@Beta2025", "role": "investor"},
    {"full_name": "Tester Two", "email": "tester2@osool.eg", "password": "Tester2@Beta2025", "role": "investor"},
    {"full_name": "Tester Three", "email": "tester3@osool.eg", "password": "Tester3@Beta2025", "role": "investor"},
    {"full_name": "Tester Four", "email": "tester4@osool.eg", "password": "Tester4@Beta2025", "role": "investor"},
    {"full_name": "Tester Five", "email": "tester5@osool.eg", "password": "Tester5@Beta2025", "role": "investor"},
    {"full_name": "Tester Six", "email": "tester6@osool.eg", "password": "Tester6@Beta2025", "role": "investor"},
    {"full_name": "Tester Seven", "email": "tester7@osool.eg", "password": "Tester7@Beta2025", "role": "investor"},
    {"full_name": "Tester Eight", "email": "tester8@osool.eg", "password": "Tester8@Beta2025", "role": "investor"},
    {"full_name": "Tester Nine", "email": "tester9@osool.eg", "password": "Tester9@Beta2025", "role": "investor"},
    {"full_name": "Tester Ten", "email": "tester10@osool.eg", "password": "Tester10@Beta2025", "role": "investor"},
]


def seed_beta_users():
    """Create or update beta user accounts."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    created = 0
    updated = 0
    
    try:
        for account in BETA_ACCOUNTS:
            # Check if user exists
            existing = db.query(User).filter(User.email == account["email"]).first()
            
            if existing:
                # Update existing user to ensure they're verified
                existing.is_verified = True
                existing.email_verified = True
                existing.role = account["role"]
                existing.password_hash = get_password_hash(account["password"])
                updated += 1
                print(f"  [OK] Updated: {account['email']} (verified, role={account['role']})")
            else:
                # Generate unique wallet address based on email
                import hashlib
                wallet_hash = hashlib.sha256(account["email"].encode()).hexdigest()[:40]
                wallet_address = f"0x{wallet_hash}"
                
                new_user = User(
                    full_name=account["full_name"],
                    email=account["email"],
                    password_hash=get_password_hash(account["password"]),
                    wallet_address=wallet_address,
                    is_verified=True,
                    email_verified=True,
                    kyc_status="approved",
                    role=account["role"]
                )
                db.add(new_user)
                created += 1
                print(f"  [+] Created: {account['email']} (role={account['role']})")
        
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"[SUCCESS] Beta User Seeding Complete!")
        print(f"   Created: {created} new accounts")
        print(f"   Updated: {updated} existing accounts")
        print(f"   Total: {len(BETA_ACCOUNTS)} beta accounts ready")
        print(f"{'='*60}")
        print(f"\n[CREDENTIALS] Beta Account Credentials:")
        print(f"{'='*60}")
        print(f"  ADMIN ACCOUNTS:")
        print(f"    mustafa@osool.eg    | Mustafa@Osool2025!")
        print(f"    hani@osool.eg       | Hani@Osool2025!")
        print(f"    abady@osool.eg      | Abady@Osool2025!")
        print(f"    sama@osool.eg       | Sama@Osool2025!")
        print(f"\n  TESTER ACCOUNTS:")
        for i in range(1, 11):
            print(f"    tester{i}@osool.eg    | Tester{i}@Beta2025")
        print(f"{'='*60}")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding users: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n[SEED] Osool Beta User Seeding Script")
    print("="*50)
    seed_beta_users()
