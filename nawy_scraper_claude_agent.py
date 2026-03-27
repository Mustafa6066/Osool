"""
Nawy Agentic Scraper — Claude SDK + Playwright
================================================
An AI-first property scraper where Claude acts as the decision-making agent
and Playwright provides browser control tools.

Architecture:
  Claude (claude-haiku-4-5-20251001) receives a set of Playwright-based tools:
    - navigate      → page.goto()
    - screenshot    → page.screenshot() → base64 image for visual analysis
    - get_page_text → page.evaluate(document.body.innerText)
    - click_element → page.get_by_text() or page.locator()
    - scroll_down   → window.scrollBy()
    - extract_json  → Claude's structured output tool (terminal call)

  For each compound URL, Claude:
    1. Takes a screenshot to understand the layout
    2. Identifies and clicks property tabs (Resale, Developer, Nawy Now)
    3. Scrolls to load all cards
    4. Calls extract_json with structured property data

  Results are piped into the same ingestion pipeline as the v2 scraper:
    - Pydantic validation via NormalizedProperty
    - Content-hash deduplication
    - PostgreSQL upsert with pgvector embeddings

Usage:
    # Single compound
    python nawy_scraper_claude_agent.py --url https://www.nawy.com/compound/mivida

    # All compounds from nawy_compound_urls.json
    python nawy_scraper_claude_agent.py --all

    # Dry-run (no DB writes)
    python nawy_scraper_claude_agent.py --url <url> --dry-run
"""

from __future__ import annotations

import asyncio
import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, BrowserContext

# ── Load env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / "backend" / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Still needed for embeddings

if not ANTHROPIC_API_KEY:
    print("❌ ANTHROPIC_API_KEY not set", flush=True)
    sys.exit(1)

sys.stdout.reconfigure(encoding="utf-8")

# ── Ingestion pipeline (optional — skips if not available) ──────────────────
PIPELINE_AVAILABLE = False
normalize_properties_fn = None

try:
    sys.path.insert(0, str(BASE_DIR / "backend"))
    from app.ingestion.llm_normalizer import normalize_properties as _norm
    from app.ingestion.repository import upsert_properties as _upsert
    normalize_properties_fn = _norm
    upsert_properties_fn = _upsert
    PIPELINE_AVAILABLE = True
    print("✅ Ingestion pipeline loaded (Claude normalizer active)", flush=True)
except ImportError as e:
    print(f"⚠️  Ingestion pipeline not available: {e}", flush=True)
    upsert_properties_fn = None

# ── Status tracking ─────────────────────────────────────────────────────────
STATUS_PATH = Path(os.getenv("SCRAPE_STATUS_PATH", str(BASE_DIR / "data" / "scrape_status_agent.json")))

_status: dict[str, Any] = {
    "status": "idle",
    "started_at": None,
    "completed_at": None,
    "mode": "claude_agent",
    "total_compounds": 0,
    "processed_compounds": 0,
    "total_properties_found": 0,
    "total_upserted": 0,
    "errors": [],
}


def _write_status() -> None:
    try:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(json.dumps(_status, default=str), encoding="utf-8")
    except Exception as e:
        print(f"[status] write error: {e}", flush=True)


# ════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS FOR CLAUDE
# ════════════════════════════════════════════════════════════════════════════

