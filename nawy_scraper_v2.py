"""
Nawy Property Scraper v2 — Resale + Developer + Nawy Now
=========================================================
Scrapes all three sale types from nawy.com compound pages:
  1. Resale (delivered/finished units, often cash-only)
  2. Developer Sale (payment plans, future delivery)
  3. Nawy Now (ready-to-move, Nawy mortgage up to 7 years)

Also scrapes the standalone /nawy-now page for additional inventory.

Changes vs v1:
- Platform-agnostic paths (no Windows hardcodes)
- Full compound list (not limited to 3)
- Explicit tab switching (Resale → Developer → Nawy Now)
- Resale field extraction (finishing, delivery status, cash indicator)
- Detail-page scraping for resale properties (land_area, images)
- Nawy Now page scraper (/nawy-now)
- Standardized embedding model (text-embedding-3-small)
- PostgreSQL direct upsert (async via SQLAlchemy)
"""

import json
import time
import os
import sys
import re
import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# ── Platform-agnostic .env loading ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(dotenv_path=ENV_PATH)

# ── Database (PostgreSQL via SQLAlchemy) ──
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Convert to asyncpg format
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ── OpenAI Embeddings (standardized on text-embedding-3-small) ──
from openai import OpenAI
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"

sys.stdout.reconfigure(encoding='utf-8')

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

# Normalize location names to canonical form
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
    print(f"\U0001f310 Loaded {len(_PROXY_LIST)} proxies for rotation")

def _get_proxy(index: int) -> Optional[Dict[str, str]]:
    """Return Playwright-compatible proxy dict for a given compound index, cycling through the pool."""
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
    Parse raw property card text using regex.
    
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
        del_match = re.search(r'Delivery\s*(?:In|Date)?[:\s]*(20\d{2})', clean, re.IGNORECASE)
        if del_match:
            prop['delivery_date'] = del_match.group(1)
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
    
    # ── Sale Type override from text (belt & suspenders) ──
    if 'Resale' in clean:
        prop['sale_type'] = 'Resale'
    elif 'Nawy Now' in clean:
        prop['sale_type'] = 'Nawy Now'
        prop['is_nawy_now'] = True
    
    # ── Nawy Reference from URL ──
    ref_match = re.search(r'/property/(\d+)', url)
    if ref_match:
        prop['nawy_reference'] = ref_match.group(1)
    
    # Filter invalid (no price = skip)
    if not prop['price']:
        return None
    
    return prop


