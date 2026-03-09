"""
Master Seed Script — Dual-Engine Data
---------------------------------------
Runs all seed scripts in correct dependency order.

Usage:
    cd backend
    python -m scripts.seed_all
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.seed_developers import seed as seed_developers
from scripts.seed_areas import seed as seed_areas
from scripts.seed_projects import seed as seed_projects
from scripts.seed_price_history import seed as seed_price_history
from scripts.generate_comparisons import seed as seed_comparisons


async def main():
    print("=" * 50)
    print("🚀 Osool Dual-Engine — Full Data Seed")
    print("=" * 50)

    print("\n[1/5] Seeding developers...")
    await seed_developers()

    print("\n[2/5] Seeding areas...")
    await seed_areas()

    print("\n[3/5] Seeding projects...")
    await seed_projects()

    print("\n[4/5] Seeding price history...")
    await seed_price_history()

    print("\n[5/5] Generating SEO comparison pages...")
    await seed_comparisons()

    print("\n" + "=" * 50)
    print("✅ All seed data loaded successfully!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
