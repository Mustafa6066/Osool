
import json
import re
import pandas as pd
from playwright.sync_api import sync_playwright

def get_developer_from_page(page, url):
    try:
        page.goto(url, timeout=30000)
        page.wait_for_selector('h1', timeout=10000)
        
        # Strategy 1: "Compound By Developer" in H1
        h1_text = page.inner_text('h1')
        # Format often: "Compound Name In Location By Developer"
        # or "Compound Name By Developer"
        
        # Split by " By " (case insensitive)
        parts = re.split(r'\s+By\s+', h1_text, flags=re.IGNORECASE)
        if len(parts) > 1:
            return parts[-1].strip()
            
        # Strategy 2: Look for specific developer class if exists (Nawy structure varies)
        # Often there is a "Developer" section or link
        dev_link = page.query_selector('a[href*="/real-estate-developers/"]')
        if dev_link:
            return dev_link.inner_text().strip()
            
        # Strategy 3: Meta description
        meta_desc = page.get_attribute('meta[name="description"]', 'content')
        if meta_desc:
            # "Search properties in Compound by Developer..."
            parts = re.split(r'\s+by\s+', meta_desc, flags=re.IGNORECASE)
            if len(parts) > 1:
                 # Take the part after 'by' until comma or period
                 candidate = parts[1].split(',')[0].split('.')[0]
                 return candidate.strip()
                 
        return "Unknown Developer"
    except Exception as e:
        print(f"Error {url}: {e}")
        return None

def main():
    urls_file = "d:/Osool/nawy_compound_urls.json"
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)
        
    print(f"Scanning {len(urls)} compounds for developers...")
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for i, url in enumerate(urls):
            compound = url.split('/')[-1]
            dev = get_developer_from_page(page, url)
            
            # Clean compound name for matching
            # e.g. "1077-solana-east" -> "Solana East"
            clean_comp = " ".join(re.split(r'[-_]', compound)[1:]).title() # ID-name-name
            if not clean_comp: clean_comp = compound
            
            print(f"[{i+1}/{len(urls)}] {clean_comp} -> {dev}", flush=True)
            
            results.append({
                "compound_id": compound,
                "clean_name": clean_comp,
                "developer": dev if dev else "Premium Developer"
            })
            
        browser.close()
        
    # Save to JSON
    with open("d:/Osool/compound_developers.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print("✅ Saved developer map!")

if __name__ == "__main__":
    main()
