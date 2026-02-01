"""
Market Analytics Layer
----------------------
The "CFO" of the AI. It extracts real-time market truth from the database.
Replaces hardcoded assumptions with data-driven facts.

Async implementation using SQLAlchemy >= 1.4 (2.0 style).
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text
from app.models import Property

logger = logging.getLogger(__name__)

class MarketAnalyticsLayer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_real_time_market_pulse(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Queries the DB to find the ACTUAL average price and inventory count
        for a specific location right now.
        """
        try:
            # Normalize location string for search (e.g., "New Cairo" -> "%New Cairo%")
            # Simple sanitization
            location_clean = location.replace("%", "")
            search_term = f"%{location_clean}%"

            # 1. Aggregation Query
            # Calculate Average Price/Sqm, Inventory, Min Price, Max Price
            stmt = select(
                func.avg(Property.price / Property.size_sqm).label('avg_price_sqm'),
                func.count(Property.id).label('inventory_count'),
                func.min(Property.price).label('entry_price'),
                func.max(Property.price).label('ceiling_price')
            ).where(
                Property.location.ilike(search_term),
                Property.price > 0,
                Property.size_sqm > 0
            )

            result = await self.db.execute(stmt)
            stats = result.first()

            if not stats or not stats.avg_price_sqm:
                return None

            # 2. Calculate "Market Heat" (New listings in last 30 days)
            # Using PostgreSQL interval syntax. For SQLite fallback compatibility we might need logic check
            # but sticking to Postgres standard as per user request.
            heat_stmt = select(func.count(Property.id)).where(
                Property.location.ilike(search_term),
                Property.created_at >= func.now() - text("INTERVAL '30 days'")
            )
            heat_result = await self.db.execute(heat_stmt)
            recent_listings = heat_result.scalar() or 0

            return {
                "location": location,
                "avg_price_sqm": int(stats.avg_price_sqm),
                "inventory_count": stats.inventory_count,
                "entry_level_price": int(stats.entry_price),
                "ceiling_price": int(stats.ceiling_price),
                "market_heat_index": "High" if recent_listings > 10 else "Stable",
                "last_updated": "Live from Database"
            }
        except Exception as e:
            logger.error(f"Market Analytics Error for {location}: {e}")
            return None

    async def get_investment_hotspots(self) -> List[Dict]:
        """
        Scans the entire DB to find areas with supply density (Proxy for activity).
        """
        try:
            # Group by location, count density, avg price
            stmt = select(
                Property.location,
                func.avg(Property.price).label('avg_ticket'),
                func.count(Property.id).label('count')
            ).group_by(
                Property.location
            ).having(
                func.count(Property.id) > 2  # Min threshold
            ).order_by(
                text('avg_ticket DESC')
            ).limit(4)

            result = await self.db.execute(stmt)
            rows = result.all()

            return [
                {
                    "area": r.location, 
                    "avg_ticket": int(r.avg_ticket) if r.avg_ticket else 0, 
                    "supply": r.count
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Investment Hotspots Error: {e}")
            return []
