"""
Nawy Property Scraper (Python Logic)
Extracts raw text and processes it in Python for robustness.
"""

import json
import time
import os
import sys
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

def parse_property_text(text, url, compound_name):
    """Parse raw property card text using Python regex"""
    prop = {
        'compound': compound_name,
        'type': 'Unit',
        'location': '',
        'price': '',
        'beds': '',
        'baths': '',
        'area': '',
        'delivery': '',
        'monthly_installment': '',
        'installment_years': '',
        'installment_period': '',
        'saleType': 'Developer', # Default
        'url': url
    }
    
    # Text cleaning
    clean_text = text.replace('\n', ' ').strip()
    
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
        prop['price'] = price_match.group(1).replace(',', '')
        
    # Beds
    beds_match = re.search(r'(\d+)\s*Beds?', clean_text, re.IGNORECASE)
    if beds_match:
        prop['beds'] = beds_match.group(1)
        
    # Baths
    baths_match = re.search(r'(\d+)\s*Baths?', clean_text, re.IGNORECASE)
    if baths_match:
        prop['baths'] = baths_match.group(1)
        
    # Area
    area_match = re.search(r'(\d+)\s*m²', clean_text, re.IGNORECASE)
    if area_match:
        prop['area'] = area_match.group(1)
        
    # Delivery
    del_match = re.search(r'(20\d{2})', clean_text)
    if del_match:
        prop['delivery'] = del_match.group(1)
        
    # Payment: "449,812 Monthly / 7 Years" or "Quarterly"
    # Capture Amount + Period
    pay_match = re.search(r'(\d+(?:,\d{3})*)\s*(Monthly|Quarterly)', clean_text, re.IGNORECASE)
    if pay_match:
        amount = float(pay_match.group(1).replace(',', ''))
        period = pay_match.group(2).lower()
        prop['installment_period'] = period.title()
        
        if period == 'quarterly':
            prop['monthly_installment'] = round(amount / 3)
        else:
            prop['monthly_installment'] = int(amount)
            
    # Years
    years_match = re.search(r'(\d+)\s*Years', clean_text, re.IGNORECASE)
    if years_match:
        prop['installment_years'] = years_match.group(1)

    # Sale Type
    if 'Resale' in clean_text:
        prop['saleType'] = 'Resale'

    # Filter out empty/invalid cards (must have price or be valid)
    if not prop['price']:
        return None
        
    return prop

def scrape_compound_properties(page, compound_url, compound_name):
    properties = []
    page_num = 1
    
    try:
        print(f"  📍 Navigating to {compound_name}...", flush=True)
        page.goto(compound_url, timeout=60000)
        
        try:
            page.wait_for_selector('a[href*="/property/"]', timeout=30000)
        except:
             # Try scrolling
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
        def get_raw_cards():
            return page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a[href*="/property/"]')).map(a => ({
                    text: a.innerText,
                    url: a.href
                }));
            }''')

        # 1. Scrape RESALE tab
        print("    👀 Scraping Resale...", flush=True)
        while True:
            raw_cards = get_raw_cards()
            valid_items = []
            for card in raw_cards:
                parsed = parse_property_text(card['text'], card['url'], compound_name)
                if parsed:
                    valid_items.append(parsed)
            
            if valid_items:
                properties.extend(valid_items)
                print(f"      + PyParsed {len(valid_items)} resale items (Page {page_num})", flush=True)
            
            # Next button
            try:
                # Try multiple selectors for next button
                found_next = False
                selectors = [
                    f".pagination li a:text('{page_num + 1}')",
                    "a[aria-label='Next page']",
                    "li:has-text('Next') a",
                    "a:has-text('Next')"
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
                    valid_items = []
                    seen_urls = set(p['url'] for p in properties)
                    
                    for card in raw_cards:
                        if card['url'] in seen_urls: continue
                        
                        parsed = parse_property_text(card['text'], card['url'], compound_name)
                        if parsed:
                            parsed['saleType'] = 'Developer' # Override
                            valid_items.append(parsed)
                            
                    if valid_items:
                        properties.extend(valid_items)
                        print(f"      + PyParsed {len(valid_items)} developer items (Page {page_num})", flush=True)
                    
                    # Next button (same logic)
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
            # print(f"    Tab switch error: {e}", flush=True)
            pass
            
    except Exception as e:
        print(f"  ❌ Error: {e}", flush=True)

    return properties

def main():
    urls_file = "d:/Osool/nawy_compound_urls.json"
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)

    all_data = []
    print(f"🚀 Restarting Python-Side Scraper...", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, url in enumerate(urls):
            name = url.split('/')[-1]
            try:
                props = scrape_compound_properties(page, url, name)
                all_data.extend(props)
                
                if (i+1) % 5 == 0:
                    df = pd.DataFrame(all_data)
                    df.to_excel("d:/Osool/nawy_data_partial_py.xlsx", index=False)
                    print(f"  💾 Saved progress ({len(all_data)} rows)", flush=True)
                    
            except Exception as e:
                print(f"  ❌ Failed {name}: {e}", flush=True)

        browser.close()

    if all_data:
        df = pd.DataFrame(all_data)
        out = f"d:/Osool/nawy_final_py_{datetime.now().strftime('%H%M')}.xlsx"
        df.to_excel(out, index=False)
        print(f"✅ DONE! Saved {len(all_data)} rows to {out}", flush=True)

if __name__ == "__main__":
    main()