PLAYWRIGHT_TOOLS = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a URL and wait for the page to load.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to navigate to"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "screenshot",
        "description": (
            "Take a screenshot of the current page. Returns the image as a base64-encoded JPEG "
            "so you can visually inspect the page layout and content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "full_page": {
                    "type": "boolean",
                    "description": "If true, captures the full scrollable page. Default false.",
                },
            },
        },
    },
    {
        "name": "get_page_text",
        "description": "Get all visible text content from the current page (up to 8000 chars).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "click_element",
        "description": (
            "Click an element identified by its visible text or CSS selector. "
            "Use text content for tab buttons like 'Resale', 'Developer', 'Nawy Now'. "
            "Falls back to CSS selector if text matching fails."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "Visible text OR CSS selector to click",
                },
            },
            "required": ["selector"],
        },
    },
    {
        "name": "scroll_down",
        "description": "Scroll the page down to reveal more content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pixels": {
                    "type": "integer",
                    "description": "How many pixels to scroll down. Default 800.",
                },
            },
        },
    },
    {
        "name": "extract_json",
        "description": (
            "FINAL STEP: Extract all property listings you have discovered and output them "
            "as a structured JSON array. Call this once you have explored all tabs and "
            "gathered all available data. Always call this even if no properties were found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "properties": {
                    "type": "array",
                    "description": "Array of property objects extracted from the page",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "price": {"type": "number", "description": "Price in EGP, 0 if unknown"},
                            "size_sqm": {"type": "integer", "description": "Built-up area in sqm"},
                            "bedrooms": {"type": "integer"},
                            "bathrooms": {"type": "integer"},
                            "type": {
                                "type": "string",
                                "enum": [
                                    "Apartment", "Villa", "Townhouse", "Studio", "Duplex",
                                    "Penthouse", "Chalet", "Office", "Retail", "Twin House",
                                    "Mixed Use", "Other",
                                ],
                            },
                            "finishing": {
                                "type": "string",
                                "enum": [
                                    "Core & Shell", "Semi-Finished", "Fully Finished",
                                    "Furnished", "Unknown",
                                ],
                            },
                            "location": {"type": "string", "description": "Egyptian area/zone name"},
                            "developer": {"type": "string"},
                            "compound": {"type": "string"},
                            "delivery_date": {"type": "string", "description": "e.g. 'Q2 2026' or 'Immediate'"},
                            "down_payment_pct": {"type": "number", "description": "Percentage 0-100"},
                            "installment_years": {"type": "integer"},
                            "monthly_installment": {"type": "number", "description": "Monthly payment in EGP"},
                            "sale_type": {
                                "type": "string",
                                "enum": ["Developer", "Resale", "Nawy Now"],
                            },
                            "source_url": {"type": "string"},
                        },
                        "required": ["title", "price", "sale_type"],
                    },
                },
                "tabs_visited": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Which tabs you clicked (e.g. ['Resale', 'Developer'])",
                },
            },
            "required": ["properties"],
        },
    },
]

SCRAPER_SYSTEM_PROMPT = """
You are an expert real estate data extraction agent for Nawy.com, Egypt's largest property platform.
Your job: scrape ALL property listings from a compound/project page.

STRATEGY:
1. Take a screenshot to understand the page layout
2. Look for property type tabs at the top of the listings section:
   - Tabs are usually labelled: "Resale", "Developer" (or "Developer Units"), "Nawy Now"
   - Click EACH tab to extract properties from all categories
3. For each tab:
   a. Take a screenshot to see the listings
   b. Scroll down 2-3 times to reveal all properties
   c. Use get_page_text to extract property details if screenshots aren't clear enough
4. Once you have explored all available tabs, call extract_json with EVERYTHING you found

DATA EXTRACTION RULES:
- Egyptian prices are in EGP. Format: "X,XXX,XXX EGP" or "XXX,XXX / month"
- If you see "Starting from X EGP", that is the minimum price
- Bedrooms: look for "BR", "Beds", "غرف" numbers
- Size: look for "sqm", "m²", "متر" values
- Delivery: look for years like "2026", "Q2 2027", or "Immediate"
- Down payment: look for "% down", "% مقدم"
- sale_type: "Resale" for resale tab, "Developer" for developer/new units, "Nawy Now" for instant

LOCATIONS (use exact canonical names):
New Cairo, Sheikh Zayed, 6th October, New Administrative Capital, North Coast,
Ain Sokhna, Mostakbal City, New Zayed, Madinaty, El Rehab, El Shorouk,
West Cairo, East Cairo, Hurghada, Alexandria, Zamalek, Maadi, Heliopolis

Always call extract_json at the end, even if 0 properties were found.
Be thorough — check ALL available tabs.
""".strip()


# ════════════════════════════════════════════════════════════════════════════
# PLAYWRIGHT TOOL EXECUTOR
# ════════════════════════════════════════════════════════════════════════════

