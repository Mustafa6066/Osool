import asyncio

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models import Property


async def inspect_ingestion() -> None:
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(select(func.count(Property.id)))
        total_count = count_result.scalar() or 0
        print(f"[*] Total active properties in database: {total_count}")

        anomaly_result = await session.execute(
            select(Property)
            .where(Property.osool_score.is_not(None), Property.osool_score >= 80)
            .order_by(Property.osool_score.desc())
            .limit(1)
        )
        unit = anomaly_result.scalar_one_or_none()

        if unit:
            print(f"[+] Scraper scoring looks healthy. Best anomaly: {unit.compound} - {unit.price} EGP")
        else:
            print("[-] Critical: no properties meet the anomaly threshold (osool_score >= 80). Check scraper selectors and ingestion jobs.")


if __name__ == "__main__":
    asyncio.run(inspect_ingestion())
