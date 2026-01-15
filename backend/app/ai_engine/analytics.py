"""
Conversation Analytics Tracking for Osool AI Sales Agent
--------------------------------------------------------
Tracks AI agent performance for optimization and conversion analysis.

Database Model:
- conversation_analytics table stores session metrics
- Used for: conversion tracking, A/B testing, performance optimization

Phase 3: AI Personality Enhancement
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func

# Note: This model should be added to backend/app/models.py
# Including it here for reference

"""
class ConversationAnalytics(Base):
    __tablename__ = "conversation_analytics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=True)  # NULL for anonymous users

    # Segmentation
    customer_segment = Column(String)  # luxury, first_time, savvy, unknown
    lead_temperature = Column(String)  # hot, warm, cold
    lead_score = Column(Integer, default=0)

    # Behavior Tracking
    properties_viewed = Column(Integer, default=0)
    tools_used = Column(JSON, default=list)  # List of tool names
    objections_raised = Column(JSON, default=list)  # List of objection types

    # Outcome Metrics
    conversion_status = Column(String, default="browsing")  # browsing, reserved, abandoned
    reservation_generated = Column(Boolean, default=False)
    viewing_scheduled = Column(Boolean, default=False)

    # Engagement Metrics
    session_duration_seconds = Column(Integer, default=0)
    message_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Additional Context
    user_intent = Column(String)  # residential, investment, resale, unknown
    budget_mentioned = Column(Integer, nullable=True)  # Budget in EGP
    preferred_locations = Column(JSON, default=list)  # List of location strings
