"""
Consultation Booking Endpoints
------------------------------
Brokerage-first booking flow for physical viewings and developer meetings.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import ConsultationBooking, Property, User


router = APIRouter(prefix="/api/consultations", tags=["Consultations"])


class ConsultationBookingRequest(BaseModel):
    property_id: Optional[int] = Field(default=None, description="Optional property ID for the booking")
    booking_type: str = Field(..., pattern="^(physical_viewing|developer_meeting)$")
    scheduled_time: datetime
    assigned_broker_notes: Optional[str] = Field(default=None, max_length=2000)


@router.post("/book")
async def create_consultation_booking(
    req: ConsultationBookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.property_id is not None:
        prop_result = await db.execute(select(Property).where(Property.id == req.property_id))
        property_obj = prop_result.scalar_one_or_none()
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

    now_ref = datetime.now(timezone.utc) if req.scheduled_time.tzinfo else datetime.utcnow()
    if req.scheduled_time <= now_ref:
        raise HTTPException(status_code=400, detail="scheduled_time must be in the future")

    booking = ConsultationBooking(
        user_id=current_user.id,
        property_id=req.property_id,
        booking_type=req.booking_type,
        scheduled_time=req.scheduled_time,
        assigned_broker_notes=req.assigned_broker_notes,
        status="scheduled",
    )

    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    return {
        "success": True,
        "booking_id": booking.id,
        "booking_type": booking.booking_type,
        "status": booking.status,
        "scheduled_time": booking.scheduled_time,
        "message": "Consultation booking created successfully.",
    }


@router.get("/my")
async def my_consultations(
    status: Optional[str] = Query(default=None, pattern="^(scheduled|completed|cancelled)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(ConsultationBooking).where(ConsultationBooking.user_id == current_user.id)
    if status:
        q = q.where(ConsultationBooking.status == status)

    q = q.order_by(ConsultationBooking.scheduled_time.asc())
    result = await db.execute(q)
    bookings = result.scalars().all()

    return {
        "items": [
            {
                "id": b.id,
                "property_id": b.property_id,
                "booking_type": b.booking_type,
                "status": b.status,
                "scheduled_time": b.scheduled_time,
                "created_at": b.created_at,
            }
            for b in bookings
        ]
    }
