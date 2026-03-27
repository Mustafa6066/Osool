"""
Geopolitical & Macroeconomic Scraper
------------------------------------
Collects and processes geopolitical events and macro-economic news
that impact the Egyptian real estate market.

Data Sources (RSS feeds + free APIs):
1. Al Jazeera English RSS (Middle East focus)
2. Reuters Middle East RSS
3. Central Bank of Egypt (CBE) news
4. Trading Economics Egypt indicators
5. World Bank Egypt RSS

Processing Pipeline:
1. Fetch raw articles from RSS/API sources
2. Filter for relevance (keyword + region matching)
3. Rule-based summarization: extract impact on Egyptian RE market (zero tokens)
4. Classify impact level (high/medium/low) and tag impact areas
5. Store in GeopoliticalEvent table

Runs as a scheduled job (daily via APScheduler, also available as Celery task).
Uses httpx (async) matching the existing economic_scraper pattern.
"""

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeopoliticalEvent
from app.services.cache import cache

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# RSS FEED SOURCES
# ═══════════════════════════════════════════════════════════════

RSS_SOURCES: List[Dict[str, str]] = [
    {
        "name": "Al Jazeera English - Middle East",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "region": "middle_east",
    },
    {
        "name": "Reuters - World",
        "url": "https://feeds.reuters.com/reuters/worldNews",
        "region": "global",
    },
    {
        "name": "BBC News - Middle East",
        "url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        "region": "middle_east",
    },
    {
        "name": "World Bank - Egypt",
        "url": "https://blogs.worldbank.org/en/rss.xml",
        "region": "egypt",
    },
    # ── Arabic-language sources ──
    {
        "name": "Enterprise Press - Egypt",
        "url": "https://enterprise.press/feed/",
        "region": "egypt",
    },
    {
        "name": "Al-Borsa News - Egypt Economy",
        "url": "https://www.alborsanews.com/feed/",
        "region": "egypt",
    },
]


# ═══════════════════════════════════════════════════════════════
# RELEVANCE KEYWORDS (English + Arabic)
# Events matching these are candidates for RE impact analysis
# ═══════════════════════════════════════════════════════════════

RELEVANCE_KEYWORDS: Dict[str, List[str]] = {
    "conflict": [
        "war", "conflict", "military", "attack", "missile", "red sea",
        "houthi", "suez canal", "strait", "blockade", "sanctions",
        "حرب", "صراع", "عسكري", "هجوم", "البحر الأحمر", "قناة السويس",
    ],
    "monetary_policy": [
        "central bank", "interest rate", "monetary policy", "rate cut",
        "rate hike", "cbe", "federal reserve", "ecb", "imf",
        "البنك المركزي", "سعر الفائدة", "السياسة النقدية", "صندوق النقد",
    ],
    "currency": [
        "exchange rate", "usd", "egp", "devaluation", "float",
        "dollar", "currency", "forex", "pound",
        "سعر الصرف", "الدولار", "الجنيه", "تعويم",
    ],
    "oil_energy": [
        "oil price", "brent", "crude", "opec", "natural gas",
        "energy", "petroleum", "fuel",
        "أسعار النفط", "أوبك", "الطاقة", "البنزين",
    ],
    "inflation": [
        "inflation", "cpi", "consumer price", "cost of living",
        "price surge", "purchasing power",
        "التضخم", "الأسعار", "تكلفة المعيشة", "القوة الشرائية",
    ],
    "construction_costs": [
        "steel", "cement", "rebar", "construction material",
        "building cost", "supply chain", "shipping",
        "حديد", "أسمنت", "مواد بناء", "سلسلة التوريد",
    ],
    "foreign_investment": [
        "foreign investment", "fdi", "capital inflow", "investor confidence",
        "sovereign wealth", "gulf investment",
        "استثمار أجنبي", "تدفق رأس المال", "صندوق سيادي",
    ],
    "fiscal_policy": [
        "government spending", "budget", "fiscal", "subsidy",
        "tax reform", "public debt", "gdp",
        "الموازنة", "الدين العام", "الناتج المحلي", "الضرائب",
    ],
    "regulation": [
        "real estate law", "property law", "building regulation",
        "urban development", "new capital", "new cities",
        "registration", "tabu", "licensing",
        "قانون العقارات", "التنظيم العقاري", "المدن الجديدة", "العاصمة الإدارية",
        "الشهر العقاري", "التراخيص", "هيئة المجتمعات العمرانية",
        "اشتراطات البناء", "قانون التصالح",
    ],
}

