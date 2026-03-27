"""
Nawy Property Scraper v3 — Full Discovery + Zero Token
=======================================================

Three phases, no AI API calls, no hardcoded URL lists:

  Phase 1: Compound Discovery (pure HTTP — no browser)
    - Fetches buildId from Nawy's NEXT_DATA
    - Paginates https://www.nawy.com/_next/data/{buildId}/en/search.json?page=N
    - Discovers ALL ~1700 compounds automatically
    - Falls back to area-page link scraping if the data API fails

  Phase 2: Compound Scraping (Playwright)
    - For each compound slug: navigate, extract __NEXT_DATA__
    - Reads availablePropertyTypes[*].properties[] — all units pre-loaded server-side
    - Injects compound-level context (name, developer, area, payment plans)
    - Deterministic normalize → differential hash upsert (0 tokens)

  Phase 3: Nawy Now (HTTP pagination + Playwright for page 1)
    - Paginates /nawy-now pages via _next/data API (603 units, 51 pages)
    - Also collects nawyNowFeatured units from NEXT_DATA
    - Normalizes with is_nawy_now=True flag
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import httpx
from dotenv import load_dotenv
from playwright.async_api import BrowserContext, Page, async_playwright

# ── Platform-agnostic .env loading ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(dotenv_path=ENV_PATH)

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("nawy_scraper_v3")

# ── Ingestion pipeline ──
PIPELINE_AVAILABLE = False
normalize_properties_fn = None
normalize_unit_list_fn = None
NormalizedProperty = None

try:
    from app.ingestion.deterministic_normalizer import (
        NormalizedProperty as _NP,
        normalize_properties as _np_fn,
        normalize_unit_list as _nul_fn,
    )
    normalize_properties_fn = _np_fn
    normalize_unit_list_fn = _nul_fn
    NormalizedProperty = _NP
    PIPELINE_AVAILABLE = True
    print("✅ Deterministic normalizer loaded (0 tokens)", flush=True)
except ImportError as e:
    print(f"⚠️  Ingestion pipeline not available: {e}", flush=True)

# ── Database (sync — Strategy 3 fallback) ──
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS & BROWSER FINGERPRINTING
# ═══════════════════════════════════════════════════════════════

BASE_URL = "https://www.nawy.com"
SEARCH_URL = f"{BASE_URL}/search"
NAWY_NOW_URL = f"{BASE_URL}/nawy-now"

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-infobars",
    "--window-size=1920,1080",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 2560, "height": 1440},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

LOCALES = ["ar-EG", "ar-EG,ar;q=0.9,en-US;q=0.8", "en-US,en;q=0.9,ar;q=0.8"]
TIMEZONES = ["Africa/Cairo"]

_PROXY_LIST: List[str] = []
_proxy_raw = os.getenv("PROXY_LIST", "").strip()
if _proxy_raw:
    _PROXY_LIST = [p.strip() for p in _proxy_raw.split(",") if p.strip()]


def _pick_fingerprint() -> Dict:
    return {
        "viewport": random.choice(VIEWPORTS),
        "user_agent": random.choice(USER_AGENTS),
        "locale": random.choice(LOCALES),
        "timezone_id": TIMEZONES[0],
    }


def _get_proxy(index: int) -> Optional[Dict[str, str]]:
    if not _PROXY_LIST:
        return None
    return {"server": _PROXY_LIST[index % len(_PROXY_LIST)]}


# ═══════════════════════════════════════════════════════════════
# PHASE 1 — COMPOUND DISCOVERY (pure HTTP, no browser)
# ═══════════════════════════════════════════════════════════════

AREA_SLUGS = [
    "new-cairo", "new-capital-city", "6th-of-october-city", "el-sheikh-zayed",
    "mostakbal-city", "ain-sokhna", "north-coast", "ras-el-hekma",
    "new-zayed", "october-gardens", "northern-expansion", "obour",
    "badr-city", "heliopolis", "maadi", "new-heliopolis",
]


async def _get_build_id_via_http() -> Optional[str]:
    """Fetch Nawy buildId from the search page NEXT_DATA (HTTP only)."""
    try:
        async with httpx.AsyncClient(timeout=30, headers={"User-Agent": USER_AGENTS[0]}) as client:
            resp = await client.get(SEARCH_URL, follow_redirects=True)
            if resp.status_code == 200:
                # Extract buildId from the embedded NEXT_DATA JSON
                import re
                m = re.search(r'"buildId"\s*:\s*"([^"]+)"', resp.text)
                if m:
                    return m.group(1)
    except Exception as e:
        logger.warning("HTTP buildId fetch failed: %s", e)
    return None


async def discover_compounds_via_api(page: Page) -> List[str]:
    """
    Phase 1a: Use Nawy's Next.js data API to discover ALL compound slugs.
    - Navigates once (browser) to get buildId
    - Then pages through search results via httpx (fast, no browser)
    Returns list of compound slugs like ["38-hyde-park", "145-palm-hills", ...]
    """
    print("\n🔍 Phase 1: Discovering all compounds...", flush=True)

    # Get buildId + page 1 data via browser
    await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=45000)
    await asyncio.sleep(random.uniform(1, 2))

    page1_data = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        if (!el) return null;
        const d = JSON.parse(el.textContent);
        const ssr = d.props?.pageProps?.loadedSearchResultsSSR || {};
        return {
            buildId: d.buildId,
            total: ssr.total || 0,
            pageSize: ssr.pageSize || 12,
            slugs: (ssr.results || []).map(r => r.slug).filter(Boolean),
        };
    }""")

    if not page1_data or not page1_data.get("buildId"):
        print("  ⚠️ Could not get buildId from browser, trying HTTP...", flush=True)
        build_id = await _get_build_id_via_http()
        if not build_id:
            return await discover_compounds_via_area_pages(page)
        total = 1800
        page_size = 12
        all_slugs: Set[str] = set()
    else:
        build_id = page1_data["buildId"]
        total = page1_data["total"]
        page_size = page1_data["pageSize"] or 12
        all_slugs = set(page1_data["slugs"])

    total_pages = (total + page_size - 1) // page_size
    print(f"  buildId: {build_id[:12]}... | {total} compounds | {total_pages} pages", flush=True)

    # Paginate pages 2..N via httpx (no browser)
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "application/json",
        "Referer": BASE_URL,
    }
    async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
        for pg in range(2, total_pages + 1):
            url = f"{BASE_URL}/_next/data/{build_id}/en/search.json?page={pg}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    ssr = data.get("pageProps", {}).get("loadedSearchResultsSSR", {})
                    for r in ssr.get("results", []):
                        if r.get("slug"):
                            all_slugs.add(r["slug"])
                elif resp.status_code == 404:
                    # buildId stale — stop pagination
                    logger.warning("Data API 404 at page %d — buildId may be stale", pg)
                    break

                if pg % 25 == 0:
                    print(f"  Discovery: page {pg}/{total_pages} | {len(all_slugs)} compounds found", flush=True)

                await asyncio.sleep(0.08)  # gentle rate limit
            except Exception as e:
                logger.warning("Discovery page %d failed: %s", pg, e)

    slugs = sorted(all_slugs)
    print(f"  ✅ Discovered {len(slugs)} compounds", flush=True)
    return slugs


