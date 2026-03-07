"""
Gamification API Endpoints
----------------------------
REST API for investor progression, achievements, favorites, and saved searches.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.auth import get_current_user
from app.models import (
    User, UserFavorite, SavedSearch, Property,
    Achievement, UserAchievement,
)
from app.services.gamification import gamification_engine

import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


# ═══════════════════════════════════════════════════════════════
# INVESTOR PROFILE
# ═══════════════════════════════════════════════════════════════

@router.get("/profile")
async def get_investor_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full investor gamification profile.
    Returns: level, XP, streaks, achievements, readiness score.
    """
    # Update login streak on profile access
    await gamification_engine.update_streak(user.id, db)
    profile = await gamification_engine.get_full_profile(user.id, db)
    return profile


@router.get("/achievements")
async def get_all_achievements(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all achievements with unlock status for current user.
    """
    # Get all defined achievements
    result = await db.execute(select(Achievement).order_by(Achievement.category, Achievement.tier))
    all_achievements = result.scalars().all()

    # Get user's unlocked achievements
    result = await db.execute(
        select(UserAchievement.achievement_id, UserAchievement.unlocked_at)
        .filter(UserAchievement.user_id == user.id)
    )
    unlocked_map = {row.achievement_id: row.unlocked_at for row in result.all()}

    return {
        "total": len(all_achievements),
        "unlocked": len(unlocked_map),
        "achievements": [
            {
                "key": a.key,
                "title_en": a.title_en,
                "title_ar": a.title_ar,
                "description_en": a.description_en,
                "description_ar": a.description_ar,
                "icon": a.icon,
                "category": a.category,
                "tier": a.tier,
                "xp_reward": a.xp_reward,
                "unlocked": a.id in unlocked_map,
                "unlocked_at": unlocked_map[a.id].isoformat() if a.id in unlocked_map else None,
            }
            for a in all_achievements
        ],
    }


@router.get("/leaderboard")
async def get_leaderboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Top 20 investors by XP (anonymized - first name + last initial only).
    """
    from app.models import InvestorProfile
    from sqlalchemy import func

    result = await db.execute(
        select(
            InvestorProfile.xp,
            InvestorProfile.level,
            InvestorProfile.properties_analyzed,
            User.full_name,
        )
        .join(User, InvestorProfile.user_id == User.id)
        .order_by(InvestorProfile.xp.desc())
        .limit(20)
    )

    leaders = []
    for i, row in enumerate(result.all()):
        # Anonymize: "Mohamed Hani" → "Mohamed H."
        name = row.full_name or "Investor"
        parts = name.split()
        display_name = parts[0] + (" " + parts[1][0] + "." if len(parts) > 1 else "")

        leaders.append({
            "rank": i + 1,
            "name": display_name,
            "xp": row.xp,
            "level": row.level,
            "properties_analyzed": row.properties_analyzed,
        })

    return {"leaderboard": leaders}


# ═══════════════════════════════════════════════════════════════
# FAVORITES / SHORTLIST
# ═══════════════════════════════════════════════════════════════

class FavoriteNoteRequest(BaseModel):
    notes: Optional[str] = None


@router.post("/favorite/{property_id}")
async def toggle_favorite(
    property_id: int,
    body: Optional[FavoriteNoteRequest] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle favorite on a property. If already favorited, removes it."""
    # Check property exists
    prop_result = await db.execute(select(Property).filter(Property.id == property_id))
    prop = prop_result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check if already favorited
    result = await db.execute(
        select(UserFavorite).filter(
            UserFavorite.user_id == user.id,
            UserFavorite.property_id == property_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Remove favorite
        await db.delete(existing)
        await db.commit()
        return {"status": "removed", "property_id": property_id}
    else:
        # Add favorite
        fav = UserFavorite(
            user_id=user.id,
            property_id=property_id,
            notes=body.notes if body else None,
        )
        db.add(fav)
        await db.commit()

        # Award XP for first favorite
        xp_result = await gamification_engine.award_xp(user.id, "first_favorite", db)

        return {
            "status": "added",
            "property_id": property_id,
            "xp": xp_result,
        }


@router.get("/favorites")
async def get_favorites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's shortlisted properties with details."""
    result = await db.execute(
        select(UserFavorite, Property)
        .join(Property, UserFavorite.property_id == Property.id)
        .filter(UserFavorite.user_id == user.id)
        .order_by(UserFavorite.added_at.desc())
    )

    favorites = []
    for fav, prop in result.all():
        favorites.append({
            "id": fav.id,
            "property_id": prop.id,
            "title": prop.title,
            "location": prop.location,
            "developer": prop.developer,
            "price": float(prop.price) if prop.price else 0,
            "price_per_sqm": float(prop.price_per_sqm) if prop.price_per_sqm else 0,
            "size_sqm": prop.size_sqm,
            "bedrooms": prop.bedrooms,
            "image_url": prop.image_url,
            "notes": fav.notes,
            "added_at": fav.added_at.isoformat() if fav.added_at else None,
        })

    return {"total": len(favorites), "favorites": favorites}


# ═══════════════════════════════════════════════════════════════
# SAVED SEARCHES
# ═══════════════════════════════════════════════════════════════

class SavedSearchRequest(BaseModel):
    name: str = Field(..., max_length=100)
    location: Optional[str] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    bedrooms: Optional[int] = None
    property_type: Optional[str] = None


@router.post("/saved-search")
async def create_saved_search(
    req: SavedSearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a background search agent."""
    # Limit to 5 saved searches per user
    result = await db.execute(
        select(SavedSearch).filter(
            SavedSearch.user_id == user.id,
            SavedSearch.is_active == True,
        )
    )
    existing = result.scalars().all()
    if len(existing) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 active saved searches")

    filters = {
        "location": req.location,
        "budget_min": req.budget_min,
        "budget_max": req.budget_max,
        "bedrooms": req.bedrooms,
        "property_type": req.property_type,
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    search = SavedSearch(
        user_id=user.id,
        name=req.name,
        filters_json=json.dumps(filters, ensure_ascii=False),
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)

    return {
        "id": search.id,
        "name": search.name,
        "filters": filters,
        "status": "active",
    }


@router.get("/saved-searches")
async def list_saved_searches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's saved search agents."""
    result = await db.execute(
        select(SavedSearch)
        .filter(SavedSearch.user_id == user.id)
        .order_by(SavedSearch.created_at.desc())
    )
    searches = result.scalars().all()

    return {
        "total": len(searches),
        "searches": [
            {
                "id": s.id,
                "name": s.name,
                "filters": json.loads(s.filters_json),
                "is_active": s.is_active,
                "match_count": s.match_count,
                "last_checked_at": s.last_checked_at.isoformat() if s.last_checked_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in searches
        ],
    }


@router.delete("/saved-search/{search_id}")
async def delete_saved_search(
    search_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved search agent."""
    result = await db.execute(
        select(SavedSearch).filter(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user.id,
        )
    )
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    await db.delete(search)
    await db.commit()
    return {"status": "deleted", "id": search_id}
