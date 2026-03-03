"""Seed a test user and invitation for local testing."""
import asyncio
import secrets
from app.database import AsyncSessionLocal
from app.models import User, Invitation
from app.api.auth_endpoints import get_password_hash

async def seed():
    async with AsyncSessionLocal() as session:
        # Create a test user
        user = User(
            full_name="Test Admin",
            email="admin@osool.ai",
            password_hash=get_password_hash("password123"),
            is_verified=True,
            email_verified=True,
            role="admin",
            wallet_address="0x" + secrets.token_hex(20),
            encrypted_private_key="test_key"
        )
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
