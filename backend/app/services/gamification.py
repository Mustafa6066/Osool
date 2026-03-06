"""
Gamification Engine - Professional Investor Progression System
---------------------------------------------------------------
Bloomberg Terminal meets Duolingo: rewards analysis, not speculation.

Levels: Curious (0) → Informed (100) → Analyst (500) → Strategist (2000) → Mogul (5000)
XP Actions: Ask questions, use tools, compare properties, audit contracts, streaks
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models import InvestorProfile, Achievement, UserAchievement

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# LEVEL DEFINITIONS
# ═══════════════════════════════════════════════════════════════

LEVELS = [
    {"key": "curious",      "min_xp": 0,    "title_en": "Curious",     "title_ar": "فضولي",      "unlocks": "Basic search, market overview"},
    {"key": "informed",     "min_xp": 100,  "title_en": "Informed",    "title_ar": "مُطّلع",     "unlocks": "ROI calculator, developer comparison"},
    {"key": "analyst",      "min_xp": 500,  "title_en": "Analyst",     "title_ar": "محلّل",      "unlocks": "Advanced analytics, price heatmap, saved searches"},
    {"key": "strategist",   "min_xp": 2000, "title_en": "Strategist",  "title_ar": "استراتيجي",  "unlocks": "Portfolio view, deal room, custom alerts"},
    {"key": "mogul",        "min_xp": 5000, "title_en": "Mogul",       "title_ar": "قطب عقاري",  "unlocks": "Priority support, off-market access, exclusive reports"},
]

# ═══════════════════════════════════════════════════════════════
# XP AWARD TABLE
# ═══════════════════════════════════════════════════════════════

XP_ACTIONS = {
    "ask_question":         5,
    "use_analysis_tool":    15,
    "compare_properties":   20,
    "audit_contract":       25,
    "area_research":        30,
    "first_favorite":       10,
    "streak_7":             50,
    "streak_30":            150,
    "streak_90":            500,
    "referral":             100,
    "view_property_detail": 3,
    "use_inflation_calc":   15,
    "developer_comparison": 15,
}

# ═══════════════════════════════════════════════════════════════
# ACHIEVEMENT SEED DATA
# ═══════════════════════════════════════════════════════════════

ACHIEVEMENT_SEEDS = [
    {
        "key": "market_hawk",
        "title_en": "Market Hawk", "title_ar": "صقر السوق",
        "description_en": "Viewed 10+ market analyses", "description_ar": "شاف أكتر من 10 تحليلات سوقية",
        "icon": "eye", "category": "analysis", "xp_reward": 75,
        "requirement_type": "count", "requirement_value": 10, "tier": "silver",
    },
    {
        "key": "due_diligence_master",
        "title_en": "Due Diligence Master", "title_ar": "سيد العناية الواجبة",
        "description_en": "Audited 5+ contracts", "description_ar": "راجع أكتر من 5 عقود",
        "icon": "shield-check", "category": "analysis", "xp_reward": 100,
        "requirement_type": "count", "requirement_value": 5, "tier": "gold",
    },
    {
        "key": "inflation_fighter",
        "title_en": "Inflation Fighter", "title_ar": "محارب التضخم",
        "description_en": "Used inflation hedge calculator 3+ times", "description_ar": "استخدم حاسبة التحوط من التضخم 3 مرات",
        "icon": "trending-up", "category": "analysis", "xp_reward": 50,
        "requirement_type": "count", "requirement_value": 3, "tier": "bronze",
    },
    {
        "key": "developer_guru",
        "title_en": "Developer Guru", "title_ar": "خبير المطورين",
        "description_en": "Compared 5+ developers", "description_ar": "قارن بين 5 مطورين أو أكتر",
        "icon": "building-2", "category": "exploration", "xp_reward": 75,
        "requirement_type": "count", "requirement_value": 5, "tier": "silver",
    },
    {
        "key": "early_bird",
        "title_en": "Early Bird", "title_ar": "الطير البدري",
        "description_en": "7-day login streak", "description_ar": "دخل 7 أيام متتالية",
        "icon": "flame", "category": "consistency", "xp_reward": 50,
        "requirement_type": "streak", "requirement_value": 7, "tier": "bronze",
    },
    {
        "key": "diamond_hands",
        "title_en": "Diamond Hands", "title_ar": "إيدين ألماس",
        "description_en": "30-day login streak", "description_ar": "دخل 30 يوم متتالي",
        "icon": "gem", "category": "consistency", "xp_reward": 200,
        "requirement_type": "streak", "requirement_value": 30, "tier": "gold",
    },
    {
        "key": "the_auditor",
        "title_en": "The Auditor", "title_ar": "المدقق",
        "description_en": "Used all 5 analysis tools", "description_ar": "استخدم أدوات التحليل الـ 5 كلهم",
        "icon": "check-circle", "category": "exploration", "xp_reward": 100,
        "requirement_type": "threshold", "requirement_value": 5, "tier": "silver",
    },
    {
        "key": "first_blood",
        "title_en": "First Blood", "title_ar": "أول خطوة",
        "description_en": "Favorited your first property", "description_ar": "حطيت أول عقار في المفضلة",
        "icon": "heart", "category": "exploration", "xp_reward": 25,
        "requirement_type": "count", "requirement_value": 1, "tier": "bronze",
    },
    {
        "key": "market_sage",
        "title_en": "Market Sage", "title_ar": "حكيم السوق",
        "description_en": "Reached Strategist level", "description_ar": "وصل لمستوى استراتيجي",
        "icon": "crown", "category": "mastery", "xp_reward": 300,
        "requirement_type": "threshold", "requirement_value": 2000, "tier": "gold",
    },
    {
        "key": "area_expert",
        "title_en": "Area Expert", "title_ar": "خبير المنطقة",
        "description_en": "Analyzed 20+ properties in one area", "description_ar": "حلل أكتر من 20 عقار في منطقة واحدة",
        "icon": "map-pin", "category": "mastery", "xp_reward": 100,
        "requirement_type": "count", "requirement_value": 20, "tier": "silver",
    },
]


def _get_level_for_xp(xp: int) -> Dict:
    """Return the level info for a given XP value."""
    current = LEVELS[0]
    for level in LEVELS:
        if xp >= level["min_xp"]:
            current = level
    return current


def _get_next_level(current_key: str) -> Optional[Dict]:
    """Return the next level info, or None if at max."""
    for i, level in enumerate(LEVELS):
        if level["key"] == current_key and i < len(LEVELS) - 1:
            return LEVELS[i + 1]
    return None


class GamificationEngine:
    """Core gamification logic: XP, levels, achievements, streaks."""

    async def seed_achievements(self, session: AsyncSession):
        """Seed achievement definitions into the database (idempotent)."""
        try:
            for seed in ACHIEVEMENT_SEEDS:
                existing = await session.execute(
                    select(Achievement).filter(Achievement.key == seed["key"])
                )
                if not existing.scalar_one_or_none():
                    session.add(Achievement(**seed))
            await session.commit()
            logger.info(f"Seeded {len(ACHIEVEMENT_SEEDS)} achievements")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed achievements: {e}", exc_info=True)
            raise

    async def get_or_create_profile(self, user_id: int, session: AsyncSession) -> InvestorProfile:
        """Get or create an investor profile for a user."""
        try:
            result = await session.execute(
                select(InvestorProfile).filter(InvestorProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()

            if not profile:
                profile = InvestorProfile(user_id=user_id)
                session.add(profile)
                await session.commit()
                await session.refresh(profile)

            return profile
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to get/create profile for user {user_id}: {e}", exc_info=True)
            raise

    async def award_xp(
        self,
        user_id: int,
        action: str,
        session: AsyncSession,
        custom_amount: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Award XP for an action. Returns XP gained, new total, and any level-up info.

        Returns:
            {
                "xp_awarded": 15,
                "total_xp": 340,
                "level": "informed",
                "level_up": None | {"from": "curious", "to": "informed", ...},
                "achievements_unlocked": [...]
            }
        """
        amount = custom_amount or XP_ACTIONS.get(action, 0)
        if amount <= 0:
            return {"xp_awarded": 0, "total_xp": 0, "level": "curious", "level_up": None, "achievements_unlocked": []}

        profile = await self.get_or_create_profile(user_id, session)
        old_level = profile.level
        profile.xp += amount

        # Check level change
        new_level_info = _get_level_for_xp(profile.xp)
        level_up = None

        if new_level_info["key"] != old_level:
            profile.level = new_level_info["key"]
            level_up = {
                "from": old_level,
                "to": new_level_info["key"],
                "title_en": new_level_info["title_en"],
                "title_ar": new_level_info["title_ar"],
                "unlocks": new_level_info["unlocks"],
            }

        # Update tool usage tracking
        try:
            tools = json.loads(profile.tools_used or "{}")
            tools[action] = tools.get(action, 0) + 1
            profile.tools_used = json.dumps(tools)
        except (json.JSONDecodeError, TypeError):
            profile.tools_used = json.dumps({action: 1})

        try:
            await session.commit()
            await session.refresh(profile)
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to commit XP award for user {user_id}, action {action}: {e}", exc_info=True)
            raise

        # Check achievements (separate transaction scope)
        try:
            achievements = await self.check_achievements(user_id, session)
        except Exception as e:
            logger.warning(f"Achievement check failed (non-fatal): {e}")
            achievements = []

        return {
            "xp_awarded": amount,
            "total_xp": profile.xp,
            "level": profile.level,
            "level_up": level_up,
            "achievements_unlocked": achievements,
        }

    async def update_streak(self, user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """Update login streak for today. Returns streak info."""
        profile = await self.get_or_create_profile(user_id, session)
        today = date.today()

        last_active = None
        if profile.last_active_date:
            if hasattr(profile.last_active_date, 'date'):
                last_active = profile.last_active_date.date()
            else:
                last_active = profile.last_active_date

        if last_active == today:
            # Already logged in today
            return {
                "streak": profile.login_streak,
                "longest": profile.longest_streak,
                "streak_bonus": None,
            }

        streak_bonus = None

        if last_active and (today - last_active).days == 1:
            # Consecutive day
            profile.login_streak += 1
        elif last_active and (today - last_active).days > 1:
            # Streak broken
            profile.login_streak = 1
        else:
            # First login
            profile.login_streak = 1

        # Update longest streak
        if profile.login_streak > profile.longest_streak:
            profile.longest_streak = profile.login_streak

        profile.last_active_date = datetime.combine(today, datetime.min.time())

        # Award streak bonuses
        if profile.login_streak == 7:
            streak_bonus = await self.award_xp(user_id, "streak_7", session)
        elif profile.login_streak == 30:
            streak_bonus = await self.award_xp(user_id, "streak_30", session)
        elif profile.login_streak == 90:
            streak_bonus = await self.award_xp(user_id, "streak_90", session)

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to commit streak update for user {user_id}: {e}", exc_info=True)
            raise

        return {
            "streak": profile.login_streak,
            "longest": profile.longest_streak,
            "streak_bonus": streak_bonus,
        }

    async def track_area(self, user_id: int, area: str, session: AsyncSession):
        """Track property analysis in an area."""
        profile = await self.get_or_create_profile(user_id, session)
        try:
            areas = json.loads(profile.areas_explored or "{}")
        except (json.JSONDecodeError, TypeError):
            areas = {}

        areas[area] = areas.get(area, 0) + 1
        profile.areas_explored = json.dumps(areas, ensure_ascii=False)
        profile.properties_analyzed += 1
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to track area for user {user_id}, area {area}: {e}", exc_info=True)
            raise

    async def check_achievements(self, user_id: int, session: AsyncSession) -> List[Dict]:
        """Check and unlock any newly qualified achievements."""
        profile = await self.get_or_create_profile(user_id, session)
        unlocked = []

        # Get all achievements
        result = await session.execute(select(Achievement))
        all_achievements = result.scalars().all()

        # Get already unlocked
        result = await session.execute(
            select(UserAchievement.achievement_id)
            .filter(UserAchievement.user_id == user_id)
        )
        already_unlocked = {row for row in result.scalars().all()}

        tools = {}
        try:
            tools = json.loads(profile.tools_used or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        areas = {}
        try:
            areas = json.loads(profile.areas_explored or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        for achievement in all_achievements:
            if achievement.id in already_unlocked:
                continue

            qualified = False

            if achievement.key == "market_hawk":
                total_analyses = sum(tools.get(t, 0) for t in [
                    "use_analysis_tool", "area_research", "use_inflation_calc"
                ])
                qualified = total_analyses >= achievement.requirement_value

            elif achievement.key == "due_diligence_master":
                qualified = tools.get("audit_contract", 0) >= achievement.requirement_value

            elif achievement.key == "inflation_fighter":
                qualified = tools.get("use_inflation_calc", 0) >= achievement.requirement_value

            elif achievement.key == "developer_guru":
                qualified = tools.get("developer_comparison", 0) >= achievement.requirement_value

            elif achievement.key == "early_bird":
                qualified = profile.login_streak >= achievement.requirement_value

            elif achievement.key == "diamond_hands":
                qualified = profile.longest_streak >= achievement.requirement_value

            elif achievement.key == "the_auditor":
                unique_tools = len([k for k, v in tools.items() if v > 0])
                qualified = unique_tools >= achievement.requirement_value

            elif achievement.key == "first_blood":
                qualified = tools.get("first_favorite", 0) >= 1

            elif achievement.key == "market_sage":
                qualified = profile.xp >= achievement.requirement_value

            elif achievement.key == "area_expert":
                qualified = any(count >= achievement.requirement_value for count in areas.values())

            if qualified:
                ua = UserAchievement(user_id=user_id, achievement_id=achievement.id)
                session.add(ua)
                # Bonus XP for achievement
                profile.xp += achievement.xp_reward
                unlocked.append({
                    "key": achievement.key,
                    "title_en": achievement.title_en,
                    "title_ar": achievement.title_ar,
                    "icon": achievement.icon,
                    "tier": achievement.tier,
                    "xp_reward": achievement.xp_reward,
                })

        if unlocked:
            # Re-check level after achievement XP
            new_level = _get_level_for_xp(profile.xp)
            profile.level = new_level["key"]
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to commit achievements for user {user_id}: {e}", exc_info=True)
                raise

        return unlocked

    async def calculate_readiness_score(self, user_id: int, session: AsyncSession) -> int:
        """
        Calculate Investment Readiness Score (0-100).
        Based on: tools used, properties analyzed, knowledge depth, budget clarity.
        """
        profile = await self.get_or_create_profile(user_id, session)

        score = 0

        # Properties analyzed (max 25 pts)
        score += min(profile.properties_analyzed * 2, 25)

        # Tools diversity (max 25 pts)
        try:
            tools = json.loads(profile.tools_used or "{}")
            unique_tools = len([k for k, v in tools.items() if v > 0])
            score += min(unique_tools * 5, 25)
        except (json.JSONDecodeError, TypeError):
            pass

        # Areas explored (max 15 pts)
        try:
            areas = json.loads(profile.areas_explored or "{}")
            score += min(len(areas) * 5, 15)
        except (json.JSONDecodeError, TypeError):
            pass

        # Level bonus (max 20 pts)
        level_bonus = {"curious": 0, "informed": 5, "analyst": 10, "strategist": 15, "mogul": 20}
        score += level_bonus.get(profile.level, 0)

        # Streak bonus (max 15 pts)
        score += min(profile.login_streak, 15)

        final_score = min(score, 100)

        # Persist
        profile.investment_readiness_score = final_score
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to persist readiness score for user {user_id}: {e}", exc_info=True)
            # Non-critical failure, return calculated score anyway
            logger.warning(f"Returning calculated readiness score {final_score} despite commit failure")

        return final_score

    async def get_full_profile(self, user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """Get complete investor gamification profile."""
        profile = await self.get_or_create_profile(user_id, session)
        readiness = await self.calculate_readiness_score(user_id, session)

        # Get achievements
        result = await session.execute(
            select(UserAchievement, Achievement)
            .join(Achievement, UserAchievement.achievement_id == Achievement.id)
            .filter(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        achievements = [
            {
                "key": ach.key,
                "title_en": ach.title_en,
                "title_ar": ach.title_ar,
                "icon": ach.icon,
                "tier": ach.tier,
                "category": ach.category,
                "unlocked_at": ua.unlocked_at.isoformat() if ua.unlocked_at else None,
            }
            for ua, ach in result.all()
        ]

        current_level = _get_level_for_xp(profile.xp)
        next_level = _get_next_level(current_level["key"])

        return {
            "xp": profile.xp,
            "level": current_level["key"],
            "level_title_en": current_level["title_en"],
            "level_title_ar": current_level["title_ar"],
            "level_unlocks": current_level["unlocks"],
            "next_level": {
                "key": next_level["key"],
                "title_en": next_level["title_en"],
                "title_ar": next_level["title_ar"],
                "xp_required": next_level["min_xp"],
                "xp_remaining": next_level["min_xp"] - profile.xp,
            } if next_level else None,
            "investment_readiness_score": readiness,
            "login_streak": profile.login_streak,
            "longest_streak": profile.longest_streak,
            "properties_analyzed": profile.properties_analyzed,
            "achievements": achievements,
            "achievement_count": len(achievements),
            "areas_explored": json.loads(profile.areas_explored or "{}"),
            "tools_used": json.loads(profile.tools_used or "{}"),
        }


# Singleton
gamification_engine = GamificationEngine()
