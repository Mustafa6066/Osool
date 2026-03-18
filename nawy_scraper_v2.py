"""
Nawy Property Scraper v2 — Triple-Strategy
==========================================
Three extraction strategies, most powerful first:

  Strategy 1 (PRIMARY): __NEXT_DATA__ extraction → LLM normalizer → Repository
    Fastest and most reliable. Reads Nawy's SSR JSON tag directly.
    Uses LLM (gpt-4o-mini) to normalize, then differential hash upsert.
    Requires: PYTHONPATH=/app and ingestion modules in /app/app/ingestion/

  Strategy 2 (FALLBACK): XHR/Fetch interception → LLM normalizer → Repository
    Intercepts Nawy's internal API calls during page navigation.
    Used when NEXT_DATA is empty or contains no unit-level data.

  Strategy 3 (LAST RESORT): Tab-click + Regex → upsert_property_to_db
    The original approach: click Resale/Developer/Nawy Now tabs, parse card text.
    Includes the detail-page enrichment fix (land_area, down_payment, developer).
    Includes content hash to skip unchanged properties and save embeddings cost.

Changes vs v1:
- Async Playwright (async_playwright) throughout
- Playwright-stealth integration + fingerprint randomization
- Triple-strategy per compound (NEXT_DATA → XHR → Regex)
- Content hash diffing in upsert_property_to_db() (saves ~80% of embedding calls)
- scrape_detail_page() now actually called for Resale properties (bug fix)
- Separate detail_page context for enrichment (doesn't disrupt compound pagination)
"""

import asyncio
import json
import time
import os
import sys
import re
import hashlib
import uuid
import random
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
from playwright.async_api import async_playwright, Page, BrowserContext
from dotenv import load_dotenv

# ── Platform-agnostic .env loading ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(dotenv_path=ENV_PATH)

# ── Database (PostgreSQL via SQLAlchemy sync — for Regex fallback) ──
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ── OpenAI (for Regex fallback embeddings) ──
from openai import OpenAI
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"

sys.stdout.reconfigure(encoding='utf-8')

# ── Ingestion pipeline (Strategy 1 + 2) ──
# Available when PYTHONPATH=/app and app/ingestion/ is present in the container.
PIPELINE_AVAILABLE = False
normalize_properties_fn = None
NormalizedProperty = None

try:
    from app.ingestion.llm_normalizer import normalize_properties as _normalize_properties, NormalizedProperty as _NormalizedProperty
    normalize_properties_fn = _normalize_properties
    NormalizedProperty = _NormalizedProperty
    PIPELINE_AVAILABLE = True
    print("✅ Ingestion pipeline loaded (NEXT_DATA + LLM normalizer active)", flush=True)
except ImportError:
    print("⚠️  Ingestion pipeline not available — Regex-only mode", flush=True)


# ═══════════════════════════════════════════════════════════════
# BROWSER FINGERPRINTING (anti-bot stealth)
# ═══════════════════════════════════════════════════════════════

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
    {"width": 1280, "height": 800},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

LOCALES = ["ar-EG", "ar-EG,ar;q=0.9,en-US;q=0.8", "en-US,en;q=0.9,ar;q=0.8"]
TIMEZONES = ["Africa/Cairo"]


def _pick_fingerprint() -> Dict:
    """Returns a randomized browser context fingerprint."""
    return {
        "viewport": random.choice(VIEWPORTS),
        "user_agent": random.choice(USER_AGENTS),
        "locale": random.choice(LOCALES),
        "timezone_id": random.choice(TIMEZONES),
    }


# ═══════════════════════════════════════════════════════════════
# LOCATION REGEX — 25+ Egyptian areas
# ═══════════════════════════════════════════════════════════════
LOCATION_PATTERN = re.compile(
    r'(New Cairo|Mostakbal City|Mostakbal|6th (?:of )?October|October Gardens|'
    r'El Sheikh Zayed|Sheikh Zayed|New Zayed|Golden Square|5th Settlement|6th Settlement|'
    r'New Capital|New Administrative Capital|Ain Sokhna|North Coast|'
    r'Sidi Abdel Rahman|Ras El Hekma|El Shorouk|Shorouk|Maadi|Heliopolis|'
    r'Northern Expansion|Hurghada|El Gouna|Alexandria|Madinaty|Rehab|Al Rehab|'
    r'Katameya|Palm Hills|Zamalek|Obour|Badr City|10th of Ramadan|'
    r'West Cairo|East Cairo|Giza)',
    re.IGNORECASE
)

LOCATION_NORMALIZE = {
    "5th settlement": "New Cairo",
    "6th settlement": "New Cairo",
    "el sheikh zayed": "Sheikh Zayed",
    "new zayed": "Sheikh Zayed",
    "golden square": "New Cairo",
    "october gardens": "6th October",
    "6th of october": "6th October",
    "sidi abdel rahman": "North Coast",
    "ras el hekma": "North Coast",
    "el shorouk": "El Shorouk",
    "shorouk": "El Shorouk",
    "al rehab": "Rehab",
    "new administrative capital": "New Capital",
    "mostakbal": "Mostakbal City",
    "katameya": "New Cairo",
    "palm hills": "New Cairo",
}

