"""
Developer → flagship compound resolution for the free-path comparison flow.

When the user names a developer (e.g., "Hassan Allam", "Sodic") instead of a
specific compound, we auto-pick the developer's most-stocked compound. The
mapping below lists each developer's compounds in flagship order; the resolver
returns the first one that actually has ≥5 available property rows.
"""
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Property


DEVELOPER_TO_COMPOUNDS: dict[str, List[str]] = {
    "Hassan Allam": ["Swan Lake", "Hap Town", "Park View"],
    "Sodic": ["Sodic East", "Sodic West", "Caesar", "Villette"],
    "La Vista": ["La Vista City", "La Vista Bay", "La Vista Ras El Hekma", "El Patio"],
    "Emaar": ["Marassi", "Uptown Cairo", "Mivida", "Cairo Gate"],
    "ORA": ["ZED East", "ZED West", "Silver Sands"],
    "Tatweer Misr": ["Bloomfields", "Fouka Bay", "IL Monte Galala"],
    "Palm Hills": ["Palm Hills New Cairo", "Palm Hills Katameya", "Badya"],
    "Mountain View": ["Mountain View iCity", "Mountain View Hyde Park", "Mountain View Aliva"],
    "Madinet Masr": ["Sarai", "Taj City"],
}

_MIN_ROWS_FOR_FLAGSHIP = 5


async def resolve_to_compound(
    name: str,
    db: AsyncSession,
) -> Optional[str]:
    """
    If `name` is a developer in DEVELOPER_TO_COMPOUNDS, return that developer's
    first compound that has ≥5 available property rows. Otherwise return `name`
    unchanged (treated as a compound name).

    Returns None if `name` is a known developer but none of their compounds are
    sufficiently stocked — caller should ask the user to pick one explicitly.
    """
    candidates = DEVELOPER_TO_COMPOUNDS.get(name)
    if not candidates:
        # Not a tracked developer — assume the user gave a compound name directly.
        return name

    for compound in candidates:
        stmt = (
            select(func.count(Property.id))
            .where(Property.compound == compound)
            .where(Property.is_available == True)  # noqa: E712
        )
        count = (await db.execute(stmt)).scalar_one()
        if count >= _MIN_ROWS_FOR_FLAGSHIP:
            return compound

    return None


def list_developer_compounds(name: str) -> List[str]:
    """
    Public helper for the dialog layer when it needs to suggest compounds to
    the user (e.g., "أي كمبوند بالظبط من Hassan Allam؟ مثلاً: Swan Lake, Hap Town.").
    """
    return list(DEVELOPER_TO_COMPOUNDS.get(name, []))
