"""
Seed Egyptian Real Estate Projects
------------------------------------
Populates seo_projects table with 30+ real projects from major developers.

Usage:
    cd backend
    python -m scripts.seed_projects
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import SEOProject, Developer, Area, ProjectType, ProjectStatus
from sqlalchemy import select


PROJECT_TYPE_MAP = {
    "COMPOUND": ProjectType.RESIDENTIAL.value,
    "RESORT": ProjectType.RESORT.value,
    "TOWER": ProjectType.RESIDENTIAL.value,
}

PROJECT_STATUS_MAP = {
    "SELLING": ProjectStatus.UNDER_CONSTRUCTION.value,
    "DELIVERED": ProjectStatus.DELIVERED.value,
}


async def get_lookup(session):
    """Build slug→id lookups for developers and areas."""
    devs = (await session.execute(select(Developer))).scalars().all()
    areas = (await session.execute(select(Area))).scalars().all()
    return (
        {d.slug: d.id for d in devs},
        {a.slug: a.id for a in areas},
    )


# (slug, name, name_ar, developer_slug, area_slug, type, status, price_min, price_max, down_pct, installments_months, delivery_year, bedrooms_min, bedrooms_max, area_sqm_min, area_sqm_max, amenities_json)
# Note: price_min/max are total prices; we derive per-meter from unit sizes.
# bedrooms_min/max are kept in tuple but not stored (no model column).
PROJECTS = [
    ("zed-sheikh-zayed", "ZED Sheikh Zayed", "زيد الشيخ زايد", "ora-developers", "sheikh-zayed", "COMPOUND", "SELLING", 5_500_000, 22_000_000, 10, 96, 2027, 1, 4, 80, 320, '["Golf Course","Clubhouse","Gym","Swimming Pool","Commercial Area"]'),
    ("zed-east", "ZED East", "زيد إيست", "ora-developers", "el-shorouk", "COMPOUND", "SELLING", 4_000_000, 15_000_000, 10, 84, 2026, 1, 4, 75, 280, '["Parks","Gym","Retail","Lake","Kids Area"]'),
    ("sodic-east", "Sodic East", "سوديك إيست", "sodic", "el-shorouk", "COMPOUND", "SELLING", 4_200_000, 18_000_000, 10, 96, 2027, 2, 5, 120, 350, '["Sports Club","Lakes","Retail","Schools","Medical Center"]'),
    ("sodic-west-the-estates", "The Estates by Sodic", "ذا إستيتس سوديك", "sodic", "sheikh-zayed", "COMPOUND", "SELLING", 12_000_000, 45_000_000, 15, 84, 2026, 3, 6, 200, 600, '["Golf Course","Clubhouse","Lagoon","Spa","Equestrian"]'),
    ("vye-sodic", "VYE by Sodic", "فاي سوديك", "sodic", "new-capital-r7", "COMPOUND", "SELLING", 5_800_000, 20_000_000, 10, 96, 2028, 1, 4, 90, 300, '["Smart Home","Gym","Commercial","Green Spaces","Running Tracks"]'),
    ("o-west", "O West", "أو ويست", "orascom-development", "6th-october", "COMPOUND", "SELLING", 6_000_000, 25_000_000, 10, 96, 2027, 2, 5, 110, 400, '["Golf Course","Clubhouse","Commercial Strip","Parks","Schools"]'),
    ("marassi", "Marassi", "مراسي", "emaar-misr", "north-coast", "RESORT", "DELIVERED", 4_500_000, 30_000_000, 20, 60, 2020, 1, 5, 70, 350, '["Beach","Marina","Golf Course","Hotels","Water Park"]'),
    ("uptown-cairo", "Uptown Cairo", "أبتاون كايرو", "emaar-misr", "6th-october", "COMPOUND", "DELIVERED", 8_000_000, 40_000_000, 25, 48, 2018, 2, 6, 150, 500, '["Golf Course","Clubhouse","Retail","Schools","Medical"]'),
    ("palm-hills-katameya", "Palm Hills Katameya", "بالم هيلز القطامية", "palm-hills", "el-shorouk", "COMPOUND", "DELIVERED", 7_000_000, 35_000_000, 20, 60, 2019, 3, 6, 180, 550, '["Golf Course","Sports Club","Lakes","Retail"]'),
    ("palm-hills-new-cairo", "Palm Hills New Cairo", "بالم هيلز القاهرة الجديدة", "palm-hills", "mostakbal-city", "COMPOUND", "SELLING", 5_000_000, 22_000_000, 10, 96, 2027, 2, 5, 120, 380, '["Clubhouse","Swimming Pool","Parks","Commercial Area","Schools"]'),
    ("badya-palm-hills", "Badya by Palm Hills", "بادية بالم هيلز", "palm-hills", "6th-october", "COMPOUND", "SELLING", 4_800_000, 20_000_000, 10, 96, 2028, 1, 5, 90, 350, '["Smart City","AI Management","Lakes","Commercial","University"]'),
    ("mountain-view-icity", "Mountain View iCity", "ماونتن فيو آي سيتي", "mountain-view", "6th-october", "COMPOUND", "SELLING", 5_500_000, 18_000_000, 10, 84, 2026, 1, 4, 85, 300, '["iClub","Parks","Commercial","Schools","Medical"]'),
    ("mountain-view-ras-el-hikma", "Mountain View Ras El Hikma", "ماونتن فيو رأس الحكمة", "mountain-view", "ras-el-hikma", "RESORT", "SELLING", 6_000_000, 25_000_000, 15, 84, 2027, 1, 4, 70, 250, '["Beach","Infinity Pool","Restaurants","Water Sports","Spa"]'),
    ("mountain-view-chillout-park", "Mountain View Chillout Park", "ماونتن فيو تشيل أوت بارك", "mountain-view", "6th-october", "COMPOUND", "SELLING", 4_200_000, 14_000_000, 10, 96, 2027, 1, 3, 75, 220, '["Nature Park","Jogging Track","Gym","Retail","Kids Area"]'),
    ("madinaty-tmg", "Madinaty", "مدينتي", "tmg", "madinaty", "COMPOUND", "DELIVERED", 3_500_000, 25_000_000, 20, 60, 2015, 1, 6, 80, 450, '["Golf Course","Open Air Mall","Medical City","Schools","Sports Club"]'),
    ("noor-city-tmg", "Noor City", "مدينة نور", "tmg", "mostakbal-city", "COMPOUND", "SELLING", 3_000_000, 15_000_000, 5, 120, 2030, 1, 5, 70, 350, '["Smart City","Green Belt","Commercial","Schools","Medical"]'),
    ("hyde-park-new-cairo", "Hyde Park New Cairo", "هايد بارك القاهرة الجديدة", "hyde-park", "mostakbal-city", "COMPOUND", "SELLING", 5_200_000, 22_000_000, 10, 96, 2027, 2, 5, 100, 350, '["Central Park","Clubhouse","Commercial","Schools","Gym"]'),
    ("il-bosco-new-capital", "IL Bosco New Capital", "إل بوسكو العاصمة", "tatweer-misr", "new-capital-r7", "COMPOUND", "SELLING", 6_500_000, 25_000_000, 10, 96, 2027, 2, 5, 120, 380, '["Italian Design","Central Park","Commercial","Schools","Clubhouse"]'),
    ("bloomfields", "Bloomfields", "بلوم فيلدز", "tatweer-misr", "mostakbal-city", "COMPOUND", "SELLING", 4_500_000, 18_000_000, 10, 96, 2027, 1, 4, 90, 300, '["Sustainability","Parks","Commercial","Schools","Clubhouse"]'),
    ("fouka-bay", "Fouka Bay", "فوكا باي", "tatweer-misr", "north-coast", "RESORT", "SELLING", 4_000_000, 16_000_000, 15, 84, 2026, 1, 4, 65, 250, '["Beach","Infinity Pools","Restaurants","Water Sports","Kids"]'),
    ("la-vista-bay", "La Vista Bay", "لافيستا باي", "la-vista", "ain-sokhna", "RESORT", "DELIVERED", 3_500_000, 15_000_000, 20, 60, 2021, 1, 4, 60, 220, '["Beach","Pool","Restaurant","Water Sports"]'),
    ("el-patio-7", "El Patio 7", "الباتيو 7", "la-vista", "el-shorouk", "COMPOUND", "SELLING", 5_500_000, 18_000_000, 10, 84, 2026, 2, 5, 120, 350, '["Clubhouse","Swimming Pool","Commercial","Parks"]'),
    ("silversands-north-coast", "Silversands North Coast", "سيلفرساندز الساحل", "ora-developers", "north-coast", "RESORT", "SELLING", 5_000_000, 22_000_000, 15, 84, 2027, 1, 4, 70, 280, '["Beach","Hotel","Spa","Infinity Pool","Marina"]'),
    ("city-edge-towers-new-alamein", "City Edge Towers New Alamein", "أبراج سيتي إيدج العلمين", "city-edge", "new-alamein", "TOWER", "SELLING", 3_500_000, 12_000_000, 10, 96, 2027, 1, 3, 60, 200, '["Sea View","Pool","Commercial","Hotel Services"]'),
    ("mazarine-new-alamein", "Mazarine New Alamein", "مازارين العلمين", "city-edge", "new-alamein", "TOWER", "SELLING", 4_000_000, 15_000_000, 10, 84, 2027, 1, 3, 70, 220, '["Beach Front","Pool","Gym","Commercial","Hotel"]'),
    ("aeon-6th-october", "Aeon", "إيون", "marakez", "6th-october", "COMPOUND", "SELLING", 5_000_000, 20_000_000, 10, 96, 2028, 2, 5, 110, 350, '["Mall of Arabia Access","Clubhouse","Parks","Schools"]'),
    ("keeva-sabbour", "Keeva by Sabbour", "كيفا صبور", "al-ahly-sabbour", "sheikh-zayed", "COMPOUND", "SELLING", 6_000_000, 20_000_000, 10, 96, 2027, 2, 5, 130, 350, '["Clubhouse","Swimming Pool","Sports","Parks","Commercial"]'),
    ("aria-sabbour", "Aria by Sabbour", "أريا صبور", "al-ahly-sabbour", "mostakbal-city", "COMPOUND", "SELLING", 4_500_000, 16_000_000, 10, 96, 2028, 1, 4, 90, 280, '["Green Spaces","Clubhouse","Retail","Schools","Gym"]'),
    ("swan-lake-residences", "Swan Lake Residences", "سوان ليك ريزيدنسز", "hassan-allam-properties", "el-shorouk", "COMPOUND", "SELLING", 7_000_000, 30_000_000, 10, 84, 2027, 3, 6, 180, 500, '["Lake","Golf Course","Clubhouse","Retail","Schools"]'),
    ("haptown", "HAPTown", "هاب تاون", "hassan-allam-properties", "mostakbal-city", "COMPOUND", "SELLING", 4_500_000, 18_000_000, 10, 96, 2028, 1, 5, 85, 320, '["Smart Home","Clubhouse","Parks","Commercial","Schools"]'),
    ("park-view-new-capital", "Park View New Capital", "بارك فيو العاصمة", "hassan-allam-properties", "new-capital-r5", "COMPOUND", "SELLING", 5_000_000, 20_000_000, 10, 96, 2027, 2, 5, 100, 350, '["Central Park","Clubhouse","Retail","Schools","Gym"]'),
]


async def seed():
    async with AsyncSessionLocal() as session:
        dev_map, area_map = await get_lookup(session)

        if not dev_map or not area_map:
            print("❌ Run seed_developers and seed_areas first!")
            return

        import json
        from datetime import datetime
        count = 0
        for row in PROJECTS:
            slug = row[0]
            existing = await session.execute(
                select(SEOProject).where(SEOProject.slug == slug)
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭️  {row[1]} already exists, skipping")
                continue

            dev_id = dev_map.get(row[3])
            area_id = area_map.get(row[4])
            if not dev_id:
                print(f"  ⚠️  Developer '{row[3]}' not found, skipping {row[1]}")
                continue
            if not area_id:
                print(f"  ⚠️  Area '{row[4]}' not found, skipping {row[1]}")
                continue

            # Derive price per meter from total price / unit size
            area_min = float(row[14] or 100)
            area_max = float(row[15] or area_min)
            min_price_per_m = int(row[7] / area_max) if row[7] and area_max else 0
            max_price_per_m = int(row[8] / area_min) if row[8] and area_min else 0

            project_type = PROJECT_TYPE_MAP.get(row[5], ProjectType.RESIDENTIAL.value)
            project_status = PROJECT_STATUS_MAP.get(row[6], ProjectStatus.UNDER_CONSTRUCTION.value)

            project = SEOProject(
                slug=slug,
                name=row[1],
                name_ar=row[2],
                developer_id=dev_id,
                area_id=area_id,
                project_type=project_type,
                status=project_status,
                min_price_per_meter=min_price_per_m,
                max_price_per_meter=max_price_per_m,
                avg_price_per_meter=(min_price_per_m + max_price_per_m) / 2,
                down_payment_min=row[9],
                installment_years=row[10] // 12 if row[10] else None,
                expected_delivery=datetime(row[11], 1, 1) if row[11] else None,
                min_unit_size=row[14],
                max_unit_size=row[15],
                amenities=row[16],  # already a JSON string
            )
            session.add(project)
            count += 1
            print(f"  ✅ Added {row[1]}")

        await session.commit()
        print(f"\n🏠 Seeded {count} projects")


if __name__ == "__main__":
    asyncio.run(seed())
