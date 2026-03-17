"""
Stealth Playwright Scraper — Core Scraper
------------------------------------------
Pillar 1 + 5: Invisible API Interception + Anti-Bot Stealth.

Dual extraction strategy for Nawy.com (Next.js application):

  Strategy 1 (PRIMARY): Extract <script id="__NEXT_DATA__" type="application/json">
    → Nawy SSR pages embed the full Apollo/REST response in this tag.
    → More reliable than XHR: always present, no race condition, structurally stable.

  Strategy 2 (FALLBACK): Intercept outbound XHR/Fetch requests via Playwright route
    → Catches AJAX-loaded data (compound unit tabs, pagination).
    → Stores all responses matching /api/ or /graphql patterns.

Stealth features:
  - playwright-stealth patches navigator.webdriver, chrome runtime, permissions,
    plugins, languages — defeats most bot detection heuristics.
  - Fingerprint randomization: viewport, user-agent, locale, timezone per request.
  - Human-like delays between page interactions.
  - Proxy rotation via PROXY_LIST env var (BrightData / ScraperAPI / custom).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from playwright.async_api import (
    BrowserContext,
    Page,
    PlaywrightContextManager,
    Route,
    async_playwright,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Fingerprint Pool
# ─────────────────────────────────────────────────────────────────────────────

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 2560, "height": 1440},
    {"width": 1280, "height": 800},
]

USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Realistic Egyptian residential users: Arabic + English accept-languages
LOCALES = ["ar-EG", "ar-EG,ar;q=0.9,en-US;q=0.8", "en-US,en;q=0.9,ar;q=0.8"]
TIMEZONES = ["Africa/Cairo"]

MIN_DELAY_S = 1.5
MAX_DELAY_S = 4.0

# Browser launch args that defeat AutomationControlled flag
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-infobars",
    "--window-size=1920,1080",
]

# XHR patterns to intercept on Nawy.com
XHR_INTERCEPT_PATTERNS = [
    "**/api/**",
    "**/_next/data/**",  # Next.js static JSON files (getStaticProps / getServerSideProps)
    "**/graphql**",
]

# Keys that indicate a response contains property/unit data
_PROPERTY_SIGNAL_KEYS = {
    "units", "compound", "compounds", "properties", "listings", "results",
    "price", "minPrice", "min_price", "area", "size", "builtUpArea",
}


# ─────────────────────────────────────────────────────────────────────────────
# Custom Exception
# ─────────────────────────────────────────────────────────────────────────────

class ScraperError(Exception):
    """Raised when all extraction strategies fail after all retries."""


# ─────────────────────────────────────────────────────────────────────────────
# Proxy Rotation
# ─────────────────────────────────────────────────────────────────────────────

def _parse_proxy_list() -> list[dict]:
    """
    Parses PROXY_LIST env var into Playwright proxy dicts.

    Accepted formats (comma-separated list):
      - http://host:port
      - http://user:pass@host:port
      - socks5://host:port

    Returns empty list if PROXY_LIST is unset (direct connection).
    """
    raw = os.getenv("PROXY_LIST", "").strip()
    if not raw:
        return []

    proxies = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        try:
            parsed = urlparse(entry)
            proxy = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
            if parsed.username:
                proxy["username"] = parsed.username
            if parsed.password:
                proxy["password"] = parsed.password
            proxies.append(proxy)
        except Exception as exc:
            logger.warning("[scraper] Invalid proxy entry '%s': %s", entry, exc)

    return proxies


_PROXY_LIST: list[dict] = []  # Lazy-loaded singleton


def _pick_proxy() -> Optional[dict]:
    """Returns a random proxy dict or None for direct connection."""
    global _PROXY_LIST
    if not _PROXY_LIST:
        _PROXY_LIST = _parse_proxy_list()
    return random.choice(_PROXY_LIST) if _PROXY_LIST else None


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Strategies
# ─────────────────────────────────────────────────────────────────────────────

async def _extract_next_data(page: Page) -> Optional[dict]:
    """
    Strategy 1 (PRIMARY): Parse <script id="__NEXT_DATA__"> tag.

    This tag is injected by Next.js on every SSR page and contains the full
    page props as JSON. It includes the compound data and unit listings that
    were fetched server-side — no JavaScript execution required.

    Returns:
        Parsed dict or None if the tag is absent or unparseable.
    """
    try:
        raw_json = await page.evaluate(
            """
            () => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? el.textContent : null;
            }
            """
        )
        if not raw_json:
            logger.debug("[scraper] __NEXT_DATA__ tag not found on page")
            return None

        data = json.loads(raw_json)
        logger.debug("[scraper] __NEXT_DATA__ extracted successfully (%d chars)", len(raw_json))
        return data

    except json.JSONDecodeError as exc:
        logger.warning("[scraper] __NEXT_DATA__ JSON parse error: %s", exc)
        return None
    except Exception as exc:
        logger.warning("[scraper] __NEXT_DATA__ extraction error: %s", exc)
        return None


def _is_property_response(data: Any) -> bool:
    """Heuristic: does this JSON payload contain property/unit data?"""
    if isinstance(data, dict):
        keys = set(data.keys())
        return bool(keys & _PROPERTY_SIGNAL_KEYS)
    if isinstance(data, list) and data:
        return _is_property_response(data[0])
    return False


async def _extract_xhr_intercept(page: Page, url: str) -> Optional[dict]:
    """
    Strategy 2 (FALLBACK): Intercept Nawy's internal XHR/Fetch API calls.

    Registers route handlers BEFORE navigation, collects all JSON responses
    that look like property data, then returns the richest one.

    This catches:
    - _next/data/ static JSON (getServerSideProps payloads for CSR navigation)
    - /api/compounds/, /api/units/ REST endpoints
    - GraphQL responses (if Nawy uses GraphQL)

    Returns:
        The most data-rich intercepted JSON payload, or None.
    """
    intercepted: list[dict] = []

    async def handle_route(route: Route) -> None:
        """Pass-through handler that captures response bodies."""
        response = await route.fetch()
        try:
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                body = await response.body()
                data = json.loads(body)
                if _is_property_response(data):
                    intercepted.append(data)
                    logger.debug("[scraper] XHR intercepted: %s (%d chars)", route.request.url, len(body))
        except Exception:
            pass  # Non-JSON or failed response — silently skip
        finally:
            await route.fulfill(response=response)

    # Register intercept handlers before navigation
    for pattern in XHR_INTERCEPT_PATTERNS:
        await page.route(pattern, handle_route)

    try:
        await page.goto(url, wait_until="networkidle", timeout=45_000)
        await _human_delay()
    except Exception as exc:
        logger.warning("[scraper] XHR intercept navigation error: %s", exc)

    if not intercepted:
        return None

    # Return the response with the most keys (most data-rich)
    return max(intercepted, key=lambda d: len(str(d)) if isinstance(d, dict) else 0)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _human_delay(
    min_s: float = MIN_DELAY_S,
    max_s: float = MAX_DELAY_S,
) -> None:
    """Async sleep for a random duration — mimics human reading time."""
    await asyncio.sleep(random.uniform(min_s, max_s))


def _pick_fingerprint() -> dict:
    """Returns a randomized browser context fingerprint."""
    return {
        "viewport": random.choice(VIEWPORTS),
        "user_agent": random.choice(USER_AGENTS),
        "locale": random.choice(LOCALES),
        "timezone_id": random.choice(TIMEZONES),
        "proxy": _pick_proxy(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main Scraper Entry Point
# ─────────────────────────────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
)
async def scrape_compound(compound_url: str) -> dict:
    """
    Scrapes one Nawy.com compound detail page.

    Pillar 1 — Dual extraction:
      Tries __NEXT_DATA__ first (faster, more reliable).
      Falls back to XHR interception if __NEXT_DATA__ is absent or empty.

    Pillar 5 — Anti-bot stealth:
      playwright-stealth patches all known automation fingerprints.
      Random viewport + UA + locale + timezone + proxy per call.
      Human-like interaction delays.

    Tenacity retries on PlaywrightError or asyncio.TimeoutError with
    exponential backoff (5s → 10s → 60s cap, 3 attempts).

    Args:
        compound_url: Full Nawy.com URL, e.g. "https://www.nawy.com/compounds/marassi"

    Returns:
        Raw JSON dict with _meta key added:
        {
          "_meta": {"source_url": ..., "strategy": "next_data|xhr", "scraped_at": ISO},
          ...data from Nawy
        }

    Raises:
        ScraperError: All strategies and all retries exhausted.
    """
    fp = _pick_fingerprint()
    strategy_used = "unknown"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=BROWSER_ARGS,
        )

        try:
            context: BrowserContext = await browser.new_context(
                viewport=fp["viewport"],
                user_agent=fp["user_agent"],
                locale=fp["locale"],
                timezone_id=fp["timezone_id"],
                proxy=fp["proxy"],           # None = direct connection
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=False,
            )

            # Block resource types that waste bandwidth and may fingerprint us
            await context.route(
                "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot,mp4,avi}",
                lambda route: route.abort(),
            )

            page: Page = await context.new_page()

            # Apply playwright-stealth (patches navigator.webdriver etc.)
            # Handles both v1 (stealth_async) and v2 (Stealth class) APIs.
            try:
                try:
                    # playwright-stealth v2 API
                    from playwright_stealth import Stealth
                    await Stealth().apply_stealth_async(page)
                    logger.debug("[scraper] playwright-stealth v2 applied")
                except (ImportError, AttributeError):
                    # playwright-stealth v1 API fallback
                    from playwright_stealth import stealth_async
                    await stealth_async(page)
                    logger.debug("[scraper] playwright-stealth v1 applied")
            except ImportError:
                logger.warning(
                    "[scraper] playwright-stealth not installed — "
                    "run: pip install playwright-stealth"
                )

            # ── Strategy 1: __NEXT_DATA__ ───────────────────────────────────
            try:
                await page.goto(compound_url, wait_until="domcontentloaded", timeout=30_000)
                await _human_delay(0.8, 1.5)  # Let React hydrate briefly
                raw_data = await _extract_next_data(page)
            except Exception as nav_exc:
                logger.warning("[scraper] Initial navigation error for %s: %s", compound_url, nav_exc)
                raw_data = None

            if raw_data and _has_meaningful_data(raw_data):
                strategy_used = "next_data"
                logger.info("[scraper] Strategy 1 (NEXT_DATA) succeeded for %s", compound_url)
            else:
                # ── Strategy 2: XHR Interception ───────────────────────────
                logger.info("[scraper] Strategy 1 failed — attempting XHR interception for %s", compound_url)
                try:
                    await page.unroute("**/*")  # Clear existing routes before XHR setup
                    raw_data = await _extract_xhr_intercept(page, compound_url)
                    if raw_data:
                        strategy_used = "xhr_intercept"
                        logger.info("[scraper] Strategy 2 (XHR) succeeded for %s", compound_url)
                except Exception as xhr_exc:
                    logger.error("[scraper] XHR interception error for %s: %s", compound_url, xhr_exc)
                    raw_data = None

        finally:
            await browser.close()

    if not raw_data:
        raise ScraperError(
            f"All extraction strategies exhausted for {compound_url}. "
            "Check network connectivity, proxy validity, and whether Nawy's page structure has changed."
        )

    # Attach metadata for downstream processing
    raw_data["_meta"] = {
        "source_url": compound_url,
        "strategy": strategy_used,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }

    return raw_data


def _has_meaningful_data(data: Any) -> bool:
    """
    Quick sanity check: does the extracted dict contain something useful?
    Prevents passing empty pageProps to the normalizer.
    """
    if not isinstance(data, dict):
        return False
    # Check for Next.js page props structure
    page_props = (
        data.get("props", {}).get("pageProps", {})
    )
    if page_props and len(page_props) > 1:
        return True
    # Fallback: just check total key count
    return len(str(data)) > 200
