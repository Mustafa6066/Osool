from celery import shared_task
from app.database import SessionLocal
from app.models import Property
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)

@shared_task(name="scrape_nawy")
def scrape_nawy_task():
    """Regularly scrapes Nawy website for new listings."""
    from app.services.nawy_api_scraper import nawy_api_scraper
    
    properties = nawy_api_scraper.scrape_new_cairo()
    if not properties:
        logger.warning("No properties scraped from Nawy.")
        return 0
        
    _upsert_properties(properties)
    return len(properties)

@shared_task(name="scrape_aqarmap")
def scrape_aqarmap_task():
    """Regularly scrapes Aqarmap website for new listings."""
    from app.services.aqarmap_stealth_scraper import aqarmap_scraper
    import asyncio

    # Run the async scraper in the Celery worker
    loop = asyncio.get_event_loop()
    properties = loop.run_until_complete(aqarmap_scraper.scrape_new_cairo(pages=5))

    if not properties:
        logger.warning("No properties scraped from Aqarmap.")
        return 0

    _upsert_properties(properties)
    return len(properties)

def _upsert_properties(properties_list):
    """
    Upserts properties into the database.
    Since we are using SQLite for dev, we'll do a simple loop.
    For PostgreSQL, ON CONFLICT DO UPDATE is better.
    """
    db = SessionLocal()
    try:
        count = 0
        for prop_data in properties_list:
            # Try to find existing by URL or Nawy Reference
            url = prop_data.get("url") or prop_data.get("nawy_url")
            nawy_ref = prop_data.get("nawy_reference")

            existing = None
            if url:
                existing = db.query(Property).filter(Property.url == url).first()
            if not existing and nawy_ref:
                 existing = db.query(Property).filter(Property.nawy_reference == nawy_ref).first()

            if existing:
                # Update price and availability
                existing.price = prop_data["price"]
                existing.is_available = True
            else:
                # Insert new
                new_prop = Property(**prop_data)
                db.add(new_prop)

            count += 1

        db.commit()
        logger.info(f"Successfully upserted {count} properties.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upsert properties: {e}")
    finally:
        db.close()
