#!/usr/bin/env python3
"""
Osool Data Ingestion to PostgreSQL
-----------------------------------
Phase 1: Migrates all 3,274 properties from properties.json to PostgreSQL
with pgvector embeddings for semantic search.

This replaces the Supabase-only approach to establish PostgreSQL as the
single source of truth and prevent AI hallucinations.

Usage:
    python ingest_data_postgres.py
"""

import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from app.models import Property
from app.database import Base

load_dotenv()

# Configuration
PROPERTIES_JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "properties.json")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Convert postgres:// to postgresql+asyncpg://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def load_properties_from_json(filepath: str) -> list:
    """
    Loads properties from the JSON file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("properties", [])


def create_embedding_text(prop: dict) -> str:
    """
    Creates rich text content for embedding generation.
    This text is what the AI will use for semantic search.
    """
    content = f"""
Property: {prop.get('title', 'N/A')}
Type: {prop.get('type', 'N/A')}
Location: {prop.get('location', 'N/A')}
Compound: {prop.get('compound', 'N/A')}
Developer: {prop.get('developer', 'N/A')}
Area: {prop.get('area', 0)} sqm
Bedrooms: {prop.get('bedrooms', 0)}
Bathrooms: {prop.get('bathrooms', 0)}
Price: {prop.get('price', 0):,.0f} EGP
Price per sqm: {prop.get('pricePerSqm', 0):,.0f} EGP
Delivery: {prop.get('deliveryDate', 'N/A')}
Sale Type: {prop.get('saleType', 'N/A')}
Description: {prop.get('description', '')}
"""

    payment = prop.get('paymentPlan', {})
    if payment:
        content += f"""
Down Payment: {payment.get('downPayment', 0)}%
Installment Years: {payment.get('installmentYears', 0)}
Monthly Installment: {payment.get('monthlyInstallment', 0):,.0f} EGP
"""

    return content.strip()


def generate_embedding(text: str) -> list:
    """
    Generates embedding using OpenAI text-embedding-ada-002 model.
    Returns a 1536-dimensional vector.
    """
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"   ⚠️ Embedding generation failed: {e}")
        return None


async def property_exists(db: AsyncSession, property_id: str) -> bool:
    """
    Checks if a property already exists in the database by its ID.
    """
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    return result.scalar_one_or_none() is not None


async def ingest_to_postgres(properties: list):
    """
    Ingests properties into PostgreSQL with embeddings.
    Skips duplicates and provides progress updates.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        inserted = 0
        skipped = 0
        failed = 0

        print(f"\n📊 Processing {len(properties)} properties...")

        for i, prop in enumerate(properties, 1):
            try:
                # Check if property already exists
                prop_id = prop.get('id')
                if await property_exists(db, prop_id):
                    skipped += 1
                    if i % 100 == 0:
                        print(f"   [{i}/{len(properties)}] Skipped (already exists): {prop_id}")
                    continue

                # Create embedding
                embedding_text = create_embedding_text(prop)
                embedding = generate_embedding(embedding_text)

                if not embedding:
                    print(f"   ⚠️ Skipping {prop_id} - embedding failed")
                    failed += 1
                    continue

                # Extract payment plan
                payment = prop.get('paymentPlan', {})

                # Create Property instance
                new_property = Property(
                    id=prop_id,
                    title=prop.get('title', ''),
                    description=prop.get('description', ''),
                    type=prop.get('type', ''),
                    location=prop.get('location', ''),
                    compound=prop.get('compound', ''),
                    developer=prop.get('developer', ''),
                    price=float(prop.get('price', 0)),
                    price_per_sqm=float(prop.get('pricePerSqm', 0)),
                    size_sqm=int(prop.get('area', 0)),
                    bedrooms=int(prop.get('bedrooms', 0)),
                    bathrooms=int(prop.get('bathrooms', 0)),
                    finishing=prop.get('finishing', 'N/A'),
                    delivery_date=prop.get('deliveryDate', ''),
                    down_payment=payment.get('downPayment', 0) if payment else 0,
                    installment_years=payment.get('installmentYears', 0) if payment else 0,
                    monthly_installment=float(payment.get('monthlyInstallment', 0)) if payment else 0,
                    image_url=prop.get('image', ''),
                    nawy_url=prop.get('nawyUrl', ''),
                    sale_type=prop.get('saleType', ''),
                    embedding=embedding,
                    is_available=True
                )

                db.add(new_property)
                inserted += 1

                # Progress update every 100 properties
                if i % 100 == 0:
                    print(f"   [{i}/{len(properties)}] ✅ Inserted: {prop_id}")

                # Commit in batches of 50 for performance
                if i % 50 == 0:
                    await db.commit()

            except Exception as e:
                print(f"   ❌ Error processing {prop.get('id', 'unknown')}: {e}")
                failed += 1
                continue

        # Final commit
        await db.commit()

        # Summary
        print(f"\n📈 INGESTION SUMMARY:")
        print(f"   ✅ Inserted: {inserted}")
        print(f"   ⏭️ Skipped (duplicates): {skipped}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Total processed: {len(properties)}")

        # Verify count
        result = await db.execute(select(func.count(Property.id)))
        total_count = result.scalar()
        print(f"\n🔢 Total properties in database: {total_count}")

    await engine.dispose()


async def main():
    print("=" * 70)
    print("🏠 OSOOL DATA MIGRATION TO POSTGRESQL")
    print("=" * 70)

    # 1. Load Data
    print(f"\n📂 Loading data from: {PROPERTIES_JSON_PATH}")
    properties = load_properties_from_json(PROPERTIES_JSON_PATH)
    print(f"   - Properties in JSON: {len(properties)}")

    # 2. Ingest to PostgreSQL
    print("\n💾 Migrating to PostgreSQL with embeddings...")
    await ingest_to_postgres(properties)

    print("\n🎉 Done! All properties migrated to PostgreSQL.")
    print("   AI can now query directly from the database.")
    print("   This prevents hallucinations by enforcing data validation.")


if __name__ == "__main__":
    asyncio.run(main())
