from celery import shared_task
import asyncio
import logging
from uuid import uuid4

from app.ingestion.scraper_schemas import validate_raw_batch
from app.ingestion.deterministic_normalizer import normalize_unit_list
from app.ingestion.repository import upsert_properties

logger = logging.getLogger(__name__)

@shared_task(name="scrape_nawy")
def scrape_nawy_task():
    """Regularly scrapes Nawy website for new listings."""
    from app.services.nawy_api_scraper import nawy_api_scraper
    
    properties = nawy_api_scraper.scrape_new_cairo()
    if not properties:
        logger.warning("No properties scraped from Nawy.")
        return 0

    result = _ingest_properties_zero_token(properties, source="nawy_api_scraper")
    return result.get("total", 0)

@shared_task(name="scrape_aqarmap")
def scrape_aqarmap_task():
    """Regularly scrapes Aqarmap website for new listings."""
    from app.services.aqarmap_stealth_scraper import aqarmap_scraper

    # Run the async scraper in the Celery worker
    properties = asyncio.run(aqarmap_scraper.scrape_new_cairo(pages=5))

    if not properties:
        logger.warning("No properties scraped from Aqarmap.")
        return 0

    result = _ingest_properties_zero_token(properties, source="aqarmap_stealth_scraper")
    return result.get("total", 0)

async def _ingest_properties_async(properties_list, source: str):
    """
    Zero-token ingestion pipeline:
    raw dicts -> validation -> deterministic normalization -> differential upsert.
    """
    valid_rows, report = validate_raw_batch(properties_list)

    if not valid_rows:
        logger.warning("No valid %s properties after validation. %s", source, report.summary)
        return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": report.rejected}

    normalized = normalize_unit_list(valid_rows, source_url=source)
    if not normalized.properties:
        logger.warning("No normalized %s properties after deterministic mapping.", source)
        return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": report.rejected + normalized.skipped_count}

    upsert_result = await upsert_properties(normalized.properties, run_id=str(uuid4()))

    logger.info(
        "%s ingestion complete: valid=%d inserted=%d updated=%d skipped=%d errors=%d",
        source,
        report.valid,
        upsert_result.inserted,
        upsert_result.updated,
        upsert_result.skipped,
        upsert_result.errors,
    )

    return {
        "total": upsert_result.total,
        "inserted": upsert_result.inserted,
        "updated": upsert_result.updated,
        "skipped": upsert_result.skipped,
        "errors": upsert_result.errors,
    }


def _ingest_properties_zero_token(properties_list, source: str):
    """
    Sync wrapper for Celery tasks.
    """
    try:
        return asyncio.run(_ingest_properties_async(properties_list, source=source))
    except Exception as e:
        logger.error("Failed zero-token ingestion for %s: %s", source, e)
        return {"total": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 1}
