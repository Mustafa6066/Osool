import asyncio
import sys
import os
import random
import string
from sqlalchemy import select

# Append backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal, init_db
from app.models import User
from app.auth import get_password_hash
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def generate_simple_password(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def seed_users():
    print("Starting User Seeding (Async)...")
    
    # Initialize DB (create tables if not exist)
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # 1. Main Beta Users
        core_users = [
            {"name": "Mustafa", "email": "mustafa@osool.eg", "role": "admin"},
            {"name": "Hani", "email": "hani@osool.eg", "role": "investor"},
            {"name": "Abady", "email": "abady@osool.eg", "role": "investor"},
            {"name": "Sama", "email": "sama@osool.eg", "role": "investor"},
        ]
        
        # 2. Tester Users
        testers = []
        for i in range(1, 11):
            testers.append({
                "name": f"Tester {i}",
                "email": f"tester{i}@osool.eg",
                "role": "investor"
            })
        
        all_users = core_users + testers
        created_credentials = []

        print("-" * 60)
        print(f"{'Full Name':<15} | {'Email':<25} | {'Password':<15} | {'Role':<10}")
        print("-" * 60)

        for user_data in all_users:
            # Check if user exists
            result = await db.execute(select(User).filter(User.email == user_data["email"]))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️  Skipping {user_data['name']} (Already exists)")
                continue
            
            if user_data["name"] in ["Mustafa", "Hani", "Abady", "Sama"]:
                plain_password = "Password123!"
            else:
                plain_password = generate_simple_password()
                
            hashed_pw = get_password_hash(plain_password)
            
            new_user = User(
                email=user_data["email"],
                full_name=user_data["name"],
                password_hash=hashed_pw,
                role=user_data["role"],
                is_verified=True,
                email_verified=True
            )
            
            db.add(new_user)
            created_credentials.append(f"{user_data['email']}:{plain_password}")
            
            print(f"{user_data['name']:<15} | {user_data['email']:<25} | {plain_password:<15} | {user_data['role']:<10}")
        
        await db.commit()
        
        print("-" * 60)
        print(f"✅ Seeding Complete. Created {len(created_credentials)} new users.")
        
        # Save credentials
        with open("BETA_USER_CREDENTIALS.txt", "w") as f:
            f.write("BETA USER CREDENTIALS\n=====================\n")
            for line in created_credentials:
                 f.write(line + "\n")
        print("📁 Credentials saved to 'BETA_USER_CREDENTIALS.txt'.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_users())
