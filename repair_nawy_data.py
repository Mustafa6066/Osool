"""
Repair Script for Nawy Data
Visits specific URLs with missing attributes to fill holes.
"""
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def repair_data():
    input_file = 'd:/Osool/nawy_final_py_1805.xlsx'
    output_file = 'd:/Osool/nawy_final_refined.xlsx'
    
    df = pd.read_csv(input_file) if input_file.endswith('.csv') else pd.read_excel(input_file)
    print(f"Loaded {len(df)} rows.")
    
    # Identify rows to repair
    # 1. Missing Baths AND NOT Commercial
    # 2. Missing Payment? Maybe skip for now as it takes too long.
    
    commercial_types = ['Office', 'Retail', 'Clinic']
    
    # helper for filtering
    mask = (df['baths'].isnull()) & (~df['type'].isin(commercial_types))
    repair_indices = df[mask].index.tolist()
    
    print(f"Properties to repair: {len(repair_indices)}")
    
    if not repair_indices:
        print("No repairs needed.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        count = 0
        for idx in repair_indices:
            url = df.at[idx, 'url']
            print(f"[{count+1}/{len(repair_indices)}] Repairing {url} ...", flush=True)
            
            try:
                page.goto(url, timeout=60000)
                page.wait_for_load_state("domcontentloaded")
                
                # Get full text of the page body (sometimes details are in description)
                body_text = page.inner_text("body")
                
                # Try to find Baths
                if pd.isna(df.at[idx, 'baths']):
                    # Look for "X Bathrooms" or "X Baths" or icons
                    # Expanded regex
                    baths_match = re.search(r'(\d+)\s*(?:Bathrooms?|Baths?)', body_text, re.IGNORECASE)
                    if baths_match:
                        val = int(baths_match.group(1))
                        df.at[idx, 'baths'] = val
                        print(f"  -> Found Baths: {val}", flush=True)
                    else:
                        print("  -> Baths still missing", flush=True)
                        
                # Try to find Type if Unit
                if df.at[idx, 'type'] == 'Unit':
                    type_match = re.search(r'(Townhouse|Apartment|Villa|Duplex|Penthouse|Twinhouse|Chalet|Studio|Office|Retail|Clinic)', body_text, re.IGNORECASE)
                    if type_match:
                        new_type = type_match.group(1)
                        if new_type in commercial_types:
                             print(f"  -> Identified as {new_type} (Commercial)", flush=True)
                        else:
                             print(f"  -> Identified as {new_type}", flush=True)
                        df.at[idx, 'type'] = new_type

                count += 1
                
                # Save periodically
                if count % 10 == 0:
                    df.to_excel(output_file, index=False)
                    print("  (Saved progress)", flush=True)
                    
            except Exception as e:
                print(f"  Failed: {e}", flush=True)
                
        browser.close()
        
    df.to_excel(output_file, index=False)
    print(f"✅ DONE! Saved refined data to {output_file}")

if __name__ == "__main__":
    repair_data()
