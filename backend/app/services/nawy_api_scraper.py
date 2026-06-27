import json
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import httpx

from app.services.normalization import PropertyNormalizer

logger = logging.getLogger(__name__)

class NawyApiScraper:
    """
    Zero-Token scraper for Nawy using Next.js data extraction.
    """

    BASE_URL = "https://www.nawy.com/areas/new-cairo"

    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=30.0
        )

    def scrape_new_cairo(self) -> List[Dict[str, Any]]:
        """
        Fetches the New Cairo page and extracts property data from the Next.js __NEXT_DATA__ tag.
        """
        logger.info(f"Starting Nawy scrape for {self.BASE_URL}")
        try:
            response = self.client.get(self.BASE_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', id='__NEXT_DATA__', type='application/json')

            if not script_tag:
                logger.error("Could not find __NEXT_DATA__ script tag on Nawy page.")
                return []

            data = json.loads(script_tag.string)
            properties = self._parse_nextjs_data(data)
            logger.info(f"Successfully extracted {len(properties)} properties from Nawy.")
            return properties

        except httpx.HTTPError as e:
            logger.error(f"HTTP Error during Nawy scrape: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during Nawy scrape: {e}")
            return []

    def _parse_nextjs_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Navigates the deeply nested Next.js JSON to extract property listings.
        Note: The actual structure might change, this requires periodic verification.
        """
        properties = []
        try:
            # This is a generic path, would need to be tuned to exact Nawy structure
            # Let's assume we find the apollo state or pageProps where listings reside
            props = data.get("props", {}).get("pageProps", {})

            # Look for common keys where properties might be stored
            listings = []
            for key in ["initialState", "dehydratedState", "data", "searchResult"]:
                if key in props:
                    # Recursive search for an array of items that look like properties
                    listings = self._find_listings_in_dict(props[key])
                    if listings:
                        break

            for item in listings:
                prop = self._normalize_nawy_item(item)
                if prop:
                    properties.append(prop)

            return properties
        except Exception as e:
            logger.error(f"Error parsing Nawy JSON data: {e}")
            return []

    def _find_listings_in_dict(self, d: Any) -> List[Dict]:
        """Recursively search for a list of properties."""
        if isinstance(d, dict):
            if "properties" in d and isinstance(d["properties"], list):
                return d["properties"]
            if "edges" in d and isinstance(d["edges"], list):
                return d["edges"]
            for v in d.values():
                res = self._find_listings_in_dict(v)
                if res:
                    return res
        elif isinstance(d, list):
            for item in d:
                res = self._find_listings_in_dict(item)
                if res:
                    return res
        return []

    def _normalize_nawy_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Converts raw Nawy item to Osool standard schema."""
        try:
            # Extract fields based on typical GraphQL/API responses
            node = item.get("node", item) # Handle edge/node pagination structure

            price = node.get("price") or node.get("minPrice") or 0
            size = node.get("builtUpArea") or node.get("area") or 0

            if not price or not size:
                return None

            price_int = PropertyNormalizer.clean_price(str(price))
            size_int = PropertyNormalizer.extract_size(str(size))

            # `area` is also used as a numeric built-up-area size fallback above,
            # so never treat a number as a location — fall back to explicit area
            # keys. A wrong (numeric) location would fail validation and DROP the row.
            node_area = node.get("area")
            if isinstance(node_area, dict):
                node_area = node_area.get("name")
            elif not isinstance(node_area, str):
                node_area = None
            node_area = node_area or node.get("areaName") or node.get("city")
            raw_url = node.get("url")

            return {
                "title": node.get("name") or node.get("title", "Property in New Cairo"),
                # I19: derive the real area; never hardcode "new cairo" (that
                # poisons the New Cairo median). None → "Unknown" downstream.
                "location": node_area or None,
                "compound": node.get("compound", {}).get("name") if isinstance(node.get("compound"), dict) else node.get("compound"),
                "developer": node.get("developer", {}).get("name") if isinstance(node.get("developer"), dict) else node.get("developer"),
                "price": price_int,
                "size_sqm": size_int,
                "price_per_sqm": price_int / size_int if size_int > 0 else 0,
                "bedrooms": int(node.get("bedrooms", 0) or 0),
                "bathrooms": int(node.get("bathrooms", 0) or 0),
                "finishing": PropertyNormalizer.map_finishing(node.get("finishing", "")),
                "sale_type": node.get("saleType", "Developer"),
                "is_nawy_now": node.get("isNawyNow", False),
                "installment_years": node.get("paymentPlanYears", 0),
                "down_payment": node.get("downPayment", 0),
                # I11: only build a URL when the node has one — never synthesize
                # the bare base URL (all url-less rows would collapse onto it and
                # overwrite each other on the single nawy_url dedup key).
                "nawy_url": f"https://www.nawy.com{raw_url}" if raw_url else None,
                "nawy_reference": node.get("id") or node.get("reference"),
                "image_url": node.get("image", {}).get("url") if isinstance(node.get("image"), dict) else None
            }
        except Exception as e:
            logger.debug(f"Could not normalize Nawy item: {e}")
            return None

nawy_api_scraper = NawyApiScraper()