async def discover_compounds_via_area_pages(page: Page) -> List[str]:
    """
    Phase 1b: Fallback — scrape compound links from each area page.
    Used when the _next/data API is unavailable (buildId stale).
    """
    print("  🔄 Falling back to area-page discovery...", flush=True)
    all_slugs: Set[str] = set()

    for area_slug in AREA_SLUGS:
        try:
            await page.goto(f"{BASE_URL}/area/{area_slug}", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            # Scroll to load all compound cards
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.8)

            slugs = await page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href*="/compound/"]'));
                return links.map(a => {
                    const m = a.href.match(/\\/compound\\/([^/?#]+)/);
                    return m ? m[1] : null;
                }).filter(Boolean);
            }""")
            all_slugs.update(slugs)
            print(f"    {area_slug}: {len(slugs)} compounds (total: {len(all_slugs)})", flush=True)
        except Exception as e:
            logger.warning("Area page %s failed: %s", area_slug, e)

    # Also scrape the main search page
    try:
        await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
        slugs = await page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href*="/compound/"]'));
            return links.map(a => {
                const m = a.href.match(/\\/compound\\/([^/?#]+)/);
                return m ? m[1] : null;
            }).filter(Boolean);
        }""")
        all_slugs.update(slugs)
    except Exception as e:
        logger.warning("Search page fallback failed: %s", e)

    slugs = sorted(all_slugs)
    print(f"  ✅ Fallback discovered {len(slugs)} compounds", flush=True)
    return slugs


# ═══════════════════════════════════════════════════════════════
# PHASE 2 — COMPOUND SCRAPING (Playwright + NEXT_DATA)
# ═══════════════════════════════════════════════════════════════

async def scrape_compound(
    page: Page,
    slug: str,
    run_id: str,
) -> int:
    """
    Scrape one compound page.
    Extracts all units from __NEXT_DATA__ availablePropertyTypes[*].properties[].
    Returns number of properties upserted.
    """
    url = f"{BASE_URL}/compound/{slug}"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(random.uniform(0.6, 1.4))

        raw_json_str = await page.evaluate("""() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? el.textContent : null;
        }""")

        if not raw_json_str:
            print(f"    ⚠️ No NEXT_DATA for {slug}", flush=True)
            return 0

        next_data = json.loads(raw_json_str)
        pp = next_data.get("props", {}).get("pageProps", {})

        # Count available units
        apt = pp.get("availablePropertyTypes", [])
        total_units = sum(len(g.get("properties", [])) for g in apt)

        if total_units == 0:
            print(f"    ⚠️ 0 units in NEXT_DATA for {slug}", flush=True)
            return 0

        next_data["_meta"] = {
            "source_url": url,
            "strategy": "next_data_v3",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

        result = await normalize_properties_fn(next_data)

        if not result.properties:
            print(f"    ⚠️ Normalizer returned 0 for {slug} ({total_units} raw)", flush=True)
            return 0

        from app.ingestion.repository import upsert_properties
        upsert_result = await upsert_properties(result.properties, run_id)
        print(
            f"    ✅ +{upsert_result.inserted} new, ~{upsert_result.updated} updated, "
            f"{upsert_result.skipped} unchanged | {total_units} units loaded",
            flush=True,
        )
        return upsert_result.total

    except Exception as e:
        print(f"    ❌ {slug}: {e}", flush=True)
        return 0


# ═══════════════════════════════════════════════════════════════
# PHASE 3 — NAWY NOW (HTTP pagination)
# ═══════════════════════════════════════════════════════════════

async def scrape_nawy_now(page: Page, run_id: str) -> int:
    """
    Phase 3: Collect ALL Nawy Now listings via HTTP pagination.
    Returns number of properties upserted.
    """
    if not PIPELINE_AVAILABLE:
        print("  ⚠️ Pipeline not available — skipping Nawy Now", flush=True)
        return 0

    print("\n🏠 Phase 3: Scraping Nawy Now...", flush=True)

    # Load page 1 via Playwright to get buildId + initial data
    await page.goto(NAWY_NOW_URL, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(random.uniform(0.8, 1.5))

    page1 = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        if (!el) return null;
        const d = JSON.parse(el.textContent);
        const pp = d.props?.pageProps || {};
        const ssr = pp.loadedSearchResultsSSR || {};
        return {
            buildId: d.buildId,
            total: ssr.total || 0,
            pageSize: ssr.pageSize || 12,
            results: ssr.results || [],
            featured: pp.nawyNowFeatured || [],
        };
    }""")

    if not page1:
        print("  ❌ Could not load Nawy Now page", flush=True)
        return 0

    build_id = page1["buildId"]
    total = page1["total"]
    page_size = page1["pageSize"] or 12
    total_pages = (total + page_size - 1) // page_size

    print(f"  {total} Nawy Now units | {total_pages} pages", flush=True)

    all_units: List[dict] = list(page1["results"])

    # Add featured (may overlap with results — deduped by URL in upsert)
    for feat in page1.get("featured", []):
        all_units.append(feat)

    # Paginate pages 2..N via httpx
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "application/json",
        "Referer": BASE_URL,
    }
    async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
        for pg in range(2, total_pages + 1):
            url = f"{BASE_URL}/_next/data/{build_id}/en/nawy-now.json?page={pg}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    ssr = data.get("pageProps", {}).get("loadedSearchResultsSSR", {})
                    all_units.extend(ssr.get("results", []))
                elif resp.status_code == 404:
                    logger.warning("Nawy Now data API 404 at page %d — buildId stale", pg)
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning("Nawy Now page %d failed: %s", pg, e)

    print(f"  Normalizing {len(all_units)} Nawy Now units...", flush=True)

    result = normalize_unit_list_fn(all_units, source_url=NAWY_NOW_URL)

    if not result.properties:
        print("  ⚠️ No Nawy Now properties normalized", flush=True)
        return 0

    from app.ingestion.repository import upsert_properties
    upsert_result = await upsert_properties(result.properties, run_id)
    print(
        f"  ✅ Nawy Now: +{upsert_result.inserted} new, ~{upsert_result.updated} updated, "
        f"{upsert_result.skipped} unchanged",
        flush=True,
    )
    return upsert_result.total


# ═══════════════════════════════════════════════════════════════
# BROWSER CONTEXT FACTORY
# ═══════════════════════════════════════════════════════════════

async def _new_context(browser, proxy_index: int) -> BrowserContext:
    fp = _pick_fingerprint()
    proxy = _get_proxy(proxy_index)
    kwargs = {
        "user_agent": fp["user_agent"],
        "viewport": fp["viewport"],
        "locale": fp["locale"],
        "timezone_id": fp["timezone_id"],
        "java_script_enabled": True,
    }
    if proxy:
        kwargs["proxy"] = proxy
    ctx = await browser.new_context(**kwargs)
    # Block media to reduce bandwidth
    await ctx.route(
        "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot,mp4,webm}",
        lambda route: route.abort(),
    )
    return ctx


async def _apply_stealth(page: Page) -> None:
    try:
        from playwright_stealth import Stealth
        await Stealth().apply_stealth_async(page)
        print("   Stealth: playwright-stealth v2 active", flush=True)
    except (ImportError, AttributeError):
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
            print("   Stealth: playwright-stealth v1 active", flush=True)
        except ImportError:
            print("   Stealth: not installed", flush=True)


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def main() -> None:
    run_id = str(uuid.uuid4())
    start_time = time.time()

    print("🚀 Nawy Scraper v3 — Full Discovery Mode", flush=True)
    print(f"   Run ID: {run_id}", flush=True)
    print(f"   Pipeline: {'deterministic (0 tokens)' if PIPELINE_AVAILABLE else 'unavailable'}", flush=True)
    print(f"   Database: {'configured' if DATABASE_URL else 'NOT CONFIGURED'}", flush=True)
    print(f"   Proxies: {len(_PROXY_LIST) or 'none (direct)'}", flush=True)

    total_processed = 0
    failed_compounds: List[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)
        context = await _new_context(browser, 0)
        page = await context.new_page()
        await _apply_stealth(page)

        # ── Phase 1: Discover all compounds ──
        compound_slugs = await discover_compounds_via_api(page)

        if not compound_slugs:
            print("❌ No compounds discovered — aborting", flush=True)
            await browser.close()
            return

        print(f"\n🏗️  Phase 2: Scraping {len(compound_slugs)} compounds...", flush=True)

        BATCH_SIZE = 10  # Rotate context every N compounds

        for i, slug in enumerate(compound_slugs):
            name = slug.split("-", 1)[-1].replace("-", " ").title() if "-" in slug else slug
            print(f"\n[{i+1}/{len(compound_slugs)}] {name} ({slug})", flush=True)

            if PIPELINE_AVAILABLE:
                count = await scrape_compound(page, slug, run_id)
                total_processed += count
                if count == 0:
                    failed_compounds.append(slug)
            else:
                print("   ⚠️ Pipeline not available — skipping", flush=True)
                failed_compounds.append(slug)

            # Rotate browser context every BATCH_SIZE compounds
            if (i + 1) % BATCH_SIZE == 0 and (i + 1) < len(compound_slugs):
                print(f"\n  🔄 Rotating context (batch {(i+1)//BATCH_SIZE})...", flush=True)
                await context.close()
                await asyncio.sleep(random.uniform(3, 6))
                context = await _new_context(browser, (i + 1) // BATCH_SIZE)
                page = await context.new_page()
                await _apply_stealth(page)

        # ── Phase 3: Nawy Now ──
        nawy_now_count = await scrape_nawy_now(page, run_id)
        total_processed += nawy_now_count

        await context.close()
        await browser.close()

    elapsed = time.time() - start_time

    # ── Summary ──
    print(f"\n{'='*60}", flush=True)
    print(f"✅ SCRAPING COMPLETE", flush=True)
    print(f"   Compounds scraped: {len(compound_slugs)}", flush=True)
    print(f"   Properties processed: {total_processed}", flush=True)
    print(f"   Failed compounds: {len(failed_compounds)}", flush=True)
    print(f"   Elapsed: {elapsed/60:.1f} min", flush=True)
    if failed_compounds:
        print(f"   Failed (first 10): {failed_compounds[:10]}", flush=True)
    print(f"{'='*60}", flush=True)

    # ── Save summary ──
    summary = {
        "scrape_date": datetime.now(timezone.utc).isoformat(),
        "scrape_run_id": run_id,
        "total_compounds": len(compound_slugs),
        "total_properties": total_processed,
        "failed_count": len(failed_compounds),
        "failed_compounds": failed_compounds[:50],
        "elapsed_seconds": round(elapsed),
        "strategy_mode": "deterministic_v3",
    }
    summary_file = os.path.join(BASE_DIR, "data", "scrape_summary.json")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    # ── Redis run ID ──
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            prev = r.get("scraper:run_id:current")
            if prev:
                r.set("scraper:run_id:previous", prev, ex=604800)
            r.set("scraper:run_id:current", run_id, ex=604800)
            print(f"   📌 Run ID registered in Redis", flush=True)
        except Exception as e:
            print(f"   ⚠️ Redis registration failed: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
