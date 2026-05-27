"""
Nawy.com spider.

Phase 1 — Compound discovery via Nawy's Next.js data (no Scrapling, pure httpx).
Phase 2 — Per-compound page scrape via Scrapling StealthyFetcher; parse __NEXT_DATA__.
Phase 3 — Nawy Now listing pages (paginated; flat-unit payload).

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
    from scrapling.fetchers import StealthyFetcher
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

    async def crawl_nawy_now(self, max_pages: int = MAX_PAGES_PER_AREA, dry_run: bool = False) -> SpiderResult:
        """
        Scrape /nawy-now paginated feed. Each page's __NEXT_DATA__ contains a
        flat list of *unit-level* records (not compound-level) with everything
        we need: paymentPlan, readyBy, compound, area, developer, finishing.

        Stops early when:
          - page returns 0 results
          - we hit the declared `total`
          - we exhaust `max_pages`
        """
        result = SpiderResult()
        seen_ids: set[int] = set()
        for page_no in range(1, max_pages + 1):
            url = f"{NAWY_BASE}/nawy-now?page={page_no}"
            html = await self._fetch_no_stealth(url)
            if not html:
                result.pages_failed += 1
                break

            units, total = self._extract_nawy_now_page(html, url)
            if not units:
                logger.info("[nawy] nawy-now page %d empty — stopping pagination", page_no)
                break

            fresh = [u for u in units if u.get("id") not in seen_ids]
            for u in fresh:
                if u.get("id") is not None:
                    seen_ids.add(u["id"])

            result.raw_properties.extend(fresh)
            result.pages_fetched += 1
            logger.info(
                "[nawy] nawy-now page %d: +%d units (cumulative %d / total %d)",
                page_no, len(fresh), len(seen_ids), total or -1,
            )

            if total and len(seen_ids) >= total:
                logger.info("[nawy] nawy-now reached declared total %d — done", total)
                break

            await asyncio.sleep(REQUEST_DELAY_SECONDS)
        return result

    # ── Internals ─────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def _discover_compounds(self, area_slug: str) -> list[str]:
        """
        Hits Nawy's compound listing page and pulls slugs from __NEXT_DATA__.

        Path supported (2026-05 onwards):
          props.pageProps.loadedSearchResultsSSR.results[*].slug  (current)
        Legacy paths kept as fallbacks:
          props.pageProps.compounds[*].slug
          props.pageProps.searchResults.compounds[*].slug
        """
        slugs: list[str] = []
        seen: set[str] = set()

        for page_no in range(1, MAX_PAGES_PER_AREA + 1):
            url = f"{NAWY_BASE}/search?area={area_slug}&page={page_no}"
            try:
                resp = await self._http.get(url)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("[nawy] search fetch failed page %d for %s: %s", page_no, area_slug, exc)
                break
            envelope = extract_compound_page(resp.text, url)
            page_props = (envelope.get("props") or {}).get("pageProps") or {}

            page_slugs = self._slugs_from_page_props(page_props)
            new_slugs = [s for s in page_slugs if s not in seen]
            for s in new_slugs:
                seen.add(s)
                slugs.append(s)

            ssr = page_props.get("loadedSearchResultsSSR") or {}
            total = ssr.get("total") if isinstance(ssr, dict) else None
            page_size = ssr.get("pageSize") if isinstance(ssr, dict) else None

            if not new_slugs:
                break
            if total and page_size and page_no * page_size >= total:
                break

            await asyncio.sleep(REQUEST_DELAY_SECONDS)

        return slugs

    @staticmethod
    def _slugs_from_page_props(page_props: dict) -> list[str]:
        slugs: list[str] = []

        # Current (2026-05) path: pageProps.loadedSearchResultsSSR.results[*].slug
        ssr = page_props.get("loadedSearchResultsSSR") or {}
        if isinstance(ssr, dict):
            for entry in ssr.get("results") or []:
                if isinstance(entry, dict) and entry.get("slug"):
                    slugs.append(entry["slug"])

        # Legacy: pageProps.compounds[*].slug
        for comp in page_props.get("compounds") or []:
            if isinstance(comp, dict) and comp.get("slug"):
                slug = comp["slug"]
                if slug not in slugs:
                    slugs.append(slug)

        # Legacy: pageProps.searchResults.compounds[*].slug
        search = page_props.get("searchResults") or {}
        if isinstance(search, dict):
            for comp in search.get("compounds") or []:
                if isinstance(comp, dict) and comp.get("slug"):
                    slug = comp["slug"]
                    if slug not in slugs:
                        slugs.append(slug)

        return slugs

    def _extract_nawy_now_page(self, html: str, url: str) -> tuple[list[dict], Optional[int]]:
        """Pull the unit list + declared total from a /nawy-now page's __NEXT_DATA__."""
        envelope = extract_compound_page(html, url)
        page_props = (envelope.get("props") or {}).get("pageProps") or {}
        ssr = page_props.get("loadedSearchResultsSSR") or {}
        if not isinstance(ssr, dict):
            return [], None
        results = ssr.get("results") or []
        total = ssr.get("total") if isinstance(ssr.get("total"), int) else None

        # Tag each unit so the ingestion path knows it's a Nawy Now flat unit
        # (the deterministic normalizer already recognizes saleType="nawy_now"
        # but we add isNawyNow for extra safety against deduplication on title).
        flat: list[dict] = []
        for u in results:
            if not isinstance(u, dict):
                continue
            u.setdefault("saleType", "nawy_now")
            u["isNawyNow"] = True
            u["_source_url"] = url
            flat.append(u)
        return flat, total

    async def _fetch_no_stealth(self, url: str) -> Optional[str]:
        """Plain httpx fetch — used for /nawy-now JSON-bearing pages.

        We skip StealthyFetcher here because:
          (a) Nawy's SSR returns full __NEXT_DATA__ to httpx
          (b) Playwright is significantly slower per page and we paginate up to 35x
        """
        try:
            resp = await self._http.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            logger.error("[nawy] httpx fetch failed for %s: %s", url, exc)
            return None

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
                body = page.body if hasattr(page, "body") else str(page)
                # StealthyFetcher returns bytes — decode for downstream str-pattern regex.
                if isinstance(body, (bytes, bytearray)):
                    body = body.decode("utf-8", errors="replace")
                return body
            except Exception as exc:
                logger.warning("[nawy] StealthyFetcher failed for %s: %s — falling back to httpx", url, exc)

        try:
            resp = await self._http.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception as exc:
            logger.error("[nawy] httpx fetch failed for %s: %s", url, exc)
            return None
