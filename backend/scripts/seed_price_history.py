"""
Seed Price History
-------------------
Generates 12 months of realistic price-per-sqm data for every
area and a sample of projects. Simulates Egyptian market appreciation.

Usage:
    cd backend
    python -m scripts.seed_price_history
"""
import asyncio
import random
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import PriceHistory, Area, SEOProject
from sqlalchemy import select, func


async def seed():
    async with AsyncSessionLocal() as session:
        # --- area-level history ---
        areas = (await session.execute(select(Area))).scalars().all()
        projects = (await session.execute(select(SEOProject))).scalars().all()

        if not areas:
            print("❌ Run seed_areas first!")
            return

        # Check if already seeded
        count = (await session.execute(select(func.count(PriceHistory.id)))).scalar()
        if count and count > 50:
            print(f"⏭️  Price history already has {count} rows, skipping")
            return

        today = date.today().replace(day=1)
        rows = []

        for area in areas:
            base_price = float(area.avg_price_per_meter or 25000)
            monthly_rate = (area.price_growth_ytd or 20.0) / 100.0 / 12.0

            for month_offset in range(12, 0, -1):
                record_date = today - timedelta(days=30 * month_offset)
                factor = (1 + monthly_rate) ** (12 - month_offset)
                noise = random.uniform(-0.02, 0.02)
                price = int(base_price * factor * (1 + noise))

                rows.append(PriceHistory(
                    area_id=area.id,
                    project_id=None,
                    date=record_date,
                    price_per_m2=price,
                    source="osool-analytics",
                ))

        for project in projects:
            base_price = float(project.min_price_per_meter or 25000)
            monthly_rate = random.uniform(0.012, 0.035)

            for month_offset in range(12, 0, -1):
                record_date = today - timedelta(days=30 * month_offset)
                factor = (1 + monthly_rate) ** (12 - month_offset)
                noise = random.uniform(-0.03, 0.03)
                price = int(base_price * factor * (1 + noise))

                rows.append(PriceHistory(
                    area_id=None,
                    project_id=project.id,
                    date=record_date,
                    price_per_m2=price,
                    source="osool-analytics",
                ))

        session.add_all(rows)
        await session.commit()
        print(f"📊 Seeded {len(rows)} price history records "
              f"({len(areas)} areas × 12 months + {len(projects)} projects × 12 months)")


if __name__ == "__main__":
    asyncio.run(seed())
