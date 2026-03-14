"""
Verify User Query - Targeted Test
---------------------------------
Tests specific user query: "عايز شقه في التجمع"
Checks for:
1. Correct routing/intent detection.
2. Market data injection (New Cairo).
3. Analytics integration.
4. Final response generation quality.
"""

import asyncio
import sys
import os
import logging
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ai_engine.wolf_orchestrator import wolf_brain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY_QUERY")

async def test_specific_query():
    query = "عايز شقه في التجمع"
    print(f"\n🧪 TESTING QUERY: '{query}'")
    print("=" * 60)

    import time
    start_time = time.time()
    
    try:
        print(f"[{time.time() - start_time:.2f}s] Sending request to Wolf Brain...")
        
        # Process the turn with empty history (fresh session)
        response_data = await wolf_brain.process_turn(
            query=query,
            history=[],
            session_id="verify_tagamoa_query"
        )
        
        print(f"[{time.time() - start_time:.2f}s] Response received!")
        
        # Extract key components
        response_text = response_data.get("response", "")
        strategy = response_data.get("strategy", {})
        metadata = response_data.get("metadata", {})
        
        # 1. Print Response
        print("\n🤖 AI RESPONSE:")
        print("-" * 20)
        print(response_text)
        print("-" * 20)
        
        # 2. Analyze Strategy
        print("\n🧠 STRATEGY DETAILS:")
        print(f"   - Intent: {strategy.get('intent')}")
        print(f"   - Needs Analytics: {strategy.get('needs_analytics')}")
        print(f"   - Model Used: {response_data.get('model_used')}")
        
        # 3. Analyze Analytics Data
        print("\n📊 ANALYTICS DATA (Injected):")
        # Depending on how wolf_brain returns data, it might be in metadata or context
        # Check context keys that look like market data
        context_used = strategy.get("context_used", {})
        
        market_pulse = context_used.get("real_time_market_pulse")
        if market_pulse:
            print("   ✅ Real-time Market Pulse FOUND:")
            print(json.dumps(market_pulse, indent=4, ensure_ascii=False))
        else:
            print("   ⚠️ No Real-time Market Pulse found in context.")

        hotspots = context_used.get("investment_hotspots")
        if hotspots:
             print(f"   ✅ Investment Hotspots FOUND: {len(hotspots)} items")
        else:
             print("   ⚠️ No Investment Hotspots found.")
             
        # 4. Validation Checks
        print("\n✅ VALIDATION CHECKS:")
        
        # Check for Tagamoa/New Cairo mentions or data
        has_location_data = (
            "New Cairo" in str(context_used) or 
            "Tagamoa" in str(context_used) or
            "التجمع" in response_text
        )
        print(f"   - Location Data/Context detected: {'PASS' if has_location_data else 'FAIL'}")
        
        # Check if response is not empty
        print(f"   - Response generated: {'PASS' if response_text else 'FAIL'}")
        
        print(f"[{time.time() - start_time:.2f}s] Test Complete")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_query())
