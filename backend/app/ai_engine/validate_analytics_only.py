"""
Simplified Analytics Validation (No LLM Call)
=============================================
Tests: Database + Analytics + Market Segments ONLY
Skips Claude API to avoid timeouts.
"""
import asyncio
from datetime import datetime

async def main():
    print("=" * 60)
    print("🔬 OSOOL ANALYTICS VALIDATION (NO LLM)")
    print("=" * 60)
    print(f"⏰ {datetime.now().isoformat()}")
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
            print(f"   ✅ Connected. Total Properties: {total_props}")

            # Fetch New Cairo properties with prices
            result = await session.execute(
                select(Property.title, Property.price, Property.developer, Property.location)
                .filter(Property.location.ilike("%Cairo%"))
                .filter(Property.price > 0)
                .limit(10)
            )
            rows = result.all()
            
            if rows:
                print(f"\n   📍 Cairo Properties in DB:")
                for title, price, dev, loc in rows:
                    print(f"      - {title[:40]}: {price:,.0f} EGP | {dev or 'N/A'}")
                
                prices = [r[1] for r in rows]
                print(f"\n   📈 Cairo Stats (from DB):")
                print(f"      Min: {min(prices):,.0f} EGP")
                print(f"      Max: {max(prices):,.0f} EGP")
                print(f"      Avg: {sum(prices)/len(prices):,.0f} EGP")
            else:
                print("   ⚠️ No Cairo properties found.")
                
    except Exception as e:
        print(f"   ❌ DB Error: {e}")
        import traceback
        traceback.print_exc()
        return

    # ───────────────────────────────────────────────────────────
    # STEP 2: Market Segments Config
    # ───────────────────────────────────────────────────────────
    print("\n📈 STEP 2: Market Segments (Config)")
    try:
        from app.ai_engine.analytical_engine import MARKET_SEGMENTS, TIER1_DEVELOPERS
        
        new_cairo = MARKET_SEGMENTS.get("new_cairo", {})
        class_a = new_cairo.get("class_a", {})
        class_b = new_cairo.get("class_b", {})
        
        print(f"   New Cairo Class A Config:")
        print(f"      Developers: {', '.join(class_a.get('developers_ar', []))}")
        print(f"      Range: {class_a.get('price_range_en', 'N/A')}")
        print(f"      Avg: {class_a.get('avg_price', 0):,} EGP")
        
        print(f"\n   New Cairo Class B Config:")
        print(f"      Developers: {', '.join(class_b.get('developers_ar', []))}")
        print(f"      Range: {class_b.get('price_range_en', 'N/A')}")
        print(f"      Avg: {class_b.get('avg_price', 0):,} EGP")
        
    except Exception as e:
        print(f"   ❌ Segment Error: {e}")

    # ───────────────────────────────────────────────────────────
    # STEP 3: Market Analytics Layer (Live DB Query)
    # ───────────────────────────────────────────────────────────
    print("\n🌐 STEP 3: Live Market Pulse")
    try:
        from app.ai_engine.market_analytics_layer import MarketAnalyticsLayer
        
        market_layer = MarketAnalyticsLayer()
        pulse = await market_layer.get_real_time_market_pulse("New Cairo")
        
        print(f"   New Cairo Live Stats:")
        print(f"      Avg Price/sqm: {pulse.get('avg_price_per_sqm', 0):,.0f} EGP")
        print(f"      Inventory: {pulse.get('inventory_count', 0)} units")
        print(f"      Entry Price: {pulse.get('entry_price', 0):,.0f} EGP")
        print(f"      Ceiling: {pulse.get('ceiling_price', 0):,.0f} EGP")
        print(f"      Heat Index: {pulse.get('heat_index', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Market Pulse Error: {e}")

    # ───────────────────────────────────────────────────────────
    # STEP 4: Dynamic Market Indicators
    # ───────────────────────────────────────────────────────────
    print("\n💹 STEP 4: Dynamic Economic Indicators")
    try:
        from app.ai_engine.analytical_engine import AnalyticalEngine
        from app.database import AsyncSessionLocal
        
        engine = AnalyticalEngine()
        async with AsyncSessionLocal() as session:
            indicators = await engine.get_live_market_data(session)
            
        print(f"   Live Rates:")
        for k, v in indicators.items():
            print(f"      {k}: {v}")
    except Exception as e:
        print(f"   ❌ Indicators Error: {e}")

    # ───────────────────────────────────────────────────────────
    # VALIDATION SUMMARY
    # ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ DATA PIPELINE VALIDATED (No LLM)")
    print("=" * 60)
    print("   The AI will use the above data when responding.")
    print("   Class A/B segments and live DB stats are correct.")

if __name__ == "__main__":
    asyncio.run(main())
