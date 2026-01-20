"""
Osool Data Import Script
------------------------
Imports all properties from data.js into Railway PostgreSQL database.

Usage:
    python scripts/import_data.py

Environment:
    DATABASE_URL - PostgreSQL connection string
"""

import json
import os
import sys
import re
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def extract_js_data(js_file_path: str) -> dict:
    """Extract the JSON object from a JavaScript file that assigns to window.egyptianData."""
    with open(js_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the JSON object - it starts after "window.egyptianData = "
    match = re.search(r'window\.egyptianData\s*=\s*(\{[\s\S]*\})\s*;?\s*$', content)
    if not match:
        raise ValueError("Could not find window.egyptianData in the file")
    
    json_str = match.group(1)
    return json.loads(json_str)

async def import_properties():
    """Import all properties from data.js into the database."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Use the Railway public URL for local import
        database_url = "postgresql://postgres:BeQqFYfalLZejuHJrakJGShPGoiUZoIx@tramway.proxy.rlwy.net:44789/railway"
    
    # Convert to async URL
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    print(f"🔌 Connecting to database...")
    
    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Load data from data.js
    data_js_path = Path(__file__).parent.parent.parent / "public" / "assets" / "js" / "data.js"
    print(f"📂 Loading data from: {data_js_path}")
    
    data = extract_js_data(str(data_js_path))
    properties = data.get('properties', [])
    
    print(f"📊 Found {len(properties)} properties to import")
    
    async with AsyncSessionLocal() as session:
        # Clear existing properties (optional - comment out if you want to append)
        print("🧹 Clearing existing properties...")
        await session.execute(text("DELETE FROM properties"))
        await session.commit()
        
        # Import in batches
        batch_size = 100
        imported = 0
        
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i + batch_size]
            
            for prop in batch:
                # Map data.js fields to database model
                payment_plan = prop.get('paymentPlan', {})
                
                insert_sql = text("""
                    INSERT INTO properties (
                        title, description, type, location, compound, developer,
                        price, price_per_sqm, size_sqm, bedrooms, bathrooms, finishing,
                        delivery_date, down_payment, installment_years, monthly_installment,
                        image_url, nawy_url, sale_type, is_available, created_at
                    ) VALUES (
                        :title, :description, :type, :location, :compound, :developer,
                        :price, :price_per_sqm, :size_sqm, :bedrooms, :bathrooms, :finishing,
                        :delivery_date, :down_payment, :installment_years, :monthly_installment,
                        :image_url, :nawy_url, :sale_type, :is_available, NOW()
                    )
                """)
                
                await session.execute(insert_sql, {
                    'title': prop.get('title', 'Unknown'),
                    'description': prop.get('description', ''),
                    'type': prop.get('type', 'Apartment'),
                    'location': prop.get('location', 'Unknown'),
                    'compound': prop.get('compound', ''),
                    'developer': prop.get('developer', ''),
                    'price': float(prop.get('price', 0)),
                    'price_per_sqm': float(prop.get('pricePerSqm', 0)),
                    'size_sqm': int(prop.get('size', prop.get('sqm', prop.get('area', 0)))),
                    'bedrooms': int(prop.get('bedrooms', 0)),
                    'bathrooms': int(prop.get('bathrooms', 0)),
                    'finishing': prop.get('finishing', 'Fully Finished'),
                    'delivery_date': str(prop.get('deliveryDate', '')),
                    'down_payment': int(payment_plan.get('downPayment', 10)),
                    'installment_years': int(payment_plan.get('installmentYears', 0)),
                    'monthly_installment': float(payment_plan.get('monthlyInstallment', 0)),
                    'image_url': prop.get('image', ''),
                    'nawy_url': prop.get('nawyUrl', ''),
                    'sale_type': prop.get('saleType', 'Developer'),
                    'is_available': True
                })
            
            await session.commit()
            imported += len(batch)
            print(f"✅ Imported {imported}/{len(properties)} properties...")
        
        print(f"\n🎉 Successfully imported {imported} properties!")
        
        # Verify count
        result = await session.execute(text("SELECT COUNT(*) FROM properties"))
        count = result.scalar()
        print(f"📈 Database now has {count} properties")

if __name__ == "__main__":
    import asyncio
    asyncio.run(import_properties())
