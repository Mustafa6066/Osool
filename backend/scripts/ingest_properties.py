
import json
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.insert(0, os.path.abspath('d:/Osool/backend'))

DATA_FILE = "d:/Osool/data/properties.json"

# Load Env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"DEBUG: RAW DATABASE_URL = {DATABASE_URL}")

# Fix URL for Sync Engine
if DATABASE_URL:
    if "asyncpg" in DATABASE_URL:
         DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
    if "aiosqlite" in DATABASE_URL:
         DATABASE_URL = DATABASE_URL.replace("+aiosqlite", "")

print(f"DEBUG: SYNC DATABASE_URL = {DATABASE_URL}")

def ingest_properties():
    print("🚀 Starting Property Ingestion (RAW SQL Mode)...")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL is not set.")
        return

    if not os.path.exists(DATA_FILE):
        print(f"❌ Data file not found: {DATA_FILE}")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        properties = data.get("properties", [])
        print(f"📦 Found {len(properties)} properties in JSON file.")

    engine = create_engine(DATABASE_URL, echo=False)

    with engine.connect() as conn:
        # Create table if not exists (simplified fallback or rely on main app migration)
        # We assume table exists because diagnos_data ran query against it.
        
        count = 0
        inserted = 0
        target_properties = properties 
        print(f"ℹ️  Processing ALL {len(target_properties)} properties.")

        for item in target_properties:
            # Check if exists
            check_sql = text("SELECT 1 FROM properties WHERE title = :title AND location = :location")
            result = conn.execute(check_sql, {"title": item['title'], "location": item['location']}).scalar()
            
            if result:
                print(f"⚠️ Skipping duplicate: {item['title']}")
                count += 1
                continue

            # Insert SQL
            # We explicitly SKIP 'embedding' to avoid SQLite Vector error.
            # We also ensure column names match exactly app/models.py
            insert_sql = text("""
                INSERT INTO properties (
                    title, description, type, location, compound, developer,
                    price, price_per_sqm, size_sqm, bedrooms, bathrooms,
                    finishing, delivery_date, down_payment, installment_years,
                    monthly_installment, image_url, nawy_url, sale_type, is_available
                ) VALUES (
                    :title, :description, :type, :location, :compound, :developer,
                    :price, :price_per_sqm, :size_sqm, :bedrooms, :bathrooms,
                    :finishing, :delivery_date, :down_payment, :installment_years,
                    :monthly_installment, :image_url, :nawy_url, :sale_type, :is_available
                )
            """)
            
            params = {
                "title": item['title'],
                "description": item.get('description', ''),
                "type": item['type'],
                "location": item['location'],
                "compound": item.get('compound'),
                "developer": item.get('developer'),
                "price": float(item['price']),
                "price_per_sqm": float(item.get('pricePerSqm', 0)),
                "size_sqm": int(item['size']),
                "bedrooms": int(item['bedrooms']),
                "bathrooms": int(item.get('bathrooms', 0)),
                "finishing": item.get('finishing', 'Core & Shell'),
                "delivery_date": str(item.get('deliveryDate', '')),
                "down_payment": int(item.get('paymentPlan', {}).get('downPayment', 0)),
                "installment_years": int(item.get('paymentPlan', {}).get('installmentYears', 0)),
                "monthly_installment": float(item.get('paymentPlan', {}).get('monthlyInstallment', 0)),
                "image_url": item.get('image'),
                "nawy_url": item.get('nawyUrl'),
                "sale_type": item.get('saleType', 'Resale'),
                "is_available": True
            }

            try:
                conn.execute(insert_sql, params)
                inserted += 1
            except Exception as e:
                print(f"❌ Insert failed for {item['title']}: {e}")

            count += 1
            if inserted % 10 == 0:
                conn.commit()
                print(f"✅ Committed {inserted} properties...")
        
        conn.commit()
        print(f"🎉 Ingestion Complete. Processed: {count}, Inserted: {inserted}")

if __name__ == "__main__":
    ingest_properties()
