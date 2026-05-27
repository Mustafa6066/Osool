"""
Aqarmap.com.eg spider.

Phase 1 — Walk paginated listing index for an area slug.
          URL pattern (verified 2026-05-27):
              /en/for-sale/property-type/cairo/<area>/?page=<n>
          Older `/property/egypt/cairo/<area>-city/page-N/` form is dead.
Phase 2 — For each listing-detail URL, fetch with Scrapling StealthyFetcher
          (Aqarmap blocks plain httpx with an empty body) and extract via
          JSON-LD RealEstateListing schema.
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

# Aqarmap slug aliases for our canonical area names — Aqarmap dropped the
# `-city` suffix in 2026 and reorganised some paths.
AREA_PATH_MAP: dict[str, str] = {
    "new-cairo": "new-cairo",
    "6th-october": "6-october",
    "new-administrative-capital": "new-capital-city",
    "north-coast": "north-coast",
    "sheikh-zayed": "el-sheikh-zayed-city",
    "new-zayed": "el-sheikh-zayed-city",  # New Zayed indexed under Sheikh Zayed
    "ain-sokhna": "al-ain-al-sukhna",
}


class AqarmapSpider(SiteSpider):
    name = "aqarmap"

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            },
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
            # 2026 URL pattern — query-string pagination
            if page_no == 1:
                index_url = f"{AQARMAP_BASE}/en/for-sale/property-type/cairo/{path}/"
            else:
                index_url = f"{AQARMAP_BASE}/en/for-sale/property-type/cairo/{path}/?page={page_no}"

            html = await self._fetch_html(index_url)
            if not html:
                break
            page_links = extract_listing_links(html, index_url)
            if not page_links:
                logger.info("[aqarmap] %s page %d empty — stopping pagination", path, page_no)
                break
            detail_urls.extend(page_links)
            await asyncio.sleep(REQUEST_DELAY_SECONDS)

        # Dedup
        detail_urls = list(dict.fromkeys(detail_urls))
        logger.info("[aqarmap] %s: %d detail URLs discovered", path, len(detail_urls))

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
        """
        Aqarmap blocks raw httpx with an empty body. Always prefer Scrapling's
        StealthyFetcher (Playwright + anti-bot). Falls back to httpx only when
        Scrapling isn't importable (dev machine), which will likely fail loudly.
        """
        if _STEALTH_OK:
            try:
                page = await asyncio.to_thread(
                    StealthyFetcher.fetch,
                    url,
                    headless=True,
                    network_idle=True,
                )
                body = page.body if hasattr(page, "body") else str(page)
                # StealthyFetcher returns bytes — decode for downstream str-pattern regex.
                if isinstance(body, (bytes, bytearray)):
                    body = body.decode("utf-8", errors="replace")
                if body and len(body) > 1000:
                    return body
                logger.warning("[aqarmap] StealthyFetcher returned suspiciously short body for %s (%d chars)", url, len(body or ""))
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
