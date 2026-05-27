import pandas as pd
import json
import re

def clean_compound(name):
    # "1077-solana-east" -> "Solana East"
    # Remove leading digits and dash
    name = re.sub(r'^\d+-', '', name)
    # Replace dashes with spaces and title case
    return name.replace('-', ' ').title()


def get_image_for_type(prop_type):
    prop_type = str(prop_type).lower()
    # Gradient/Color coding for professional look
    # Villa: Dark Blue text on Gold background
    if 'villa' in prop_type:
        return "https://placehold.co/600x400/1a1a2e/f1c40f?text=Luxury+Villa"
    # Apartment: White text on Blue background
    elif 'apartment' in prop_type:
        return "https://placehold.co/600x400/2980b9/ffffff?text=Modern+Apartment"
    # Townhouse/Twinhouse: Green
    elif 'town' in prop_type or 'twin' in prop_type:
        return "https://placehold.co/600x400/27ae60/ffffff?text=Premium+House"
    # Chalet: Teal
    elif 'chalet' in prop_type:
        return "https://placehold.co/600x400/16a085/ffffff?text=Coastal+Chalet"
    # Office/Clinic: Gray
    elif 'office' in prop_type or 'clinic' in prop_type or 'retail' in prop_type:
        return "https://placehold.co/600x400/7f8c8d/ffffff?text=Commercial+Unit"
    # Default
    return f"https://placehold.co/600x400/34495e/ffffff?text={prop_type.title()}"


def load_developer_map():
    try:
        with open('d:/Osool/compound_developers.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Map compound_id -> developer
            return {item['compound_id']: item['developer'] for item in data}
    except Exception as e:
        print(f"Warning: Could not load developer map: {e}")
        return {}

def convert():
    input_file = 'd:/Osool/nawy_final_refined.xlsx'
    output_file = 'd:/Osool/public/assets/js/data.js'
    
    df = pd.read_excel(input_file)
    dev_map = load_developer_map()
    
    properties = []
    
    for i, row in df.iterrows():
        try:
            raw_id = str(row['compound'])
            compound_clean = clean_compound(raw_id)
            
            price = int(row['price']) if pd.notnull(row['price']) else 0
            area = int(row['area']) if pd.notnull(row['area']) else 0
            beds = int(row['beds']) if pd.notnull(row['beds']) and row['beds'] != '' else 0
            baths = int(row['baths']) if pd.notnull(row['baths']) and row['baths'] != '' else 0
            
            monthly = int(row['monthly_installment']) if pd.notnull(row['monthly_installment']) and row['monthly_installment'] != '' else 0
            years = int(row['installment_years']) if pd.notnull(row['installment_years']) and row['installment_years'] != '' else 1
            
            prop_type = row['type'] if pd.notnull(row['type']) else "Unit"
            
            # Developer Logic (From Map)
            dev_name = dev_map.get(raw_id, "Premium Developer")
            if dev_name in ["Unknown Developer", None, ""]:
                dev_name = "Premium Developer"
            
            # Fallback to column if map failed but column exists (rare/impossible now)
            if dev_name == "Premium Developer" and 'developer' in row and pd.notnull(row['developer']):
                 dev_name = str(row['developer']).strip()

            prop = {
                "id": f"NC{i+1}",
                "title": f"{prop_type} in {compound_clean}",
                "type": prop_type,
                "location": row['location'] if pd.notnull(row['location']) else "New Cairo",
                "compound": compound_clean,
                "developer": dev_name, 
                "area": area,
                "size": area, 
                "sqm": area, 
                "bua": area,
                "bedrooms": beds,
                "bathrooms": baths,
                "price": price,
                "pricePerSqm": int(price / area) if area > 0 else 0,
                "deliveryDate": str(int(row['delivery'])) if pd.notnull(row['delivery']) else "2027",
                "paymentPlan": {
                    "downPayment": 10, 
                    "installmentYears": years,
                    "monthlyInstallment": monthly
                },
                "image": get_image_for_type(prop_type),
                "description": f"Luxury {prop_type} in {compound_clean}. Delivery {row['delivery']}."
            }
            properties.append(prop)
        except Exception as e:
            print(f"Skipping row {i}: {e}")
            pass
            
    # Metadata
    data = {
        "metadata": {
            "totalProperties": len(properties),
            "lastUpdated": "2025-12-28",
            "marketStats": {
                "averagePricePerSqm": 45000,
                "hotLocations": ["New Cairo", "Mostakbal City", "Golden Square", "6th Settlement"]
            }
        },
        "properties": properties
    }
    
    # Write to JS file
    json_str = json.dumps(data, indent=4)
    js_content = f"window.egyptianData = {json_str};"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"✅ Generated data.js with {len(properties)} properties.")

if __name__ == "__main__":
    convert()
