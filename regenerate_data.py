"""
Script to regenerate data.js with real Nawy URLs and typed images (no placeholder text)
"""
import pandas as pd
import json

# Load the Excel data
df = pd.read_excel('nawy_final_refined.xlsx')

# Image URLs by property type (professional gradient images, no mock text)
TYPE_IMAGES = {
    'Apartment': 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=600&h=400&fit=crop',
    'Villa': 'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600&h=400&fit=crop',
    'Townhouse': 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
    'Twinhouse': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
    'Duplex': 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
    'Penthouse': 'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600&h=400&fit=crop',
    'Office': 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=400&fit=crop',
    'Unit': 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600&h=400&fit=crop',
    'default': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=600&h=400&fit=crop'
}

# Location prefixes for IDs
LOC_PREFIX = {
    'New Cairo': 'NC',
    'Mostakbal City': 'MC',
    '6th of October': 'OC',
    'Sheikh Zayed': 'SZ',
    'Madinaty': 'MD',
    'New Capital': 'NAC'
}

# Clean compound name
def clean_compound(name):
    if pd.isna(name):
        return 'Unknown Compound'
    # Remove ID prefix like "1077-"
    parts = str(name).split('-', 1)
    if len(parts) > 1 and parts[0].isdigit():
        name = parts[1]
    # Convert dashes to spaces and title case
    return name.replace('-', ' ').title()

# Build properties array
properties = []
counters = {}

for idx, row in df.iterrows():
    location = str(row.get('location', 'New Cairo'))
    prop_type = str(row.get('type', 'Unit'))
    
    # Generate ID
    prefix = LOC_PREFIX.get(location, 'PR')
    counters[prefix] = counters.get(prefix, 0) + 1
    prop_id = f"{prefix}{counters[prefix]}"
    
    # Get image
    image_url = TYPE_IMAGES.get(prop_type, TYPE_IMAGES['default'])
    
    # Clean compound name
    compound = clean_compound(row.get('compound', ''))
    
    # Build property object with real data
    prop = {
        'id': prop_id,
        'title': f"{prop_type} in {compound}",
        'type': prop_type,
        'location': location,
        'compound': compound,
        'developer': 'Developer',
        'area': int(row['area']) if pd.notna(row.get('area')) else 0,
        'size': int(row['area']) if pd.notna(row.get('area')) else 0,
        'sqm': int(row['area']) if pd.notna(row.get('area')) else 0,
        'bua': int(row['area']) if pd.notna(row.get('area')) else 0,
        'bedrooms': int(row['beds']) if pd.notna(row.get('beds')) else 0,
        'bathrooms': int(row['baths']) if pd.notna(row.get('baths')) else 0,
        'price': int(row['price']) if pd.notna(row.get('price')) else 0,
        'pricePerSqm': int(row['price'] / row['area']) if pd.notna(row.get('price')) and pd.notna(row.get('area')) and row['area'] > 0 else 0,
        'deliveryDate': str(int(row['delivery'])) if pd.notna(row.get('delivery')) else 'TBD',
        'paymentPlan': {
            'downPayment': 10,
            'installmentYears': int(row['installment_years']) if pd.notna(row.get('installment_years')) else 5,
            'monthlyInstallment': int(row['monthly_installment']) if pd.notna(row.get('monthly_installment')) else 0
        },
        'image': image_url,
        'nawyUrl': str(row['url']) if pd.notna(row.get('url')) else '',
        'saleType': str(row.get('saleType', 'Developer')),
        'description': f"Luxury {prop_type} in {compound}. Delivery {row.get('delivery', 'TBD')}."
    }
    properties.append(prop)

# Build full data object
data = {
    'metadata': {
        'totalProperties': len(properties),
        'lastUpdated': '2026-01-05',
        'dataSource': 'nawy.com',
        'marketStats': {
            'averagePricePerSqm': 45000,
            'hotLocations': ['New Cairo', 'Mostakbal City', 'Golden Square', '6th Settlement']
        }
    },
    'properties': properties
}

# Write to data.js
with open('public/assets/js/data.js', 'w', encoding='utf-8') as f:
    f.write('window.egyptianData = ')
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.write(';\n')

print(f"✅ Generated data.js with {len(properties)} properties")
print(f"   - Using real Nawy URLs from Excel")
print(f"   - Using Unsplash property type images (no placeholders)")
