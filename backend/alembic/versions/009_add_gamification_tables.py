"""Add gamification tables

Revision ID: 009_add_gamification_tables
Revises: 008_add_user_memories
Create Date: 2026-03-01

Adds:
- investor_profiles table (XP, level, streaks, etc.)
- achievements table (achievement definitions)
- user_achievements table (unlocked achievements per user)
- user_favorites table (bookmarked properties)
- saved_searches table (saved search filters)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_add_gamification_tables'
down_revision = '008_add_user_memories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all gamification tables (idempotent - skips if they exist)."""

    # 1. investor_profiles
    op.execute("""
        CREATE TABLE IF NOT EXISTS investor_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            investment_readiness_score INTEGER NOT NULL DEFAULT 0,
            login_streak INTEGER NOT NULL DEFAULT 0,
            longest_streak INTEGER NOT NULL DEFAULT 0,
            last_active_date TIMESTAMP,
            areas_explored TEXT DEFAULT '[]',
            tools_used TEXT DEFAULT '[]',
            properties_analyzed INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # 2. achievements
    op.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id SERIAL PRIMARY KEY,
            key VARCHAR(100) NOT NULL UNIQUE,
            title_en VARCHAR(200) NOT NULL,
            title_ar VARCHAR(200) NOT NULL,
            description_en TEXT NOT NULL,
            description_ar TEXT NOT NULL,
            icon VARCHAR(50) NOT NULL DEFAULT '🏆',
            category VARCHAR(50) NOT NULL DEFAULT 'general',
            xp_reward INTEGER NOT NULL DEFAULT 50,
            requirement_type VARCHAR(100) NOT NULL DEFAULT 'manual',
            requirement_value INTEGER NOT NULL DEFAULT 1,
            tier VARCHAR(20) NOT NULL DEFAULT 'bronze'
        )
    """)

    # 3. user_achievements
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            achievement_id INTEGER NOT NULL REFERENCES achievements(id),
            unlocked_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, achievement_id)
        )
    """)

    # 4. user_favorites
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_favorites (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            property_id INTEGER NOT NULL REFERENCES properties(id),
            notes TEXT,
            added_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, property_id)
        )
    """)

    # 5. saved_searches
    op.execute("""
        CREATE TABLE IF NOT EXISTS saved_searches (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name VARCHAR(200) NOT NULL,
            filters_json TEXT NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            last_checked_at TIMESTAMP,
            match_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_investor_profiles_user_id ON investor_profiles(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_achievements_user_id ON user_achievements(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_favorites_user_id ON user_favorites(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_saved_searches_user_id ON saved_searches(user_id)")


def downgrade() -> None:
    """Drop gamification tables."""
    op.execute("DROP TABLE IF EXISTS saved_searches CASCADE")
    op.execute("DROP TABLE IF EXISTS user_favorites CASCADE")
    op.execute("DROP TABLE IF EXISTS user_achievements CASCADE")
    op.execute("DROP TABLE IF EXISTS achievements CASCADE")
    op.execute("DROP TABLE IF EXISTS investor_profiles CASCADE")
