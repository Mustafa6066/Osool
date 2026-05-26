import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import asyncio
import os
import contextlib
from urllib.parse import urlparse

from app.services.normalization import PropertyNormalizer

logger = logging.getLogger(__name__)

class AqarmapStealthScraper:
    """
    Zero-Token scraper for Aqarmap using Playwright and residential proxies.
    """

    BASE_URL = "https://aqarmap.com.eg/en/for-sale/property-type/cairo/new-cairo/"
    CARD_SELECTOR = ".search-listing-card, .listing-card"

    def __init__(self):
        # E.g., http://username:password@proxy.iproyal.com:12345
        self.proxy_url = os.getenv("IPROYAL_PROXY_URL")
        self.obscura_cdp_url = os.getenv("OBSCURA_CDP_URL")
        self.obscura_required = os.getenv("OBSCURA_REQUIRED", "false").lower() == "true"
        self.obscura_connect_timeout_ms = int(os.getenv("OBSCURA_CONNECT_TIMEOUT_MS", "20000"))

    def _normalize_cdp_endpoint(self, endpoint: str) -> str:
        """
        Convert ws://.../devtools/browser to http://host:port for stable CDP attach.
        """
        endpoint = (endpoint or "").strip()
        if not endpoint:
            return endpoint

        parsed = urlparse(endpoint)
        if parsed.scheme in {"ws", "wss"} and parsed.hostname and parsed.port:
            http_scheme = "https" if parsed.scheme == "wss" else "http"
            return f"{http_scheme}://{parsed.hostname}:{parsed.port}"
        return endpoint

    async def _create_browser_and_context(self, playwright, context_kwargs, prefer_obscura: bool = True):
        """
        Prefer Obscura CDP when configured, with safe fallback to local Chromium.
        """
        if prefer_obscura and self.obscura_cdp_url:
            try:
                cdp_endpoint = self._normalize_cdp_endpoint(self.obscura_cdp_url)
                logger.info("Attempting Obscura CDP connection: %s", cdp_endpoint)
                browser = await playwright.chromium.connect_over_cdp(
                    cdp_endpoint,
                    timeout=self.obscura_connect_timeout_ms,
                )
                if browser.contexts:
                    logger.info("Aqarmap scraper browser mode: obscura-cdp (existing context)")
                    return browser, browser.contexts[0], "obscura-cdp", False

                logger.info("Aqarmap scraper browser mode: obscura-cdp (new context)")
                return browser, await browser.new_context(**context_kwargs), "obscura-cdp", True
            except Exception as exc:
                if self.obscura_required:
                    raise RuntimeError("Failed to connect to required Obscura CDP endpoint") from exc
                logger.warning(
                    "Obscura CDP connection failed; falling back to Playwright Chromium: %s",
                    exc,
                )

        launch_args = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        }
        if self.proxy_url:
            launch_args["proxy"] = {"server": self.proxy_url}

        browser = await playwright.chromium.launch(**launch_args)
        logger.info("Aqarmap scraper browser mode: playwright-local")
        return browser, await browser.new_context(**context_kwargs), "playwright-local", True

    async def _collect_page_properties(self, page, pages: int, all_properties: List[Dict[str, Any]], seen_urls: set) -> None:
        for i in range(1, pages + 1):
            url = f"{self.BASE_URL}?page={i}" if i > 1 else self.BASE_URL
            logger.info(f"Scraping Aqarmap page {i}: {url}")

            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for listings to appear
            await page.wait_for_selector(self.CARD_SELECTOR, timeout=15000)

            # Extract data using DOM selectors
            cards = await page.query_selector_all(self.CARD_SELECTOR)

            for card in cards:
                prop = await self._extract_card_data(card)
                if prop and prop["url"] not in seen_urls:
                    seen_urls.add(prop["url"])
                    all_properties.append(prop)

            # Small delay between pages
            await asyncio.sleep(2)

    async def _close_browser_resources(self, page, context, browser, close_context: bool = True) -> None:
        if page:
            with contextlib.suppress(Exception):
                await page.close()
        if context and close_context:
            with contextlib.suppress(Exception):
                await context.close()
        if browser:
            with contextlib.suppress(Exception):
                await browser.close()

    async def scrape_new_cairo(self, pages: int = 2) -> List[Dict[str, Any]]:
        """
        Scrapes multiple pages of Aqarmap New Cairo listings.
        """
        logger.info(f"Starting Aqarmap stealth scrape for {self.BASE_URL}")
        all_properties = []
        seen_urls = set()

        try:
            async with async_playwright() as p:
                context_kwargs = dict(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                    has_touch=False,
                    is_mobile=False,
                    java_script_enabled=True,
                )

                browser = None
                context = None
                page = None
                mode = "unknown"
                owns_context = True

                browser, context, mode, owns_context = await self._create_browser_and_context(p, context_kwargs)

                # Add scripts to bypass bot detection
                await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                page = await context.new_page()

                try:
                    await self._collect_page_properties(page, pages, all_properties, seen_urls)

                except Exception as e:
                    logger.error(f"Error during Aqarmap scrape page loading: {e}")
                    if mode == "obscura-cdp" and not self.obscura_required:
                        logger.warning("Retrying Aqarmap scrape with Playwright fallback after Obscura navigation failure")
                        await self._close_browser_resources(page, context, browser, close_context=owns_context)
                        browser = None
                        context = None
                        page = None
                        owns_context = True

                        browser, context, _, owns_context = await self._create_browser_and_context(
                            p,
                            context_kwargs,
                            prefer_obscura=False,
                        )
                        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                        page = await context.new_page()
                        await self._collect_page_properties(page, pages, all_properties, seen_urls)
                finally:
                    await self._close_browser_resources(page, context, browser, close_context=owns_context)

        except Exception as e:
             logger.error(f"Error initializing Playwright/Browser: {e}")

        logger.info(f"Successfully extracted {len(all_properties)} properties from Aqarmap.")
        return all_properties

    async def _extract_card_data(self, card) -> Dict[str, Any]:
        """Extracts text from a single listing card."""
        try:
            # Prefer explicit selectors, then fallback to card text parsing for resilience.
            card_text = (await card.inner_text() or "").strip()

            # Only keep actual listing cards to avoid summary/analytics boxes.
            url = await self._first_href(
                card,
                [
                    "a[href*='/en/listing/']",
                    "a[href*='/ar/listing/']",
                ],
            ) or ""
            if not url:
                return None
            if url and not url.startswith("http"):
                 url = f"https://aqarmap.com.eg{url}"

            title = await self._first_inner_text(
                card,
                [
                    ".card-title",
                    ".listing-card-details h2",
                    ".listing-card-details h3",
                    "[class*='title']",
                    "h2",
                    "h3",
                ],
            ) or "Property"

            raw_price = await self._first_inner_text(
                card,
                [
                    ".search-listing-card__price",
                    "[class*='price']",
                    "[data-testid*='price']",
                ],
            )
            price_int = PropertyNormalizer.clean_price(raw_price)

            raw_size = await self._first_inner_text(
                card,
                [
                    ".search-listing-card__size",
                    "[class*='size']",
                    "[class*='area']",
                    "[data-testid*='area']",
                ],
            )
            size_int = PropertyNormalizer.extract_size(raw_size)

            if not size_int and card_text:
                size_int = PropertyNormalizer.extract_size(card_text)

            # Discard noisy parses from non-property text.
            if price_int < 100000 or size_int < 20:
                return None

            if not price_int or not size_int:
                return None

            raw_location = await self._first_inner_text(
                card,
                [
                    ".search-listing-card__address",
                    "[class*='address']",
                    "[class*='location']",
                    "[class*='district']",
                ],
            ) or "New Cairo"
            location = PropertyNormalizer.normalize_area(raw_location)

            return {
                "title": title.strip(),
                "location": location,
                "price": price_int,
                "size_sqm": size_int,
                "price_per_sqm": price_int / size_int if size_int > 0 else 0,
                "sale_type": "Resale", # Aqarmap is primarily resale
                "url": url,
                "is_available": True
            }
        except Exception as e:
            logger.debug(f"Could not extract card data: {e}")
            return None

    async def _first_inner_text(self, card, selectors: List[str]) -> str:
        for selector in selectors:
            element = await card.query_selector(selector)
            if element:
                text = (await element.inner_text() or "").strip()
                if text:
                    return text
        return ""

    async def _first_href(self, card, selectors: List[str]) -> str:
        for selector in selectors:
            element = await card.query_selector(selector)
            if element:
                href = (await element.get_attribute("href") or "").strip()
                if href:
                    return href
        return ""

aqarmap_scraper = AqarmapStealthScraper()
