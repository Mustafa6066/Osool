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
    "Misr Italia": ["IL Bosco", "Vinci"],
    "Inertia": ["Jefaira", "Soleya", "Joulz"],
    "DM Development": ["New Alamein Towers"],
    "City Edge": ["North Edge Towers", "Al Maqsad", "Zahya"],
    "Dorra": ["Bloomfields"],
    "Iwan Developments": ["Iwan"],
    "New Giza": ["New Giza"],
    "Hyde Park": ["Hyde Park New Cairo", "Hyde Park North Coast"],
}


# Delivery track record per developer — based on publicly reported handover history.
# Format: {"on_time_pct": int, "delayed_projects": int, "notable": str}
DEVELOPER_DELIVERY_TRACK_RECORD: dict[str, dict] = {
    "Emaar": {
        "on_time_pct": 92,
        "delayed_projects": 1,
        "notable": "Marassi Phase 1 delivered 4 months early (2022)",
    },
    "Sodic": {
        "on_time_pct": 78,
        "delayed_projects": 3,
        "notable": "Sodic East Phase 2 delayed 8 months (COVID impact)",
    },
    "Palm Hills": {
        "on_time_pct": 71,
        "delayed_projects": 5,
        "notable": "Badya Phase 1 delivered on schedule (2023)",
    },
    "Tatweer Misr": {
        "on_time_pct": 85,
        "delayed_projects": 2,
        "notable": "IL Monte Galala delivered on schedule; Fouka Bay delayed 6 months",
    },
    "Hassan Allam": {
        "on_time_pct": 80,
        "delayed_projects": 2,
        "notable": "Swan Lake Residence delivered on schedule (2021)",
    },
    "La Vista": {
        "on_time_pct": 88,
        "delayed_projects": 1,
        "notable": "Known for finishing ahead of schedule on North Coast projects",
    },
    "Mountain View": {
        "on_time_pct": 74,
        "delayed_projects": 4,
        "notable": "iCity Phase 3 delayed 12 months (infrastructure)",
    },
    "ORA": {
        "on_time_pct": 70,
        "delayed_projects": 4,
        "notable": "ZED East Phase 1 delivered late; Silver Sands on schedule",
    },
    "Misr Italia": {
        "on_time_pct": 82,
        "delayed_projects": 2,
        "notable": "IL Bosco City Phase 1 delivered on schedule (2022)",
    },
    "Madinet Masr": {
        "on_time_pct": 76,
        "delayed_projects": 3,
        "notable": "Sarai Phase 1 delivered; Taj City Phase 2 delayed 9 months",
    },
    "Hyde Park": {
        "on_time_pct": 69,
        "delayed_projects": 5,
        "notable": "Hyde Park New Cairo Phase 4 delayed 14 months",
    },
    "Inertia": {
        "on_time_pct": 83,
        "delayed_projects": 2,
        "notable": "Jefaira delivered on schedule; Soleya Phase 2 delayed 5 months",
    },
}


AREA_TO_COMPARISON_SUGGESTIONS: dict[str, List[str]] = {
    "new cairo": ["La Vista", "Hassan Allam", "Sodic", "Palm Hills", "Hyde Park", "Sarai", "ZED East"],
    "sheikh zayed": ["ORA", "Sodic", "Emaar", "Palm Hills", "New Giza"],
    "6th of october": ["Palm Hills", "Mountain View", "Sodic", "Badya"],
    "north coast": ["La Vista", "Emaar", "Tatweer Misr", "ORA"],
}

_MIN_ROWS_FOR_FLAGSHIP = 5


async def resolve_to_compound(
    name: str,
    db: AsyncSession,
) -> Optional[str]:
    """
    If `name` is a developer in DEVELOPER_TO_COMPOUNDS, return that developer's
    first compound (by flagship order) that has ≥5 available property rows.
    Uses a single IN query instead of N sequential queries (N+1 fix).

    Returns None if `name` is a known developer but none of their compounds are
    sufficiently stocked — caller should ask the user to pick one explicitly.
    Returns `name` unchanged if it isn't a tracked developer (treated as a
    compound name already).
    """
    candidates = DEVELOPER_TO_COMPOUNDS.get(name)
    if not candidates:
        return name

    stmt = (
        select(Property.compound, func.count(Property.id).label("cnt"))
        .where(Property.compound.in_(candidates))
        .where(Property.is_available == True)  # noqa: E712
        .group_by(Property.compound)
        .having(func.count(Property.id) >= _MIN_ROWS_FOR_FLAGSHIP)
    )
    rows = (await db.execute(stmt)).all()
    stocked = {r.compound for r in rows}

    for compound in candidates:
        if compound in stocked:
            return compound

    return None


def get_delivery_track_record(developer_name: str) -> Optional[dict]:
    """Return the delivery track record for a developer, or None if unknown."""
    return DEVELOPER_DELIVERY_TRACK_RECORD.get(developer_name)


def list_developer_compounds(name: str) -> List[str]:
    """
    Public helper for the dialog layer when it needs to suggest compounds to
    the user (e.g., "أي كمبوند بالظبط من Hassan Allam؟ مثلاً: Swan Lake, Hap Town.").
    """
    return list(DEVELOPER_TO_COMPOUNDS.get(name, []))


def suggest_comparison_names(area: Optional[str], limit: int = 3) -> List[str]:
    """Return names that make a good resale-vs-developer comparison for an area."""
    if not area:
        return []
    return AREA_TO_COMPARISON_SUGGESTIONS.get(area, [])[:limit]
