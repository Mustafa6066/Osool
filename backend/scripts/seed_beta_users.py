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

# Beta accounts configuration
BETA_ACCOUNTS = [
    # Admin accounts (Core Team)
    {"full_name": "Mustafa", "email": "mustafa@osool.eg", "role": "admin"},
    {"full_name": "Hani", "email": "hani@osool.eg", "role": "admin"},
    {"full_name": "Abady", "email": "abady@osool.eg", "role": "admin"},
    {"full_name": "Sama", "email": "sama@osool.eg", "role": "admin"},
    
    # Tester accounts
    {"full_name": "Tester One", "email": "tester1@osool.eg", "role": "investor"},
    {"full_name": "Tester Two", "email": "tester2@osool.eg", "role": "investor"},
    {"full_name": "Tester Three", "email": "tester3@osool.eg", "role": "investor"},
    {"full_name": "Tester Four", "email": "tester4@osool.eg", "role": "investor"},
    {"full_name": "Tester Five", "email": "tester5@osool.eg", "role": "investor"},
    {"full_name": "Tester Six", "email": "tester6@osool.eg", "role": "investor"},
    {"full_name": "Tester Seven", "email": "tester7@osool.eg", "role": "investor"},
    {"full_name": "Tester Eight", "email": "tester8@osool.eg", "role": "investor"},
    {"full_name": "Tester Nine", "email": "tester9@osool.eg", "role": "investor"},
    {"full_name": "Tester Ten", "email": "tester10@osool.eg", "role": "investor"},
]

COMMON_PASSWORD = "Osool2025"


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
                existing.password_hash = get_password_hash(COMMON_PASSWORD)
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
                    password_hash=get_password_hash(COMMON_PASSWORD),
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
        
        print(f"\n{'='*50}")
        print(f"[SUCCESS] Beta User Seeding Complete!")
        print(f"   Created: {created} new accounts")
        print(f"   Updated: {updated} existing accounts")
        print(f"   Total: {len(BETA_ACCOUNTS)} beta accounts ready")
        print(f"{'='*50}")
        print(f"\n[KEY] Common Password: {COMMON_PASSWORD}")
        print(f"[EMAIL] Admin Emails: mustafa@osool.eg, hani@osool.eg, abady@osool.eg, sama@osool.eg")
        print(f"[EMAIL] Tester Emails: tester1@osool.eg through tester10@osool.eg")
        
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
