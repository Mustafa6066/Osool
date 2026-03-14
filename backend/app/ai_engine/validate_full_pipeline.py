"""
Full Pipeline Validation Script
================================
Tests: Database -> Analytics -> Wolf Brain -> AI Response
"""
import asyncio
import json
from datetime import datetime

async def main():
    print("=" * 60)
    print("🔬 OSOOL FULL PIPELINE VALIDATION")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()

    # ───────────────────────────────────────────────────────────
    # STEP 1: Database Connection & Property Count
    # ───────────────────────────────────────────────────────────
    print("📊 STEP 1: Database Connection")
    try:
        from app.database import AsyncSessionLocal
        from app.models import Property
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(Property.id)))
            total_props = result.scalar_one()
            print(f"   ✅ Connected to DB. Total Properties: {total_props}")

            # Fetch New Cairo properties
            result = await session.execute(
                select(Property).filter(Property.location.ilike("%New Cairo%")).limit(5)
            )
            sample = result.scalars().all()
            if sample:
                print(f"   📍 Sample New Cairo Properties:")
                for p in sample[:3]:
                    print(f"      - {p.title}: {p.price:,.0f} EGP ({p.developer})")
            else:
                print("   ⚠️ No New Cairo properties found in DB.")
    except Exception as e:
        print(f"   ❌ DB Error: {e}")
        return

    # ───────────────────────────────────────────────────────────
    # STEP 2: Analytical Engine - Market Segments
    # ───────────────────────────────────────────────────────────
    print("\n📈 STEP 2: Market Segments Validation")
    try:
        from app.ai_engine.analytical_engine import MARKET_SEGMENTS, TIER1_DEVELOPERS
        
        new_cairo = MARKET_SEGMENTS.get("new_cairo", {})
        class_a = new_cairo.get("class_a", {})
        
        print(f"   New Cairo Class A:")
        print(f"      Developers: {', '.join(class_a.get('developers_ar', []))}")
        print(f"      Price Range: {class_a.get('price_range_en', 'N/A')}")
        print(f"      Avg Price: {class_a.get('avg_price', 0):,} EGP")
        
        print(f"\n   TIER1_DEVELOPERS (Global):")
        tier1_ar = [d for d in TIER1_DEVELOPERS if any(c > '\u0600' for c in d)]
        print(f"      Arabic: {', '.join(tier1_ar[:5])}...")
    except Exception as e:
        print(f"   ❌ Segment Error: {e}")

    # ───────────────────────────────────────────────────────────
    # STEP 3: Market Analytics Layer (Live DB Query)
    # ───────────────────────────────────────────────────────────
    print("\n🌐 STEP 3: Live Market Pulse (DB Query)")
    try:
        from app.ai_engine.market_analytics_layer import MarketAnalyticsLayer
        
        market_layer = MarketAnalyticsLayer()
        pulse = await market_layer.get_real_time_market_pulse("New Cairo")
        
        print(f"   New Cairo Market Pulse:")
        print(f"      Avg Price/sqm: {pulse.get('avg_price_per_sqm', 0):,.0f} EGP")
        print(f"      Inventory: {pulse.get('inventory_count', 0)} units")
        print(f"      Entry Price: {pulse.get('entry_price', 0):,.0f} EGP")
        print(f"      Heat Index: {pulse.get('heat_index', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Market Pulse Error: {e}")

    # ───────────────────────────────────────────────────────────
    # STEP 4: Wolf Orchestrator - Process Turn
    # ───────────────────────────────────────────────────────────
    print("\n🐺 STEP 4: Wolf Brain Response ('عايز شقه في التجمع')")
    try:
        from app.ai_engine.wolf_orchestrator import wolf_brain
        
        result = await asyncio.wait_for(
            wolf_brain.process_turn(
                query="عايز شقه في التجمع",
                history=[],
                profile=None,
                language="ar"
            ),
            timeout=90  # 90 second timeout
        )
        
        response_text = result.get("response", "")
        properties = result.get("properties", [])
        intent = result.get("intent", {})
        
        print(f"   Intent Detected: {intent.get('intent', 'N/A')}")
        print(f"   Properties Found: {len(properties)}")
        print(f"   Processing Time: {result.get('processing_time_ms', 'N/A')} ms")
        
        print("\n   📝 AI Response (first 500 chars):")
        print("   " + "-" * 50)
        print(f"   {response_text[:500]}...")
        print("   " + "-" * 50)
        
        if properties:
            print(f"\n   🏠 Top Property:")
            top = properties[0]
            print(f"      Title: {top.get('title')}")
            print(f"      Price: {top.get('price', 0):,.0f} EGP")
            print(f"      Developer: {top.get('developer')}")
            print(f"      Osool Score: {top.get('osool_score', 'N/A')}")
            
    except asyncio.TimeoutError:
        print("   ⏱️ Timeout: Wolf Brain took > 90s.")
    except Exception as e:
        print(f"   ❌ Wolf Brain Error: {e}")
        import traceback
        traceback.print_exc()

    # ───────────────────────────────────────────────────────────
    # SUMMARY
    # ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("🏁 VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
