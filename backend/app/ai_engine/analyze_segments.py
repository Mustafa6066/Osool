import asyncio
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models import Property
from app.ai_engine.analytical_engine import TIER1_DEVELOPERS, TIER2_DEVELOPERS

async def analyze_market_segments():
    async with AsyncSessionLocal() as session:
        print("📊 Analyzing Market Segments from Database...\n")

        locations = ["New Cairo", "Sheikh Zayed"]
        
        # Normalize developer lists for matching
        tier1_normalized = [d.lower() for d in TIER1_DEVELOPERS]
        
        for loc in locations:
            print(f"--- {loc} ---")
            
            # Fetch all properties for this location
            # Note: In a large DB, we'd do this aggregation in SQL, but for flexible classification logic/small datasets, python is fine.
            # Using ilike for broader matching
            stmt = select(Property).filter(Property.location.ilike(f"%{loc}%"))
            result = await session.execute(stmt)
            properties = result.scalars().all()
            
            if not properties:
                print(f"⚠️ No properties found for {loc}")
                continue

            class_a_prices = []
            class_b_prices = []
            
            class_a_devs_found = set()
            class_b_devs_found = set()

            for p in properties:
                if not p.price or not p.developer:
                    continue
                
                dev_lower = p.developer.lower()
                
                # Check classification
                is_class_a = any(t in dev_lower for t in tier1_normalized)
                
                if is_class_a:
                    class_a_prices.append(p.price)
                    class_a_devs_found.add(p.developer)
                else:
                    # Assume Class B for now if not Class A, or check Tier 2
                    # adhering to user's strict Class A definition
                    class_b_prices.append(p.price)
                    class_b_devs_found.add(p.developer)

            def print_stats(name, prices, devs):
                if not prices:
                    print(f"  {name}: No data found.")
                    return
                avg_p = sum(prices) / len(prices)
                min_p = min(prices)
                max_p = max(prices)
                print(f"  {name}:")
                print(f"    Count: {len(prices)}")
                print(f"    Range: {min_p:,.0f} - {max_p:,.0f} EGP")
                print(f"    Avg:   {avg_p:,.0f} EGP")
                print(f"    Devs:  {', '.join(list(devs)[:5])}...")

            print_stats("Class A (Tier 1)", class_a_prices, class_a_devs_found)
            print_stats("Class B (Tier 2/Other)", class_b_prices, class_b_devs_found)
            print()

if __name__ == "__main__":
    asyncio.run(analyze_market_segments())