async def _execute_tool(page: Page, tool_name: str, tool_input: dict[str, Any]) -> str:
    """Execute a Playwright action based on Claude's tool call."""

    if tool_name == "navigate":
        url = tool_input["url"]
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(2000)
            return f"Navigated to: {url}"
        except Exception as e:
            return f"Navigation error: {e}"

    elif tool_name == "screenshot":
        full_page = tool_input.get("full_page", False)
        try:
            screenshot_bytes = await page.screenshot(
                full_page=full_page, type="jpeg", quality=65
            )
            b64 = base64.standard_b64encode(screenshot_bytes).decode()
            # Return a JSON payload that the caller will convert to image content
            return json.dumps({"__type": "image", "media_type": "image/jpeg", "data": b64})
        except Exception as e:
            return f"Screenshot error: {e}"

    elif tool_name == "get_page_text":
        try:
            text: str = await page.evaluate("() => document.body.innerText")
            return text[:8000]
        except Exception as e:
            return f"get_page_text error: {e}"

    elif tool_name == "click_element":
        selector = tool_input.get("selector", "")
        try:
            await page.get_by_text(selector, exact=False).first.click(timeout=6000)
            await page.wait_for_timeout(1800)
            return f"Clicked: {selector!r}"
        except Exception:
            try:
                await page.locator(selector).first.click(timeout=6000)
                await page.wait_for_timeout(1800)
                return f"Clicked selector: {selector!r}"
            except Exception as e2:
                return f"Click failed for {selector!r}: {e2}"

    elif tool_name == "scroll_down":
        pixels = tool_input.get("pixels", 800)
        await page.evaluate(f"window.scrollBy(0, {int(pixels)})")
        await page.wait_for_timeout(600)
        return f"Scrolled {pixels}px"

    elif tool_name == "extract_json":
        # Handled in the agentic loop — just confirm receipt
        count = len(tool_input.get("properties", []))
        tabs = tool_input.get("tabs_visited", [])
        return f"Recorded {count} properties from tabs: {tabs}"

    return f"Unknown tool: {tool_name}"


def _make_image_tool_result(tool_use_id: str, b64_data: str, media_type: str) -> dict:
    """Build a tool_result with an embedded image for Claude's vision."""
    return {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64_data,
                },
            }
        ],
    }


# ════════════════════════════════════════════════════════════════════════════
# MAIN AGENTIC SCRAPING FUNCTION
# ════════════════════════════════════════════════════════════════════════════

async def scrape_compound_with_claude(
    page: Page,
    url: str,
    compound_name: str,
    client: anthropic.AsyncAnthropic,
    max_iterations: int = 14,
) -> list[dict]:
    """
    Claude acts as the agent. Given a compound URL and Playwright tools,
    Claude navigates, inspects, and extracts all property listings.

    Returns list of raw property dicts (before Pydantic normalization).
    """
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Scrape all property listings from this Nawy.com compound page:\n"
                f"URL: {url}\n"
                f"Compound name: {compound_name}\n\n"
                f"Start by navigating to the URL, take a screenshot, then extract everything."
            ),
        }
    ]

    extracted_properties: list[dict] = []

    for iteration in range(max_iterations):
        try:
            response = await client.messages.create(
                model=os.getenv("CLAUDE_HAIKU_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=4096,
                system=SCRAPER_SYSTEM_PROMPT,
                tools=PLAYWRIGHT_TOOLS,
                messages=messages,
            )
        except anthropic.APIError as e:
            print(f"    [Claude API error iter={iteration}]: {e}", flush=True)
            break

        stop_reason = response.stop_reason

        if stop_reason == "end_turn":
            print(f"    [Agent] Done after {iteration + 1} iterations", flush=True)
            break

        if stop_reason != "tool_use":
            print(f"    [Agent] Unexpected stop_reason={stop_reason}", flush=True)
            break

        # Process all tool calls in this response
        tool_results: list[dict] = []

        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_use_id = block.id

            print(f"    → [{iteration+1}] {tool_name}({json.dumps({k: v for k, v in tool_input.items() if k != 'properties'})[:80]})", flush=True)

            raw_result = await _execute_tool(page, tool_name, tool_input)

            # Capture extracted properties
            if tool_name == "extract_json":
                extracted_properties = tool_input.get("properties", [])
                for prop in extracted_properties:
                    prop.setdefault("compound", compound_name)
                    prop.setdefault("source_url", url)

            # Check if result is a screenshot image
            try:
                parsed = json.loads(raw_result)
                if isinstance(parsed, dict) and parsed.get("__type") == "image":
                    tool_results.append(
                        _make_image_tool_result(
                            tool_use_id,
                            parsed["data"],
                            parsed["media_type"],
                        )
                    )
                    continue
            except (json.JSONDecodeError, TypeError):
                pass

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": raw_result[:4000],
            })

        # Append assistant turn + tool results to conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # Stop early if extract_json was called
        if any(b.type == "tool_use" and b.name == "extract_json" for b in response.content):
            # One final Claude turn to acknowledge and end
            final_resp = await client.messages.create(
                model=os.getenv("CLAUDE_HAIKU_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=128,
                system=SCRAPER_SYSTEM_PROMPT,
                tools=PLAYWRIGHT_TOOLS,
                messages=messages,
            )
            break

    return extracted_properties


# ════════════════════════════════════════════════════════════════════════════
# BROWSER SETUP
# ════════════════════════════════════════════════════════════════════════════

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1440,900",
]


