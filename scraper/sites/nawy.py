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
from resilience import get_host_breaker, should_block
from settings import MAX_PAGES_PER_AREA, REQUEST_DELAY_SECONDS, SCRAPER_DISABLE_BROWSER
from sites.base import SiteSpider, SpiderResult

logger = logging.getLogger(__name__)

NAWY_BASE = "https://www.nawy.com"
NAWY_LISTING_API = "https://listing-api.nawy.com/v1/search/properties"

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
        import random

        from proxy_pool import mask_proxy
        from settings import SCRAPER_PROXY_URLS, browser_headers

        # S1: present as a real browser and route through a residential proxy when
        # configured. A single Railway IP hitting the listing-api ~1,588× with the
        # UA "OsoolScraper/2.0" is trivially fingerprinted and banned — which kills
        # the primary data source. Pick one proxy per crawl run from the pool.
        self._proxy = random.choice(SCRAPER_PROXY_URLS) if SCRAPER_PROXY_URLS else ""
        http_kwargs: dict = {
            "headers": browser_headers(),
            "timeout": 30.0,
            "follow_redirects": True,
        }
        if self._proxy:
            http_kwargs["proxy"] = self._proxy
            logger.info("[nawy] httpx routed through proxy %s", mask_proxy(self._proxy))
        self._http = httpx.AsyncClient(**http_kwargs)

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
        """Scrape only the Nawy Now (instant-delivery) slice via the listing API."""
        return await self.crawl_via_listing_api(
            max_pages=max_pages, filters={"isNawyNow": "true"}, label="nawy-now",
        )

    async def crawl_all_units(self, max_pages: int = MAX_PAGES_PER_AREA, dry_run: bool = False) -> SpiderResult:
        """
        Walk Nawy's complete unit-level inventory via the listing API:
            https://listing-api.nawy.com/v1/search/properties?page=N&pageSize=12

        No filters → all 19,055+ units across every area and every compound.
        Each unit carries the full schema (paymentPlan, readyBy,
        compound{name,slug}, area{name}, developer{name}, finishing,
        unitArea, bedrooms, bathrooms, saleType). The HTML SSR path
        through /compound/<slug> is much slower (Playwright per compound)
        and yields the same data — we bypass it entirely.
        """
        return await self.crawl_via_listing_api(
            max_pages=max_pages, filters=None, label="nawy-all",
        )

    async def crawl_via_listing_api(
        self,
        max_pages: int,
        filters: Optional[dict] = None,
        label: str = "nawy-api",
    ) -> SpiderResult:
        """
        Generic paginated walk of /v1/search/properties on listing-api.

        Stops early when:
          - the page returns 0 results
          - cumulative seen ids >= declared total
          - we exhaust `max_pages`

        `filters` is a dict of extra query-string params (e.g.
        {"isNawyNow": "true"} for the Nawy Now slice or
        {"areaId": "2"} for a single area).
        """
        result = SpiderResult()
        seen_ids: set[int] = set()

        extra_qs = ""
        if filters:
            extra_qs = "".join(f"&{k}={v}" for k, v in filters.items())

        for page_no in range(1, max_pages + 1):
            url = f"{NAWY_LISTING_API}?page={page_no}&pageSize=12{extra_qs}"
            payload = await self._fetch_json(url)
            if not payload:
                # _fetch_json already exhausted bounded retries, so this is a
                # genuine failure, not a transient blip. Record it as a partial
                # run (pages_failed > 0) so the caller refuses to publish this
                # truncated crawl as the stale-safe anchor. [Phase 0 / S4 → I4]
                result.pages_failed += 1
                logger.warning(
                    "[nawy] %s truncated at page %d after fetch failure — "
                    "marking run partial", label, page_no,
                )
                break

            units, total = self._extract_listing_api_page(payload, url)
            if not units:
                logger.info("[nawy] %s page %d empty — stopping pagination", label, page_no)
                break

            fresh = [u for u in units if u.get("id") not in seen_ids]
            for u in fresh:
                if u.get("id") is not None:
                    seen_ids.add(u["id"])

            result.raw_properties.extend(fresh)
            result.pages_fetched += 1
            logger.info(
                "[nawy] %s page %d: +%d units (cumulative %d / total %d)",
                label, page_no, len(fresh), len(seen_ids), total or -1,
            )

            if total and len(seen_ids) >= total:
                logger.info("[nawy] %s reached declared total %d — done", label, total)
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

    def _extract_listing_api_page(self, payload: dict, url: str) -> tuple[list[dict], Optional[int]]:
        """Pull the unit list + declared total from a listing-api JSON page."""
        if not isinstance(payload, dict):
            return [], None
        results = payload.get("results") or []
        total = payload.get("total") if isinstance(payload.get("total"), int) else None

        # Tag each unit so the ingestion path knows it's a Nawy Now flat unit.
        # The deterministic normalizer reads saleType=="nawy_now" + isNawyNow
        # to flip is_nawy_now=true on the resulting NormalizedProperty.
        flat: list[dict] = []
        for u in results:
            if not isinstance(u, dict):
                continue
            u.setdefault("saleType", "nawy_now")
            u["isNawyNow"] = True
            u["_source_url"] = url
            flat.append(u)
        return flat, total

    async def _fetch_json(self, url: str, *, max_attempts: int = 4) -> Optional[dict]:
        """
        Plain httpx JSON fetch for Nawy's public listing-api XHR endpoint.

        Bounded retry with exponential backoff, honoring Retry-After on 429.
        Only TRANSIENT failures (429, 5xx, transport/connection errors) are
        retried; a permanent 4xx (bad filter / 404) returns None immediately.
        Returns None ONLY after retries are exhausted — the caller (S4) treats
        that as a partial-run signal (pages_failed), never a clean end-of-pages.
        Without this, a single transient 429/reset truncated the whole walk and
        the truncated run could then be published as authoritative. A per-host
        circuit breaker (S20) short-circuits once the listing-api has failed
        repeatedly. The walk already breaks on the first failure, so the breaker's
        main value is CROSS-run/cross-job (it persists in the long-running worker
        process and stops repeatedly hammering a banned host). [Phase 0 / S4, Phase 1 / S20]
        """
        breaker = get_host_breaker(url)
        if should_block(breaker):
            logger.error("[nawy] listing-api circuit OPEN — short-circuiting %s", url)
            return None

        backoff = 2.0
        for attempt in range(1, max_attempts + 1):
            try:
                resp = await self._http.get(url)
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait = (
                        float(retry_after)
                        if retry_after and retry_after.isdigit()
                        else backoff
                    )
                    logger.warning(
                        "[nawy] listing-api 429 for %s (attempt %d/%d) — backing off %.1fs",
                        url, attempt, max_attempts, wait,
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(wait)
                        backoff = min(backoff * 2, 30.0)
                        continue
                    breaker.on_failure()
                    return None
                if 400 <= resp.status_code < 500:
                    # Permanent client error — not a host-health signal; do not
                    # trip the breaker, and don't waste the backoff budget.
                    logger.error(
                        "[nawy] listing-api %d for %s — not retrying",
                        resp.status_code, url,
                    )
                    return None
                resp.raise_for_status()  # raises on 5xx → retried below
                breaker.on_success()
                return resp.json()
            except Exception as exc:
                logger.warning(
                    "[nawy] listing-api fetch error for %s (attempt %d/%d): %s",
                    url, attempt, max_attempts, exc,
                )
                if attempt < max_attempts:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)
                    continue
                logger.error(
                    "[nawy] listing-api fetch failed after %d attempts: %s",
                    max_attempts, url,
                )
                breaker.on_failure()
                return None
        # Unreachable in practice (each attempt returns or continues) — defensive
        # fallthrough that must NOT double-count a failure.
        return None

    async def _fetch(self, url: str) -> Optional[str]:
        """StealthyFetcher when available (Cloudflare-aware), plain httpx otherwise."""
        if _STEALTH_OK and not SCRAPER_DISABLE_BROWSER:
            try:
                fetch_kwargs = {"headless": True, "network_idle": True}
                if self._proxy:  # S1: same residential proxy as the httpx path
                    fetch_kwargs["proxy"] = self._proxy
                page = await asyncio.to_thread(
                    StealthyFetcher.fetch,
                    url,
                    **fetch_kwargs,
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
