"""
Clear chat history from Railway PostgreSQL database.
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# SECURITY: never hardcode credentials. Read from the environment.
# (The previously-committed Railway password has been removed and MUST be rotated.)
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set. Try: railway run python -m scripts.clear_chat_history")

async def clear_chat_history():
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT COUNT(*) FROM chat_messages"))
        count_before = result.scalar()
        print(f"📊 Found {count_before} chat messages")
        
        await db.execute(text("DELETE FROM chat_messages"))
        await db.commit()
        
        print("✅ All chat history cleared!")

if __name__ == "__main__":
    asyncio.run(clear_chat_history())
