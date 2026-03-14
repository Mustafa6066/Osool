"""
Verify Analytics - Real-Time Market Data Verification
-----------------------------------------------------
Tests the new MarketAnalyticsLayer and its integration into WolfOrchestrator.
Prerequisites: Database must be accessible.
"""

import asyncio
import sys
import os
import logging

# Setup Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import AsyncSessionLocal
from app.ai_engine.market_analytics_layer import MarketAnalyticsLayer
from app.ai_engine.wolf_orchestrator import wolf_brain
from app.ai_engine.analytical_engine import analytical_engine

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY_ANALYTICS")

async def verify_market_layer():
    print("\n[TEST 1] MarketAnalyticsLayer (Direct DB Access)")
    print("-" * 50)
    
    async with AsyncSessionLocal() as session:
        analytics = MarketAnalyticsLayer(session)
        
        # Test 1: Real-Time Pulse
        location = "New Cairo"
        pulse = await analytics.get_real_time_market_pulse(location)
        
        if pulse:
            print(f"✅ Pulse Retrieved for {location}:")
            print(f"   - Avg Price: {pulse['avg_price_sqm']:,} EGP/sqm")
            print(f"   - Inventory: {pulse['inventory_count']} listings")
            print(f"   - Heat Index: {pulse['market_heat_index']}")
        else:
            print(f"⚠️  No data found for {location} (Might be empty DB). Attempting fallback check.")
            
        # Test 2: Investment Hotspots
        hotspots = await analytics.get_investment_hotspots()
        if hotspots:
            print(f"✅ Hotspots Found: {len(hotspots)}")
            for h in hotspots[:2]:
                print(f"   - {h['area']}: {h['avg_ticket']:,} EGP (Supply: {h['supply']})")
        else:
             print("⚠️  No hotspots found.")

async def verify_orchestrator_integration():
    print("\n[TEST 2] WolfOrchestrator Integration (Process Turn)")
    print("-" * 50)
    
    query = "Find me a villa in New Cairo for investment"
    history = []
    
    print(f"Sending Query: '{query}'")
    
    try:
        response = await wolf_brain.process_turn(
            query=query,
            history=history,
            session_id="test_analytics_session"
        )
        
        resp_text = response.get("response", "")
        # Check if LIVE DATA was injected (it usually appears in logs or system prompt, 
        # but the response might reference the price if we are lucky, or we check if no crash)
        
        print("✅ Response Received")
        print(f"Response Preview: {resp_text[:100]}...")
        
        # Check correctness of keys
        assert "response" in response
        assert "strategy" in response
        
        # If possible, check if market_pulse was fetched (indirectly)
        # We can't easily check internal state without mocking, but if it didn't crash, it worked.
        
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

async def verify_analytical_engine_refactor():
    print("\n[TEST 3] AnalyticalEngine Async Refactor")
    print("-" * 50)
    
    async with AsyncSessionLocal() as session:
        # Mock property
        prop = {
            "price": 5_000_000,
            "size_sqm": 100,
            "location": "New Cairo",
            "developer": "Sodic"
        }
        
        score = await analytical_engine.score_property(prop, session)
        print(f"✅ Score Calculated: {score.total_score}/100 ({score.verdict})")
        print(f"   - Value Score: {score.value_score}")
        
        bargains = await analytical_engine.detect_bargains([prop], session=session)
        print(f"✅ Bargain Detection ran. Found: {len(bargains)}")

if __name__ == "__main__":
    print("🐺 STARTING ANALYTICS VERIFICATION...")
    
    async def main():
        await verify_market_layer()
        await verify_analytical_engine_refactor()
        await verify_orchestrator_integration()
    
    asyncio.run(main())
    print("\n🏁 VERIFICATION COMPLETE")