async def _create_context(playwright_instance) -> tuple:
    browser = await playwright_instance.chromium.launch(
        headless=True,
        args=BROWSER_ARGS,
    )
    context = await browser.new_context(
        viewport={"width": 1440, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        timezone_id="Africa/Cairo",
    )
    # Block heavy resources to speed up scraping
    await context.route(
        "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf}",
        lambda route: route.abort(),
    )
    page = await context.new_page()
    return browser, context, page


# ════════════════════════════════════════════════════════════════════════════
# INGEST RESULTS
# ════════════════════════════════════════════════════════════════════════════

async def _ingest_results(raw_properties: list[dict], dry_run: bool = False) -> int:
    """Normalize + upsert extracted properties. Returns count upserted."""
    if not raw_properties:
        return 0

    if dry_run:
        print(f"    [dry-run] Would ingest {len(raw_properties)} properties", flush=True)
        for p in raw_properties[:3]:
            print(f"      • {p.get('title', '?')} — {p.get('price', 0):,.0f} EGP — {p.get('type', '?')}", flush=True)
        return 0

    if not PIPELINE_AVAILABLE or normalize_properties_fn is None:
        print(f"    [no pipeline] Extracted {len(raw_properties)} properties (not ingested)", flush=True)
        return 0

    try:
        normalized = await normalize_properties_fn(raw_properties)
        if normalized:
            count = await upsert_properties_fn(normalized)
            return count
    except Exception as e:
        print(f"    [ingest error] {e}", flush=True)

    return 0


# ════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ════════════════════════════════════════════════════════════════════════════

async def run_single(url: str, dry_run: bool = False) -> None:
    compound_name = url.rstrip("/").split("/")[-1].replace("-", " ").title()
    print(f"\n🤖 Claude Agent scraping: {compound_name}", flush=True)
    print(f"   URL: {url}", flush=True)

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    async with async_playwright() as pw:
        browser, context, page = await _create_context(pw)
        try:
            t0 = time.monotonic()
            raw_props = await scrape_compound_with_claude(page, url, compound_name, client)
            elapsed = time.monotonic() - t0

            print(f"   ✅ Extracted {len(raw_props)} properties in {elapsed:.1f}s", flush=True)
            upserted = await _ingest_results(raw_props, dry_run=dry_run)
            if not dry_run:
                print(f"   💾 Upserted: {upserted}", flush=True)

        finally:
            await context.close()
            await browser.close()


async def run_all(dry_run: bool = False) -> None:
    urls_path = BASE_DIR / "nawy_compound_urls.json"
    if not urls_path.exists():
        print(f"❌ {urls_path} not found", flush=True)
        return

    with open(urls_path, encoding="utf-8") as f:
        data = json.load(f)

    # Normalise format: list of strings OR list of dicts with 'url' key
    compound_list: list[dict] = []
    for item in data:
        if isinstance(item, str):
            compound_list.append({"url": item, "name": item.split("/")[-1]})
        elif isinstance(item, dict):
            compound_list.append(item)

    _status.update({
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total_compounds": len(compound_list),
    })
    _write_status()

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    total_props = 0
    total_upserted = 0

    async with async_playwright() as pw:
        browser, context, page = await _create_context(pw)
        try:
            for idx, compound in enumerate(compound_list):
                url = compound.get("url", "")
                name = compound.get("name", url.split("/")[-1])

                print(f"\n[{idx+1}/{len(compound_list)}] 🤖 {name}", flush=True)

                try:
                    raw_props = await scrape_compound_with_claude(page, url, name, client)
                    total_props += len(raw_props)

                    upserted = await _ingest_results(raw_props, dry_run=dry_run)
                    total_upserted += upserted

                    _status["processed_compounds"] = idx + 1
                    _status["total_properties_found"] = total_props
                    _status["total_upserted"] = total_upserted
                    _write_status()

                except Exception as e:
                    err_msg = f"{name}: {e}"
                    print(f"   ❌ Error: {err_msg}", flush=True)
                    _status["errors"].append(err_msg)
                    _write_status()

                # Brief pause between compounds
                await asyncio.sleep(3)

        finally:
            await context.close()
            await browser.close()

    _status.update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    _write_status()
    print(f"\n✅ Done. {total_props} properties found, {total_upserted} upserted.", flush=True)


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Nawy Agentic Scraper (Claude + Playwright)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single compound URL to scrape")
    group.add_argument("--all", action="store_true", help="Scrape all compounds from nawy_compound_urls.json")
    parser.add_argument("--dry-run", action="store_true", help="Extract but do not write to database")
    args = parser.parse_args()

    if args.url:
        asyncio.run(run_single(args.url, dry_run=args.dry_run))
    else:
        asyncio.run(run_all(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
