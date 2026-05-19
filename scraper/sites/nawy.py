"""
Nawy.com spider.

Phase 1 — Compound discovery via Nawy's Next.js data API (no Scrapling, pure httpx).
Phase 2 — Per-compound page scrape via Scrapling StealthyFetcher; parse __NEXT_DATA__.
Phase 3 — Nawy Now listing pages (paginated).

Output: raw unit dicts shaped for app.ingestion.deterministic_normalizer.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from extractors.nawy_selectors import extract_compound_page
from settings import MAX_PAGES_PER_AREA, REQUEST_DELAY_SECONDS
from sites.base import SiteSpider, SpiderResult

logger = logging.getLogger(__name__)

NAWY_BASE = "https://www.nawy.com"

try:
    from scrapling import StealthyFetcher
    _STEALTH_OK = True
except ImportError:
    StealthyFetcher = None  # type: ignore
    _STEALTH_OK = False
    logger.warning("Scrapling StealthyFetcher unavailable — nawy spider will use plain httpx")


class NawySpider(SiteSpider):
    name = "nawy"

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; OsoolScraper/2.0)"},
            timeout=30.0,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    # ── Public API ────────────────────────────────────────────────────────

    async def crawl_area(self, area_slug: str, dry_run: bool = False) -> SpiderResult:
        result = SpiderResult()
        compound_slugs = await self._discover_compounds(area_slug)
        logger.info("[nawy] %s: discovered %d compounds", area_slug, len(compound_slugs))

        for slug in compound_slugs[:MAX_PAGES_PER_AREA]:
            sub = await self.crawl_compound(slug, dry_run=dry_run)
            result.raw_properties.extend(sub.raw_properties)
            result.pages_fetched += sub.pages_fetched
            result.pages_failed += sub.pages_failed
            await asyncio.sleep(REQUEST_DELAY_SECONDS)
        return result

    async def crawl_compound(self, compound_slug: str, dry_run: bool = False) -> SpiderResult:
        result = SpiderResult()
        url = f"{NAWY_BASE}/compound/{compound_slug}"
        html = await self._fetch(url)
        if not html:
            result.pages_failed += 1
            return result
        result.pages_fetched += 1

        next_data = extract_compound_page(html, url)
        # Pass the wrapped __NEXT_DATA__ back as a single "unit dict" — the
        # ingestion adapter knows how to feed it to normalize_properties().
        next_data["_nawy_compound_envelope"] = True
        result.raw_properties.append(next_data)
        return result

    # ── Internals ─────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _discover_compounds(self, area_slug: str) -> list[str]:
        """
        Hits Nawy's compound listing page and pulls slugs out of its embedded
        __NEXT_DATA__. No browser needed.
        """
        url = f"{NAWY_BASE}/search?area={area_slug}"
        resp = await self._http.get(url)
        resp.raise_for_status()
        envelope = extract_compound_page(resp.text, url)

        slugs: set[str] = set()

        # Pattern A: pageProps.compounds[*].slug
        page_props = (envelope.get("props") or {}).get("pageProps") or {}
        for comp in page_props.get("compounds") or []:
            slug = (comp or {}).get("slug")
            if slug:
                slugs.add(slug)

        # Pattern B: pageProps.searchResults.compounds[*].slug
        search = page_props.get("searchResults") or {}
        for comp in search.get("compounds") or []:
            slug = (comp or {}).get("slug")
            if slug:
                slugs.add(slug)

        return sorted(slugs)

    async def _fetch(self, url: str) -> Optional[str]:
        """StealthyFetcher when available (Cloudflare-aware), plain httpx otherwise."""
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
                logger.warning("[nawy] StealthyFetcher failed for %s: %s — falling back to httpx", url, exc)

        try:
            resp = await self._http.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            logger.error("[nawy] httpx fetch failed for %s: %s", url, exc)
            return None
