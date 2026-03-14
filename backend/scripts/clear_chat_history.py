"""
Clear chat history from Railway PostgreSQL database.
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:BeQqFYfalLZejuHJrakJGShPGoiUZoIx@tramway.proxy.rlwy.net:44789/railway"

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
