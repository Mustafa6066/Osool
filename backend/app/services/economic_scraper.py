"""
Egyptian Economic Data Scraper
------------------------------
Collects macroeconomic indicators relevant to real estate investment decisions.

Sources:
- Trading Economics (scraping attempt)
- CBE (Central Bank of Egypt) reference
- Manual fallback data (updated periodically by team)

Stores data in the MarketIndicator table for use by the AI brain.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# FALLBACK DATA (Updated manually — serves as baseline)
# ═══════════════════════════════════════════════════════════════
FALLBACK_ECONOMIC_DATA = {
    # Inflation & Currency
    "inflation_rate": {"value": 0.136, "source": "CAPMAS Feb 2026 (Manual)", "category": "macro"},
    "usd_egp_rate": {"value": 51.50, "source": "CBE Midpoint Feb 2026 (Manual)", "category": "currency"},
    "usd_egp_parallel": {"value": 54.10, "source": "Parallel Market Feb 2026 (Manual)", "category": "currency"},

    # Banking & Interest Rates
    "bank_cd_rate": {"value": 0.22, "source": "NBE/CIB Feb 2026 (Manual)", "category": "banking"},
    "mortgage_rate": {"value": 0.18, "source": "NBE Housing Finance Feb 2026 (Manual)", "category": "banking"},
    "cbk_overnight_rate": {"value": 0.2775, "source": "CBE Feb 2026 (Manual)", "category": "banking"},

    # Construction Costs
    "construction_cost_index": {"value": 142, "source": "Engineering Syndicate Feb 2026 (Manual)", "category": "construction"},
    "cement_price_ton": {"value": 2800, "source": "Market Average Feb 2026 (Manual)", "category": "construction"},
    "rebar_price_ton": {"value": 42000, "source": "Market Average Feb 2026 (Manual)", "category": "construction"},
    "construction_base_cost_sqm": {"value": 15000, "source": "Industry Average Feb 2026 (Manual)", "category": "construction"},

    # Real Estate Performance
    "real_property_growth": {"value": 0.145, "source": "Research Average Feb 2026 (Manual)", "category": "real_estate"},
    "nominal_property_appreciation": {"value": 0.304, "source": "Research YoY Feb 2026 (Manual)", "category": "real_estate"},
    "rental_yield_avg": {"value": 0.075, "source": "Market Research Feb 2026 (Manual)", "category": "real_estate"},
    "rent_increase_rate": {"value": 0.12, "source": "Market Research Feb 2026 (Manual)", "category": "real_estate"},

    # Alternative Investments
    "gold_appreciation": {"value": 0.15, "source": "Egypt Gold Board Feb 2026 (Manual)", "category": "alternatives"},
    "gold_price_egp_gram": {"value": 4800, "source": "Egypt Gold Board Feb 2026 (Manual)", "category": "alternatives"},

    # GDP & Economy
    "gdp_growth_rate": {"value": 0.042, "source": "IMF Forecast Feb 2026 (Manual)", "category": "macro"},
    "population_growth": {"value": 0.017, "source": "CAPMAS Feb 2026 (Manual)", "category": "macro"},
    "urbanization_rate": {"value": 0.432, "source": "World Bank Feb 2026 (Manual)", "category": "macro"},
}


async def scrape_trading_economics() -> Dict[str, Dict]:
    """
    Attempt to scrape Trading Economics for Egyptian economic indicators.
    Falls back gracefully if scraping fails.
    """
    indicators = {}
    try:
        async with httpx.AsyncClient(
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
        ) as client:
            # Try Egypt indicators page
            resp = await client.get("https://tradingeconomics.com/egypt/indicators")
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Look for indicator table rows
                rows = soup.select("table tr")
                for row in rows:
                    cells = row.select("td")
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True).lower()
                        try:
                            value_text = cells[1].get_text(strip=True).replace(",", "").replace("%", "")
                            value = float(value_text)
                        except (ValueError, IndexError):
                            continue

                        # Map known indicators
                        if "inflation" in name and "rate" in name:
                            indicators["inflation_rate"] = {
                                "value": value / 100 if value > 1 else value,
                                "source": f"Trading Economics {datetime.now().strftime('%b %Y')}",
                            }
                        elif "interest" in name and "rate" in name:
                            indicators["cbk_overnight_rate"] = {
                                "value": value / 100 if value > 1 else value,
                                "source": f"Trading Economics {datetime.now().strftime('%b %Y')}",
                            }
                        elif "gdp" in name and "growth" in name:
                            indicators["gdp_growth_rate"] = {
                                "value": value / 100 if value > 1 else value,
                                "source": f"Trading Economics {datetime.now().strftime('%b %Y')}",
                            }

                logger.info(f"Trading Economics: scraped {len(indicators)} indicators")
            else:
                logger.warning(f"Trading Economics returned status {resp.status_code}")

    except Exception as e:
        logger.warning(f"Trading Economics scrape failed: {e}")

    return indicators


async def scrape_gold_price() -> Optional[Dict]:
    """Attempt to get current gold price in EGP."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.goldpricez.com/eg/gold-prices-in-egypt",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Try to find gold 24K price
                price_elements = soup.select(".gold-price, .price-value, td")
                for el in price_elements:
                    text = el.get_text(strip=True)
                    if "EGP" in text or any(c.isdigit() for c in text):
                        try:
                            price = float("".join(c for c in text if c.isdigit() or c == "."))
                            if 1000 < price < 20000:  # Reasonable gram price range
                                return {
                                    "value": price,
                                    "source": f"Gold Price Scrape {datetime.now().strftime('%b %Y')}",
                                }
                        except ValueError:
                            continue
    except Exception as e:
        logger.warning(f"Gold price scrape failed: {e}")

    return None


