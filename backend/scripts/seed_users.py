
import os
import random
import string
import sys
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models
try:
    from app.models import User, Base
except ImportError as e:
    print(f"❌ Failed to import models: {e}")
    sys.exit(1)

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("⚠️ DATABASE_URL not found, defaulting to SQLite (Sync)")
    DATABASE_URL = "sqlite:///./osool_dev.db"

# Force sync for this script
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
if "+aiosqlite" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "")

print(f"🔌 Connecting to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
except Exception as e:
    print(f"❌ Failed to create engine: {e}")
    sys.exit(1)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for i in range(length))

def seed_users():
    print("🌱 Seeding 14 Beta Users (Synchronous Mode)...")
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
            
        with SessionLocal() as db:
            # Define users
            beta_users = [
                {"name": "Mustafa", "email": "mustafa@osool.eg", "role": "admin"},
                {"name": "Hani", "email": "hani@osool.eg", "role": "admin"},
                {"name": "Abady", "email": "abady@osool.eg", "role": "tester"},
                {"name": "Sama", "email": "sama@osool.eg", "role": "tester"},
            ]
            
            # Add 10 generic testers
            for i in range(1, 11):
                beta_users.append({
                    "name": f"Tester {i}",
                    "email": f"tester{i}@osool.eg",
                    "role": "tester"
                })
                
            created_count = 0
            credentials = []

            for user_data in beta_users:
                # Check if user exists
                # Note: execute(select(...)) returns a Result object in 1.4/2.0
                stmt = select(User).filter(User.email == user_data["email"])
                existing_user = db.execute(stmt).scalars().first()
                
                if not existing_user:
                    password = generate_random_password()
                    new_user = User(
                        email=user_data["email"],
                        full_name=user_data["name"],
                        password_hash=get_password_hash(password),
                        role=user_data["role"],
                        is_verified=True,
                        phone_verified=True,
                        phone_number=f"+2010000000{random.randint(10, 99)}"
                    )
                    db.add(new_user)
                    created_count += 1
                    credentials.append(f"User: {user_data['name']} | Email: {user_data['email']} | Password: {password}")
                    print(f"✅ Created: {user_data['name']}")
                else:
                    print(f"⚠️ Skipped: {user_data['name']} (Already exists)")
                    
            db.commit()
            
            print(f"\n🎉 Successfully seeded {created_count} new users.")
            
            if credentials:
                print("\n🔐 CREDENTIALS (SAVE THESE):")
                print("="*60)
                for cred in credentials:
                    print(cred)
                print("="*60)
                
                # Save to file
                with open("BETA_CREDENTIALS.md", "a") as f:
                    f.write("\n\n## New Batch\n")
                    for cred in credentials:
                        f.write(f"- {cred}\n")
                print("Checking beta credentials file... saved.")
                
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    seed_users()
