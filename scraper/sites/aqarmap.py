"""
Aqarmap.com.eg spider.

Phase 1 — Walk paginated listing index for an area slug (pure httpx).
Phase 2 — For each listing-detail URL, fetch with Scrapling StealthyFetcher
          and extract attributes.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from extractors.aqarmap_selectors import extract_detail_page, extract_listing_links
from settings import MAX_PAGES_PER_AREA, REQUEST_DELAY_SECONDS
from sites.base import SiteSpider, SpiderResult

logger = logging.getLogger(__name__)

AQARMAP_BASE = "https://aqarmap.com.eg"

try:
    from scrapling.fetchers import StealthyFetcher
    _STEALTH_OK = True
except ImportError:
    StealthyFetcher = None  # type: ignore
    _STEALTH_OK = False

# Aqarmap slug aliases for our canonical area names.
AREA_PATH_MAP: dict[str, str] = {
    "new-cairo": "new-cairo-city",
    "6th-october": "6-october-city",
    "new-administrative-capital": "new-administrative-capital",
    "north-coast": "north-coast",
    "sheikh-zayed": "sheikh-zayed-city",
    "new-zayed": "new-zayed",
    "ain-sokhna": "al-ain-al-sukhna",
}


class AqarmapSpider(SiteSpider):
    name = "aqarmap"

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; OsoolScraper/2.0)"},
            timeout=30.0,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def crawl_area(self, area_slug: str, dry_run: bool = False) -> SpiderResult:
        result = SpiderResult()
        path = AREA_PATH_MAP.get(area_slug, area_slug)

        detail_urls: list[str] = []
        for page_no in range(1, MAX_PAGES_PER_AREA + 1):
            index_url = f"{AQARMAP_BASE}/en/for-sale/property/egypt/cairo/{path}/page-{page_no}/"
            html = await self._fetch_html(index_url)
            if not html:
                break
            page_links = extract_listing_links(html, index_url)
            if not page_links:
                logger.info("[aqarmap] %s page %d empty — stopping pagination", path, page_no)
                break
            detail_urls.extend(page_links)
            await asyncio.sleep(REQUEST_DELAY_SECONDS)

        logger.info("[aqarmap] %s: %d detail URLs discovered", path, len(detail_urls))

        # Dedup
        detail_urls = list(dict.fromkeys(detail_urls))

        for url in detail_urls:
            detail = await self._scrape_detail(url)
            if detail:
                result.raw_properties.append(detail)
                result.pages_fetched += 1
            else:
                result.pages_failed += 1
            await asyncio.sleep(REQUEST_DELAY_SECONDS)
        return result

    async def crawl_compound(self, compound_slug: str, dry_run: bool = False) -> SpiderResult:
        """Aqarmap doesn't index by compound — treat the slug as an area filter."""
        return await self.crawl_area(compound_slug, dry_run=dry_run)

    # ── Internals ─────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _fetch_html(self, url: str) -> Optional[str]:
        if _STEALTH_OK:
            try:
                page = await asyncio.to_thread(
                    StealthyFetcher.fetch,
                    url,
                    headless=True,
                    network_idle=True,
                )
                return page.body if hasattr(page, "body") else str(page)
            except Exception as exc:
                logger.warning("[aqarmap] StealthyFetcher failed for %s: %s — fallback httpx", url, exc)

        try:
            resp = await self._http.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            logger.error("[aqarmap] httpx fetch failed for %s: %s", url, exc)
            return None

    async def _scrape_detail(self, url: str) -> Optional[dict]:
        html = await self._fetch_html(url)
        if not html:
            return None
        try:
            return extract_detail_page(html, url)
        except Exception as exc:
            logger.warning("[aqarmap] detail extract failed for %s: %s", url, exc)
            return None
