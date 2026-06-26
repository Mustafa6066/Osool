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
import json
import logging
from typing import Optional

import httpx

from extractors.aqarmap_selectors import extract_detail_page, extract_listing_links
from proxy_pool import build_proxy_pool, mask_proxy
from resilience import get_host_breaker, should_block
from settings import (
    MAX_PAGES_PER_AREA,
    REQUEST_DELAY_SECONDS,
    SCRAPER_DISABLE_BROWSER,
    browser_headers,
)
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


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse a Retry-After header (delta-seconds form) into seconds."""
    if value and value.strip().isdigit():
        return float(value.strip())
    return None


_BLOCK_MARKERS = (
    "captcha",
    "are you human",
    "access denied",
    "request blocked",
    "cloudflare",
    "attention required",
)


def _looks_blocked(status: Optional[int], body: Optional[str]) -> bool:
    """
    Heuristic block detector (S3). Aqarmap serves 403/429 or a tiny challenge
    page when it dislikes the egress; treat those as a block so we rotate off the
    proxy instead of re-hitting the same banned IP and deepening the ban.
    """
    if status in (403, 429, 503):
        return True
    if not body or len(body) < 1000:
        return True
    low = body[:4000].lower()
    return any(m in low for m in _BLOCK_MARKERS)


class AqarmapSpider(SiteSpider):
    name = "aqarmap"

    def __init__(self) -> None:
        # S2: rotate across a residential proxy POOL, quarantining any proxy that
        # returns a block, instead of pinning every request to one IP. httpx
        # clients are created lazily per proxy ("" = direct) and reused.
        self._pool = build_proxy_pool()
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _client_for(self, proxy: str) -> httpx.AsyncClient:
        key = proxy or ""
        client = self._clients.get(key)
        if client is None:
            kwargs: dict = {
                "headers": browser_headers(),
                "timeout": 30.0,
                "follow_redirects": True,
            }
            if proxy:
                kwargs["proxy"] = proxy
            client = httpx.AsyncClient(**kwargs)
            self._clients[key] = client
        return client

    async def aclose(self) -> None:
        for client in self._clients.values():
            try:
                await client.aclose()
            except Exception:
                pass
        self._clients.clear()

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

    async def _fetch_html(self, url: str) -> Optional[str]:
        """
        Block-aware fetch with proxy rotation (S2/S3). Replaces the old blanket
        @retry that re-hit 403 blocks on the SAME proxy, deepening the ban. On a
        block we quarantine the proxy, rotate to another, honor Retry-After, and
        back off with jitter; when the whole pool is exhausted we alert + back off
        instead of hammering a banned egress.
        """
        # S20: per-host circuit breaker. If the host has failed repeatedly the
        # circuit is OPEN — short-circuit instead of grinding every URL through
        # the full attempt loop against a banned/down host.
        breaker = get_host_breaker(url)
        if should_block(breaker):
            logger.error(
                "[aqarmap] circuit OPEN for %s — short-circuiting (host blocked/down)",
                url,
            )
            return None
        configured = self._pool.size
        max_attempts = max(3, min(configured or 1, 5))
        backoff = 2.0
        host_contacted = False  # did any attempt actually reach the host?
        for attempt in range(1, max_attempts + 1):
            proxy = self._pool.get()
            if configured and proxy is None:
                logger.error(
                    "[aqarmap] proxy pool exhausted — backing off instead of hammering %s",
                    url,
                )
                await self._alert_pool_exhausted(url)
                await asyncio.sleep(self._pool.jittered_backoff(backoff))
                backoff = min(backoff * 2, 30.0)
                continue

            host_contacted = True
            body, retry_after, blocked = await self._attempt_fetch(url, proxy)
            if body and not blocked:
                self._pool.report_success(proxy)
                breaker.on_success()
                return body

            self._pool.report_block(proxy, retry_after)
            wait = retry_after or self._pool.jittered_backoff(backoff)
            logger.warning(
                "[aqarmap] attempt %d/%d blocked/failed for %s (proxy=%s) — rotating, wait %.1fs",
                attempt, max_attempts, url, mask_proxy(proxy), wait,
            )
            await asyncio.sleep(wait)
            backoff = min(backoff * 2, 30.0)

        logger.error("[aqarmap] giving up on %s after %d attempts", url, max_attempts)
        if host_contacted:
            # Only penalize the HOST breaker if we actually reached the host. A
            # give-up caused purely by proxy-pool exhaustion is a proxy problem,
            # not a host block — don't spuriously open the host circuit.
            breaker.on_failure()
        return None

    async def _attempt_fetch(
        self, url: str, proxy: Optional[str]
    ) -> tuple[Optional[str], Optional[float], bool]:
        """One fetch attempt → (body|None, retry_after|None, blocked). [S3]"""
        # Prefer StealthyFetcher (Playwright + anti-bot). Aqarmap serves empty
        # bodies to plain httpx, so httpx is only a weak fallback.
        if _STEALTH_OK and not SCRAPER_DISABLE_BROWSER:
            try:
                fetch_kwargs = {"headless": True, "network_idle": True}
                if proxy:
                    fetch_kwargs["proxy"] = proxy
                page = await asyncio.to_thread(StealthyFetcher.fetch, url, **fetch_kwargs)
                body = page.body if hasattr(page, "body") else str(page)
                if isinstance(body, (bytes, bytearray)):
                    body = body.decode("utf-8", errors="replace")
                if _looks_blocked(None, body):
                    logger.warning(
                        "[aqarmap] StealthyFetcher body looks blocked for %s (proxy=%s, %d chars)",
                        url, mask_proxy(proxy), len(body or ""),
                    )
                    return None, None, True
                return body, None, False
            except Exception as exc:
                logger.warning(
                    "[aqarmap] StealthyFetcher failed for %s (proxy=%s): %s",
                    url, mask_proxy(proxy), exc,
                )

        try:
            resp = await self._client_for(proxy or "").get(url)
            retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            if _looks_blocked(resp.status_code, resp.text):
                return None, retry_after, True
            return resp.text, None, False
        except Exception as exc:
            logger.error(
                "[aqarmap] httpx fetch failed for %s (proxy=%s): %s",
                url, mask_proxy(proxy), exc,
            )
            return None, None, True

    async def _alert_pool_exhausted(self, url: str) -> None:
        """Best-effort health alert when every proxy is quarantined. [S2]"""
        try:
            import redis.asyncio as aioredis

            from settings import HEALTH_ALERT_KEY, HEALTH_ALERT_KEEP, REDIS_URL

            payload = json.dumps({
                "site": "aqarmap",
                "type": "proxy_pool_exhausted",
                "pool_size": self._pool.size,
                "url": url,
            })
            client = aioredis.from_url(REDIS_URL, decode_responses=True)
            async with client:
                await client.lpush(HEALTH_ALERT_KEY, payload)
                await client.ltrim(HEALTH_ALERT_KEY, 0, HEALTH_ALERT_KEEP - 1)
        except Exception:
            pass

    async def _scrape_detail(self, url: str) -> Optional[dict]:
        html = await self._fetch_html(url)
        if not html:
            return None
        try:
            return extract_detail_page(html, url)
        except Exception as exc:
            logger.warning("[aqarmap] detail extract failed for %s: %s", url, exc)
            return None