async def update_market_indicators(db_session) -> Dict[str, any]:
    """
    Main entry point: scrape economic data + merge with fallback + store to DB.

    Called by:
    - Admin endpoint: POST /admin/update-economic-data
    - Cron job (future)
    """
    from app.models import MarketIndicator
    from sqlalchemy import select

    # 1. Try scraping (best-effort)
    scraped_data = {}
    try:
        trading_econ, gold_price = await asyncio.gather(
            scrape_trading_economics(),
            scrape_gold_price(),
            return_exceptions=True
        )

        if isinstance(trading_econ, dict):
            scraped_data.update(trading_econ)
        if isinstance(gold_price, dict):
            scraped_data["gold_price_egp_gram"] = gold_price

    except Exception as e:
        logger.warning(f"Scraping phase failed: {e}")

    # 2. Merge: scraped overrides fallback
    final_data = {}
    for key, fallback in FALLBACK_ECONOMIC_DATA.items():
        if key in scraped_data:
            final_data[key] = scraped_data[key]
        else:
            final_data[key] = fallback

    # 3. Upsert into MarketIndicator table
    updated_count = 0
    for key, data in final_data.items():
        try:
            result = await db_session.execute(
                select(MarketIndicator).where(MarketIndicator.key == key)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = data["value"]
                existing.source = data.get("source", "Manual Update")
            else:
                indicator = MarketIndicator(
                    key=key,
                    value=data["value"],
                    source=data.get("source", "Manual Update")
                )
                db_session.add(indicator)
            updated_count += 1
        except Exception as e:
            logger.warning(f"Failed to upsert {key}: {e}")

    await db_session.commit()
    logger.info(f"Economic scraper: updated {updated_count}/{len(final_data)} market indicators")

    return {
        "updated": updated_count,
        "total": len(final_data),
        "scraped": len(scraped_data),
        "fallback": len(final_data) - len(scraped_data),
        "indicators": {k: v["value"] for k, v in final_data.items()},
    }