# Flatten for quick scanning
ALL_KEYWORDS = []
for kw_list in RELEVANCE_KEYWORDS.values():
    ALL_KEYWORDS.extend(kw_list)


# ═══════════════════════════════════════════════════════════════
# IMPACT → REAL ESTATE MAPPING (Rule-based, zero tokens)
# ═══════════════════════════════════════════════════════════════

IMPACT_MAPPING: Dict[str, Dict[str, Any]] = {
    "conflict": {
        "tags": ["supply_chain", "construction_costs", "shipping_disruption"],
        "impact_template": (
            "Regional conflict and security tensions disrupt supply chains "
            "through the Suez Canal/Red Sea corridor, increasing shipping costs "
            "for construction materials (steel, cement). Off-plan purchases at "
            "current developer prices lock in pre-inflation pricing."
        ),
    },
    "monetary_policy": {
        "tags": ["interest_rates", "mortgage_affordability", "capital_cost"],
        "impact_template": (
            "Central bank rate decisions directly affect mortgage affordability "
            "and developer financing costs. Rate hikes increase bank CD returns "
            "(competing with RE yields), while cuts lower borrowing costs and "
            "stimulate property demand."
        ),
    },
    "currency": {
        "tags": ["currency_devaluation", "inflation_hedge", "foreign_buyer_advantage"],
        "impact_template": (
            "Currency movements affect real estate as an inflation hedge. "
            "EGP devaluation makes Egyptian property cheaper for foreign investors "
            "and increases the urgency to convert cash to hard assets. "
            "Long payment plans become advantageous as future installments are paid "
            "in devalued currency."
        ),
    },
    "oil_energy": {
        "tags": ["construction_costs", "operating_costs", "inflation_pressure"],
        "impact_template": (
            "Oil price fluctuations cascade into construction costs (transport, "
            "energy-intensive materials like cement and steel). Rising oil also "
            "increases Gulf sovereign wealth, potentially increasing Gulf investor "
            "appetite for Egyptian real estate."
        ),
    },
    "inflation": {
        "tags": ["inflation_hedge", "purchasing_power", "real_returns"],
        "impact_template": (
            "Persistent inflation erodes cash purchasing power. Real estate has "
            "historically outpaced Egyptian inflation (property appreciation ~30% "
            "vs inflation ~14%). Ready-to-move units with rental income provide "
            "immediate CPI-beating returns."
        ),
    },
    "construction_costs": {
        "tags": ["construction_costs", "developer_repricing", "off_plan_advantage"],
        "impact_template": (
            "Rising construction material costs force developers to reprice future "
            "phases. Current off-plan buyers lock in today's pricing before the "
            "next adjustment. Ready-to-move properties are immune to material cost "
            "increases."
        ),
    },
    "foreign_investment": {
        "tags": ["foreign_investment", "demand_increase", "price_appreciation"],
        "impact_template": (
            "Foreign direct investment inflows into Egyptian real estate increase "
            "demand in premium areas (New Capital, North Coast, New Alamein). "
            "Gulf sovereign wealth fund activity signals confidence in market "
            "fundamentals."
        ),
    },
    "fiscal_policy": {
        "tags": ["government_spending", "infrastructure", "urban_expansion"],
        "impact_template": (
            "Government fiscal policy and infrastructure spending drive urban "
            "expansion and new city development. Budget allocations to new cities "
            "improve connectivity and property values in adjacent areas."
        ),
    },
    "regulation": {
        "tags": ["regulatory_change", "market_transparency", "buyer_protection"],
        "impact_template": (
            "Regulatory changes in real estate law affect buyer protection, "
            "developer obligations, and market transparency. New urban development "
            "policies shape supply dynamics and investment hotspots."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════
# RSS FETCH & PARSE
# ═══════════════════════════════════════════════════════════════

async def _fetch_rss_feed(client: httpx.AsyncClient, source: Dict[str, str]) -> List[Dict[str, str]]:
    """Fetch and parse a single RSS feed with retry. Returns list of article dicts."""
    articles: List[Dict[str, str]] = []
    last_error = None

    for attempt in range(3):
        try:
            resp = await client.get(source["url"], timeout=15)
            if resp.status_code != 200:
                logger.warning(f"RSS fetch failed for {source['name']}: HTTP {resp.status_code} (attempt {attempt+1}/3)")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                continue

            root = ET.fromstring(resp.text)

            # Handle both RSS 2.0 (<channel><item>) and Atom (<entry>) formats
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for item in items[:30]:  # Limit to newest 30 per source
                title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                desc_el = (
                    item.find("description")
                    or item.find("{http://www.w3.org/2005/Atom}summary")
                    or item.find("{http://www.w3.org/2005/Atom}content")
                )
                link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                pub_el = item.find("pubDate") or item.find("{http://www.w3.org/2005/Atom}published")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                description = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                link = ""
                if link_el is not None:
                    link = link_el.get("href", "") or (link_el.text.strip() if link_el.text else "")
                pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else ""

                if title:
                    articles.append({
                        "title": title,
                        "description": _strip_html(description),
                        "link": link,
                        "pub_date": pub_date,
                        "source_name": source["name"],
                        "region": source["region"],
                    })

            return articles  # Success — return immediately

        except ET.ParseError as e:
            logger.warning(f"XML parse error for {source['name']}: {e}")
            last_error = e
            break  # XML parse errors won't be fixed by retrying
        except Exception as e:
            logger.warning(f"RSS fetch error for {source['name']} (attempt {attempt+1}/3): {e}")
            last_error = e
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

    return articles


def _strip_html(text: str) -> str:
    """Remove HTML tags from RSS description text."""
    return re.sub(r"<[^>]+>", "", text).strip()


# ═══════════════════════════════════════════════════════════════
# RELEVANCE FILTERING
# ═══════════════════════════════════════════════════════════════

def _is_relevant(article: Dict[str, str]) -> Tuple[bool, str, List[str]]:
    """
    Check if an article is relevant to Egyptian RE investment.
    Returns (is_relevant, primary_category, matched_keywords).
    """
    text = (article.get("title", "") + " " + article.get("description", "")).lower()

    matched_category = ""
    matched_keywords: List[str] = []

    for category, keywords in RELEVANCE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                if not matched_category:
                    matched_category = category
                matched_keywords.append(kw)

    return bool(matched_category), matched_category, matched_keywords


def _assess_impact_level(article: Dict[str, str], category: str, matched_keywords: List[str]) -> str:
    """Heuristic impact assessment based on keyword density and category."""
    keyword_count = len(set(matched_keywords))

    # High-impact categories by default
    high_impact_categories = {"conflict", "currency", "monetary_policy"}
    if category in high_impact_categories and keyword_count >= 2:
        return "high"

    # Egypt-specific content is higher impact
    text_lower = (article.get("title", "") + " " + article.get("description", "")).lower()
    egypt_mentions = sum(1 for w in ["egypt", "cairo", "مصر", "القاهرة", "cbe", "egp"] if w in text_lower)

    if egypt_mentions >= 1 and keyword_count >= 2:
        return "high"
    if keyword_count >= 3:
        return "high"
    if keyword_count >= 2:
        return "medium"
    return "low"


# ═══════════════════════════════════════════════════════════════
# RULE-BASED SUMMARIZATION (zero tokens)
# ═══════════════════════════════════════════════════════════════

def _rule_based_summary(article: Dict[str, str], category: str) -> Dict[str, Any]:
    """Generate summary from rule-based mapping — zero token cost."""
    mapping = IMPACT_MAPPING.get(category, IMPACT_MAPPING["inflation"])
    return {
        "summary": f"{article['title']}. {article.get('description', '')[:200]}",
        "real_estate_impact": mapping["impact_template"],
        "impact_tags": mapping["tags"],
    }


# ═══════════════════════════════════════════════════════════════
# DATE PARSING
# ═══════════════════════════════════════════════════════════════

def _parse_pub_date(date_str: str) -> datetime:
    """Parse RSS pubDate into timezone-aware datetime. Fallback to now()."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",      # RFC 822 (RSS standard)
        "%a, %d %b %Y %H:%M:%S GMT",      # GMT variant
        "%Y-%m-%dT%H:%M:%S%z",            # ISO 8601
        "%Y-%m-%dT%H:%M:%SZ",             # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",              # Simple
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
# DEDUPLICATION
# ═══════════════════════════════════════════════════════════════

async def _is_duplicate(db: AsyncSession, title: str, source: str) -> bool:
    """Check if this event already exists (by title + source)."""
    stmt = select(func.count(GeopoliticalEvent.id)).where(
        GeopoliticalEvent.title == title,
        GeopoliticalEvent.source == source,
    )
    result = await db.execute(stmt)
    count = result.scalar() or 0
    return count > 0


# ═══════════════════════════════════════════════════════════════
# MAIN SCRAPER PIPELINE
# ═══════════════════════════════════════════════════════════════

async def scrape_geopolitical_events(db: AsyncSession) -> Dict[str, Any]:
    """
    Main pipeline: Fetch → Filter → Summarize → Store.
    Zero token cost — uses rule-based impact summarization only.

    Returns:
        {"fetched": int, "relevant": int, "stored": int, "errors": int}
    """
    stats = {"fetched": 0, "relevant": 0, "stored": 0, "errors": 0, "duplicates": 0}

    logger.info("🌍 [GEOPOLITICAL SCRAPER] Starting geopolitical event collection...")

    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; OsoolBot/1.0; +https://osool.eg)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
        follow_redirects=True,
        timeout=20,
    ) as client:

        # 1. Fetch all RSS feeds concurrently
        tasks = [_fetch_rss_feed(client, source) for source in RSS_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles: List[Dict[str, str]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Feed {RSS_SOURCES[i]['name']} failed: {result}")
                stats["errors"] += 1
            elif isinstance(result, list):
                all_articles.extend(result)

        stats["fetched"] = len(all_articles)
        logger.info(f"📰 Fetched {stats['fetched']} articles from {len(RSS_SOURCES)} sources")

        # 2. Filter for relevance
        relevant_articles: List[Tuple[Dict[str, str], str, List[str]]] = []
        for article in all_articles:
            is_rel, category, keywords = _is_relevant(article)
            if is_rel:
                relevant_articles.append((article, category, keywords))

        stats["relevant"] = len(relevant_articles)
        logger.info(f"🎯 {stats['relevant']} articles passed relevance filter")

        # 3. Process and store each relevant article
        for article, category, keywords in relevant_articles:
            try:
                # Deduplication
                if await _is_duplicate(db, article["title"], article["source_name"]):
                    stats["duplicates"] += 1
                    continue

                # Impact assessment
                impact_level = _assess_impact_level(article, category, keywords)

                # Summarization (rule-based, zero tokens)
                summary_data: Dict[str, Any] = _rule_based_summary(article, category)

                # Parse tags
                tags = summary_data.get("impact_tags", [])
                tags_json = json.dumps(tags) if isinstance(tags, list) else str(tags)

                # Parse date
                event_date = _parse_pub_date(article.get("pub_date", ""))

                # Set expiration (high=30d, medium=14d, low=7d)
                expiry_days = {"high": 30, "medium": 14, "low": 7}
                expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days.get(impact_level, 14))

                # Create and store the event
                # Parse sentiment from LLM (default 0.0 for rule-based)
                raw_sentiment = summary_data.get("sentiment_score", 0.0)
                try:
                    sentiment = max(-1.0, min(1.0, float(raw_sentiment)))
                except (TypeError, ValueError):
                    sentiment = 0.0

                event = GeopoliticalEvent(
                    title=article["title"][:300],
                    summary=summary_data.get("summary", article.get("description", ""))[:2000],
                    source=article["source_name"][:200],
                    source_url=article.get("link", "")[:2000],
                    event_date=event_date,
                    category=category,
                    region=article.get("region", "middle_east"),
                    impact_level=impact_level,
                    impact_tags=tags_json,
                    real_estate_impact=summary_data.get("real_estate_impact", "")[:2000],
                    sentiment_score=sentiment,
                    is_active=True,
                    expires_at=expires_at,
                )

                db.add(event)
                stats["stored"] += 1

            except Exception as e:
                logger.warning(f"Failed to process article '{article.get('title', '?')[:50]}': {e}")
                stats["errors"] += 1

        # 4. Commit all events
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"Database commit failed: {e}")
            await db.rollback()
            stats["stored"] = 0
            stats["errors"] += 1

    # 5. Expire old events
    try:
        from sqlalchemy import update as sa_update
        expire_stmt = (
            sa_update(GeopoliticalEvent)
            .where(GeopoliticalEvent.expires_at < datetime.now(timezone.utc))
            .where(GeopoliticalEvent.is_active == True)  # noqa: E712
            .values(is_active=False)
        )
        await db.execute(expire_stmt)
        await db.commit()
    except Exception as e:
        logger.warning(f"Event expiration cleanup failed: {e}")

    # 6. Invalidate cache so AI layer picks up fresh events
    cache.delete("geopolitical_context")
    cache.delete("geopolitical_events_recent")

    logger.info(
        f"🌍 [GEOPOLITICAL SCRAPER] Complete: "
        f"fetched={stats['fetched']}, relevant={stats['relevant']}, "
        f"stored={stats['stored']}, duplicates={stats['duplicates']}, errors={stats['errors']}"
    )
    return stats


# ═══════════════════════════════════════════════════════════════
# STANDALONE RUNNER (for manual execution / testing)
# ═══════════════════════════════════════════════════════════════

async def run_geopolitical_scraper():
    """Standalone runner for the geopolitical scraper (used by scheduler)."""
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await scrape_geopolitical_events(db)
        return result
