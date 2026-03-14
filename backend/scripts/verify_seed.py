import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select, func

async def check_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        print(f"Total users in DB: {count}")
        
        # Verify specific users
        core_users = ["mustafa@osool.com", "hani@osool.com"]
        for email in core_users:
            res = await session.execute(select(User).filter(User.email == email))
            user = res.scalar_one_or_none()
            if user:
                print(f"Verified user: {user.email}")
            else:
                print(f"MISSING user: {email}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_users())
