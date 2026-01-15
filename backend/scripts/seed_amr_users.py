import asyncio
import sys
import os
import logging
from sqlalchemy import select

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import User
from app.auth import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORE_USERS = ["Mustafa", "Hani", "Abady", "Sama"]
TESTERS = [f"Tester{i:02d}" for i in range(1, 11)]

COMMON_PASSWORD = "Pass123!@#"

async def seed_users():
    async with AsyncSessionLocal() as session:
        # Combine lists
        all_users = CORE_USERS + TESTERS
        
        hashed_password = get_password_hash(COMMON_PASSWORD)
        
        for name in all_users:
            email = f"{name.lower()}@osool.com"
            
            # Check if user exists
            result = await session.execute(select(User).filter(User.email == email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info(f"User {name} ({email}) already exists. Skipping.")
                continue
                
            new_user = User(
                email=email,
                full_name=name,
                password_hash=hashed_password,
                role="investor", 
                is_verified=True,
                email_verified=True
            )
            
            session.add(new_user)
            logger.info(f"Creating user: {name} ({email})")
            
        try:
            await session.commit()
            logger.info("✅ Successfully seeded all users.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Failed to commit users: {e}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_users())