"""


class ConversationAnalyticsService:
    """Service for tracking and analyzing AI agent conversations."""

    def __init__(self, db_session=None):
        """
        Initialize analytics service.

        Args:
            db_session: SQLAlchemy database session (optional, can be set later)
        """
        self.db = db_session
    
    def set_db_session(self, db_session):
        """Set the database session for analytics operations."""
        self.db = db_session

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        customer_segment: str = "unknown"
    ) -> Dict:
        """
        Create new analytics session.

        Args:
            session_id: Unique session identifier
            user_id: User ID if authenticated
            customer_segment: Initial segment classification

        Returns:
            Dict with session data
        """
        from app.models import ConversationAnalytics

        analytics = ConversationAnalytics(
            session_id=session_id,
            user_id=user_id,
            customer_segment=customer_segment,
            lead_temperature="cold",  # Start cold
            lead_score=0
        )

        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)

        return {
            "session_id": analytics.session_id,
            "created_at": analytics.created_at,
            "customer_segment": analytics.customer_segment
        }

    async def update_session(
        self,
        session_id: str,
        updates: Dict
    ) -> bool:
        """
        Update analytics session with new data.

        Args:
            session_id: Session identifier
            updates: Dict of fields to update

        Returns:
            True if successful, False otherwise

        Example:
            await analytics_service.update_session(
                session_id="abc123",
                updates={
                    "customer_segment": "luxury",
                    "lead_temperature": "hot",
                    "lead_score": 65,
                    "properties_viewed": 5
                }
            )
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if not analytics:
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(analytics, key):
                setattr(analytics, key, value)

        self.db.commit()
        return True

    async def track_tool_usage(
        self,
        session_id: str,
        tool_name: str
    ) -> None:
        """
        Track when a tool is used during conversation.

        Args:
            session_id: Session identifier
            tool_name: Name of the tool used
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if analytics:
            tools_used = analytics.tools_used or []
            tools_used.append({
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            analytics.tools_used = tools_used
            self.db.commit()

    async def track_objection(
        self,
        session_id: str,
        objection_type: str
    ) -> None:
        """
        Track when an objection is raised.

        Args:
            session_id: Session identifier
            objection_type: Type of objection (e.g., "price_too_high")
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if analytics:
            objections = analytics.objections_raised or []
            objections.append({
                "type": objection_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            analytics.objections_raised = objections
            self.db.commit()

    async def track_property_view(
        self,
        session_id: str,
        property_id: int
    ) -> None:
        """
        Track when a property is viewed.

        Args:
            session_id: Session identifier
            property_id: Property ID that was viewed
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if analytics:
            analytics.properties_viewed += 1
            self.db.commit()

    async def mark_conversion(
        self,
        session_id: str,
        conversion_type: str  # "reservation" or "viewing"
    ) -> None:
        """
        Mark a conversion event (reservation or viewing scheduled).

        Args:
            session_id: Session identifier
            conversion_type: Type of conversion
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if analytics:
            analytics.conversion_status = "reserved" if conversion_type == "reservation" else "viewing_scheduled"

            if conversion_type == "reservation":
                analytics.reservation_generated = True
            elif conversion_type == "viewing":
                analytics.viewing_scheduled = True

            self.db.commit()

    async def finalize_session(
        self,
        session_id: str,
        final_status: str = "abandoned"
    ) -> None:
        """
        Finalize session when user leaves.

        Args:
            session_id: Session identifier
            final_status: Final conversion status
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if analytics:
            # Calculate session duration
            if analytics.created_at:
                duration = (datetime.utcnow() - analytics.created_at).total_seconds()
                analytics.session_duration_seconds = int(duration)

            # Set final status if not already converted
            if analytics.conversion_status == "browsing":
                analytics.conversion_status = final_status

            self.db.commit()

    async def get_session_metrics(self, session_id: str) -> Optional[Dict]:
        """
        Get metrics for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with session metrics or None
        """
        from app.models import ConversationAnalytics

        analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.session_id == session_id
        ).first()

        if not analytics:
            return None

        return {
            "session_id": analytics.session_id,
            "user_id": analytics.user_id,
            "customer_segment": analytics.customer_segment,
            "lead_temperature": analytics.lead_temperature,
            "lead_score": analytics.lead_score,
            "properties_viewed": analytics.properties_viewed,
            "tools_used": analytics.tools_used,
            "objections_raised": analytics.objections_raised,
            "conversion_status": analytics.conversion_status,
            "reservation_generated": analytics.reservation_generated,
            "viewing_scheduled": analytics.viewing_scheduled,
            "session_duration_seconds": analytics.session_duration_seconds,
            "message_count": analytics.message_count,
            "created_at": analytics.created_at.isoformat() if analytics.created_at else None
        }

    async def get_conversion_metrics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict:
        """
        Get aggregated conversion metrics.

        Args:
            date_from: Start date (optional)
            date_to: End date (optional)

        Returns:
            Dict with aggregated metrics
        """
        from app.models import ConversationAnalytics
        from sqlalchemy import func

        query = self.db.query(ConversationAnalytics)

        if date_from:
            query = query.filter(ConversationAnalytics.created_at >= date_from)
        if date_to:
            query = query.filter(ConversationAnalytics.created_at <= date_to)

        # Get all sessions
        total_sessions = query.count()

        # Conversion counts
        reservations = query.filter(ConversationAnalytics.reservation_generated == True).count()
        viewings = query.filter(ConversationAnalytics.viewing_scheduled == True).count()

        # Lead temperature distribution
        hot_leads = query.filter(ConversationAnalytics.lead_temperature == "hot").count()
        warm_leads = query.filter(ConversationAnalytics.lead_temperature == "warm").count()
        cold_leads = query.filter(ConversationAnalytics.lead_temperature == "cold").count()

        # Segment distribution
        luxury = query.filter(ConversationAnalytics.customer_segment == "luxury").count()
        first_time = query.filter(ConversationAnalytics.customer_segment == "first_time").count()
        savvy = query.filter(ConversationAnalytics.customer_segment == "savvy").count()

        # Average metrics
        avg_duration = query.with_entities(
            func.avg(ConversationAnalytics.session_duration_seconds)
        ).scalar() or 0

        avg_properties_viewed = query.with_entities(
            func.avg(ConversationAnalytics.properties_viewed)
        ).scalar() or 0

        # Conversion rates
        reservation_rate = (reservations / total_sessions * 100) if total_sessions > 0 else 0
        viewing_rate = (viewings / total_sessions * 100) if total_sessions > 0 else 0

        return {
            "total_sessions": total_sessions,
            "conversions": {
                "reservations": reservations,
                "viewings": viewings,
                "reservation_rate": round(reservation_rate, 2),
                "viewing_rate": round(viewing_rate, 2)
            },
            "lead_distribution": {
                "hot": hot_leads,
                "warm": warm_leads,
                "cold": cold_leads
            },
            "segment_distribution": {
                "luxury": luxury,
                "first_time": first_time,
                "savvy": savvy
            },
            "averages": {
                "session_duration_seconds": round(avg_duration, 2),
                "properties_viewed": round(avg_properties_viewed, 2)
            }
        }

    async def get_most_common_objections(self, limit: int = 10) -> List[Dict]:
        """
        Get most common objection types.

        Args:
            limit: Number of top objections to return

        Returns:
            List of dicts with objection type and count
        """
        from app.models import ConversationAnalytics
        from collections import Counter

        all_analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.objections_raised != None
        ).all()

        # Flatten all objections
        all_objections = []
        for analytics in all_analytics:
            if analytics.objections_raised:
                for obj in analytics.objections_raised:
                    all_objections.append(obj.get("type"))

        # Count occurrences
        objection_counts = Counter(all_objections)

        # Return top N
        return [
            {"objection_type": obj_type, "count": count}
            for obj_type, count in objection_counts.most_common(limit)
        ]

    async def get_most_used_tools(self, limit: int = 10) -> List[Dict]:
        """
        Get most frequently used tools.

        Args:
            limit: Number of top tools to return

        Returns:
            List of dicts with tool name and usage count
        """
        from app.models import ConversationAnalytics
        from collections import Counter

        all_analytics = self.db.query(ConversationAnalytics).filter(
            ConversationAnalytics.tools_used != None
        ).all()

        # Flatten all tools
        all_tools = []
        for analytics in all_analytics:
            if analytics.tools_used:
                for tool in analytics.tools_used:
                    all_tools.append(tool.get("tool"))

        # Count occurrences
        tool_counts = Counter(all_tools)

        # Return top N
        return [
            {"tool_name": tool_name, "usage_count": count}
            for tool_name, count in tool_counts.most_common(limit)
        ]


# Example usage
if __name__ == "__main__":
    """
    Example usage of ConversationAnalyticsService.

    In production, integrate this into sales_agent.py:

    1. On conversation start:
       analytics_service.create_session(session_id, user_id, segment)

    2. During conversation:
       analytics_service.track_tool_usage(session_id, "run_valuation_ai")
       analytics_service.track_objection(session_id, "price_too_high")
       analytics_service.track_property_view(session_id, property_id)

    3. On conversion:
       analytics_service.mark_conversion(session_id, "reservation")

    4. On session end:
       analytics_service.finalize_session(session_id, "abandoned")

    5. For reporting:
       metrics = await analytics_service.get_conversion_metrics()
       objections = await analytics_service.get_most_common_objections()
    """

    print("ConversationAnalyticsService - Ready for integration")
    print("\nNext steps:")
    print("1. Add ConversationAnalytics model to backend/app/models.py")
    print("2. Create Alembic migration: alembic revision --autogenerate -m 'Add conversation_analytics'")
    print("3. Run migration: alembic upgrade head")
    print("4. Integrate into sales_agent.py chat method")
    print("\nSee docstrings above for usage examples.")
