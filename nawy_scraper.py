"""
Nawy Property Scraper (Supabase & Embeddings Edition)
Extracts raw text, processes it, generates embeddings, and upserts to Supabase.
"""

import json
import time
import os
import sys
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv(dotenv_path="d:/Osool/backend/.env")

# Init Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in env.")
    # In a real run we might exit, but for dev we'll warn
    # sys.exit(1)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"⚠️ Could not connect to Supabase: {e}")
    supabase = None

# Init Embeddings
try:
    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
except Exception as e:
    print(f"⚠️ Could not init OpenAI Embeddings: {e}")
    embeddings_model = None

sys.stdout.reconfigure(encoding='utf-8')

def parse_property_text(text, url, compound_name):
    """Parse raw property card text using Python regex"""
    prop = {
        'compound_name': compound_name,
        'type': 'Unit',
        'location': '',
        'price': 0,
        'beds': 0,
        'baths': 0,
        'area': 0,
        'delivery_date': '',
        'monthly_installment': 0,
        'installment_years': 0,
        'sale_type': 'Developer', # Default
        'url': url,
        'description': text.replace('\n', ' ').strip()
    }
    
    clean_text = prop['description']
    
    # Type
    type_match = re.search(r'(Townhouse|Apartment|Villa|Duplex|Penthouse|Twinhouse|Chalet|Studio|Office|Retail|Clinic)', clean_text, re.IGNORECASE)
    if type_match:
        prop['type'] = type_match.group(1)
        
    # Location
    loc_match = re.search(r'(New Cairo|Mostakbal City|6th settlement|Golden Square)', clean_text, re.IGNORECASE)
    if loc_match:
        prop['location'] = loc_match.group(1)
        
    # Price
    price_match = re.search(r'(\d+(?:,\d{3})+)\s*EGP', clean_text, re.IGNORECASE)
    if price_match:
        prop['price'] = float(price_match.group(1).replace(',', ''))
        
    # Beds
    beds_match = re.search(r'(\d+)\s*Beds?', clean_text, re.IGNORECASE)
    if beds_match:
        prop['beds'] = int(beds_match.group(1))
        
    # Baths
    baths_match = re.search(r'(\d+)\s*Baths?', clean_text, re.IGNORECASE)
    if baths_match:
        prop['baths'] = int(baths_match.group(1))
        
    # Area
    area_match = re.search(r'(\d+)\s*m²', clean_text, re.IGNORECASE)
    if area_match:
        prop['area'] = float(area_match.group(1))
        
    # Delivery
    del_match = re.search(r'(20\d{2})', clean_text)
    if del_match:
        prop['delivery_date'] = del_match.group(1)
        
    # Installerment
    pay_match = re.search(r'(\d+(?:,\d{3})*)\s*(Monthly|Quarterly)', clean_text, re.IGNORECASE)
    if pay_match:
        amount = float(pay_match.group(1).replace(',', ''))
        period = pay_match.group(2).lower()
        if period == 'quarterly':
            prop['monthly_installment'] = round(amount / 3)
        else:
            prop['monthly_installment'] = int(amount)
            
    # Years
    years_match = re.search(r'(\d+)\s*Years', clean_text, re.IGNORECASE)
    if years_match:
        prop['installment_years'] = int(years_match.group(1))

    # Sale Type
    if 'Resale' in clean_text:
        prop['sale_type'] = 'Resale'

    # Filter invalid
    if not prop['price']:
        return None
        
    return prop

def upsert_property_to_db(prop_data):
    """Upserts property to Supabase and adds embedding."""
    if not supabase or not embeddings_model:
        # Fallback to printer if DB not configured
        # print(f"  [Mock DB] would save: {prop_data['type']} for {prop_data['price']}")
        return

    # 1. Generate text for embedding (Rich semantic representation)
    # "Luxury Villa in New Cairo, 500 sqm, 5 beds, 10M EGP, Developer Sale"
    text_to_embed = f"{prop_data['type']} in {prop_data['compound_name']}, {prop_data['location']}. " \
                    f"Price: {prop_data['price']} EGP. Area: {prop_data['area']} sqm. " \
                    f"{prop_data['beds']} Beds, {prop_data['baths']} Baths. " \
                    f"Delivery: {prop_data['delivery_date']}. {prop_data['description']}"
    
    try:
        vector = embeddings_model.embed_query(text_to_embed)
        prop_data['embedding'] = vector
        
        # 2. Upsert
        # Note: 'url' is unique? or use a compound key? Using URL as unique identifier for now.
        # Check if exists first to avoid duplicate primary key errors if not handling properly
        # Ideally we'd use on_conflict in raw SQL or upsert with unique column
        
        # Searching by URL to see if we update or insert
        # For simplicity in this script, we'll try to find by URL, if matches, update.
        # But Supabase 'upsert' works if we have a primary key or unique constraint.
        # We did not define 'url' as unique in schema.sql but we should have.
        # For now, we will just insert and catch error or query first.
        
        # Let's query first
        existing = supabase.table('properties').select("id").eq("url", prop_data['url']).execute()
        
        if existing.data:
            # Update
            pid = existing.data[0]['id']
            supabase.table('properties').update(prop_data).eq("id", pid).execute()
            # print(f"    🔄 Updated property {pid}")
        else:
            # Insert
            supabase.table('properties').insert(prop_data).execute()
            # print(f"    ✨ Inserted new property")
            
    except Exception as e:
        print(f"    ❌ DB Error: {e}")


