"""
Osool Market Intelligence Service
----------------------------------
Provides real-time market data and analytics for Egyptian real estate.

Phase 6: Market context for AI recommendations.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.services.cache import cache
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Analyzes market trends from property database to provide AI with context.
    """

    def __init__(self):
        self.cache_ttl = 86400  # 24 hours
        logger.info("✅ Market Data Service initialized")

    async def get_market_stats(self, db) -> Dict:
        """
        Get overall market statistics.

        Returns:
            Dictionary with market-wide metrics
        """
        cache_key = "market:stats:overall"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from sqlalchemy import select, func
            from app.models import Property

            # Calculate market statistics
            result = await db.execute(
                select(
                    func.count(Property.id).label('total_properties'),
                    func.avg(Property.price).label('avg_price'),
                    func.avg(Property.price_per_sqm).label('avg_price_per_sqm'),
                    func.min(Property.price).label('min_price'),
                    func.max(Property.price).label('max_price')
                )
            )
            stats = result.first()

            market_data = {
                "total_properties": stats.total_properties or 0,
                "avg_price": round(stats.avg_price or 0, 2),
                "avg_price_per_sqm": round(stats.avg_price_per_sqm or 0, 2),
                "min_price": stats.min_price or 0,
                "max_price": stats.max_price or 0,
                "last_updated": datetime.utcnow().isoformat()
            }

            cache.set(cache_key, market_data, self.cache_ttl)
            return market_data

        except Exception as e:
            logger.error(f"❌ Failed to get market stats: {e}")
            return {
                "total_properties": 0,
                "avg_price": 0,
                "avg_price_per_sqm": 45000,  # Egypt average fallback
                "error": str(e)
            }

    async def get_location_stats(self, db, location: str) -> Dict:
        """
        Get statistics for a specific location.

        Args:
            db: Database session
            location: Location name (e.g., "New Cairo")

        Returns:
            Dictionary with location-specific metrics
        """
        cache_key = f"market:location:{location.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from sqlalchemy import select, func
            from app.models import Property

            result = await db.execute(
                select(
                    func.count(Property.id).label('count'),
                    func.avg(Property.price).label('avg_price'),
                    func.avg(Property.price_per_sqm).label('avg_price_per_sqm'),
                    func.min(Property.price).label('min_price'),
                    func.max(Property.price).label('max_price')
                ).where(Property.location.ilike(f"%{location}%"))
            )
            stats = result.first()

            location_data = {
                "location": location,
                "property_count": stats.count or 0,
                "avg_price": round(stats.avg_price or 0, 2),
                "avg_price_per_sqm": round(stats.avg_price_per_sqm or 0, 2),
                "min_price": stats.min_price or 0,
                "max_price": stats.max_price or 0,
                "market_activity": self._calculate_market_activity(stats.count),
                "last_updated": datetime.utcnow().isoformat()
            }

            cache.set(cache_key, location_data, self.cache_ttl)
            return location_data

        except Exception as e:
            logger.error(f"❌ Failed to get location stats for {location}: {e}")
            return {
                "location": location,
                "property_count": 0,
                "error": str(e)
            }

    async def get_compound_analysis(self, db, compound: str) -> Dict:
        """
        Analyze a specific compound/development.

        Args:
            db: Database session
            compound: Compound name

        Returns:
            Compound analysis with trends
        """
        cache_key = f"market:compound:{compound.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from sqlalchemy import select, func
            from app.models import Property

            result = await db.execute(
                select(
                    func.count(Property.id).label('count'),
                    func.avg(Property.price).label('avg_price'),
                    func.avg(Property.price_per_sqm).label('avg_price_per_sqm'),
                    Property.developer,
                    Property.location
                ).where(Property.compound.ilike(f"%{compound}%")).group_by(
                    Property.developer, Property.location
                )
            )
            stats = result.first()

            if stats:
                compound_data = {
                    "compound": compound,
                    "developer": stats.developer,
                    "location": stats.location,
                    "available_units": stats.count or 0,
                    "avg_price": round(stats.avg_price or 0, 2),
                    "avg_price_per_sqm": round(stats.avg_price_per_sqm or 0, 2),
                    "demand_indicator": self._calculate_demand(stats.count),
                    "last_updated": datetime.utcnow().isoformat()
                }
            else:
                compound_data = {
                    "compound": compound,
                    "available_units": 0,
                    "message": "No data available for this compound"
                }

            cache.set(cache_key, compound_data, self.cache_ttl)
            return compound_data

        except Exception as e:
            logger.error(f"❌ Failed to analyze compound {compound}: {e}")
            return {
                "compound": compound,
                "error": str(e)
            }

    async def get_hot_locations(self, db, limit: int = 5) -> List[Dict]:
        """
        Get the hottest (most active) locations.

        Args:
            db: Database session
            limit: Number of locations to return

        Returns:
            List of hot locations with metrics
        """
        cache_key = f"market:hot_locations:top{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from sqlalchemy import select, func
            from app.models import Property

            result = await db.execute(
                select(
                    Property.location,
                    func.count(Property.id).label('property_count'),
                    func.avg(Property.price_per_sqm).label('avg_price_per_sqm')
                ).group_by(Property.location).order_by(
                    func.count(Property.id).desc()
                ).limit(limit)
            )

            hot_locations = []
            for row in result:
                hot_locations.append({
                    "location": row.location,
                    "property_count": row.property_count,
                    "avg_price_per_sqm": round(row.avg_price_per_sqm or 0, 2),
                    "trend": "🔥 High Demand"
                })

            cache.set(cache_key, hot_locations, self.cache_ttl)
            return hot_locations

        except Exception as e:
            logger.error(f"❌ Failed to get hot locations: {e}")
            return []

    async def compare_to_market(self, db, price: float, location: str, size_sqm: int) -> Dict:
        """
        Compare a property price to market average.

        Args:
            db: Database session
            price: Property price
            location: Property location
            size_sqm: Property size

        Returns:
            Comparison analysis
        """
        try:
            location_stats = await self.get_location_stats(db, location)

            if not location_stats or location_stats.get('property_count', 0) == 0:
                return {
                    "verdict": "INSUFFICIENT_DATA",
                    "message": f"Not enough market data for {location}"
                }

            price_per_sqm = price / size_sqm if size_sqm > 0 else 0
            market_avg = location_stats['avg_price_per_sqm']

            if market_avg == 0:
                return {
                    "verdict": "INSUFFICIENT_DATA",
                    "message": "Market average not available"
                }

            difference_percent = ((price_per_sqm - market_avg) / market_avg) * 100

            if difference_percent < -15:
                verdict = "BARGAIN"
                message = f"🎯 Excellent value! {abs(difference_percent):.1f}% below market average"
            elif difference_percent < -5:
                verdict = "GOOD_DEAL"
                message = f"👍 Good deal. {abs(difference_percent):.1f}% below market average"
            elif difference_percent <= 5:
                verdict = "FAIR"
                message = f"✅ Fair market price. Within 5% of market average"
            elif difference_percent <= 15:
                verdict = "ABOVE_MARKET"
                message = f"⚠️ Slightly overpriced. {difference_percent:.1f}% above market average"
            else:
                verdict = "OVERPRICED"
                message = f"🚫 Overpriced. {difference_percent:.1f}% above market average"

            return {
                "verdict": verdict,
                "message": message,
                "property_price_per_sqm": round(price_per_sqm, 2),
                "market_avg_price_per_sqm": round(market_avg, 2),
                "difference_percent": round(difference_percent, 2),
                "location": location,
                "comparable_properties": location_stats['property_count']
            }

        except Exception as e:
            logger.error(f"❌ Failed to compare to market: {e}")
            return {
                "verdict": "ERROR",
                "error": str(e)
            }

    def _calculate_market_activity(self, property_count: int) -> str:
        """Calculate market activity level based on property count."""
        if property_count > 100:
            return "Very High"
        elif property_count > 50:
            return "High"
        elif property_count > 20:
            return "Moderate"
        elif property_count > 5:
            return "Low"
        else:
            return "Very Low"

    def _calculate_demand(self, available_units: int) -> str:
        """Calculate demand indicator based on available units."""
        if available_units < 5:
            return "🔥 High Demand (Limited Stock)"
        elif available_units < 15:
            return "📈 Good Demand"
        elif available_units < 30:
            return "📊 Moderate Demand"
        else:
            return "📉 Low Demand (High Stock)"

    async def get_market_trends(self, db, location: Optional[str] = None) -> Dict:
        """
        Get market trends and insights.

        Args:
            db: Database session
            location: Optional location filter

        Returns:
            Market trends and insights
        """
        try:
            if location:
                location_stats = await self.get_location_stats(db, location)
                hot_locations = [location_stats] if location_stats else []
            else:
                hot_locations = await self.get_hot_locations(db)

            market_stats = await self.get_market_stats(db)

            return {
                "overall_market": market_stats,
                "hot_locations": hot_locations,
                "insights": [
                    f"Average property price in Egypt: {market_stats['avg_price']:,.0f} EGP",
                    f"Average price per sqm: {market_stats['avg_price_per_sqm']:,.0f} EGP",
                    "Market data updated daily from Nawy.com",
                    "Prices valid for 48 hours only"
                ],
                "disclaimer": "Past performance does not guarantee future results. This is not financial advice."
            }

        except Exception as e:
            logger.error(f"❌ Failed to get market trends: {e}")
            return {
                "error": str(e),
                "message": "Unable to fetch market trends at this time"
            }


# Singleton instance
market_data_service = MarketDataService()
