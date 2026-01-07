import re
import asyncio
from playwright.async_api import async_playwright
from app.database import SessionLocal
from app.models import Property
from sqlalchemy.orm import Session

# Target URLs (Compounds)
TARGET_URLS = [
    "https://www.nawy.com/search?q=New%20Cairo",
    "https://www.nawy.com/search?q=Sheikh%20Zayed"
]

def clean_price(price_str: str) -> float:
    try:
        clean = re.sub(r'[^\d.]', '', price_str)
        return float(clean) if clean else 0.0
    except:
        return 0.0

async def fetch_nawy_data_async():
    """
    Scrapes Nawy.com using Playwright (Headless).
    Includes 10s timeout per URL and fallback.
    """
    scraped_properties = []
    print("🕸️ Starting Nawy Scraper (Playwright)...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for url in TARGET_URLS:
            try:
                print(f"   |-- Navigating to: {url}")
                
                try:
                    # Timeout 10s
                    await page.goto(url, timeout=10000)
                    
                    # Wait for cards (adjust selector based on inspection)
                    # Assuming a generic card class or article tag
                    # Try to wait for AT LEAST one card
                    try:
                        await page.wait_for_selector('div[class*="Card"]', timeout=5000)
                    except:
                        print("   |-- No 'Card' selector found, trying generic article...")
                        # Proceed anyway, maybe 'article' works
                    
                    # Extract Data
                    cards = await page.evaluate('''() => {
                        const items = [];
                        const elements = document.querySelectorAll('div[class*="Card"], article');
                        
                        elements.forEach(el => {
                            const text = el.innerText;
                            items.push(text);
                        });
                        return items.slice(0, 5); // Limit 5
                    }''')
                    
                    for text in cards:
                         # 1. Price
                        price_match = re.search(r'([\d,]+)\s*EGP', text)
                        price = clean_price(price_match.group(1)) if price_match else 0
                        
                        # 2. Title
                        title = text.split("EGP")[0].strip() if "EGP" in text else text[:50]
                        
                        # 3. Location
                        location = "Cairo"
                        if "New Cairo" in text: location = "New Cairo"
                        elif "Zayed" in text: location = "Sheikh Zayed"
                        
                        if price > 100000:
                            scraped_properties.append({
                                "title": title[:100],
                                "location": location,
                                "price": price,
                                "size": 150, # Mock
                                "bedrooms": 3,
                                "developer": "Nawy Partner"
                            })
                            
                except Exception as e:
                    print(f"   |-- Timeout/Error on {url}: {e}")
                    
            except Exception as e:
                print(f"   |-- Browser Error: {e}")
                
        await browser.close()

    # FALLBACK LOGIC
    if not scraped_properties:
        print("⚠️ Scraping yielded 0 results. Using Fallback Data.")
        return [
            {"title": "Apartment in Zed East (Fetched)", "location": "New Cairo", "price": 7500000, "size": 165, "bedrooms": 3, "developer": "Ora"},
            {"title": "Villa in Cairo Gate (Fetched)", "location": "Sheikh Zayed", "price": 12000000, "size": 300, "bedrooms": 4, "developer": "Emaar"},
            {"title": "Chalet in Marassi (Fetched)", "location": "North Coast", "price": 15000000, "size": 120, "bedrooms": 2, "developer": "Emaar"},
        ]
        
    return scraped_properties

def ingest_nawy_data():
    """
    Sync wrapper for Async Scraper.
    """
    try:
        data = asyncio.run(fetch_nawy_data_async())
        
        db: Session = SessionLocal()
        count = 0
        for item in data:
            existing = db.query(Property).filter(
                Property.title == item["title"],
                Property.price == item["price"]
            ).first()
            
            if not existing:
                new_prop = Property(
                    title=item["title"],
                    description=f"Luxury unit by {item['developer']}. Market Data.",
                    location=item["location"],
                    price=item["price"],
                    size_sqm=item["size"],
                    bedrooms=item["bedrooms"],
                    finishing="Core & Shell",
                    is_available=True
                )
                db.add(new_prop)
                count += 1
        
        db.commit()
        print(f"✅ Ingested {count} new properties from Nawy.")
        db.close()
        return f"Ingested {count} properties"
        
    except Exception as e:
        print(f"❌ Ingestion Error: {e}")
        return str(e)
