"""
Seed Egyptian Real Estate Areas
---------------------------------
Populates the areas table with 12 major investment zones.

Usage:
    cd backend
    python -m scripts.seed_areas
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import Area
from sqlalchemy import select


AREAS = [
    {
        "name": "Sheikh Zayed",
        "name_ar": "الشيخ زايد",
        "slug": "sheikh-zayed",
        "city": "Giza",
        "avg_price_per_meter": 35000,
        "price_growth_ytd": 22.5,
        "rental_yield": 5.2,
        "description": "Sheikh Zayed City is a premium satellite city west of Cairo, known for upscale compounds and proximity to the Ring Road.",
        "description_ar": "مدينة الشيخ زايد مدينة فرعية راقية غرب القاهرة، معروفة بالكمبوندات الفاخرة وقربها من الطريق الدائري.",
    },
    {
        "name": "6th of October City",
        "name_ar": "مدينة السادس من أكتوبر",
        "slug": "6th-october",
        "city": "Giza",
        "avg_price_per_meter": 22000,
        "price_growth_ytd": 18.0,
        "rental_yield": 6.0,
        "description": "One of Egypt's largest new cities with a diverse mix of housing, education, and industry. Home to Mall of Arabia and major universities.",
        "description_ar": "واحدة من أكبر المدن الجديدة في مصر بخليط متنوع من السكن والتعليم والصناعة. موطن مول العرب والجامعات الكبرى.",
    },
    {
        "name": "New Administrative Capital – R5",
        "name_ar": "العاصمة الإدارية – R5",
        "slug": "new-capital-r5",
        "city": "New Capital",
        "avg_price_per_meter": 28000,
        "price_growth_ytd": 30.0,
        "rental_yield": 4.5,
        "description": "R5 is a prime residential district in Egypt's New Administrative Capital, featuring mid-to-high-end developments and government housing.",
        "description_ar": "R5 حي سكني رئيسي في العاصمة الإدارية يضم مشاريع متوسطة إلى فاخرة وإسكان حكومي.",
    },
    {
        "name": "New Administrative Capital – R7",
        "name_ar": "العاصمة الإدارية – R7",
        "slug": "new-capital-r7",
        "city": "New Capital",
        "avg_price_per_meter": 32000,
        "price_growth_ytd": 32.0,
        "rental_yield": 4.8,
        "description": "R7 is the most in-demand residential district in the New Capital, home to IL Bosco, The City of Odyssia, and several embassy sectors.",
        "description_ar": "R7 أكثر الأحياء طلباً في العاصمة الإدارية، موطن إل بوسكو ومدينة أوديسيا وعدة قطاعات سفارات.",
    },
    {
        "name": "New Administrative Capital – R8",
        "name_ar": "العاصمة الإدارية – R8",
        "slug": "new-capital-r8",
        "city": "New Capital",
        "avg_price_per_meter": 25000,
        "price_growth_ytd": 28.0,
        "rental_yield": 5.0,
        "description": "R8 is a growing residential area in the New Capital with affordable luxury offerings and strong investment potential.",
        "description_ar": "R8 منطقة سكنية متنامية في العاصمة الإدارية تقدم رفاهية بأسعار معقولة وإمكانيات استثمارية قوية.",
    },
    {
        "name": "New Alamein",
        "name_ar": "العلمين الجديدة",
        "slug": "new-alamein",
        "city": "Matrouh",
        "avg_price_per_meter": 45000,
        "price_growth_ytd": 35.0,
        "rental_yield": 3.5,
        "description": "New Alamein is a massive government-backed coastal city on the Mediterranean, featuring towers, hotels, and a year-round residential vision.",
        "description_ar": "العلمين الجديدة مدينة ساحلية ضخمة على البحر المتوسط مدعومة حكومياً تضم أبراجاً وفنادق ورؤية سكنية على مدار العام.",
    },
    {
        "name": "Ras El Hikma",
        "name_ar": "رأس الحكمة",
        "slug": "ras-el-hikma",
        "city": "Matrouh",
        "avg_price_per_meter": 55000,
        "price_growth_ytd": 40.0,
        "rental_yield": 3.0,
        "description": "Ras El Hikma is Egypt's hottest investment zone following the $35B UAE deal. Crystal-clear waters and mega-resort developments.",
        "description_ar": "رأس الحكمة أكثر مناطق الاستثمار سخونة بعد صفقة الإمارات بـ35 مليار دولار. مياه كريستالية ومنتجعات ضخمة.",
    },
    {
        "name": "Ain Sokhna",
        "name_ar": "العين السخنة",
        "slug": "ain-sokhna",
        "city": "Suez",
        "avg_price_per_meter": 30000,
        "price_growth_ytd": 20.0,
        "rental_yield": 5.5,
        "description": "Ain Sokhna is Cairo's closest Red Sea getaway, about 90 minutes from the capital. Popular for weekend homes and resort chalets.",
        "description_ar": "العين السخنة أقرب وجهة بحر أحمر للقاهرة على بعد 90 دقيقة. مشهورة ببيوت العطلات والشاليهات.",
    },
    {
        "name": "Mostakbal City",
        "name_ar": "مدينة المستقبل",
        "slug": "mostakbal-city",
        "city": "Cairo",
        "avg_price_per_meter": 26000,
        "price_growth_ytd": 25.0,
        "rental_yield": 5.0,
        "description": "Mostakbal City is an emerging smart city east of Cairo, adjacent to the New Capital. Known for Bloomfields, HAPTOWN, and Sarai.",
        "description_ar": "مدينة المستقبل مدينة ذكية ناشئة شرق القاهرة مجاورة للعاصمة الإدارية. معروفة ببلوم فيلدز وهاب تاون وسراي.",
    },
    {
        "name": "Madinaty",
        "name_ar": "مدينتي",
        "slug": "madinaty",
        "city": "Cairo",
        "avg_price_per_meter": 32000,
        "price_growth_ytd": 18.0,
        "rental_yield": 5.8,
        "description": "Madinaty is TMG's flagship mega-development east of Cairo — a self-contained city with golf courses, malls, and 600,000+ residents.",
        "description_ar": "مدينتي مشروع طلعت مصطفى الرائد شرق القاهرة — مدينة متكاملة بملاعب غولف ومولات وأكثر من 600 ألف ساكن.",
    },
    {
        "name": "El Shorouk",
        "name_ar": "الشروق",
        "slug": "el-shorouk",
        "city": "Cairo",
        "avg_price_per_meter": 18000,
        "price_growth_ytd": 15.0,
        "rental_yield": 6.5,
        "description": "El Shorouk City is an affordable satellite city northeast of Cairo with universities, malls, and good connectivity to the Ring Road.",
        "description_ar": "مدينة الشروق مدينة فرعية بأسعار معقولة شمال شرق القاهرة بها جامعات ومولات واتصال جيد بالطريق الدائري.",
    },
    {
        "name": "North Coast (Sahel)",
        "name_ar": "الساحل الشمالي",
        "slug": "north-coast",
        "city": "Matrouh",
        "avg_price_per_meter": 40000,
        "price_growth_ytd": 30.0,
        "rental_yield": 3.2,
        "description": "Egypt's Mediterranean coastline stretching from Alexandria to Marsa Matrouh. The premier summer destination with resorts by all major developers.",
        "description_ar": "ساحل مصر المتوسطي الممتد من الإسكندرية إلى مرسى مطروح. الوجهة الصيفية الأولى بمنتجعات من جميع كبار المطورين.",
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        for area_data in AREAS:
            existing = await session.execute(
                select(Area).where(Area.slug == area_data["slug"])
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭️  {area_data['name']} already exists, skipping")
                continue

            area = Area(**area_data)
            session.add(area)
            print(f"  ✅ Added {area_data['name']}")

        await session.commit()
        print(f"\n📍 Seeded {len(AREAS)} areas")


if __name__ == "__main__":
    asyncio.run(seed())
