
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath('d:/Osool/backend'))

from app.database import AsyncSessionLocal
from app.models import Property
from sqlalchemy import select, text, func

async def check_data():
    async with AsyncSessionLocal() as db:
        print("--- Checking Database Content ---")
        
        # 1. Count Total Properties
        count_query = select(func.count()).select_from(Property)
        result = await db.execute(count_query)
        total_count = result.scalar()
        print(f"Total Properties: {total_count}")
        
        if total_count == 0:
            print("❌ Database is EMPTY. The AI has nothing to see.")
            return

        # 2. Check for Embeddings
        # Note: 'embedding' column might not be selectable easily if it's vectors, 
        # so we check if it is not null
        embedding_query = select(func.count()).select_from(Property).filter(Property.embedding.isnot(None))
        result = await db.execute(embedding_query)
        embedding_count = result.scalar()
        print(f"Properties with Embeddings: {embedding_count}")
        
        if embedding_count == 0:
            print("⚠️ No properties have embeddings. Vector search will FAIL (but text fallback should work).")
        elif embedding_count < total_count:
            print(f"⚠️ Only {embedding_count}/{total_count} properties have embeddings.")
            
        # 3. Check specific search terms to verify text data
        print("\n--- Testing Text Data Content ---")
        terms = ["Tamera", "New Cairo", "Zayed", "Apartment"]
        for term in terms:
            search_query = select(func.count()).select_from(Property).filter(
                Property.title.ilike(f"%{term}%") | 
                Property.description.ilike(f"%{term}%") |
                Property.location.ilike(f"%{term}%")
            )
            result = await db.execute(search_query)
            term_count = result.scalar()
            print(f"Matches for '{term}': {term_count}")

            if term_count > 0:
                # Print one sample
                sample_query = select(Property).filter(
                     Property.title.ilike(f"%{term}%") | 
                     Property.description.ilike(f"%{term}%")
                ).limit(1)
                res = await db.execute(sample_query)
                prop = res.scalar()
                print(f"  -> Sample: ID={prop.id} Title='{prop.title}' Price={prop.price}")

if __name__ == "__main__":
    asyncio.run(check_data())