def generate_embedding_text(prop: Dict) -> str:
    """
    Create rich semantic text for embedding generation.
    Includes sale type, finishing, delivery status for resale differentiation.
    """
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
    if prop['land_area']:
        parts.append(f"Land Area: {prop['land_area']} sqm")
    parts.append(prop['description'][:200])
    
    return ". ".join(parts)


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using text-embedding-3-small (standardized across codebase)."""
    if not openai_client:
        return None
    try:
        response = openai_client.embeddings.create(input=text, model=EMBEDDING_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"    ⚠️ Embedding error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# DATABASE UPSERT (PostgreSQL via SQLAlchemy sync for scraper)
# ═══════════════════════════════════════════════════════════════
def get_db_engine():
    """Create sync SQLAlchemy engine for scraper use."""
    if not DATABASE_URL:
        return None
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    from sqlalchemy import create_engine
    return create_engine(sync_url, pool_pre_ping=True)


def upsert_property_to_db(prop_data: Dict, engine=None):
    """Upsert property to PostgreSQL."""
    if engine is None:
        return
    
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    
    # Generate embedding
    embed_text = generate_embedding_text(prop_data)
    embedding = generate_embedding(embed_text)
    
    # Build title
    title = f"{prop_data['type']} in {prop_data['compound_name']}"
    if prop_data['beds']:
        title += f" - {prop_data['beds']} Beds"
    if prop_data['area']:
        title += f" - {int(prop_data['area'])} sqm"
    
    # Price per sqm
    price_per_sqm = 0
    if prop_data['area'] and prop_data['area'] > 0:
        price_per_sqm = round(prop_data['price'] / prop_data['area'])
    
    with Session(engine) as session:
        try:
            # Check if property exists by URL
            result = session.execute(
                text("SELECT id FROM properties WHERE nawy_url = :url"),
                {"url": prop_data['url']}
            )
            existing = result.fetchone()
            
            if existing:
                # Update existing
                session.execute(
                    text("""
                        UPDATE properties SET
                            title = :title,
                            description = :description,
                            type = :type,
                            location = :location,
                            compound = :compound,
                            price = :price,
                            price_per_sqm = :price_per_sqm,
                            size_sqm = :size_sqm,
                            bedrooms = :bedrooms,
                            bathrooms = :bathrooms,
                            finishing = :finishing,
                            delivery_date = :delivery_date,
                            monthly_installment = :monthly_installment,
                            installment_years = :installment_years,
                            sale_type = :sale_type,
                            nawy_url = :nawy_url,
                            is_delivered = :is_delivered,
                            is_cash_only = :is_cash_only,
                            land_area = :land_area,
                            nawy_reference = :nawy_reference,
                            is_nawy_now = :is_nawy_now,
                            scraped_at = :scraped_at,
                            embedding = :embedding,
                            is_available = true,
                            last_scrape_run_id = :last_scrape_run_id
                        WHERE id = :id
                    """),
                    _build_upsert_params(prop_data, title, price_per_sqm, embedding, existing[0])
                )
            else:
                # Insert new
                session.execute(
                    text("""
                        INSERT INTO properties (
                            title, description, type, location, compound, price, price_per_sqm,
                            size_sqm, bedrooms, bathrooms, finishing, delivery_date,
                            monthly_installment, installment_years, sale_type, nawy_url,
                            is_delivered, is_cash_only, land_area, nawy_reference, is_nawy_now,
                            scraped_at, embedding, is_available, last_scrape_run_id
                        ) VALUES (
                            :title, :description, :type, :location, :compound, :price, :price_per_sqm,
                            :size_sqm, :bedrooms, :bathrooms, :finishing, :delivery_date,
                            :monthly_installment, :installment_years, :sale_type, :nawy_url,
                            :is_delivered, :is_cash_only, :land_area, :nawy_reference, :is_nawy_now,
                            :scraped_at, :embedding, true, :last_scrape_run_id
                        )
                    """),
                    _build_upsert_params(prop_data, title, price_per_sqm, embedding)
                )
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"    ❌ DB Error: {e}")


def _build_upsert_params(prop: Dict, title: str, price_per_sqm: float, 
                          embedding: Optional[List], existing_id: Optional[int] = None) -> Dict:
    """Build parameter dict for SQL upsert."""
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
        "monthly_installment": prop['monthly_installment'],
        "installment_years": prop['installment_years'],
        "sale_type": prop['sale_type'],
        "nawy_url": prop['url'],
        "is_delivered": prop['is_delivered'],
        "is_cash_only": prop['is_cash_only'],
        "land_area": int(prop.get('land_area', 0)),
        "nawy_reference": prop.get('nawy_reference', ''),
        "is_nawy_now": prop.get('is_nawy_now', False),
        "scraped_at": prop.get('scraped_at', datetime.now(timezone.utc).isoformat()),
        "embedding": str(embedding) if embedding else None,
        "last_scrape_run_id": prop.get('scrape_run_id', ''),
    }
    if existing_id is not None:
        params["id"] = existing_id
    return params


# ═══════════════════════════════════════════════════════════════
# TAB SCRAPER — Explicit Resale / Developer / Nawy Now tabs
# ═══════════════════════════════════════════════════════════════

def _get_cards(page) -> List[Dict]:
    """Extract all property cards from the current page view."""
    return page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a[href*="/property/"]')).map(a => ({
            text: a.innerText,
            url: a.href
        }));
    }''')


def _click_tab(page, tab_name: str) -> bool:
    """
    Click a specific sale-type tab on a compound page.
    Nawy uses button/div elements with text like "Resale", "Developer Sale", "Nawy Now".
    Returns True if tab was found and clicked.
    """
    selectors = [
        f"button:has-text('{tab_name}')",
        f"div[role='tab']:has-text('{tab_name}')",
        f"a:has-text('{tab_name}')",
        f"span:has-text('{tab_name}')",
        f"li:has-text('{tab_name}')",
    ]
    for sel in selectors:
        try:
            if page.is_visible(sel, timeout=2000):
                page.click(sel)
                time.sleep(2)
                return True
        except:
            continue
    return False


def _scrape_paginated(page, compound_name: str, sale_type: str, engine=None, scrape_run_id: str = "") -> int:
    """
    Scrape all pages of the current tab.
    Returns count of properties processed.
    """
    page_num = 1
    total = 0
    seen_urls = set()
    
    while True:
        cards = _get_cards(page)
        batch_count = 0
        
        for card in cards:
            if card['url'] in seen_urls:
                continue
            seen_urls.add(card['url'])
            
            parsed = parse_property_text(card['text'], card['url'], compound_name, sale_type)
            if parsed:
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
                if page.is_visible(sel, timeout=1000):
                    page.click(sel)
                    time.sleep(2)
                    page_num += 1
                    found_next = True
                    break
            except:
                continue
        
        if not found_next:
            break
    
    return total


def scrape_compound_properties(page, compound_url: str, compound_name: str, engine=None, scrape_run_id: str = "") -> int:
    """
    Scrape a compound page, explicitly hitting each sale-type tab.
    Order: Resale → Developer Sale → Nawy Now
    """
    total = 0
    
    try:
        print(f"  📍 Navigating to {compound_name}...", flush=True)
        page.goto(compound_url, timeout=60000)
        
        # Wait for property cards to load
        try:
            page.wait_for_selector('a[href*="/property/"]', timeout=30000)
        except:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
        
        # ── 1. Resale Tab ──
        print("    🏷️ [Resale] tab...", flush=True)
        if _click_tab(page, "Resale"):
            time.sleep(2)
            count = _scrape_paginated(page, compound_name, "Resale", engine, scrape_run_id)
            total += count
            print(f"    ✅ Resale: {count} properties", flush=True)
        else:
            print("    ⚠️ No Resale tab found", flush=True)
        
        # ── 2. Developer Sale Tab ──
        print("    🏗️ [Developer Sale] tab...", flush=True)
        if _click_tab(page, "Developer Sale"):
            time.sleep(2)
            count = _scrape_paginated(page, compound_name, "Developer", engine, scrape_run_id)
            total += count
            print(f"    ✅ Developer: {count} properties", flush=True)
        else:
            # If no tab, scrape whatever is on the page as Developer
            print("    ⚠️ No Developer Sale tab, scraping default view...", flush=True)
            count = _scrape_paginated(page, compound_name, "Developer", engine, scrape_run_id)
            total += count
        
        # ── 3. Nawy Now Tab ──
        print("    🚀 [Nawy Now] tab...", flush=True)
        if _click_tab(page, "Nawy Now"):
            time.sleep(2)
            count = _scrape_paginated(page, compound_name, "Nawy Now", engine, scrape_run_id)
            total += count
            print(f"    ✅ Nawy Now: {count} properties", flush=True)
        else:
            print("    ⚠️ No Nawy Now tab found", flush=True)
    
    except Exception as e:
        print(f"  ❌ Error scraping {compound_name}: {e}", flush=True)
    
    return total


def scrape_detail_page(page, url: str) -> Optional[Dict]:
    """
    Scrape a property detail page for additional data:
    - Land area (separate from BUA)
    - Full finishing info
    - Payment plan breakdown
    - Developer info
    
    Returns dict of extra fields to merge, or None on failure.
    """
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        
        text = page.inner_text("body")
        extra = {}
        
        # Land Area
        land_match = re.search(r'Land\s*Area[:\s]+(\d+)\s*m²', text, re.IGNORECASE)
        if land_match:
            extra['land_area'] = float(land_match.group(1))
        
        # BUA
        bua_match = re.search(r'BUA[:\s]+(\d+)\s*m²', text, re.IGNORECASE)
        if bua_match:
            extra['area'] = float(bua_match.group(1))
        
        # Developer
        dev_match = re.search(r'Developer[:\s]+([A-Za-z\s&]+?)(?:\n|$)', text)
        if dev_match:
            extra['developer'] = dev_match.group(1).strip()
        
        # Down Payment
        dp_match = re.search(r'Down\s*Payment[:\s]+(\d+)%', text, re.IGNORECASE)
        if dp_match:
            extra['down_payment'] = int(dp_match.group(1))
        
        # Reference / Property ID from URL
        ref_match = re.search(r'/property/(\d+)', url)
        if ref_match:
            extra['nawy_reference'] = ref_match.group(1)
        
        return extra if extra else None
    
    except Exception as e:
        return None


# ═══════════════════════════════════════════════════════════════
# NAWY NOW PAGE SCRAPER (/nawy-now)
# ═══════════════════════════════════════════════════════════════

def scrape_nawy_now_page(page, engine=None, scrape_run_id: str = "") -> int:
    """
    Scrape the standalone /nawy-now page.
    These are ready-to-move-in properties with Nawy's own mortgage,
    separate from compound-level Nawy Now tabs.
    """
    total = 0
    NAWY_NOW_URL = "https://www.nawy.com/nawy-now"
    
    try:
        print("\n🏠 Scraping Nawy Now standalone page...", flush=True)
        page.goto(NAWY_NOW_URL, timeout=60000)
        
        try:
            page.wait_for_selector('a[href*="/property/"]', timeout=30000)
        except:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
        
        page_num = 1
        seen_urls = set()
        
        while True:
            cards = _get_cards(page)
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
                        compound = url_parts[i-1].replace('-', ' ').title()
                        break
                
                parsed = parse_property_text(card['text'], card['url'], compound, "Nawy Now")
                if parsed:
                    parsed['is_nawy_now'] = True
                    parsed['is_delivered'] = True  # Nawy Now = always delivered
                    parsed['scrape_run_id'] = scrape_run_id
                    upsert_property_to_db(parsed, engine)
                    batch += 1
            
            total += batch
            print(f"  + {batch} Nawy Now items (pg {page_num})", flush=True)
            
            # Scroll to load more (Nawy Now may use infinite scroll)
            prev_count = len(seen_urls)
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            
            new_cards = _get_cards(page)
            new_urls = {c['url'] for c in new_cards}
            if not new_urls - seen_urls:
                # Also try pagination
                found_next = False
                for sel in ["a:has-text('Next')", "button:has-text('Next')", 
                           f".pagination li a:text('{page_num + 1}')","a[aria-label='Next page']"]:
                    try:
                        if page.is_visible(sel, timeout=1000):
                            page.click(sel)
                            time.sleep(2)
                            page_num += 1
                            found_next = True
                            break
                    except:
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

def main():
    # ── Generate unique scrape run ID ──
    scrape_run_id = str(uuid.uuid4())

    # ── Load compound URLs ──
    urls_file = os.path.join(BASE_DIR, "nawy_compound_urls.json")
    if not os.path.exists(urls_file):
        print(f"❌ File not found: {urls_file}")
        return
    
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)
    
    print(f"🚀 Nawy Scraper v2 — Resale + Developer + Nawy Now", flush=True)
    print(f"   Run ID: {scrape_run_id}", flush=True)
    print(f"   Compounds to scrape: {len(urls)}", flush=True)
    print(f"   Embedding model: {EMBEDDING_MODEL}", flush=True)
    print(f"   Database: {'Connected' if DATABASE_URL else 'NOT CONFIGURED'}", flush=True)
    print(f"   Proxies: {len(_PROXY_LIST) if _PROXY_LIST else 'None (direct)'}", flush=True)
    
    # ── Init DB engine ──
    engine = get_db_engine()
    
    total_processed = 0
    total_resale = 0
    total_developer = 0
    total_nawy_now = 0
    failed_compounds = []
    
    BATCH_SIZE = 10  # Rotate proxy every N compounds

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        def _new_context(proxy_index: int):
            proxy = _get_proxy(proxy_index)
            ctx_kwargs = {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "viewport": {"width": 1440, "height": 900},
            }
            if proxy:
                ctx_kwargs["proxy"] = proxy
            return browser.new_context(**ctx_kwargs)

        context = _new_context(0)
        page = context.new_page()
        
        # ── 1. Scrape all compounds (full list, not limited to 3) ──
        for i, url in enumerate(urls):
            name = url.split('/')[-1].replace('-', ' ').title()
            print(f"\n[{i+1}/{len(urls)}] {name}", flush=True)
            
            try:
                count = scrape_compound_properties(page, url, name, engine, scrape_run_id)
                total_processed += count
            except Exception as e:
                print(f"  ❌ Failed {name}: {e}", flush=True)
                failed_compounds.append(name)
            
            # Rotate proxy + pause every BATCH_SIZE compounds
            if (i + 1) % BATCH_SIZE == 0 and (i + 1) < len(urls):
                print(f"\n  🔄 Rotating proxy context (batch {(i+1)//BATCH_SIZE})...", flush=True)
                context.close()
                time.sleep(5)
                context = _new_context((i + 1) // BATCH_SIZE)
                page = context.new_page()
        
        # ── 2. Scrape standalone Nawy Now page ──
        nawy_now_count = scrape_nawy_now_page(page, engine, scrape_run_id)
        total_nawy_now += nawy_now_count
        total_processed += nawy_now_count
        
        context.close()
        browser.close()
    
    # ── Summary ──
    print(f"\n{'='*60}", flush=True)
    print(f"✅ SCRAPING COMPLETE", flush=True)
    print(f"   Total compounds: {len(urls)}", flush=True)
    print(f"   Total properties processed: {total_processed}", flush=True)
    print(f"   Failed compounds: {len(failed_compounds)}", flush=True)
    if failed_compounds:
        print(f"   Failed: {', '.join(failed_compounds[:10])}", flush=True)
    print(f"{'='*60}", flush=True)
    
    # ── Save to JSON backup ──
    summary = {
        "scrape_date": datetime.now(timezone.utc).isoformat(),
        "scrape_run_id": scrape_run_id,
        "total_compounds": len(urls),
        "total_properties": total_processed,
        "failed_compounds": failed_compounds,
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
    main()