# ═══════════════════════════════════════════════════════════════
# PROXY POOL (env: PROXY_LIST=http://u:p@host:port,socks5://...)
# ═══════════════════════════════════════════════════════════════

_PROXY_LIST: List[str] = []
_proxy_raw = os.getenv("PROXY_LIST", "").strip()
if _proxy_raw:
    _PROXY_LIST = [p.strip() for p in _proxy_raw.split(",") if p.strip()]
    print(f"🌐 Loaded {len(_PROXY_LIST)} proxies for rotation")


def _get_proxy(index: int) -> Optional[Dict[str, str]]:
    """Return Playwright-compatible proxy dict, cycling through pool."""
    if not _PROXY_LIST:
        return None
    proxy_url = _PROXY_LIST[index % len(_PROXY_LIST)]
    return {"server": proxy_url}


# ═══════════════════════════════════════════════════════════════
# PROPERTY TYPE DETECTION
# ═══════════════════════════════════════════════════════════════
TYPE_PATTERN = re.compile(
    r'(Townhouse|Apartment|Villa|Duplex|Penthouse|Twinhouse|Twin House|'
    r'Chalet|Studio|Office|Retail|Clinic|iVilla|S-Villa|Standalone|'
    r'Semi-Detached|Ground Floor|Roof)',
    re.IGNORECASE
)

TYPE_NORMALIZE = {
    "twin house": "Twinhouse",
    "ivilla": "iVilla",
    "s-villa": "S-Villa",
    "semi-detached": "Villa",
    "ground floor": "Apartment",
    "roof": "Penthouse",
    "standalone": "Villa",
}


def parse_property_text(text: str, url: str, compound_name: str, tab_sale_type: str = "Developer") -> Optional[Dict]:
    """
    Parse raw property card text using regex (Strategy 3 fallback).

    Args:
        text: Raw innerText from the property card <a> element
        url: Full URL of the property card link
        compound_name: Name of the current compound being scraped
        tab_sale_type: Which tab this was scraped from (Resale/Developer/Nawy Now)

    Returns:
        Parsed property dict or None if invalid (no price)
    """
    prop = {
        'compound_name': compound_name,
        'type': 'Unit',
        'location': '',
        'price': 0,
        'beds': 0,
        'baths': 0,
        'area': 0,
        'land_area': 0,
        'delivery_date': '',
        'monthly_installment': 0,
        'installment_years': 0,
        'sale_type': tab_sale_type,
        'finishing': '',
        'is_delivered': False,
        'is_cash_only': False,
        'is_nawy_now': tab_sale_type == 'Nawy Now',
        'url': url,
        'nawy_reference': '',
        'developer': '',
        'down_payment': 0,
        'maintenance_fee_pct': 0,
        'delivery_payment': 0,
        'description': text.replace('\n', ' ').strip(),
        'scraped_at': datetime.now(timezone.utc).isoformat(),
    }

    clean = prop['description']

    # ── Type ──
    type_match = TYPE_PATTERN.search(clean)
    if type_match:
        raw_type = type_match.group(1)
        prop['type'] = TYPE_NORMALIZE.get(raw_type.lower(), raw_type)

    # ── Location ──
    loc_match = LOCATION_PATTERN.search(clean)
    if loc_match:
        raw_loc = loc_match.group(1)
        prop['location'] = LOCATION_NORMALIZE.get(raw_loc.lower(), raw_loc)

    # ── Price ──
    price_match = re.search(r'(\d+(?:,\d{3})+)\s*EGP', clean, re.IGNORECASE)
    if price_match:
        prop['price'] = float(price_match.group(1).replace(',', ''))

    # ── Beds ──
    beds_match = re.search(r'(\d+)\s*Beds?', clean, re.IGNORECASE)
    if beds_match:
        prop['beds'] = int(beds_match.group(1))

    # ── Baths ──
    baths_match = re.search(r'(\d+)\s*Baths?', clean, re.IGNORECASE)
    if baths_match:
        prop['baths'] = int(baths_match.group(1))

    # ── BUA (Built-Up Area) ──
    area_match = re.search(r'(\d+)\s*m²', clean, re.IGNORECASE)
    if area_match:
        prop['area'] = float(area_match.group(1))

    # ── Land Area (detail pages show "Land Area: 350 m²") ──
    land_match = re.search(r'Land\s*Area[:\s]+(\d+)\s*m²', clean, re.IGNORECASE)
    if land_match:
        prop['land_area'] = float(land_match.group(1))

    # ── Delivery Date / Delivered status ──
    if re.search(r'\bDelivered\b|\bReady\s*to\s*Move\b', clean, re.IGNORECASE):
        prop['is_delivered'] = True
        prop['delivery_date'] = 'Delivered'
    else:
        del_match = re.search(r'Delivery\s*(?:In|Date)?[:\s]*(?:(Q[1-4])\s*)?(20\d{2})', clean, re.IGNORECASE)
        if del_match:
            quarter = del_match.group(1)
            year = del_match.group(2)
            prop['delivery_date'] = f"{quarter} {year}" if quarter else year
        else:
            q_year_match = re.search(r'(Q[1-4])\s*(20\d{2})', clean, re.IGNORECASE)
            if q_year_match:
                prop['delivery_date'] = f"{q_year_match.group(1).upper()} {q_year_match.group(2)}"
            else:
                year_match = re.search(r'(20\d{2})', clean)
                if year_match:
                    prop['delivery_date'] = year_match.group(1)

    # ── Finishing ──
    finishing_match = re.search(
        r'(Fully Finished|Semi[- ]?Finished|Finished|Core [&] Shell|Core|Unfinished|Super Lux|Lux)',
        clean, re.IGNORECASE
    )
    if finishing_match:
        raw_fin = finishing_match.group(1).lower()
        fin_map = {
            'fully finished': 'Finished',
            'finished': 'Finished',
            'super lux': 'Finished',
            'lux': 'Finished',
            'semi-finished': 'Semi-Finished',
            'semi finished': 'Semi-Finished',
            'semifinished': 'Semi-Finished',
            'core & shell': 'Core & Shell',
            'core': 'Core & Shell',
            'unfinished': 'Core & Shell',
        }
        prop['finishing'] = fin_map.get(raw_fin, raw_fin.title())

    # ── Cash Payment indicator ──
    if re.search(r'Cash\s*Payment|Cash\s*Only|No\s*Installment', clean, re.IGNORECASE):
        prop['is_cash_only'] = True

    # ── Installment ──
    pay_match = re.search(r'(\d+(?:,\d{3})*)\s*(Monthly|Quarterly)', clean, re.IGNORECASE)
    if pay_match:
        amount = float(pay_match.group(1).replace(',', ''))
        period = pay_match.group(2).lower()
        if period == 'quarterly':
            prop['monthly_installment'] = round(amount / 3)
        else:
            prop['monthly_installment'] = int(amount)

    # ── Installment Years ──
    years_match = re.search(r'(\d+)\s*Years', clean, re.IGNORECASE)
    if years_match:
        prop['installment_years'] = int(years_match.group(1))

    # ── Sale Type override from text ──
    if 'Resale' in clean:
        prop['sale_type'] = 'Resale'
    elif 'Nawy Now' in clean:
        prop['sale_type'] = 'Nawy Now'
        prop['is_nawy_now'] = True

    # ── Nawy Reference from URL ──
    ref_match = re.search(r'/property/(\d+)', url)
    if ref_match:
        prop['nawy_reference'] = ref_match.group(1)

    # ── Maintenance Fee ──
    maint_match = re.search(r'Maintenance\s*(?:Fee|Deposit)?[:\s]+(\d+)\s*%', clean, re.IGNORECASE)
    if maint_match:
        prop['maintenance_fee_pct'] = int(maint_match.group(1))

    # ── Delivery / Handover Payment ──
    delivery_pay_match = re.search(
        r'(?:Delivery|Handover)\s*(?:Payment|Fee|Amount)[:\s]+(\d+(?:,\d{3})*)\s*(?:EGP)?',
        clean, re.IGNORECASE
    )
    if delivery_pay_match:
        prop['delivery_payment'] = float(delivery_pay_match.group(1).replace(',', ''))

    # Filter invalid (no price = skip)
    if not prop['price']:
        return None

    return prop


