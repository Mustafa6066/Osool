
import sys
import os
import json

# Add backend to path to allow imports
sys.path.append(os.path.abspath("backend"))

try:
    from app.ai_engine.egyptian_market import get_location_insights
except ImportError:
    # Fallback for direct execution structure
    sys.path.append(os.path.abspath("backend/app"))
    from ai_engine.egyptian_market import get_location_insights

def simulate_tool(location):
    """Simulate the logic added to sales_agent.py"""
    insights = get_location_insights(location)
    
    if not insights or "buyer_motivation" not in insights:
        return {"error": "No data"}
        
    selling_points = insights.get("selling_points", [])
    hot_compounds = insights.get("hot_compounds", [])
    growth = insights.get("growth_trend", "growing demand")
    price = insights.get("price_range", "market rates")
    
    loc_name = location
    highlight = selling_points[0] if selling_points else "new developments"
    
    flex_insight = f"{loc_name} right now is witnessing {growth}, especially near {highlight}."
    market_data = f"Market data shows {growth} with prices ranging {price}. Demand is high for {', '.join(hot_compounds[:2]) if hot_compounds else 'premium compounds'}."
    
    return {
        "location": location,
        "flex_insight": flex_insight,
        "market_data": market_data
    }

print("Testing Protocol 6 Data Generation:")
print("-" * 30)
res_nc = simulate_tool("New Cairo")
print(f"New Cairo Flex: {res_nc['flex_insight']}")
print(f"New Cairo Context: {res_nc['market_data']}")

print("-" * 30)
res_zayed = simulate_tool("Sheikh Zayed")
print(f"Zayed Flex: {res_zayed['flex_insight']}")
print(f"Zayed Context: {res_zayed['market_data']}")
