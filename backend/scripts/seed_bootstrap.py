"""
SEO Bootstrap Seed
------------------
Idempotent deploy-time bootstrap for the public SEO dataset.

This script is safe to run multiple times. It seeds the minimum public dataset
first (developers, areas), then backfills projects, price history, and SEO pages.
"""

import asyncio
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models import Developer, Area, SEOProject, PriceHistory, SEOPage
from scripts.seed_developers import seed as seed_developers
from scripts.seed_areas import seed as seed_areas
from scripts.seed_projects import seed as seed_projects
from scripts.seed_price_history import seed as seed_price_history
from scripts.generate_comparisons import seed as seed_comparisons


async def get_counts() -> dict[str, int]:
    async with AsyncSessionLocal() as session:
        return {
            "developers": (await session.execute(select(func.count(Developer.id)))).scalar() or 0,
            "areas": (await session.execute(select(func.count(Area.id)))).scalar() or 0,
            "projects": (await session.execute(select(func.count(SEOProject.id)))).scalar() or 0,
            "price_history": (await session.execute(select(func.count(PriceHistory.id)))).scalar() or 0,
            "seo_pages": (await session.execute(select(func.count(SEOPage.id)))).scalar() or 0,
        }


async def run_step(label: str, should_run: bool, step) -> bool:
    if not should_run:
        print(f"⏭️  {label}: already populated, skipping")
        return True

    print(f"▶ {label}...")
    try:
        await step()
        print(f"✅ {label} completed")
        return True
    except Exception as exc:
        print(f"❌ {label} failed: {exc}")
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("SEO bootstrap seed starting")
    print("=" * 60)

    counts = await get_counts()
    print(f"Current counts: {counts}")

    await run_step("Seed developers", counts["developers"] == 0, seed_developers)
    await run_step("Seed areas", counts["areas"] == 0, seed_areas)

    counts = await get_counts()

    await run_step("Seed projects", counts["projects"] == 0, seed_projects)
    await run_step("Seed price history", counts["price_history"] < 50, seed_price_history)
    await run_step("Generate SEO pages", counts["seo_pages"] == 0, seed_comparisons)

    final_counts = await get_counts()
    print(f"Final counts: {final_counts}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())