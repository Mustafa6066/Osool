"""
Seed Egyptian Real Estate Developers
-------------------------------------
Populates the developers table with 14 major Egyptian developers
and their performance scores.

Usage:
    cd backend
    python -m scripts.seed_developers
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models import Developer
from sqlalchemy import select


DEVELOPERS = [
    {
        "name": "Emaar Misr",
        "name_ar": "إعمار مصر",
        "slug": "emaar-misr",
        "founded_year": 2005,
        "total_projects": 8,
        "description": "A subsidiary of Emaar Properties (Dubai), Emaar Misr is one of Egypt's most prestigious developers. Known for Marassi on the North Coast and Uptown Cairo.",
        "description_ar": "فرع من إعمار العقارية (دبي)، إعمار مصر من أرقى المطورين في مصر. معروفة بمشروع مراسي على الساحل الشمالي وأبتاون كايرو.",
        "avg_delivery_score": 88,
        "avg_finish_quality": 92,
        "avg_resale_retention": 95,
        "payment_flexibility": 75,
        "overall_score": 90,
    },
    {
        "name": "Sodic",
        "name_ar": "سوديك",
        "slug": "sodic",
        "founded_year": 1996,
        "total_projects": 12,
        "description": "SODIC is a leading property developer in Egypt focused on large, mixed-use developments. Known for Sodic East, Sodic West, The Estates, and VYE.",
        "description_ar": "سوديك من الشركات الرائدة في التطوير العقاري بمصر، متخصصة في المشاريع متعددة الاستخدامات. معروفة بسوديك إيست وسوديك ويست.",
        "avg_delivery_score": 82,
        "avg_finish_quality": 85,
        "avg_resale_retention": 88,
        "payment_flexibility": 80,
        "overall_score": 84,
    },
    {
        "name": "Orascom Development",
        "name_ar": "أوراسكوم للتنمية",
        "slug": "orascom-development",
        "founded_year": 1989,
        "total_projects": 10,
        "description": "Orascom Development is known for building entire resort towns including El Gouna on the Red Sea, Taba Heights, and O West in 6th of October City.",
        "description_ar": "أوراسكوم للتنمية معروفة ببناء مدن سياحية كاملة مثل الجونة على البحر الأحمر وتابا هايتس وأو ويست في أكتوبر.",
        "avg_delivery_score": 85,
        "avg_finish_quality": 88,
        "avg_resale_retention": 92,
        "payment_flexibility": 70,
        "overall_score": 86,
    },
    {
        "name": "Palm Hills",
        "name_ar": "بالم هيلز",
        "slug": "palm-hills",
        "founded_year": 2005,
        "total_projects": 14,
        "description": "Palm Hills Developments is one of Egypt's largest listed real estate developers with projects spanning Cairo, Alexandria, and the North Coast.",
        "description_ar": "بالم هيلز من أكبر شركات التطوير العقاري المدرجة في مصر بمشاريع في القاهرة والإسكندرية والساحل الشمالي.",
        "avg_delivery_score": 78,
        "avg_finish_quality": 80,
        "avg_resale_retention": 82,
        "payment_flexibility": 85,
        "overall_score": 81,
    },
    {
        "name": "Mountain View",
        "name_ar": "ماونتن فيو",
        "slug": "mountain-view",
        "founded_year": 2005,
        "total_projects": 11,
        "description": "Mountain View is known for its lifestyle-oriented communities. Flagship projects include Mountain View iCity, Chillout Park, and Ras El Hikma resort.",
        "description_ar": "ماونتن فيو معروفة بمجتمعاتها العصرية. تشمل مشاريعها ماونتن فيو آي سيتي وتشيل أوت بارك ورأس الحكمة.",
        "avg_delivery_score": 80,
        "avg_finish_quality": 86,
        "avg_resale_retention": 85,
        "payment_flexibility": 82,
        "overall_score": 83,
    },
    {
        "name": "TMG (Talaat Moustafa Group)",
        "name_ar": "مجموعة طلعت مصطفى",
        "slug": "tmg",
        "founded_year": 1972,
        "total_projects": 18,
        "description": "TMG is Egypt's largest community developer, creator of Madinaty and Al Rehab. Known for massive, self-contained cities with full infrastructure.",
        "description_ar": "مجموعة طلعت مصطفى هي أكبر مطور مجتمعات عمرانية في مصر. مؤسس مدينتي والرحاب.",
        "avg_delivery_score": 90,
        "avg_finish_quality": 78,
        "avg_resale_retention": 90,
        "payment_flexibility": 75,
        "overall_score": 85,
    },
    {
        "name": "Hyde Park",
        "name_ar": "هايد بارك",
        "slug": "hyde-park",
        "founded_year": 2007,
        "total_projects": 4,
        "description": "Hyde Park Developments is known for its flagship project in New Cairo, offering residential, commercial, and recreational facilities.",
        "description_ar": "هايد بارك للتطوير معروفة بمشروعها الرئيسي في القاهرة الجديدة الذي يشمل وحدات سكنية وتجارية وترفيهية.",
        "avg_delivery_score": 76,
        "avg_finish_quality": 82,
        "avg_resale_retention": 78,
        "payment_flexibility": 80,
        "overall_score": 79,
    },
    {
        "name": "City Edge",
        "name_ar": "سيتي إيدج",
        "slug": "city-edge",
        "founded_year": 2017,
        "total_projects": 6,
        "description": "City Edge Developments is a joint venture between NUCA and the Housing Bank. Known for projects in the New Administrative Capital and New Alamein.",
        "description_ar": "سيتي إيدج شراكة بين هيئة المجتمعات العمرانية والبنك العقاري. معروفة بمشاريعها في العاصمة الإدارية والعلمين الجديدة.",
        "avg_delivery_score": 72,
        "avg_finish_quality": 80,
        "avg_resale_retention": 75,
        "payment_flexibility": 78,
        "overall_score": 76,
    },
    {
        "name": "Tatweer Misr",
        "name_ar": "تطوير مصر",
        "slug": "tatweer-misr",
        "founded_year": 2014,
        "total_projects": 5,
        "description": "Tatweer Misr is a fast-growing developer known for IL Bosco in the New Capital, Fouka Bay on the North Coast, and Bloomfields.",
        "description_ar": "تطوير مصر شركة سريعة النمو معروفة بمشروع إل بوسكو في العاصمة وفوكا باي على الساحل الشمالي وبلوم فيلدز.",
        "avg_delivery_score": 78,
        "avg_finish_quality": 84,
        "avg_resale_retention": 80,
        "payment_flexibility": 82,
        "overall_score": 81,
    },
    {
        "name": "La Vista",
        "name_ar": "لافيستا",
        "slug": "la-vista",
        "founded_year": 1991,
        "total_projects": 9,
        "description": "La Vista is a pioneer in Egyptian resort development on the North Coast, Red Sea, and Ain Sokhna. Known for El Patio and La Vista Bay.",
        "description_ar": "لافيستا رائدة في تطوير المنتجعات في مصر على الساحل الشمالي والبحر الأحمر وعين السخنة.",
        "avg_delivery_score": 80,
        "avg_finish_quality": 83,
        "avg_resale_retention": 84,
        "payment_flexibility": 76,
        "overall_score": 81,
    },
    {
        "name": "Ora Developers",
        "name_ar": "أورا ديفيلوبرز",
        "slug": "ora-developers",
        "founded_year": 2018,
        "total_projects": 4,
        "description": "Ora Developers, led by Naguib Sawiris, is known for premium projects including ZED Sheikh Zayed, ZED East, and Silversands North Coast.",
        "description_ar": "أورا ديفيلوبرز بقيادة نجيب ساويرس معروفة بمشاريع فاخرة مثل زيد الشيخ زايد وزيد إيست وسيلفرساندز.",
        "avg_delivery_score": 74,
        "avg_finish_quality": 88,
        "avg_resale_retention": 82,
        "payment_flexibility": 78,
        "overall_score": 80,
    },
    {
        "name": "Marakez",
        "name_ar": "مراكز",
        "slug": "marakez",
        "founded_year": 2005,
        "total_projects": 3,
        "description": "Marakez is a diversified developer known for Mall of Arabia and Aeon residential compound in 6th of October City.",
        "description_ar": "مراكز شركة تطوير متنوعة معروفة بمول العرب ومشروع إيون السكني في مدينة السادس من أكتوبر.",
        "avg_delivery_score": 82,
        "avg_finish_quality": 80,
        "avg_resale_retention": 78,
        "payment_flexibility": 72,
        "overall_score": 78,
    },
    {
        "name": "Al Ahly Sabbour",
        "name_ar": "الأهلي صبور",
        "slug": "al-ahly-sabbour",
        "founded_year": 1994,
        "total_projects": 15,
        "description": "Al Ahly Sabbour (now Sabbour) is one of Egypt's oldest and most prolific developers with projects across New Cairo, Sheikh Zayed, and the North Coast.",
        "description_ar": "الأهلي صبور من أقدم وأغزر المطورين في مصر بمشاريع في القاهرة الجديدة والشيخ زايد والساحل الشمالي.",
        "avg_delivery_score": 84,
        "avg_finish_quality": 79,
        "avg_resale_retention": 83,
        "payment_flexibility": 80,
        "overall_score": 82,
    },
    {
        "name": "Hassan Allam Properties",
        "name_ar": "حسن علام العقارية",
        "slug": "hassan-allam-properties",
        "founded_year": 2015,
        "total_projects": 5,
        "description": "Hassan Allam Properties, backed by the Hassan Allam Group, is known for Swan Lake, HAPTown, and Park View in the New Administrative Capital.",
        "description_ar": "حسن علام العقارية جزء من مجموعة حسن علام. معروفة بسوان ليك وهاب تاون وبارك فيو في العاصمة الإدارية.",
        "avg_delivery_score": 86,
        "avg_finish_quality": 85,
        "avg_resale_retention": 84,
        "payment_flexibility": 77,
        "overall_score": 83,
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        for dev_data in DEVELOPERS:
            existing = await session.execute(
                select(Developer).where(Developer.slug == dev_data["slug"])
            )
            if existing.scalar_one_or_none():
                print(f"  ⏭️  {dev_data['name']} already exists, skipping")
                continue

            dev = Developer(**dev_data)
            session.add(dev)
            print(f"  ✅ Added {dev_data['name']}")

        await session.commit()
        print(f"\n🏗️  Seeded {len(DEVELOPERS)} developers")


if __name__ == "__main__":
    asyncio.run(seed())
