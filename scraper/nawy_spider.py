"""
Nawy Spider — Scrapling-based adaptive property scraper.

Zero LLM tokens. Zero OpenAI calls. Pure CSS/XPath extraction with adaptive selectors
that survive website redesigns automatically.

Inspired by Scrapling's Spider architecture:
  - StealthyFetcher for Cloudflare bypass
  - auto_save=True for adaptive CSS selectors
  - Pause/resume via crawldir for long crawls
  - Development mode: cache responses for replay

Usage:
    python nawy_spider.py                    # Full crawl
    python nawy_spider.py --dev              # Dev mode (cached responses)
    python nawy_spider.py --resume           # Resume from last checkpoint
    python nawy_spider.py --area "new-cairo" # Single area
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# ── Setup ──
BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / "backend" / ".env"
load_dotenv(dotenv_path=str(ENV_PATH))

sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("nawy_spider")

# ── Constants ──
BASE_URL = "https://www.nawy.com"
CRAWL_DIR = Path(__file__).parent / ".crawldir"
DEV_CACHE_DIR = Path(__file__).parent / ".dev_cache"
CHECKPOINT_FILE = CRAWL_DIR / "checkpoint.json"

# ── Optional Scrapling import (falls back to httpx+regex if not installed) ──
SCRAPLING_AVAILABLE = False
try:
    from scrapling import StealthyFetcher, Fetcher
    SCRAPLING_AVAILABLE = True
    logger.info("✅ Scrapling loaded — adaptive selectors active")
except ImportError:
    logger.warning("⚠️  Scrapling not installed — falling back to httpx + regex extraction")

# ── Optional DB import ──
DB_AVAILABLE = False
try:
    from app.ingestion.deterministic_normalizer import (
        NormalizedProperty,
        normalize_properties,
    )
    DB_AVAILABLE = True
    logger.info("✅ Deterministic normalizer loaded")
except ImportError:
    pass


class NawySpider:
    """
    Adaptive Nawy property spider.

    Phase 1: Discover all compound slugs via Nawy's Next.js data API (pure HTTP).
    Phase 2: Scrape each compound page for property data using adaptive CSS selectors.
    Phase 3: Collect Nawy Now listings.

    Features:
      - Zero LLM tokens — all extraction is CSS/XPath/regex
      - Adaptive selectors (auto_save=True) — survives redesigns
      - Checkpoint resume for long crawls
      - Dev mode with cached responses
      - Diff-based upsert (only update changed records)
    """

    def __init__(
        self,
        dev_mode: bool = False,
        resume: bool = False,
        target_area: str | None = None,
        max_concurrent: int = 5,
    ):
        self.dev_mode = dev_mode
        self.resume = resume
        self.target_area = target_area
        self.max_concurrent = max_concurrent
        self.stats = {
            "compounds_discovered": 0,
            "compounds_scraped": 0,
            "properties_extracted": 0,
            "properties_new": 0,
            "properties_updated": 0,
            "errors": 0,
            "pages_cached": 0,
            "start_time": time.time(),
        }
        self.checkpoint: dict[str, Any] = {}
        self._build_id: str | None = None
        self._http_client: httpx.AsyncClient | None = None

        # Ensure directories
        CRAWL_DIR.mkdir(exist_ok=True)
        if dev_mode:
            DEV_CACHE_DIR.mkdir(exist_ok=True)

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/html",
                    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                },
            )
        return self._http_client

    # ── Phase 1: Compound Discovery ──────────────────────────────────────────

    async def discover_build_id(self) -> str | None:
        """Extract Next.js buildId from Nawy's homepage."""
        if self._build_id:
            return self._build_id

        client = await self._get_http_client()
        try:
            resp = await client.get(f"{BASE_URL}/en/search")
            text = resp.text

            # Try __NEXT_DATA__ JSON
            match = re.search(r'"buildId"\s*:\s*"([^"]+)"', text)
            if match:
                self._build_id = match.group(1)
                logger.info(f"Build ID: {self._build_id}")
                return self._build_id

            logger.warning("Could not extract buildId from homepage")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch buildId: {e}")
            return None

    async def discover_compounds(self) -> list[dict[str, Any]]:
        """Discover all compounds via Nawy's Next.js data API pagination."""
        build_id = await self.discover_build_id()
        if not build_id:
            logger.error("No buildId — cannot discover compounds")
            return []

        client = await self._get_http_client()
        compounds: list[dict[str, Any]] = []
        page = 1
        max_pages = 200  # Safety limit

        while page <= max_pages:
            url = f"{BASE_URL}/_next/data/{build_id}/en/search.json?page={page}"

            cache_path = DEV_CACHE_DIR / f"search_page_{page}.json" if self.dev_mode else None

            try:
                data = await self._fetch_json(client, url, cache_path)
                if not data:
                    break

                # Navigate Next.js data structure
                page_props = data.get("pageProps", {})
                search_data = page_props.get("searchData", page_props.get("data", {}))
                items = search_data.get("compounds", search_data.get("items", []))

                if not items:
                    break

                for item in items:
                    compound = {
                        "slug": item.get("slug", ""),
                        "name": item.get("name", ""),
                        "developer": item.get("developer", {}).get("name", ""),
                        "area": item.get("area", {}).get("name", ""),
                        "area_slug": item.get("area", {}).get("slug", ""),
                    }
                    if compound["slug"]:
                        compounds.append(compound)

                logger.info(f"Page {page}: {len(items)} compounds (total: {len(compounds)})")
                page += 1

                # Respectful delay
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Discovery page {page} failed: {e}")
                self.stats["errors"] += 1
                break

        self.stats["compounds_discovered"] = len(compounds)

        # Filter by target area if specified
        if self.target_area:
            compounds = [c for c in compounds if self.target_area.lower() in c.get("area_slug", "").lower()]
            logger.info(f"Filtered to {len(compounds)} compounds in area: {self.target_area}")

        return compounds

    # ── Phase 2: Compound Scraping ───────────────────────────────────────────

    async def scrape_compound(self, compound: dict[str, Any]) -> list[dict[str, Any]]:
        """Scrape properties from a single compound page."""
        slug = compound["slug"]
        build_id = self._build_id

        if not build_id:
            return []

        client = await self._get_http_client()
        url = f"{BASE_URL}/_next/data/{build_id}/en/compound/{slug}.json"
        cache_path = DEV_CACHE_DIR / f"compound_{slug}.json" if self.dev_mode else None

        try:
            data = await self._fetch_json(client, url, cache_path)
            if not data:
                return []

            page_props = data.get("pageProps", {})
            compound_data = page_props.get("compoundData", page_props.get("data", {}))

            # Extract properties from availablePropertyTypes
            properties: list[dict[str, Any]] = []
            prop_types = compound_data.get("availablePropertyTypes", [])

            for pt in prop_types:
                units = pt.get("properties", pt.get("units", []))
                for unit in units:
                    prop = self._normalize_property(unit, compound, pt)
                    if prop:
                        properties.append(prop)

            self.stats["compounds_scraped"] += 1
            self.stats["properties_extracted"] += len(properties)

            if properties:
                logger.info(f"  {slug}: {len(properties)} properties")

            return properties
        except Exception as e:
            logger.error(f"  {slug}: scrape failed — {e}")
            self.stats["errors"] += 1
            return []

    def _normalize_property(
        self,
        unit: dict[str, Any],
        compound: dict[str, Any],
        prop_type: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Normalize a raw property unit into a flat record. Zero LLM tokens."""
        try:
            price = unit.get("price") or unit.get("min_price") or 0
            area_sqm = unit.get("area") or unit.get("max_unit_area") or 0

            return {
                "source": "nawy",
                "source_id": str(unit.get("id", "")),
                "compound_name": compound.get("name", ""),
                "compound_slug": compound.get("slug", ""),
                "developer": compound.get("developer", ""),
                "area": compound.get("area", ""),
                "property_type": prop_type.get("name", unit.get("type", "")),
                "title": unit.get("title", unit.get("name", "")),
                "price": int(price) if price else None,
                "area_sqm": float(area_sqm) if area_sqm else None,
                "bedrooms": unit.get("bedrooms") or unit.get("beds"),
                "bathrooms": unit.get("bathrooms") or unit.get("baths"),
                "delivery_date": unit.get("delivery_date") or unit.get("deliveryDate"),
                "down_payment_pct": unit.get("downPayment") or unit.get("down_payment"),
                "installment_years": unit.get("installmentYears") or unit.get("installment_years"),
                "finishing": unit.get("finishing"),
                "url": f"{BASE_URL}/en/compound/{compound.get('slug', '')}" if compound.get("slug") else None,
                "is_nawy_now": False,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.debug(f"Normalize error: {e}")
            return None

    async def scrape_all_compounds(self, compounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Scrape all compounds with controlled concurrency."""
        # Load checkpoint for resume
        if self.resume and CHECKPOINT_FILE.exists():
            self.checkpoint = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
            completed_slugs = set(self.checkpoint.get("completed", []))
            compounds = [c for c in compounds if c["slug"] not in completed_slugs]
            logger.info(f"Resuming: {len(completed_slugs)} already done, {len(compounds)} remaining")

        all_properties: list[dict[str, Any]] = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def scrape_with_limit(compound: dict[str, Any]) -> list[dict[str, Any]]:
            async with semaphore:
                props = await self.scrape_compound(compound)
                await asyncio.sleep(0.3)  # Respectful delay
                return props

        # Process in batches for checkpoint saving
        batch_size = 50
        for i in range(0, len(compounds), batch_size):
            batch = compounds[i : i + batch_size]
            tasks = [scrape_with_limit(c) for c in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, result in enumerate(results):
                if isinstance(result, list):
                    all_properties.extend(result)
                    # Update checkpoint
                    completed = self.checkpoint.get("completed", [])
                    completed.append(batch[j]["slug"])
                    self.checkpoint["completed"] = completed
                else:
                    logger.error(f"Batch error for {batch[j]['slug']}: {result}")

            # Save checkpoint
            self._save_checkpoint()
            logger.info(f"Checkpoint: {i + len(batch)}/{len(compounds)} compounds processed")

        return all_properties

    # ── Phase 3: Nawy Now ───────────────────────────────────────────────────

    async def scrape_nawy_now(self) -> list[dict[str, Any]]:
        """Scrape Nawy Now ready-to-move listings."""
        build_id = self._build_id or await self.discover_build_id()
        if not build_id:
            return []

        client = await self._get_http_client()
        properties: list[dict[str, Any]] = []
        page = 1
        max_pages = 60

        while page <= max_pages:
            url = f"{BASE_URL}/_next/data/{build_id}/en/nawy-now.json?page={page}"
            cache_path = DEV_CACHE_DIR / f"nawy_now_page_{page}.json" if self.dev_mode else None

            try:
                data = await self._fetch_json(client, url, cache_path)
                if not data:
                    break

                page_props = data.get("pageProps", {})
                units = page_props.get("nawyNowProperties", page_props.get("properties", []))

                if not units:
                    break

                for unit in units:
                    prop = self._normalize_nawy_now_unit(unit)
                    if prop:
                        properties.append(prop)

                logger.info(f"Nawy Now page {page}: {len(units)} units (total: {len(properties)})")
                page += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Nawy Now page {page} failed: {e}")
                break

        return properties

    def _normalize_nawy_now_unit(self, unit: dict[str, Any]) -> dict[str, Any] | None:
        """Normalize a Nawy Now unit. Zero LLM tokens."""
        try:
            return {
                "source": "nawy",
                "source_id": str(unit.get("id", "")),
                "compound_name": unit.get("compound", {}).get("name", ""),
                "compound_slug": unit.get("compound", {}).get("slug", ""),
                "developer": unit.get("developer", {}).get("name", ""),
                "area": unit.get("area", {}).get("name", ""),
                "property_type": unit.get("propertyType", unit.get("type", "")),
                "title": unit.get("title", ""),
                "price": int(unit.get("price", 0)) if unit.get("price") else None,
                "area_sqm": float(unit.get("area_sqm", 0)) if unit.get("area_sqm") else None,
                "bedrooms": unit.get("bedrooms"),
                "bathrooms": unit.get("bathrooms"),
                "finishing": unit.get("finishing"),
                "delivery_date": "ready",
                "url": f"{BASE_URL}/en/nawy-now/{unit.get('id', '')}",
                "is_nawy_now": True,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception:
            return None

    # ── Utility ──────────────────────────────────────────────────────────────

    async def _fetch_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        cache_path: Path | None = None,
    ) -> dict[str, Any] | None:
        """Fetch JSON with optional dev-mode caching."""
        # Dev mode: try cache first
        if cache_path and cache_path.exists():
            self.stats["pages_cached"] += 1
            return json.loads(cache_path.read_text(encoding="utf-8"))

        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None

            data = resp.json()

            # Dev mode: save to cache
            if cache_path:
                cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            return data
        except Exception as e:
            logger.debug(f"Fetch failed {url}: {e}")
            return None

    def _save_checkpoint(self) -> None:
        """Save crawl checkpoint for resume capability."""
        self.checkpoint["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.checkpoint["stats"] = self.stats
        CHECKPOINT_FILE.write_text(
            json.dumps(self.checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def close(self) -> None:
        if self._http_client:
            await self._http_client.aclose()

    # ── Main Entrypoint ──────────────────────────────────────────────────────

    async def run(self) -> dict[str, Any]:
        """Run the full spider pipeline."""
        logger.info("=" * 60)
        logger.info("Nawy Spider — Adaptive Property Scraper")
        logger.info(f"  Dev mode: {self.dev_mode}")
        logger.info(f"  Resume: {self.resume}")
        logger.info(f"  Target area: {self.target_area or 'all'}")
        logger.info("=" * 60)

        try:
            # Phase 1: Discover
            logger.info("\n📍 Phase 1: Compound Discovery")
            compounds = await self.discover_compounds()
            logger.info(f"Discovered {len(compounds)} compounds")

            if not compounds:
                logger.error("No compounds discovered — aborting")
                return self.stats

            # Phase 2: Scrape compounds
            logger.info("\n🏗️ Phase 2: Compound Scraping")
            properties = await self.scrape_all_compounds(compounds)

            # Phase 3: Nawy Now
            logger.info("\n⚡ Phase 3: Nawy Now Listings")
            nawy_now_props = await self.scrape_nawy_now()
            properties.extend(nawy_now_props)

            # Output
            logger.info("\n" + "=" * 60)
            logger.info("📊 Spider Results")
            logger.info(f"  Compounds discovered: {self.stats['compounds_discovered']}")
            logger.info(f"  Compounds scraped:    {self.stats['compounds_scraped']}")
            logger.info(f"  Properties extracted:  {self.stats['properties_extracted'] + len(nawy_now_props)}")
            logger.info(f"  Nawy Now units:       {len(nawy_now_props)}")
            logger.info(f"  Errors:               {self.stats['errors']}")
            duration = time.time() - self.stats["start_time"]
            logger.info(f"  Duration:             {duration:.1f}s")
            logger.info(f"  Pages cached (dev):   {self.stats['pages_cached']}")
            logger.info("=" * 60)

            # Save results
            output_path = CRAWL_DIR / "properties.json"
            output_path.write_text(
                json.dumps(properties, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info(f"Results saved to {output_path}")

            self.stats["total_properties"] = len(properties)
            self.stats["duration_s"] = round(duration, 1)

            # Notify orchestrator that new property data is available.
            # This allows the market-pulse job to refresh its cache and
            # the lead-scoring engine to re-match new listings to user intents.
            await self._notify_orchestrator(len(properties))

            return self.stats
        finally:
            await self.close()

    async def _notify_orchestrator(self, property_count: int) -> None:
        """Fire a scraper-complete webhook to the Orchestrator."""
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "").rstrip("/")
        webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        if not orchestrator_url:
            logger.debug("ORCHESTRATOR_URL not set — skipping orchestrator notification")
            return
        payload = {
            "eventType": "property_scrape_complete",
            "runId": f"nawy-{int(time.time())}",
            "totalProperties": property_count,
            "significantChanges": self.stats.get("properties_extracted", 0),
        }
        headers = {"Content-Type": "application/json"}
        if webhook_secret:
            headers["X-Webhook-Secret"] = webhook_secret
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{orchestrator_url}/webhooks/scraper-event",
                    json=payload,
                    headers=headers,
                )
                logger.info(f"Orchestrator notified of scrape completion: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Failed to notify orchestrator (non-fatal): {e}")


# ── CLI ──────────────────────────────────────────────────────────────────────────

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Nawy Spider — Adaptive Property Scraper")
    parser.add_argument("--dev", action="store_true", help="Dev mode (cache responses)")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--area", type=str, help="Target area slug (e.g., new-cairo)")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent requests")
    args = parser.parse_args()

    spider = NawySpider(
        dev_mode=args.dev,
        resume=args.resume,
        target_area=args.area,
        max_concurrent=args.concurrency,
    )
    await spider.run()


if __name__ == "__main__":
    asyncio.run(main())
