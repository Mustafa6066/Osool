"""
Market Analytics Layer
----------------------
The "CFO" of the AI. It extracts real-time market truth from the database.
Replaces hardcoded assumptions with data-driven facts.

Async implementation using SQLAlchemy >= 1.4 (2.0 style).
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, text
from app.models import Property

logger = logging.getLogger(__name__)

from app.services.cache import cache

class MarketAnalyticsLayer:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_real_time_market_pulse(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Queries the DB to find the ACTUAL average price and inventory count
        for a specific location right now.
        
        Cached for 10 minutes to reduce DB load.
        """
        try:
            # 1. Check Cache
            cache_key = f"market_pulse:{location.lower().strip()}"
            cached_data = cache.get_json(cache_key)
            if cached_data:
                return cached_data

            # Normalize location string for search (e.g., "New Cairo" -> "%New Cairo%")
            location_clean = location.replace("%", "")
            search_term = f"%{location_clean}%"

            # 2. Aggregation Query
            stmt = select(
                func.avg(Property.price / Property.size_sqm).label('avg_price_sqm'),
                func.count(Property.id).label('inventory_count'),
                func.min(Property.price).label('entry_price'),
                func.max(Property.price).label('ceiling_price')
            ).where(
                Property.location.ilike(search_term),
                Property.price.between(1_000_000, 500_000_000), # Filter out outliers (1M - 500M)
                Property.size_sqm > 0
            )

            result = await self.db.execute(stmt)
            stats = result.first()

            if not stats or not stats.avg_price_sqm:
                return None

            # 3. Calculate Market Heat (Mock logic based on inventory for now)
            # Low inventory + High price = High Heat
            # High inventory = Saturated
            inventory = stats.inventory_count
            heat_index = "HIGH" if inventory < 50 else "MODERATE" if inventory < 200 else "COOL"

            data = {
                "location": location_clean,
                "avg_price_sqm": int(stats.avg_price_sqm),
                "inventory_count": inventory,
                "entry_price": int(stats.entry_price),
                "ceiling_price": int(stats.ceiling_price),
                "market_heat_index": heat_index,
                "timestamp": datetime.now().isoformat()
            }
            
            # 4. Set Cache (10 Minutes)
            cache.set_json(cache_key, data, ttl=600)
            
            return data

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
