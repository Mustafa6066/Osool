"""Seed a test user and invitation for local testing."""
import asyncio
import os
import secrets
from app.database import AsyncSessionLocal
from app.models import User, Invitation
from app.api.auth_endpoints import get_password_hash

async def seed():
    async with AsyncSessionLocal() as session:
        # Create a test user
        # Security: Generate a random password instead of hardcoding
        import secrets as _sec
        seed_password = os.getenv("SEED_ADMIN_PASSWORD", _sec.token_urlsafe(24))
        user = User(
            full_name="Test Admin",
            email="admin@osool.ai",
            password_hash=get_password_hash(seed_password),
            is_verified=True,
            email_verified=True,
            role="admin"
        )
        print(f"Generated admin password: {seed_password}")
        session.add(user)
        await session.flush()
        user_id = user.id
        print(f"Created user: id={user_id}, email=admin@osool.ai")

        # Create an invitation
        code = secrets.token_urlsafe(24)
        inv = Invitation(
            code=code,
            created_by_user_id=user_id,
            is_used=False
        )
        session.add(inv)
        await session.commit()
        print(f"Created invitation code: {code}")
        print(f"Signup link: http://localhost:3000/signup?invite={code}")

if __name__ == "__main__":
    asyncio.run(seed())
