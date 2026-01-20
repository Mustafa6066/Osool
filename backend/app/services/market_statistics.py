"""
Market Statistics Service
-------------------------
Pre-computes and stores market statistics from the properties database.
These statistics are used by the AI to provide accurate market insights.

Statistics include:
- Price ranges per location (min, max, avg)
- Price ranges per compound
- Price ranges per developer
- Average price per sqm per area
- Property counts by type
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Cache for statistics (refreshed periodically)
_market_stats_cache: Optional[Dict] = None


async def compute_market_statistics(db: AsyncSession) -> Dict:
    """
    Compute comprehensive market statistics from the properties database.
    
    Returns a dictionary with:
    - location_stats: {location: {min_price, max_price, avg_price, count, avg_price_per_sqm}}
    - compound_stats: {compound: {min_price, max_price, avg_price, count, developer}}
    - developer_stats: {developer: {min_price, max_price, avg_price, count, compounds}}
    - type_stats: {type: {min_price, max_price, avg_price, count}}
    - global_stats: {total_properties, min_price, max_price, avg_price, avg_price_per_sqm}
    """
    try:
        stats = {
            "location_stats": {},
            "compound_stats": {},
            "developer_stats": {},
            "type_stats": {},
            "global_stats": {}
        }
        
        # Global statistics
        global_result = await db.execute(
            select(
                func.count(Property.id).label('count'),
                func.min(Property.price).label('min_price'),
                func.max(Property.price).label('max_price'),
                func.avg(Property.price).label('avg_price'),
                func.avg(Property.price_per_sqm).label('avg_price_per_sqm')
            ).filter(Property.is_available == True)
        )
        global_row = global_result.first()
        stats["global_stats"] = {
            "total_properties": global_row.count or 0,
            "min_price": float(global_row.min_price or 0),
            "max_price": float(global_row.max_price or 0),
            "avg_price": round(float(global_row.avg_price or 0), 0),
            "avg_price_per_sqm": round(float(global_row.avg_price_per_sqm or 0), 0)
        }
        
        # Location statistics
        location_result = await db.execute(
            select(
                Property.location,
                func.count(Property.id).label('count'),
                func.min(Property.price).label('min_price'),
                func.max(Property.price).label('max_price'),
                func.avg(Property.price).label('avg_price'),
                func.avg(Property.price_per_sqm).label('avg_price_per_sqm')
            ).filter(Property.is_available == True)
            .group_by(Property.location)
            .order_by(func.count(Property.id).desc())
        )
        for row in location_result.all():
            if row.location:
                stats["location_stats"][row.location] = {
                    "count": row.count,
                    "min_price": float(row.min_price or 0),
                    "max_price": float(row.max_price or 0),
                    "avg_price": round(float(row.avg_price or 0), 0),
                    "avg_price_per_sqm": round(float(row.avg_price_per_sqm or 0), 0)
                }
        
        # Compound statistics
        compound_result = await db.execute(
            select(
                Property.compound,
                Property.developer,
                func.count(Property.id).label('count'),
                func.min(Property.price).label('min_price'),
                func.max(Property.price).label('max_price'),
                func.avg(Property.price).label('avg_price')
            ).filter(Property.is_available == True, Property.compound != None)
            .group_by(Property.compound, Property.developer)
            .order_by(func.count(Property.id).desc())
            .limit(100)  # Top 100 compounds
        )
        for row in compound_result.all():
            if row.compound:
                stats["compound_stats"][row.compound] = {
                    "developer": row.developer,
                    "count": row.count,
                    "min_price": float(row.min_price or 0),
                    "max_price": float(row.max_price or 0),
                    "avg_price": round(float(row.avg_price or 0), 0)
                }
        
        # Developer statistics
        developer_result = await db.execute(
            select(
                Property.developer,
                func.count(Property.id).label('count'),
                func.min(Property.price).label('min_price'),
                func.max(Property.price).label('max_price'),
                func.avg(Property.price).label('avg_price'),
                func.count(distinct(Property.compound)).label('compound_count')
            ).filter(Property.is_available == True, Property.developer != None)
            .group_by(Property.developer)
            .order_by(func.count(Property.id).desc())
            .limit(50)  # Top 50 developers
        )
        for row in developer_result.all():
            if row.developer:
                stats["developer_stats"][row.developer] = {
                    "count": row.count,
                    "compound_count": row.compound_count,
                    "min_price": float(row.min_price or 0),
                    "max_price": float(row.max_price or 0),
                    "avg_price": round(float(row.avg_price or 0), 0)
                }
        
        # Property type statistics
        type_result = await db.execute(
            select(
                Property.type,
                func.count(Property.id).label('count'),
                func.min(Property.price).label('min_price'),
                func.max(Property.price).label('max_price'),
                func.avg(Property.price).label('avg_price')
            ).filter(Property.is_available == True, Property.type != None)
            .group_by(Property.type)
            .order_by(func.count(Property.id).desc())
        )
        for row in type_result.all():
            if row.type:
                stats["type_stats"][row.type] = {
                    "count": row.count,
                    "min_price": float(row.min_price or 0),
                    "max_price": float(row.max_price or 0),
                    "avg_price": round(float(row.avg_price or 0), 0)
                }
        
        logger.info(f"✅ Computed market statistics: {stats['global_stats']['total_properties']} properties, "
                   f"{len(stats['location_stats'])} locations, {len(stats['compound_stats'])} compounds")
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to compute market statistics: {e}", exc_info=True)
        return {
            "location_stats": {},
            "compound_stats": {},
            "developer_stats": {},
            "type_stats": {},
            "global_stats": {"total_properties": 0, "min_price": 0, "max_price": 0, "avg_price": 0}
        }


async def get_market_statistics() -> Dict:
    """
    Get cached market statistics or compute fresh ones.
    """
    global _market_stats_cache
    
    # For now, always compute fresh stats (later: add caching with TTL)
    async with AsyncSessionLocal() as db:
        stats = await compute_market_statistics(db)
        _market_stats_cache = stats
        return stats


def format_statistics_for_ai(stats: Dict, location: str = None) -> str:
    """
    Format market statistics as context for the AI.
    
    Args:
        stats: Full statistics dictionary
        location: Optional specific location to highlight
    """
    lines = []
    
    # Global stats
    g = stats.get("global_stats", {})
    lines.append("═══ VERIFIED MARKET STATISTICS (FROM DATABASE) ═══")
    lines.append(f"Total Properties: {g.get('total_properties', 0):,}")
    lines.append(f"Market Price Range: {g.get('min_price', 0):,.0f} - {g.get('max_price', 0):,.0f} EGP")
    lines.append(f"Average Price: {g.get('avg_price', 0):,.0f} EGP")
    lines.append(f"Average Price/sqm: {g.get('avg_price_per_sqm', 0):,.0f} EGP/m²")
    lines.append("")
    
    # Location-specific stats if requested
    if location and location in stats.get("location_stats", {}):
        loc_stats = stats["location_stats"][location]
        lines.append(f"═══ {location.upper()} STATISTICS ═══")
        lines.append(f"Properties Available: {loc_stats.get('count', 0)}")
        lines.append(f"Price Range: {loc_stats.get('min_price', 0):,.0f} - {loc_stats.get('max_price', 0):,.0f} EGP")
        lines.append(f"Average Price: {loc_stats.get('avg_price', 0):,.0f} EGP")
        lines.append(f"Avg Price/sqm: {loc_stats.get('avg_price_per_sqm', 0):,.0f} EGP/m²")
        lines.append("")
    
    # Top 5 locations by count
    loc_stats = stats.get("location_stats", {})
    if loc_stats:
        lines.append("═══ TOP LOCATIONS BY AVAILABILITY ═══")
        sorted_locs = sorted(loc_stats.items(), key=lambda x: x[1].get('count', 0), reverse=True)[:5]
        for loc, data in sorted_locs:
            lines.append(f"• {loc}: {data.get('count', 0)} properties, "
                        f"{data.get('min_price', 0)/1000000:.1f}M - {data.get('max_price', 0)/1000000:.1f}M EGP")
    
    lines.append("")
    lines.append("USE THESE EXACT NUMBERS. DO NOT INVENT STATISTICS.")
    
    return "\n".join(lines)


async def get_location_price_range(location: str) -> Dict:
    """
    Get the actual price range for a specific location.
    """
    stats = await get_market_statistics()
    loc_stats = stats.get("location_stats", {})
    
    # Try exact match first
    if location in loc_stats:
        return loc_stats[location]
    
    # Try case-insensitive match
    for loc, data in loc_stats.items():
        if location.lower() in loc.lower() or loc.lower() in location.lower():
            return data
    
    return None
