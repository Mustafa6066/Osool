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
import time
from typing import Dict, List, Optional
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Cache for statistics (refreshed periodically)
_market_stats_cache: Optional[Dict] = None
_market_stats_timestamp: float = 0.0
_STATS_TTL_SECONDS: int = 300  # 5-minute TTL


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
    Uses TTL-based caching to avoid recomputing on every request.
    """
    global _market_stats_cache, _market_stats_timestamp
    
    now = time.time()
    if _market_stats_cache and (now - _market_stats_timestamp) < _STATS_TTL_SECONDS:
        return _market_stats_cache
    
    async with AsyncSessionLocal() as db:
        stats = await compute_market_statistics(db)
        _market_stats_cache = stats
        _market_stats_timestamp = now
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


async def compute_detailed_qa_statistics(
    db: AsyncSession,
    area: str = None,
    developer: str = None,
    bedrooms: int = None
) -> Dict:
    """
    30 Q&A Statistics for AI consumption.

    Provides comprehensive market statistics including:
    - Meter price breakdowns (min/avg/max) per area, developer, type
    - Room-based statistics (count, avg price, avg size per bedroom count)
    - Developer price comparison by location
    - Property type analysis
    - Best deals per category

    Args:
        db: Database session
        area: Optional filter by location
        developer: Optional filter by developer
        bedrooms: Optional filter by bedroom count

    Returns:
        Dictionary with detailed statistics for AI consumption
    """
    try:
        stats = {
            "meter_price_by_area": {},
            "meter_price_by_developer": {},
            "meter_price_by_type": {},
            "room_statistics": {},
            "developer_by_location": {},
            "best_price_per_area": {},
            "best_price_per_developer": {},
            "best_price_per_type": {},
            "summary": {}
        }

        # ═══════════════════════════════════════════════════════════════
        # 1. METER PRICE BY AREA (min/avg/max)
        # ═══════════════════════════════════════════════════════════════
        area_query = select(
            Property.location,
            func.min(Property.price_per_sqm).label('min_meter'),
            func.avg(Property.price_per_sqm).label('avg_meter'),
            func.max(Property.price_per_sqm).label('max_meter'),
            func.count(Property.id).label('count')
        ).filter(
            Property.is_available == True,
            Property.price_per_sqm > 0
        ).group_by(Property.location)

        if area:
            area_query = area_query.filter(Property.location.ilike(f"%{area}%"))

        area_result = await db.execute(area_query)
        for row in area_result.all():
            if row.location:
                stats["meter_price_by_area"][row.location] = {
                    "min_meter": round(float(row.min_meter or 0), 0),
                    "avg_meter": round(float(row.avg_meter or 0), 0),
                    "max_meter": round(float(row.max_meter or 0), 0),
                    "count": row.count
                }

        # ═══════════════════════════════════════════════════════════════
        # 2. METER PRICE BY DEVELOPER
        # ═══════════════════════════════════════════════════════════════
        dev_query = select(
            Property.developer,
            func.min(Property.price_per_sqm).label('min_meter'),
            func.avg(Property.price_per_sqm).label('avg_meter'),
            func.max(Property.price_per_sqm).label('max_meter'),
            func.count(Property.id).label('count')
        ).filter(
            Property.is_available == True,
            Property.price_per_sqm > 0,
            Property.developer != None
        ).group_by(Property.developer)

        if developer:
            dev_query = dev_query.filter(Property.developer.ilike(f"%{developer}%"))

        dev_result = await db.execute(dev_query)
        for row in dev_result.all():
            if row.developer:
                stats["meter_price_by_developer"][row.developer] = {
                    "min_meter": round(float(row.min_meter or 0), 0),
                    "avg_meter": round(float(row.avg_meter or 0), 0),
                    "max_meter": round(float(row.max_meter or 0), 0),
                    "count": row.count
                }

        # ═══════════════════════════════════════════════════════════════
        # 3. METER PRICE BY PROPERTY TYPE
        # ═══════════════════════════════════════════════════════════════
        type_query = select(
            Property.type,
            func.min(Property.price_per_sqm).label('min_meter'),
            func.avg(Property.price_per_sqm).label('avg_meter'),
            func.max(Property.price_per_sqm).label('max_meter'),
            func.count(Property.id).label('count')
        ).filter(
            Property.is_available == True,
            Property.price_per_sqm > 0,
            Property.type != None
        ).group_by(Property.type)

        type_result = await db.execute(type_query)
        for row in type_result.all():
            if row.type:
                stats["meter_price_by_type"][row.type] = {
                    "min_meter": round(float(row.min_meter or 0), 0),
                    "avg_meter": round(float(row.avg_meter or 0), 0),
                    "max_meter": round(float(row.max_meter or 0), 0),
                    "count": row.count
                }

        # ═══════════════════════════════════════════════════════════════
        # 4. ROOM STATISTICS (by bedroom count)
        # ═══════════════════════════════════════════════════════════════
        room_query = select(
            Property.bedrooms,
            func.count(Property.id).label('count'),
            func.avg(Property.price).label('avg_price'),
            func.min(Property.price).label('min_price'),
            func.max(Property.price).label('max_price'),
            func.avg(Property.size_sqm).label('avg_size'),
            func.avg(Property.price_per_sqm).label('avg_meter')
        ).filter(
            Property.is_available == True,
            Property.bedrooms != None
        ).group_by(Property.bedrooms).order_by(Property.bedrooms)

        if bedrooms:
            room_query = room_query.filter(Property.bedrooms == bedrooms)

        room_result = await db.execute(room_query)
        for row in room_result.all():
            if row.bedrooms is not None:
                stats["room_statistics"][str(row.bedrooms)] = {
                    "count": row.count,
                    "avg_price": round(float(row.avg_price or 0), 0),
                    "min_price": round(float(row.min_price or 0), 0),
                    "max_price": round(float(row.max_price or 0), 0),
                    "avg_size_sqm": round(float(row.avg_size or 0), 0),
                    "avg_meter": round(float(row.avg_meter or 0), 0)
                }

        # ═══════════════════════════════════════════════════════════════
        # 5. DEVELOPER BY LOCATION (cross-analysis)
        # ═══════════════════════════════════════════════════════════════
        dev_loc_query = select(
            Property.developer,
            Property.location,
            func.avg(Property.price_per_sqm).label('avg_meter'),
            func.count(Property.id).label('count')
        ).filter(
            Property.is_available == True,
            Property.developer != None,
            Property.price_per_sqm > 0
        ).group_by(
            Property.developer,
            Property.location
        ).having(func.count(Property.id) >= 2)  # At least 2 units for valid comparison

        dev_loc_result = await db.execute(dev_loc_query)
        for row in dev_loc_result.all():
            if row.developer and row.location:
                key = f"{row.developer}|{row.location}"
                stats["developer_by_location"][key] = {
                    "developer": row.developer,
                    "location": row.location,
                    "avg_meter": round(float(row.avg_meter or 0), 0),
                    "count": row.count
                }

        # ═══════════════════════════════════════════════════════════════
        # 6. BEST PRICE PER AREA (lowest meter price)
        # ═══════════════════════════════════════════════════════════════
        for loc, data in stats["meter_price_by_area"].items():
            # Find the property with lowest meter price in this area
            best_query = select(
                Property.id,
                Property.title,
                Property.price,
                Property.price_per_sqm,
                Property.developer,
                Property.compound
            ).filter(
                Property.is_available == True,
                Property.location == loc,
                Property.price_per_sqm > 0
            ).order_by(Property.price_per_sqm.asc()).limit(1)

            best_result = await db.execute(best_query)
            best_row = best_result.first()
            if best_row:
                stats["best_price_per_area"][loc] = {
                    "property_id": best_row.id,
                    "title": best_row.title,
                    "price": float(best_row.price),
                    "price_per_sqm": float(best_row.price_per_sqm),
                    "developer": best_row.developer,
                    "compound": best_row.compound
                }

        # ═══════════════════════════════════════════════════════════════
        # 7. SUMMARY STATISTICS
        # ═══════════════════════════════════════════════════════════════
        summary_query = select(
            func.count(Property.id).label('total_properties'),
            func.avg(Property.price).label('avg_price'),
            func.avg(Property.price_per_sqm).label('avg_meter'),
            func.min(Property.price_per_sqm).label('min_meter'),
            func.max(Property.price_per_sqm).label('max_meter')
        ).filter(Property.is_available == True)

        summary_result = await db.execute(summary_query)
        summary_row = summary_result.first()
        stats["summary"] = {
            "total_properties": summary_row.total_properties or 0,
            "avg_price": round(float(summary_row.avg_price or 0), 0),
            "avg_meter": round(float(summary_row.avg_meter or 0), 0),
            "min_meter": round(float(summary_row.min_meter or 0), 0),
            "max_meter": round(float(summary_row.max_meter or 0), 0),
            "areas_count": len(stats["meter_price_by_area"]),
            "developers_count": len(stats["meter_price_by_developer"]),
            "types_count": len(stats["meter_price_by_type"])
        }

        logger.info(f"✅ Computed detailed QA statistics: {stats['summary']['total_properties']} properties")
        return stats

    except Exception as e:
        logger.error(f"Failed to compute detailed QA statistics: {e}", exc_info=True)
        return {
            "meter_price_by_area": {},
            "meter_price_by_developer": {},
            "meter_price_by_type": {},
            "room_statistics": {},
            "developer_by_location": {},
            "best_price_per_area": {},
            "best_price_per_developer": {},
            "best_price_per_type": {},
            "summary": {"total_properties": 0, "error": str(e)}
        }


def format_qa_stats_for_ai(stats: Dict) -> str:
    """
    Format QA statistics into a compact string for AI context injection.
    Keeps token count low while providing key market data.
    """
    lines = []
    s = stats.get("summary", {})
    if not s.get("total_properties"):
        return ""

    lines.append(f"[DB_STATS] {s['total_properties']} properties | Avg meter: {s.get('avg_meter', 0):,.0f} EGP/m²")

    # Top 5 areas by count
    areas = stats.get("meter_price_by_area", {})
    top_areas = sorted(areas.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:5]
    if top_areas:
        lines.append("Areas: " + " | ".join(
            f"{loc}({d['count']}u,{d['avg_meter']:,.0f}/m²)" for loc, d in top_areas
        ))

    # Room stats
    rooms = stats.get("room_statistics", {})
    if rooms:
        lines.append("Rooms: " + " | ".join(
            f"{br}BR({d['count']}u,avg {d['avg_price']/1e6:.1f}M)" for br, d in sorted(rooms.items())
        ))

    # Top 3 developers
    devs = stats.get("meter_price_by_developer", {})
    top_devs = sorted(devs.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:3]
    if top_devs:
        lines.append("Devs: " + " | ".join(
            f"{dev}({d['count']}u,{d['avg_meter']:,.0f}/m²)" for dev, d in top_devs
        ))

    return "\n".join(lines)
