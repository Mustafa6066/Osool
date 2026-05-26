"""
Generate SEO Comparison Pages
-------------------------------
Creates all developer-vs-developer and area-vs-area permutations as
SEOPage entries, plus project-in-area pages for every project.

Usage:
    cd backend
    python -m scripts.generate_comparisons
"""
import asyncio
import json
import sys
import os
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import SEOPage, Developer, Area, SEOProject, SEOPageType, PageStatus
from sqlalchemy import select, func


async def seed():
    async with AsyncSessionLocal() as session:
        devs = (await session.execute(
            select(Developer).order_by(Developer.name)
        )).scalars().all()
        areas = (await session.execute(
            select(Area).order_by(Area.name)
        )).scalars().all()
        projects = (await session.execute(
            select(SEOProject).order_by(SEOProject.name)
        )).scalars().all()

        existing_count = (await session.execute(
            select(func.count(SEOPage.id))
        )).scalar()
        if existing_count and existing_count > 10:
            print(f"⏭️  SEO pages already has {existing_count} rows, skipping")
            return

        pages = []

        # --- Developer vs Developer comparisons ---
        for d1, d2 in combinations(devs, 2):
            slug = f"{d1.slug}-vs-{d2.slug}"
            title = f"{d1.name} vs {d2.name}: Developer Comparison | Osool"
            title_ar = f"مقارنة {d1.name_ar} و {d2.name_ar} | أصول"
            meta = (f"Compare {d1.name} and {d2.name}: delivery scores, "
                    f"finish quality, pricing, and resale value in Egypt.")
            pages.append(SEOPage(
                slug=slug,
                page_type=SEOPageType.COMPARISON.value,
                status=PageStatus.DRAFT.value,
                title=title,
                title_ar=title_ar,
                meta_desc=meta,
                content_json=json.dumps({
                    "type": "developer_comparison",
                    "developer_1": d1.slug,
                    "developer_2": d2.slug,
                    "keywords": [d1.slug, d2.slug, "developer-comparison", "egypt-real-estate"],
                }),
            ))

        # --- Area vs Area comparisons ---
        for a1, a2 in combinations(areas, 2):
            slug = f"{a1.slug}-vs-{a2.slug}"
            title = f"{a1.name} vs {a2.name}: Area Comparison | Osool"
            title_ar = f"مقارنة {a1.name_ar} و {a2.name_ar} | أصول"
            meta = (f"Compare {a1.name} and {a2.name}: price per sqm, "
                    f"appreciation rate, rental yield, and lifestyle in Egypt.")
            pages.append(SEOPage(
                slug=slug,
                page_type=SEOPageType.COMPARISON.value,
                status=PageStatus.DRAFT.value,
                title=title,
                title_ar=title_ar,
                meta_desc=meta,
                content_json=json.dumps({
                    "type": "area_comparison",
                    "area_1": a1.slug,
                    "area_2": a2.slug,
                    "keywords": [a1.slug, a2.slug, "area-comparison", "egypt-investment"],
                }),
            ))

        # --- Project landing pages ---
        for proj in projects:
            slug = f"project-{proj.slug}"
            title = f"{proj.name}: Prices, Payment Plans & Reviews | Osool"
            title_ar = f"{proj.name_ar}: الأسعار وخطط الدفع والتقييمات | أصول"
            meta = (f"Everything about {proj.name}: unit types, prices from "
                    f"EGP {proj.min_price_per_meter:,.0f}/m\u00b2, payment plans, delivery date, "
                    f"and expert analysis.")
            pages.append(SEOPage(
                slug=slug,
                page_type=SEOPageType.PROJECT_DEEPDIVE.value,
                status=PageStatus.DRAFT.value,
                title=title,
                title_ar=title_ar,
                meta_desc=meta,
                content_json=json.dumps({
                    "type": "project_landing",
                    "project_slug": proj.slug,
                    "keywords": [proj.slug, "project-review", "egypt-property"],
                }),
            ))

        # --- Developer profile pages ---
        for dev in devs:
            slug = f"developer-{dev.slug}"
            title = f"{dev.name}: Projects, Reviews & Scores | Osool"
            title_ar = f"{dev.name_ar}: المشاريع والتقييمات | أصول"
            meta = (f"Full profile of {dev.name}: {dev.total_projects} projects, "
                    f"delivery score {dev.avg_delivery_score}/100, all compounds listed.")
            pages.append(SEOPage(
                slug=slug,
                page_type=SEOPageType.PILLAR_GUIDE.value,
                status=PageStatus.DRAFT.value,
                title=title,
                title_ar=title_ar,
                meta_desc=meta,
                content_json=json.dumps({
                    "type": "developer_profile",
                    "developer_slug": dev.slug,
                    "keywords": [dev.slug, "developer-profile", "egypt-developers"],
                }),
            ))

        # --- Area guide pages ---
        for area in areas:
            slug = f"area-{area.slug}"
            title = f"Invest in {area.name}: Prices, Projects & Guide | Osool"
            title_ar = f"استثمر في {area.name_ar}: الأسعار والمشاريع | أصول"
            meta = (f"Complete guide to {area.name}: avg EGP {area.avg_price_per_meter:,.0f}/m\u00b2, "
                    f"{area.price_growth_ytd}% YoY growth, top projects, and investment tips.")
            pages.append(SEOPage(
                slug=slug,
                page_type=SEOPageType.ROI_TRACKER.value,
                status=PageStatus.DRAFT.value,
                title=title,
                title_ar=title_ar,
                meta_desc=meta,
                content_json=json.dumps({
                    "type": "area_guide",
                    "area_slug": area.slug,
                    "keywords": [area.slug, "area-guide", "egypt-investment"],
                }),
            ))

        session.add_all(pages)
        await session.commit()

        # Summary
        dev_comps = len(list(combinations(devs, 2)))
        area_comps = len(list(combinations(areas, 2)))
        print(f"📄 Generated SEO pages:")
        print(f"   Developer comparisons: {dev_comps}")
        print(f"   Area comparisons:      {area_comps}")
        print(f"   Project pages:         {len(projects)}")
        print(f"   Developer profiles:    {len(devs)}")
        print(f"   Area guides:           {len(areas)}")
        print(f"   Total:                 {len(pages)}")


if __name__ == "__main__":
    asyncio.run(seed())