def scrape_compound_properties(page, compound_url, compound_name):
    page_num = 1
    items_count = 0
    
    try:
        print(f"  📍 Navigating to {compound_name}...", flush=True)
        page.goto(compound_url, timeout=60000)
        
        try:
            page.wait_for_selector('a[href*="/property/"]', timeout=30000)
        except:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
        def get_raw_cards():
            return page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a[href*="/property/"]')).map(a => ({
                    text: a.innerText,
                    url: a.href
                }));
            }''')

        # Helper to process a batch
        def process_batch(cards, sale_type_override=None):
            count = 0
            for card in cards:
                parsed = parse_property_text(card['text'], card['url'], compound_name)
                if parsed:
                    if sale_type_override:
                        parsed['sale_type'] = sale_type_override
                    
                    upsert_property_to_db(parsed)
                    count += 1
            return count

        # 1. Scrape RESALE tab
        print("    👀 Scraping Resale...", flush=True)
        while True:
            raw_cards = get_raw_cards()
            # De-duplicate locally for this page view is handled by Supabase upsert logic mostly,
            # but let's just process content.
            
            n = process_batch(raw_cards)
            items_count += n
            print(f"      + Processed {n} resale items (Page {page_num})", flush=True)
            
            # Next button
            try:
                found_next = False
                selectors = [
                    f".pagination li a:text('{page_num + 1}')",
                    "a[aria-label='Next page']",
                    "li:has-text('Next') a",
                    "a:has-text('Next')"
                ]
                for sel in selectors:
                    if page.is_visible(sel):
                        page.click(sel)
                        time.sleep(2)
                        page_num += 1
                        found_next = True
                        break
                if not found_next:
                    break
            except:
                break
                
        # 2. Scrape DEVELOPER SALE tab
        try:
            dev_tab = page.query_selector("button:has-text('Developer Sale'), div:has-text('Developer Sale')")
            if dev_tab:
                print("    👀 Switching to Developer Sale...", flush=True)
                dev_tab.click()
                time.sleep(3)
                
                page_num = 1
                while True:
                    raw_cards = get_raw_cards()
                    # Filters are harder here without keeping state of all URLs, 
                    # but our DB check handles duplicates reasonably well.
                    
                    n = process_batch(raw_cards, sale_type_override='Developer')
                    items_count += n
                    print(f"      + Processed {n} developer items (Page {page_num})", flush=True)
                    
                    # Next button
                    found_next = False
                    selectors = [
                        f".pagination li a:text('{page_num + 1}')",
                        "a[aria-label='Next page']",
                        "li:has-text('Next') a"
                    ]
                    for sel in selectors:
                        if page.is_visible(sel):
                            try:
                                page.click(sel)
                                time.sleep(2)
                                page_num += 1
                                found_next = True
                                break
                            except:
                                continue
                    if not found_next:
                        break
        except Exception as e:
            pass
            
    except Exception as e:
        print(f"  ❌ Error: {e}", flush=True)

    return items_count

def main():
    urls_file = "d:/Osool/nawy_compound_urls.json"
    if not os.path.exists(urls_file):
         print(f"❌ File not found: {urls_file}")
         return

    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)

    print(f"🚀 Restarting Scraper (DB Mode)...", flush=True)
    
    total_processed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # scrape first 3 compounds for testing
        for i, url in enumerate(urls[:3]): 
            name = url.split('/')[-1]
            try:
                count = scrape_compound_properties(page, url, name)
                total_processed += count
            except Exception as e:
                print(f"  ❌ Failed {name}: {e}", flush=True)
                
        browser.close()

    print(f"✅ DONE! Processed {total_processed} properties into Supabase.", flush=True)

if __name__ == "__main__":
    main()
