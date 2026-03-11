"""Check DB state and seed developers/areas tables if empty."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select, func
from app.models import Developer, Area, Base


DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

DEVELOPERS = [
    {"name": "Emaar Misr", "name_ar": "إعمار مصر", "slug": "emaar-misr", "founded_year": 2005, "total_projects": 8, "description": "A subsidiary of Emaar Properties (Dubai), Emaar Misr is one of Egypt's most prestigious developers. Known for Marassi on the North Coast and Uptown Cairo.", "description_ar": "فرع من إعمار العقارية (دبي)، إعمار مصر من أرقى المطورين في مصر.", "avg_delivery_score": 88, "avg_finish_quality": 92, "avg_resale_retention": 95, "payment_flexibility": 75, "overall_score": 90},
    {"name": "Sodic", "name_ar": "سوديك", "slug": "sodic", "founded_year": 1996, "total_projects": 12, "description": "SODIC is a leading property developer in Egypt focused on large, mixed-use developments. Known for Sodic East, Sodic West, The Estates, and VYE.", "description_ar": "سوديك من الشركات الرائدة في التطوير العقاري بمصر.", "avg_delivery_score": 82, "avg_finish_quality": 85, "avg_resale_retention": 88, "payment_flexibility": 80, "overall_score": 84},
    {"name": "Orascom Development", "name_ar": "أوراسكوم للتنمية", "slug": "orascom-development", "founded_year": 1989, "total_projects": 10, "description": "Orascom Development is known for building entire resort towns including El Gouna on the Red Sea, Taba Heights, and O West.", "description_ar": "أوراسكوم للتنمية معروفة ببناء مدن سياحية كاملة مثل الجونة على البحر الأحمر.", "avg_delivery_score": 85, "avg_finish_quality": 88, "avg_resale_retention": 92, "payment_flexibility": 70, "overall_score": 86},
    {"name": "Palm Hills", "name_ar": "بالم هيلز", "slug": "palm-hills", "founded_year": 2005, "total_projects": 14, "description": "Palm Hills Developments is one of Egypt's largest listed real estate developers with projects spanning Cairo, Alexandria, and the North Coast.", "description_ar": "بالم هيلز من أكبر شركات التطوير العقاري المدرجة في مصر.", "avg_delivery_score": 78, "avg_finish_quality": 80, "avg_resale_retention": 82, "payment_flexibility": 85, "overall_score": 81},
    {"name": "Mountain View", "name_ar": "ماونتن فيو", "slug": "mountain-view", "founded_year": 2005, "total_projects": 11, "description": "Mountain View is known for its lifestyle-oriented communities. Flagship projects include Mountain View iCity, Chillout Park, and Ras El Hikma resort.", "description_ar": "ماونتن فيو معروفة بمجتمعاتها العصرية.", "avg_delivery_score": 80, "avg_finish_quality": 86, "avg_resale_retention": 85, "payment_flexibility": 82, "overall_score": 83},
    {"name": "TMG", "name_ar": "مجموعة طلعت مصطفى", "slug": "tmg", "founded_year": 1972, "total_projects": 18, "description": "TMG is Egypt's largest community developer, creator of Madinaty and Al Rehab. Known for massive, self-contained cities with full infrastructure.", "description_ar": "مجموعة طلعت مصطفى هي أكبر مطور مجتمعات عمرانية في مصر.", "avg_delivery_score": 90, "avg_finish_quality": 78, "avg_resale_retention": 90, "payment_flexibility": 75, "overall_score": 85},
    {"name": "Hyde Park", "name_ar": "هايد بارك", "slug": "hyde-park", "founded_year": 2007, "total_projects": 4, "description": "Hyde Park Developments is known for its flagship project in New Cairo, offering residential, commercial, and recreational facilities.", "description_ar": "هايد بارك للتطوير معروفة بمشروعها الرئيسي في القاهرة الجديدة.", "avg_delivery_score": 76, "avg_finish_quality": 82, "avg_resale_retention": 78, "payment_flexibility": 80, "overall_score": 79},
    {"name": "City Edge", "name_ar": "سيتي إيدج", "slug": "city-edge", "founded_year": 2017, "total_projects": 6, "description": "City Edge Developments is a joint venture between NUCA and the Housing Bank. Known for projects in the New Administrative Capital and New Alamein.", "description_ar": "سيتي إيدج شراكة بين هيئة المجتمعات العمرانية والبنك العقاري.", "avg_delivery_score": 72, "avg_finish_quality": 80, "avg_resale_retention": 75, "payment_flexibility": 78, "overall_score": 76},
    {"name": "Tatweer Misr", "name_ar": "تطوير مصر", "slug": "tatweer-misr", "founded_year": 2014, "total_projects": 5, "description": "Tatweer Misr is a fast-growing developer known for IL Bosco in the New Capital, Fouka Bay on the North Coast, and Bloomfields.", "description_ar": "تطوير مصر شركة سريعة النمو معروفة بمشروع إل بوسكو في العاصمة.", "avg_delivery_score": 78, "avg_finish_quality": 84, "avg_resale_retention": 80, "payment_flexibility": 82, "overall_score": 81},
    {"name": "La Vista", "name_ar": "لافيستا", "slug": "la-vista", "founded_year": 1991, "total_projects": 8, "description": "La Vista is an Egyptian developer with a strong presence on the Red Sea and North Coast, known for La Vista Ray, Patio 7, and El Patio Prime.", "description_ar": "لافيستا مطور مصري بحضور قوي على البحر الأحمر والساحل الشمالي.", "avg_delivery_score": 84, "avg_finish_quality": 80, "avg_resale_retention": 82, "payment_flexibility": 78, "overall_score": 81},
    {"name": "Ora Developers", "name_ar": "أورا للتطوير", "slug": "ora-developers", "founded_year": 2015, "total_projects": 4, "description": "Ora Developers, founded by billionaire Naguib Sawiris, is known for Solana in New Cairo and Zed in Sheikh Zayed.", "description_ar": "أورا للتطوير، تأسست على يد المليardير نجيب ساويرس، معروفة بمشروع سولانا.", "avg_delivery_score": 80, "avg_finish_quality": 88, "avg_resale_retention": 85, "payment_flexibility": 72, "overall_score": 82},
    {"name": "Hassan Allam Properties", "name_ar": "حسن علام للعقارات", "slug": "hassan-allam", "founded_year": 2007, "total_projects": 7, "description": "Hassan Allam Properties is a leading developer in Egypt known for upscale integrated communities like Bloom Fields, Haptown, and Park Central.", "description_ar": "حسن علام للعقارات مطور رائد في مصر معروف بالمجتمعات المتكاملة الراقية.", "avg_delivery_score": 82, "avg_finish_quality": 86, "avg_resale_retention": 83, "payment_flexibility": 80, "overall_score": 83},
    {"name": "Marakez", "name_ar": "مراكز", "slug": "marakez", "founded_year": 2012, "total_projects": 3, "description": "Marakez (Fawaz Alhokair Group) develops integrated lifestyle destinations. Known for Mall of Arabia and Crescent Walk.", "description_ar": "مراكز (مجموعة فواز الحكير) تطوير وجهات حياة متكاملة.", "avg_delivery_score": 75, "avg_finish_quality": 82, "avg_resale_retention": 76, "payment_flexibility": 76, "overall_score": 77},
    {"name": "Wadi Degla", "name_ar": "وادي دجلة", "slug": "wadi-degla", "founded_year": 2002, "total_projects": 9, "description": "Wadi Degla Developments is a mid-market Egyptian developer with compounds in New Cairo, Ain Sokhna, and the North Coast.", "description_ar": "وادي دجلة مطور عقاري مصري للسوق المتوسط مع كمبوندات في القاهرة الجديدة والعين السخنة.", "avg_delivery_score": 74, "avg_finish_quality": 76, "avg_resale_retention": 74, "payment_flexibility": 82, "overall_score": 76},
]

AREAS = [
    {"name": "Sheikh Zayed", "name_ar": "الشيخ زايد", "slug": "sheikh-zayed", "city": "Giza", "avg_price_per_meter": 35000, "price_growth_ytd": 22.5, "rental_yield": 5.2, "liquidity_score": 80, "demand_score": 82, "description": "Sheikh Zayed City is a premium satellite city west of Cairo, known for upscale compounds and proximity to the Ring Road.", "description_ar": "مدينة الشيخ زايد مدينة فرعية راقية غرب القاهرة."},
    {"name": "6th of October City", "name_ar": "مدينة السادس من أكتوبر", "slug": "6th-october", "city": "Giza", "avg_price_per_meter": 22000, "price_growth_ytd": 18.0, "rental_yield": 6.0, "liquidity_score": 72, "demand_score": 75, "description": "One of Egypt's largest new cities with a diverse mix of housing, education, and industry. Home to Mall of Arabia and major universities.", "description_ar": "واحدة من أكبر المدن الجديدة في مصر."},
    {"name": "New Capital – R7", "name_ar": "العاصمة الإدارية – R7", "slug": "new-capital-r7", "city": "New Capital", "avg_price_per_meter": 32000, "price_growth_ytd": 32.0, "rental_yield": 4.8, "liquidity_score": 68, "demand_score": 85, "description": "R7 is the most in-demand residential district in the New Capital, home to IL Bosco, The City of Odyssia, and several embassy sectors.", "description_ar": "R7 أكثر الأحياء طلباً في العاصمة الإدارية."},
    {"name": "New Capital – R5", "name_ar": "العاصمة الإدارية – R5", "slug": "new-capital-r5", "city": "New Capital", "avg_price_per_meter": 28000, "price_growth_ytd": 30.0, "rental_yield": 4.5, "liquidity_score": 62, "demand_score": 78, "description": "R5 is a prime residential district in Egypt's New Administrative Capital, featuring mid-to-high-end developments and government housing.", "description_ar": "R5 حي سكني رئيسي في العاصمة الإدارية."},
    {"name": "Ras El Hikma", "name_ar": "رأس الحكمة", "slug": "ras-el-hikma", "city": "Matrouh", "avg_price_per_meter": 55000, "price_growth_ytd": 40.0, "rental_yield": 3.0, "liquidity_score": 60, "demand_score": 90, "description": "Ras El Hikma is Egypt's hottest investment zone following the $35B UAE deal. Crystal-clear waters and mega-resort developments.", "description_ar": "رأس الحكمة أكثر مناطق الاستثمار سخونة بعد صفقة الإمارات."},
    {"name": "North Coast (Sahel)", "name_ar": "الساحل الشمالي", "slug": "north-coast", "city": "Matrouh", "avg_price_per_meter": 40000, "price_growth_ytd": 30.0, "rental_yield": 3.2, "liquidity_score": 65, "demand_score": 88, "description": "Egypt's Mediterranean coastline stretching from Alexandria to Marsa Matrouh. The premier summer destination with resorts by all major developers.", "description_ar": "ساحل البحر المتوسط المصري الممتد من الإسكندرية إلى مرسى مطروح."},
    {"name": "New Alamein", "name_ar": "العلمين الجديدة", "slug": "new-alamein", "city": "Matrouh", "avg_price_per_meter": 45000, "price_growth_ytd": 35.0, "rental_yield": 3.5, "liquidity_score": 58, "demand_score": 82, "description": "New Alamein is a massive government-backed coastal city on the Mediterranean, featuring towers, hotels, and a year-round residential vision.", "description_ar": "العلمين الجديدة مدينة ساحلية ضخمة على البحر المتوسط مدعومة حكومياً."},
    {"name": "Ain Sokhna", "name_ar": "العين السخنة", "slug": "ain-sokhna", "city": "Suez", "avg_price_per_meter": 30000, "price_growth_ytd": 20.0, "rental_yield": 5.5, "liquidity_score": 70, "demand_score": 78, "description": "Ain Sokhna is Cairo's closest Red Sea getaway, about 90 minutes from the capital. Popular for weekend homes and resort chalets.", "description_ar": "العين السخنة أقرب وجهة بحر أحمر للقاهرة على بعد 90 دقيقة."},
    {"name": "Mostakbal City", "name_ar": "مدينة المستقبل", "slug": "mostakbal-city", "city": "Cairo", "avg_price_per_meter": 26000, "price_growth_ytd": 25.0, "rental_yield": 5.0, "liquidity_score": 65, "demand_score": 80, "description": "Mostakbal City is an emerging smart city east of Cairo, adjacent to the New Capital. Known for Bloomfields, HAPTOWN, and Sarai.", "description_ar": "مدينة المستقبل مدينة ذكية ناشئة شرق القاهرة مجاورة للعاصمة الإدارية."},
    {"name": "Madinaty", "name_ar": "مدينتي", "slug": "madinaty", "city": "Cairo", "avg_price_per_meter": 32000, "price_growth_ytd": 18.0, "rental_yield": 5.8, "liquidity_score": 75, "demand_score": 80, "description": "Madinaty is TMG's flagship mega-development east of Cairo — a self-contained city with golf courses, malls, and 600,000+ residents.", "description_ar": "مدينتي مشروع طلعت مصطفى الرائد شرق القاهرة."},
    {"name": "New Cairo (5th Settlement)", "name_ar": "القاهرة الجديدة (التجمع الخامس)", "slug": "new-cairo", "city": "Cairo", "avg_price_per_meter": 38000, "price_growth_ytd": 22.0, "rental_yield": 5.0, "liquidity_score": 85, "demand_score": 90, "description": "New Cairo's 5th Settlement is the most established upscale district east of Cairo, home to AUC, the city's top schools, and dozens of compounds.", "description_ar": "التجمع الخامس في القاهرة الجديدة أكثر الأحياء الراقية رسوخاً شرق القاهرة."},
    {"name": "El Shorouk", "name_ar": "الشروق", "slug": "el-shorouk", "city": "Cairo", "avg_price_per_meter": 18000, "price_growth_ytd": 15.0, "rental_yield": 6.5, "liquidity_score": 68, "demand_score": 70, "description": "El Shorouk City is an affordable satellite city northeast of Cairo with universities, malls, and good connectivity to the Ring Road.", "description_ar": "مدينة الشروق مدينة فرعية بأسعار معقولة شمال شرق القاهرة."},
]


CREATE_DEVELOPERS_SQL = """
CREATE TABLE IF NOT EXISTS developers (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    name_ar VARCHAR,
    slug VARCHAR NOT NULL UNIQUE,
    logo VARCHAR,
    description TEXT,
    description_ar TEXT,
    founded_year INTEGER,
    total_projects INTEGER,
    avg_delivery_score FLOAT,
    avg_finish_quality FLOAT,
    avg_resale_retention FLOAT,
    payment_flexibility FLOAT,
    overall_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
"""

CREATE_AREAS_SQL = """
CREATE TABLE IF NOT EXISTS areas (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    name_ar VARCHAR,
    slug VARCHAR NOT NULL UNIQUE,
    city VARCHAR,
    description TEXT,
    description_ar TEXT,
    avg_price_per_meter FLOAT,
    price_growth_ytd FLOAT,
    predicted_roi_5y FLOAT,
    rental_yield FLOAT,
    liquidity_score FLOAT,
    demand_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
"""


async def main():
    # Create tables using raw SQL (avoids pgvector dependency)
    async with engine.begin() as conn:
        await conn.execute(text(CREATE_DEVELOPERS_SQL))
        await conn.execute(text(CREATE_AREAS_SQL))
        print("Tables ensured.")

    async with AsyncSessionLocal() as session:
        # Check developers count
        dev_count = await session.scalar(select(func.count(Developer.id)))
        if dev_count > 0:
            print(f"Developers already seeded ({dev_count} records). Skipping.")
        else:
            for d in DEVELOPERS:
                session.add(Developer(**d))
            await session.commit()
            print(f"✓ Seeded {len(DEVELOPERS)} developers")

        # Check areas count
        area_count = await session.scalar(select(func.count(Area.id)))
        if area_count > 0:
            print(f"Areas already seeded ({area_count} records). Skipping.")
        else:
            for a in AREAS:
                session.add(Area(**a))
            await session.commit()
            print(f"✓ Seeded {len(AREAS)} areas")

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