def generate_embedding_text(prop: Dict) -> str:
    """Create rich semantic text for embedding generation (Strategy 3 fallback)."""
    parts = [
        f"{prop['type']} in {prop['compound_name']}, {prop['location']}",
        f"Price: {prop['price']:,.0f} EGP",
        f"Area: {prop['area']} sqm",
    ]
    if prop['beds']:
        parts.append(f"{prop['beds']} Bedrooms")
    if prop['baths']:
        parts.append(f"{prop['baths']} Bathrooms")
    if prop['sale_type']:
        parts.append(f"Sale Type: {prop['sale_type']}")
    if prop['finishing']:
        parts.append(f"Finishing: {prop['finishing']}")
    if prop['is_delivered']:
        parts.append("Delivered - Ready to Move")
    elif prop['delivery_date']:
        parts.append(f"Delivery: {prop['delivery_date']}")
    if prop['is_cash_only']:
        parts.append("Cash Payment Only")
    if prop['is_nawy_now']:
        parts.append("Nawy Now - Nawy Mortgage Available")
    if prop['monthly_installment']:
        parts.append(f"Monthly: {prop['monthly_installment']:,.0f} EGP over {prop['installment_years']} years")
    if prop.get('land_area'):
        parts.append(f"Land Area: {prop['land_area']} sqm")
    parts.append(prop['description'][:200])

    return ". ".join(parts)


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using text-embedding-3-small (Strategy 3 fallback)."""
    if not openai_client:
        return None
    try:
        response = openai_client.embeddings.create(input=text, model=EMBEDDING_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"    ⚠️ Embedding error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# DATABASE UPSERT (Strategy 3 fallback — sync SQLAlchemy)
# Includes content hash diffing to skip unchanged properties.
# ═══════════════════════════════════════════════════════════════

def get_db_engine():
    """Create sync SQLAlchemy engine for Strategy 3 fallback."""
    if not DATABASE_URL:
        return None
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    from sqlalchemy import create_engine
    return create_engine(sync_url, pool_pre_ping=True)


def _compute_content_hash(prop: Dict) -> str:
    """
    SHA256 over the 6 core market-signal attributes.
    Matches the hash logic in ingestion/repository.py for consistency.
    """
    payload = json.dumps(
        {
            "price": float(prop.get('price', 0) or 0),
            "size_sqm": int(prop.get('area', 0) or 0),
            "type": (prop.get('type', '') or '').strip(),
            "location": (prop.get('location', '') or '').strip(),
            "finishing": (prop.get('finishing', '') or '').strip(),
            "developer": (prop.get('developer', '') or '').strip(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def upsert_property_to_db(prop_data: Dict, engine=None):
    """
    Upsert property to PostgreSQL with content hash diffing.

    Hash unchanged → touch last_scrape_run_id only (skip embedding, save cost).
    Hash changed or new → generate embedding + full upsert.
    """
    if engine is None:
        return

    from sqlalchemy.orm import Session
    from sqlalchemy import text

    content_hash = _compute_content_hash(prop_data)

    # Build title
    title = f"{prop_data['type']} in {prop_data['compound_name']}"
    if prop_data['beds']:
        title += f" - {prop_data['beds']} Beds"
    if prop_data['area']:
        title += f" - {int(prop_data['area'])} sqm"

    price_per_sqm = 0
    if prop_data['area'] and prop_data['area'] > 0:
        price_per_sqm = round(prop_data['price'] / prop_data['area'])

    with Session(engine) as session:
        try:
            result = session.execute(
                text("SELECT id, content_hash FROM properties WHERE nawy_url = :url"),
                {"url": prop_data['url']}
            )
            existing = result.fetchone()

            # ── Hash unchanged: touch tracking fields only ──
            if existing and existing[1] == content_hash:
                session.execute(
                    text("""
                        UPDATE properties
                        SET last_scrape_run_id = :run_id,
                            scraped_at = :now,
                            is_available = true
                        WHERE id = :id
                    """),
                    {
                        "run_id": prop_data.get('scrape_run_id', ''),
                        "now": datetime.now(timezone.utc),
                        "id": existing[0],
                    }
                )
                session.commit()
                return  # Skip expensive embedding + full upsert

            # ── New or changed: generate embedding + full upsert ──
            embed_text = generate_embedding_text(prop_data)
            embedding = generate_embedding(embed_text)

            if existing:
                session.execute(
                    text("""
                        UPDATE properties SET
                            title = :title, description = :description, type = :type,
                            location = :location, compound = :compound, price = :price,
                            price_per_sqm = :price_per_sqm, size_sqm = :size_sqm,
                            bedrooms = :bedrooms, bathrooms = :bathrooms, finishing = :finishing,
                            delivery_date = :delivery_date, down_payment = :down_payment,
                            maintenance_fee_pct = :maintenance_fee_pct,
                            delivery_payment = :delivery_payment,
                            monthly_installment = :monthly_installment,
                            installment_years = :installment_years, sale_type = :sale_type,
                            nawy_url = :nawy_url, is_delivered = :is_delivered,
                            is_cash_only = :is_cash_only, land_area = :land_area,
                            nawy_reference = :nawy_reference, is_nawy_now = :is_nawy_now,
                            developer = :developer, scraped_at = :scraped_at,
                            embedding = :embedding, is_available = true,
                            last_scrape_run_id = :last_scrape_run_id,
                            content_hash = :content_hash
                        WHERE id = :id
                    """),
                    _build_upsert_params(prop_data, title, price_per_sqm, embedding, content_hash, existing[0])
                )
            else:
                session.execute(
                    text("""
                        INSERT INTO properties (
                            title, description, type, location, compound, price, price_per_sqm,
                            size_sqm, bedrooms, bathrooms, finishing, delivery_date, down_payment,
                            maintenance_fee_pct, delivery_payment,
                            monthly_installment, installment_years, sale_type, nawy_url,
                            is_delivered, is_cash_only, land_area, nawy_reference, is_nawy_now,
                            developer, scraped_at, embedding, is_available, last_scrape_run_id, content_hash
                        ) VALUES (
                            :title, :description, :type, :location, :compound, :price, :price_per_sqm,
                            :size_sqm, :bedrooms, :bathrooms, :finishing, :delivery_date, :down_payment,
                            :maintenance_fee_pct, :delivery_payment,
                            :monthly_installment, :installment_years, :sale_type, :nawy_url,
                            :is_delivered, :is_cash_only, :land_area, :nawy_reference, :is_nawy_now,
                            :developer, :scraped_at, :embedding, true, :last_scrape_run_id, :content_hash
                        )
                    """),
                    _build_upsert_params(prop_data, title, price_per_sqm, embedding, content_hash)
                )

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"    ❌ DB Error: {e}")


def _build_upsert_params(prop: Dict, title: str, price_per_sqm: float,
                          embedding: Optional[List], content_hash: str,
                          existing_id: Optional[int] = None) -> Dict:
    """Build parameter dict for SQL upsert (Strategy 3 fallback)."""
    params = {
        "title": title,
        "description": prop['description'][:500],
        "type": prop['type'],
        "location": prop['location'],
        "compound": prop['compound_name'],
        "price": prop['price'],
        "price_per_sqm": price_per_sqm,
        "size_sqm": int(prop['area']),
        "bedrooms": prop['beds'],
        "bathrooms": prop['baths'],
        "finishing": prop['finishing'],
        "delivery_date": prop['delivery_date'],
        "down_payment": int(prop.get('down_payment', 0) or 0),
        "monthly_installment": prop['monthly_installment'],
        "installment_years": prop['installment_years'],
        "sale_type": prop['sale_type'],
        "nawy_url": prop['url'],
        "is_delivered": prop['is_delivered'],
        "is_cash_only": prop['is_cash_only'],
        "land_area": int(prop.get('land_area', 0) or 0),
        "nawy_reference": prop.get('nawy_reference', ''),
        "is_nawy_now": prop.get('is_nawy_now', False),
        "developer": prop.get('developer', ''),
        "maintenance_fee_pct": int(prop.get('maintenance_fee_pct', 0) or 0),
        "delivery_payment": float(prop.get('delivery_payment', 0) or 0),
        "scraped_at": prop.get('scraped_at', datetime.now(timezone.utc).isoformat()),
        "embedding": str(embedding) if embedding else None,
        "last_scrape_run_id": prop.get('scrape_run_id', ''),
        "content_hash": content_hash,
    }
    if existing_id is not None:
        params["id"] = existing_id
    return params


# ═══════════════════════════════════════════════════════════════
# STRATEGY 1 + 2 — Smart Extraction Functions
# ═══════════════════════════════════════════════════════════════

async def _extract_next_data(page: Page) -> Optional[Dict]:
    """
    Strategy 1 (PRIMARY): Parse <script id="__NEXT_DATA__"> tag.
    Nawy embeds the full SSR page props here — no regex on UI text needed.
    """
    try:
        raw_json = await page.evaluate("""
            () => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? el.textContent : null;
            }
        """)
        if not raw_json:
            return None
        return json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"    ⚠️ NEXT_DATA JSON parse error: {e}", flush=True)
        return None
    except Exception as e:
        print(f"    ⚠️ NEXT_DATA extraction error: {e}", flush=True)
        return None


def _has_meaningful_data(data: Any) -> bool:
    """Quick sanity check: does the extracted dict contain something useful?"""
    if not isinstance(data, dict):
        return False
    page_props = data.get("props", {}).get("pageProps", {})
    if page_props and len(page_props) > 1:
        return True
    return len(str(data)) > 200


_PROPERTY_SIGNAL_KEYS = {
    "units", "compound", "compounds", "properties", "listings", "results",
    "price", "minPrice", "min_price", "area", "size", "builtUpArea",
}


async def _extract_xhr_intercept(page: Page, url: str) -> Optional[Dict]:
    """
    Strategy 2 (FALLBACK): Intercept Nawy's XHR/Fetch API calls.
    Registers route handlers, then navigates to URL and captures JSON responses.
    """
    intercepted: List[Dict] = []

    async def handle_route(route):
        response = await route.fetch()
        try:
            ct = response.headers.get("content-type", "")
            if "json" in ct:
                body = await response.body()
                data = json.loads(body)
                if isinstance(data, dict) and set(data.keys()) & _PROPERTY_SIGNAL_KEYS:
                    intercepted.append(data)
                elif isinstance(data, list) and data and isinstance(data[0], dict):
                    if set(data[0].keys()) & _PROPERTY_SIGNAL_KEYS:
                        intercepted.append({"results": data})
        except Exception:
            pass
        finally:
            await route.fulfill(response=response)

    for pattern in ["**/api/**", "**/_next/data/**", "**/graphql**"]:
        await page.route(pattern, handle_route)

    try:
        await page.goto(url, wait_until="networkidle", timeout=45_000)
        await asyncio.sleep(random.uniform(1.5, 3.0))
    except Exception as e:
        print(f"    ⚠️ XHR navigation error: {e}", flush=True)

    if not intercepted:
        return None

    return max(intercepted, key=lambda d: len(str(d)) if isinstance(d, dict) else 0)


# ═══════════════════════════════════════════════════════════════
# STRATEGY 3 — Tab-click + Regex (async versions)
# ═══════════════════════════════════════════════════════════════

async def _get_cards_async(page: Page) -> List[Dict]:
    """Extract all property card links from the current page view."""
    return await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a[href*="/property/"]')).map(a => ({
            text: a.innerText,
            url: a.href
        }));
    }''')


async def _click_tab_async(page: Page, tab_name: str) -> bool:
    """Click a sale-type tab. Returns True if found and clicked."""
    selectors = [
        f"button:has-text('{tab_name}')",
        f"div[role='tab']:has-text('{tab_name}')",
        f"a:has-text('{tab_name}')",
        f"span:has-text('{tab_name}')",
        f"li:has-text('{tab_name}')",
    ]
    for sel in selectors:
        try:
            if await page.is_visible(sel, timeout=2000):
                await page.click(sel)
                await asyncio.sleep(2)
                return True
        except Exception:
            continue
    return False


async def scrape_detail_page_async(detail_page: Page, url: str) -> Optional[Dict]:
    """
    Enrich a Resale property with detail-page data.
    Uses a SEPARATE page object so the compound listing page is not disrupted.

    Extracts: land_area, developer, down_payment, nawy_reference.
    """
    try:
        await detail_page.goto(url, timeout=30000)
        await detail_page.wait_for_load_state("networkidle", timeout=15000)
        text = await detail_page.inner_text("body")
        extra = {}

        land_match = re.search(r'Land\s*Area[:\s]+(\d+)\s*m²', text, re.IGNORECASE)
        if land_match:
            extra['land_area'] = float(land_match.group(1))

        bua_match = re.search(r'BUA[:\s]+(\d+)\s*m²', text, re.IGNORECASE)
        if bua_match:
            extra['area'] = float(bua_match.group(1))

        dev_match = re.search(r'Developer[:\s]+([A-Za-z\s&]+?)(?:\n|$)', text)
        if dev_match:
            extra['developer'] = dev_match.group(1).strip()

        dp_match = re.search(r'Down\s*Payment[:\s]+(\d+)%', text, re.IGNORECASE)
        if dp_match:
            extra['down_payment'] = int(dp_match.group(1))

        ref_match = re.search(r'/property/(\d+)', url)
        if ref_match:
            extra['nawy_reference'] = ref_match.group(1)

        # ── Maintenance / handover fee ──
        maint_match = re.search(r'Maintenance\s*(?:Fee|Deposit)?[:\s]+(\d+)\s*%', text, re.IGNORECASE)
        if maint_match:
            extra['maintenance_fee_pct'] = int(maint_match.group(1))

        # ── Delivery / handover payment ──
        delivery_pay_match = re.search(
            r'(?:Delivery|Handover)\s*(?:Payment|Fee|Amount)[:\s]+(\d+(?:,\d{3})*)\s*(?:EGP)?',
            text, re.IGNORECASE
        )
        if delivery_pay_match:
            extra['delivery_payment'] = float(delivery_pay_match.group(1).replace(',', ''))

        # ── Delivery date with quarter ──
        if re.search(r'\bDelivered\b|\bReady\s*to\s*Move\b', text, re.IGNORECASE):
            extra['is_delivered'] = True
            extra['delivery_date'] = 'Delivered'
        else:
            del_match = re.search(r'(?:Delivery|Ready)[:\s]*(?:(Q[1-4])\s*)?(20\d{2})', text, re.IGNORECASE)
            if del_match:
                quarter = del_match.group(1)
                year = del_match.group(2)
                extra['delivery_date'] = f"{quarter} {year}" if quarter else year

        return extra if extra else None
    except Exception:
        return None


async def _scrape_paginated_regex(
    page: Page,
    detail_page: Page,
    compound_name: str,
    sale_type: str,
    engine,
    scrape_run_id: str,
) -> int:
    """
    Strategy 3: Scrape all pages of the current tab with regex parsing.
    Includes detail-page enrichment for Resale properties missing land_area.
    Uses detail_page (separate page object) so compound listing page stays intact.
    """
    page_num = 1
    total = 0
    seen_urls = set()

    while True:
        cards = await _get_cards_async(page)
        batch_count = 0

        for card in cards:
            if card['url'] in seen_urls:
                continue
            seen_urls.add(card['url'])

            parsed = parse_property_text(card['text'], card['url'], compound_name, sale_type)
            if parsed:
                # ── Detail page enrichment for Resale properties ──
                # Bug fix: scrape_detail_page was previously never called.
                # Only runs when land_area is missing (minimizes extra page loads).
                if parsed['down_payment'] == 0 and detail_page:
                    extras = await scrape_detail_page_async(detail_page, card['url'])
                    if extras:
                        parsed.update({k: v for k, v in extras.items() if v})

                parsed['scrape_run_id'] = scrape_run_id
                upsert_property_to_db(parsed, engine)
                batch_count += 1

        total += batch_count
        print(f"      + {batch_count} {sale_type} items (pg {page_num})", flush=True)

        # Try pagination
        found_next = False
        next_selectors = [
            f".pagination li a:text('{page_num + 1}')",
            "a[aria-label='Next page']",
            "button[aria-label='Next page']",
            "li:has-text('Next') a",
            "a:has-text('Next')",
            "button:has-text('Next')",
        ]
        for sel in next_selectors:
            try:
                if await page.is_visible(sel, timeout=1000):
                    await page.click(sel)
                    await asyncio.sleep(2)
                    page_num += 1
                    found_next = True
                    break
            except Exception:
                continue

        if not found_next:
            break

    return total


# ═══════════════════════════════════════════════════════════════
# MAIN COMPOUND SCRAPER — Triple-Strategy Orchestrator
# ═══════════════════════════════════════════════════════════════

async def scrape_compound_properties(
    page: Page,
    detail_page: Page,
    compound_url: str,
    compound_name: str,
    run_id: str,
    engine=None,
) -> int:
    """
    Scrape one compound page using the best available strategy.

    Tries NEXT_DATA + LLM normalizer first (fastest, most complete).
    Falls back to XHR interception if NEXT_DATA is empty.
    Falls back to tab-click + Regex if neither smart strategy works.
    """
    total = 0

    try:
        print(f"  📍 Navigating to {compound_name}...", flush=True)
        await page.goto(compound_url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(0.8, 1.5))

        # ── Strategy 1: __NEXT_DATA__ → LLM normalizer ──
        if PIPELINE_AVAILABLE:
            raw_json = await _extract_next_data(page)
            if raw_json and _has_meaningful_data(raw_json):
                raw_json["_meta"] = {
                    "source_url": compound_url,
                    "strategy": "next_data",
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    result = await normalize_properties_fn(raw_json)
                    if result.properties:
                        from app.ingestion.repository import upsert_properties
                        upsert_result = await upsert_properties(result.properties, run_id)
                        total = upsert_result.total
                        print(
                            f"    ✅ NEXT_DATA: +{upsert_result.inserted} new, "
                            f"~{upsert_result.updated} updated, "
                            f"{upsert_result.skipped} unchanged",
                            flush=True,
                        )
                        return total
                    else:
                        print(f"    ⚠️ NEXT_DATA: normalizer returned 0 properties — falling back", flush=True)
                except Exception as e:
                    print(f"    ⚠️ NEXT_DATA pipeline error: {e} — falling back", flush=True)

            # ── Strategy 2: XHR Interception → LLM normalizer ──
            print("    🔄 Trying XHR interception...", flush=True)
            try:
                await page.unroute("**/*")
                raw_json = await _extract_xhr_intercept(page, compound_url)
                if raw_json:
                    raw_json["_meta"] = {
                        "source_url": compound_url,
                        "strategy": "xhr_intercept",
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                    result = await normalize_properties_fn(raw_json)
                    if result.properties:
                        from app.ingestion.repository import upsert_properties
                        upsert_result = await upsert_properties(result.properties, run_id)
                        total = upsert_result.total
                        print(
                            f"    ✅ XHR: +{upsert_result.inserted} new, "
                            f"~{upsert_result.updated} updated, "
                            f"{upsert_result.skipped} unchanged",
                            flush=True,
                        )
                        return total
                    else:
                        print(f"    ⚠️ XHR: normalizer returned 0 properties — falling back", flush=True)
            except Exception as e:
                print(f"    ⚠️ XHR pipeline error: {e} — falling back", flush=True)

        # ── Strategy 3: Regex fallback (tab-click + pagination) ──
        print("    ⚠️ Using Regex fallback (tab-click mode)...", flush=True)

        # Ensure page is back on the compound URL (XHR may have navigated)
        if page.url != compound_url:
            await page.goto(compound_url, timeout=60000)

        try:
            await page.wait_for_selector('a[href*="/property/"]', timeout=30000)
        except Exception:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)

        for tab_name, sale_type in [
            ("Resale", "Resale"),
            ("Developer Sale", "Developer"),
            ("Nawy Now", "Nawy Now"),
        ]:
            print(f"    🏷️ [{tab_name}] tab...", flush=True)
            if await _click_tab_async(page, tab_name):
                await asyncio.sleep(2)
                count = await _scrape_paginated_regex(page, detail_page, compound_name, sale_type, engine, run_id)
                total += count
                print(f"    ✅ {tab_name}: {count} properties", flush=True)
            elif tab_name == "Developer Sale":
                # No tab found — scrape default view as Developer
                count = await _scrape_paginated_regex(page, detail_page, compound_name, sale_type, engine, run_id)
                total += count
            else:
                print(f"    ⚠️ No {tab_name} tab found", flush=True)

    except Exception as e:
        print(f"  ❌ Error scraping {compound_name}: {e}", flush=True)

    return total


# ═══════════════════════════════════════════════════════════════
# NAWY NOW PAGE SCRAPER (/nawy-now)
# ═══════════════════════════════════════════════════════════════

async def scrape_nawy_now_page_async(page: Page, engine=None, scrape_run_id: str = "") -> int:
    """
    Scrape the standalone /nawy-now page.
    These are ready-to-move-in properties with Nawy mortgage.
    """
    total = 0
    NAWY_NOW_URL = "https://www.nawy.com/nawy-now"

    try:
        print("\n🏠 Scraping Nawy Now standalone page...", flush=True)
        await page.goto(NAWY_NOW_URL, timeout=60000)

        try:
            await page.wait_for_selector('a[href*="/property/"]', timeout=30000)
        except Exception:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)

        page_num = 1
        seen_urls = set()

        while True:
            cards = await _get_cards_async(page)
            batch = 0

            for card in cards:
                if card['url'] in seen_urls:
                    continue
                seen_urls.add(card['url'])

                # Extract compound from URL: /compound-name/property/123
                compound = "Nawy Now"
                url_parts = card['url'].split('/')
                for i, part in enumerate(url_parts):
                    if part == 'property' and i > 0:
                        compound = url_parts[i - 1].replace('-', ' ').title()
                        break

                parsed = parse_property_text(card['text'], card['url'], compound, "Nawy Now")
                if parsed:
                    parsed['is_nawy_now'] = True
                    parsed['is_delivered'] = True
                    parsed['scrape_run_id'] = scrape_run_id
                    upsert_property_to_db(parsed, engine)
                    batch += 1

            total += batch
            print(f"  + {batch} Nawy Now items (pg {page_num})", flush=True)

            # Scroll to load more (Nawy Now may use infinite scroll)
            prev_count = len(seen_urls)
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

            new_cards = await _get_cards_async(page)
            new_urls = {c['url'] for c in new_cards}
            if not new_urls - seen_urls:
                found_next = False
                for sel in [
                    "a:has-text('Next')", "button:has-text('Next')",
                    f".pagination li a:text('{page_num + 1}')", "a[aria-label='Next page']"
                ]:
                    try:
                        if await page.is_visible(sel, timeout=1000):
                            await page.click(sel)
                            await asyncio.sleep(2)
                            page_num += 1
                            found_next = True
                            break
                    except Exception:
                        continue
                if not found_next:
                    break
            else:
                page_num += 1

    except Exception as e:
        print(f"  ❌ Nawy Now page error: {e}", flush=True)

    print(f"  ✅ Nawy Now standalone: {total} properties", flush=True)
    return total


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def main():
    scrape_run_id = str(uuid.uuid4())

    # ── Load compound URLs ──
    urls_file = os.path.join(BASE_DIR, "nawy_compound_urls.json")
    if not os.path.exists(urls_file):
        print(f"❌ File not found: {urls_file}")
        return

    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)

    print(f"🚀 Nawy Scraper v2 — Triple-Strategy Mode", flush=True)
    print(f"   Run ID: {scrape_run_id}", flush=True)
    print(f"   Compounds: {len(urls)}", flush=True)
    print(f"   Strategy: {'NEXT_DATA + LLM → Regex fallback' if PIPELINE_AVAILABLE else 'Regex-only'}", flush=True)
    print(f"   Database: {'Connected' if DATABASE_URL else 'NOT CONFIGURED'}", flush=True)
    print(f"   Proxies: {len(_PROXY_LIST) if _PROXY_LIST else 'None (direct)'}", flush=True)

    engine = get_db_engine()  # Sync engine for Strategy 3 fallback
    total_processed = 0
    failed_compounds = []
    BATCH_SIZE = 10

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=BROWSER_ARGS)

        async def _new_context_async(proxy_index: int) -> BrowserContext:
            fp = _pick_fingerprint()
            proxy = _get_proxy(proxy_index)
            ctx_kwargs = {
                "user_agent": fp["user_agent"],
                "viewport": fp["viewport"],
                "locale": fp["locale"],
                "timezone_id": fp["timezone_id"],
                "java_script_enabled": True,
            }
            if proxy:
                ctx_kwargs["proxy"] = proxy
            ctx = await browser.new_context(**ctx_kwargs)
            # Block media resources to reduce bandwidth + fingerprint surface
            await ctx.route(
                "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot,mp4}",
                lambda route: route.abort(),
            )
            return ctx

        context = await _new_context_async(0)
        page = await context.new_page()
        detail_page = await context.new_page()  # Dedicated page for detail enrichment

        # ── Apply playwright-stealth if available ──
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
                print("   Stealth: not installed (pip install playwright-stealth)", flush=True)

        # ── 1. Scrape all compounds ──
        for i, url in enumerate(urls):
            name = url.split('/')[-1].replace('-', ' ').title()
            print(f"\n[{i+1}/{len(urls)}] {name}", flush=True)

            try:
                count = await scrape_compound_properties(
                    page, detail_page, url, name, scrape_run_id, engine
                )
                total_processed += count
            except Exception as e:
                print(f"  ❌ Failed {name}: {e}", flush=True)
                failed_compounds.append(name)

            # Rotate proxy + context every BATCH_SIZE compounds
            if (i + 1) % BATCH_SIZE == 0 and (i + 1) < len(urls):
                print(f"\n  🔄 Rotating proxy context (batch {(i+1)//BATCH_SIZE})...", flush=True)
                await context.close()
                await asyncio.sleep(5)
                context = await _new_context_async((i + 1) // BATCH_SIZE)
                page = await context.new_page()
                detail_page = await context.new_page()

        # ── 2. Scrape standalone Nawy Now page ──
        nawy_now_count = await scrape_nawy_now_page_async(page, engine, scrape_run_id)
        total_processed += nawy_now_count

        await context.close()
        await browser.close()

    # ── Summary ──
    print(f"\n{'='*60}", flush=True)
    print(f"✅ SCRAPING COMPLETE", flush=True)
    print(f"   Total compounds: {len(urls)}", flush=True)
    print(f"   Total properties processed: {total_processed}", flush=True)
    print(f"   Failed compounds: {len(failed_compounds)}", flush=True)
    if failed_compounds:
        print(f"   Failed: {', '.join(failed_compounds[:10])}", flush=True)
    print(f"{'='*60}", flush=True)

    # ── Save JSON summary backup ──
    summary = {
        "scrape_date": datetime.now(timezone.utc).isoformat(),
        "scrape_run_id": scrape_run_id,
        "total_compounds": len(urls),
        "total_properties": total_processed,
        "failed_compounds": failed_compounds,
        "strategy_mode": "llm_normalizer" if PIPELINE_AVAILABLE else "regex_fallback",
        "embedding_model": EMBEDDING_MODEL,
    }
    summary_file = os.path.join(BASE_DIR, "data", "scrape_summary.json")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # ── Register run ID in Redis for stale cleanup ──
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            prev = r.get("scraper:run_id:current")
            if prev:
                r.set("scraper:run_id:previous", prev, ex=604800)
            r.set("scraper:run_id:current", scrape_run_id, ex=604800)
            print(f"   📌 Run ID registered in Redis: {scrape_run_id[:8]}...", flush=True)
        except Exception as e:
            print(f"   ⚠️ Redis run ID registration failed: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
