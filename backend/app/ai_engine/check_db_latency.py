
import asyncio
import sys
import os
import time
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import AsyncSessionLocal
from app.ai_engine.market_analytics_layer import MarketAnalyticsLayer

async def test_db_latency():
    print("📉 TESTING DB LATENCY...")
    
    async with AsyncSessionLocal() as session:
        # 1. Simple Connection Test
        t0 = time.time()
        await session.execute(text("SELECT 1"))
        t1 = time.time()
        print(f"✅ Simple Select (Ping): {(t1-t0)*1000:.2f}ms")
        
        # 2. Market Analytics Query (The suspect)
        market_layer = MarketAnalyticsLayer(session)
        location = "New Cairo"
        
        print(f"🔍 Running Market Pulse for '{location}'...")
        t2 = time.time()
        pulse = await market_layer.get_real_time_market_pulse(location)
        t3 = time.time()
        
        print(f"✅ Market Pulse Query: {(t3-t2)*1000:.2f}ms")
        if pulse:
            print(f"   Inventory: {pulse.get('inventory_count')}")
        else:
            print("   No data found.")

if __name__ == "__main__":
    asyncio.run(test_db_latency())
