"""Add Dual-Engine Marketing & SEO Platform tables

Revision ID: 015_add_dual_engine_models
Revises: 014_add_geopolitical_events
Create Date: 2026-03-09

Adds:
- developers: Real estate developer profiles for comparison pages
- areas: Neighborhood profiles for ROI tracker pages
- seo_projects: Curated project records for deep-dive pages
- price_history: Historical price/m² data for trend charts
- chat_intents: Structured intent extracted from chat messages
- lead_profiles: Lead scoring and segmentation
- email_events: Email drip sequence tracking
- seo_pages: Programmatic SEO page management
- ad_campaigns: Ad campaign performance tracking
- retargeting_rules: Behavior-to-audience mapping rules
- waitlist_entries: Premium waitlist signups
- reports: Generated personalized ROI reports
"""
from alembic import op
import sqlalchemy as sa


revision = '015_add_dual_engine_models'
down_revision = '014_add_geopolitical_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Developers ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS developers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL UNIQUE,
            name_ar VARCHAR(200) NOT NULL,
            slug VARCHAR(200) NOT NULL UNIQUE,
            logo TEXT,
            description TEXT,
            description_ar TEXT,
            founded_year INTEGER,
            total_projects INTEGER DEFAULT 0,
            avg_delivery_score FLOAT DEFAULT 0,
            avg_finish_quality FLOAT DEFAULT 0,
            avg_resale_retention FLOAT DEFAULT 0,
            payment_flexibility FLOAT DEFAULT 0,
            overall_score FLOAT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_developers_slug ON developers(slug)")

    # ── Areas ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS areas (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL UNIQUE,
            name_ar VARCHAR(200) NOT NULL,
            slug VARCHAR(200) NOT NULL UNIQUE,
            city VARCHAR(100) NOT NULL,
            description TEXT,
            description_ar TEXT,
            avg_price_per_meter FLOAT DEFAULT 0,
            price_growth_ytd FLOAT DEFAULT 0,
            predicted_roi_5y FLOAT DEFAULT 0,
            rental_yield FLOAT DEFAULT 0,
            liquidity_score FLOAT DEFAULT 0,
            demand_score FLOAT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_areas_slug ON areas(slug)")

    # ── SEO Projects ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS seo_projects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            name_ar VARCHAR(200) NOT NULL,
            slug VARCHAR(200) NOT NULL UNIQUE,
            developer_id INTEGER NOT NULL REFERENCES developers(id),
            area_id INTEGER NOT NULL REFERENCES areas(id),
            description TEXT,
            description_ar TEXT,
            project_type VARCHAR(30) DEFAULT 'residential',
            status VARCHAR(30) DEFAULT 'under_construction',
            launch_date TIMESTAMPTZ,
            expected_delivery TIMESTAMPTZ,
            actual_delivery TIMESTAMPTZ,
            min_price_per_meter FLOAT DEFAULT 0,
            max_price_per_meter FLOAT DEFAULT 0,
            avg_price_per_meter FLOAT DEFAULT 0,
            min_unit_size FLOAT,
            max_unit_size FLOAT,
            down_payment_min FLOAT,
            installment_years INTEGER,
            predicted_roi_1y FLOAT DEFAULT 0,
            predicted_roi_3y FLOAT DEFAULT 0,
            predicted_roi_5y FLOAT DEFAULT 0,
            resale_value_retention FLOAT DEFAULT 0,
            construction_progress FLOAT DEFAULT 0,
            unit_types TEXT,
            amenities TEXT,
            images TEXT,
            lat FLOAT,
            lng FLOAT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_projects_slug ON seo_projects(slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_projects_developer_id ON seo_projects(developer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_projects_area_id ON seo_projects(area_id)")

    # ── Price History ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES seo_projects(id),
            area_id INTEGER REFERENCES areas(id),
            price_per_m2 FLOAT NOT NULL,
            date TIMESTAMPTZ NOT NULL,
            source VARCHAR(200),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_price_history_project_date ON price_history(project_id, date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_price_history_area_date ON price_history(area_id, date)")

    # ── Chat Intents ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_intents (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR NOT NULL,
            intent_type VARCHAR(30) NOT NULL,
            entities TEXT,
            segment VARCHAR(50),
            confidence FLOAT DEFAULT 0,
            raw_query TEXT NOT NULL,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_intents_session_id ON chat_intents(session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_intents_intent_type ON chat_intents(intent_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_intents_processed ON chat_intents(processed)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_intents_created_at ON chat_intents(created_at)")

    # ── Lead Profiles ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS lead_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            score FLOAT DEFAULT 0,
            segment VARCHAR(50),
            budget_min FLOAT,
            budget_max FLOAT,
            preferred_areas TEXT,
            preferred_types TEXT,
            timeline VARCHAR(50),
            risk_appetite VARCHAR(50),
            investment_goal VARCHAR(50),
            interaction_count INTEGER DEFAULT 0,
            last_interaction TIMESTAMPTZ,
            email_sequence_step INTEGER DEFAULT 0,
            converted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_lead_profiles_user_id ON lead_profiles(user_id)")

    # ── Email Events ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS email_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            template_id VARCHAR(100) NOT NULL,
            status VARCHAR(20) DEFAULT 'queued',
            sent_at TIMESTAMPTZ,
            opened_at TIMESTAMPTZ,
            clicked_at TIMESTAMPTZ,
            metadata_json TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_events_user_id ON email_events(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_email_events_template_id ON email_events(template_id)")

    # ── SEO Pages ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS seo_pages (
            id SERIAL PRIMARY KEY,
            page_type VARCHAR(30) NOT NULL,
            slug VARCHAR(500) NOT NULL UNIQUE,
            title VARCHAR(500) NOT NULL,
            title_ar VARCHAR(500),
            meta_desc TEXT NOT NULL,
            meta_desc_ar TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            generated_from VARCHAR(50),
            source_intents TEXT,
            view_count INTEGER DEFAULT 0,
            chat_conv_rate FLOAT DEFAULT 0,
            last_built TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_pages_slug ON seo_pages(slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_pages_page_type ON seo_pages(page_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_seo_pages_status ON seo_pages(status)")

    # ── Ad Campaigns ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            id SERIAL PRIMARY KEY,
            platform VARCHAR(30) NOT NULL,
            campaign_id VARCHAR(200) NOT NULL,
            name VARCHAR(300) NOT NULL,
            status VARCHAR(30) DEFAULT 'active',
            target_segment VARCHAR(100),
            budget FLOAT,
            spend FLOAT DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            roas FLOAT DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── Retargeting Rules ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS retargeting_rules (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            trigger_type VARCHAR(50) NOT NULL,
            trigger_config TEXT,
            ad_template VARCHAR(200),
            audience VARCHAR(200),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    # ── Waitlist Entries ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS waitlist_entries (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(200),
            phone VARCHAR(50),
            segment VARCHAR(50),
            source VARCHAR(200),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_waitlist_entries_email ON waitlist_entries(email)")

    # ── Reports ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title VARCHAR(300) NOT NULL,
            report_type VARCHAR(50) NOT NULL,
            content TEXT,
            pdf_url TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_reports_user_id ON reports(user_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS reports CASCADE")
    op.execute("DROP TABLE IF EXISTS waitlist_entries CASCADE")
    op.execute("DROP TABLE IF EXISTS retargeting_rules CASCADE")
    op.execute("DROP TABLE IF EXISTS ad_campaigns CASCADE")
    op.execute("DROP TABLE IF EXISTS seo_pages CASCADE")
    op.execute("DROP TABLE IF EXISTS email_events CASCADE")
    op.execute("DROP TABLE IF EXISTS lead_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS chat_intents CASCADE")
    op.execute("DROP TABLE IF EXISTS price_history CASCADE")
    op.execute("DROP TABLE IF EXISTS seo_projects CASCADE")
    op.execute("DROP TABLE IF EXISTS areas CASCADE")
    op.execute("DROP TABLE IF EXISTS developers CASCADE")
