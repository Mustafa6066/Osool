import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import asyncio
import os

from app.services.normalization import PropertyNormalizer

logger = logging.getLogger(__name__)

class AqarmapStealthScraper:
    """
    Zero-Token scraper for Aqarmap using Playwright and residential proxies.
    """

    BASE_URL = "https://aqarmap.com.eg/en/for-sale/property-type/cairo/new-cairo/"

    def __init__(self):
        # E.g., http://username:password@proxy.iproyal.com:12345
        self.proxy_url = os.getenv("IPROYAL_PROXY_URL")

    async def scrape_new_cairo(self, pages: int = 2) -> List[Dict[str, Any]]:
        """
        Scrapes multiple pages of Aqarmap New Cairo listings.
        """
        logger.info(f"Starting Aqarmap stealth scrape for {self.BASE_URL}")
        all_properties = []

        try:
            async with async_playwright() as p:
                launch_args = {
                    "headless": True,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars"
                    ]
                }
                if self.proxy_url:
                    launch_args["proxy"] = {"server": self.proxy_url}

                browser = await p.chromium.launch(**launch_args)

                # Using Obscura techniques implicitly via context options
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                    has_touch=False,
                    is_mobile=False,
                    java_script_enabled=True,
                )

                # Add scripts to bypass bot detection
                await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                page = await context.new_page()

                try:
                    for i in range(1, pages + 1):
                        url = f"{self.BASE_URL}?page={i}" if i > 1 else self.BASE_URL
                        logger.info(f"Scraping Aqarmap page {i}: {url}")

                        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                        # Wait for listings to appear
                        await page.wait_for_selector(".search-listing-card", timeout=10000)

                        # Extract data using DOM selectors
                        cards = await page.query_selector_all(".search-listing-card")

                        for card in cards:
                            prop = await self._extract_card_data(card)
                            if prop:
                                all_properties.append(prop)

                        # Small delay between pages
                        await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"Error during Aqarmap scrape page loading: {e}")
                finally:
                    await browser.close()

        except Exception as e:
             logger.error(f"Error initializing Playwright/Browser: {e}")

        logger.info(f"Successfully extracted {len(all_properties)} properties from Aqarmap.")
        return all_properties

    async def _extract_card_data(self, card) -> Dict[str, Any]:
        """Extracts text from a single listing card."""
        try:
            # These selectors are examples and need to be verified against live Aqarmap DOM

            title_el = await card.query_selector(".card-title")
            title = await title_el.inner_text() if title_el else "Property"

            price_el = await card.query_selector(".search-listing-card__price")
            raw_price = await price_el.inner_text() if price_el else ""
            price_int = PropertyNormalizer.clean_price(raw_price)

            size_el = await card.query_selector(".search-listing-card__size")
            raw_size = await size_el.inner_text() if size_el else ""
            size_int = PropertyNormalizer.extract_size(raw_size)

            if not price_int or not size_int:
                return None

            location_el = await card.query_selector(".search-listing-card__address")
            raw_location = await location_el.inner_text() if location_el else "New Cairo"
            location = PropertyNormalizer.normalize_area(raw_location)

            # Extract URL
            link_el = await card.query_selector("a")
            url = await link_el.get_attribute("href") if link_el else ""
            if url and not url.startswith("http"):
                 url = f"https://aqarmap.com.eg{url}"

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

aqarmap_scraper = AqarmapStealthScraper()
