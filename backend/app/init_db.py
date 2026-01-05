import os
import asyncio
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.database import Base
from app.models import Property, User, Transaction
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXCEL_PATH = "../nawy_final_refined.xlsx"  # Path relative to backend/

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

# Setup OpenAI
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Setup DB
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_embedding(text: str):
    """Generate embedding for text using OpenAI."""
    try:
        response = await aclient.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

async def init_models():
    """Create tables."""
    async with engine.begin() as conn:
        print("Creating tables...")
        # Enable vector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.")

async def migrate_data():
    """Migrate data from Excel to Postgres."""
    if not os.path.exists(EXCEL_PATH):
        print(f"Excel file not found at {EXCEL_PATH}")
        return

    print(f"Reading data from {EXCEL_PATH}...")
    df = pd.read_excel(EXCEL_PATH)
    
    # Clean/Normalize column names if needed
    # Expected columns: valid_governorate, compound_name, price, final_price, etc.
    # We will map them to our Property model.
    
    async with AsyncSessionLocal() as session:
        count = 0
        for index, row in df.iterrows():
            try:
                # Construct description for embedding
                title = f"{row.get('property_type', 'Property')} in {row.get('compound_name', 'Unknown Compound')}"
                location = f"{row.get('valid_governorate', '')}, {row.get('city_name', '')}"
                
                # Check formatting
                try:
                    price = float(row.get('final_price', 0))
                except:
                    price = 0.0
                    
                try:
                    size_sqm = int(row.get('unit_area', 0))
                except:
                    size_sqm = 0
                
                try:
                    bedrooms = int(row.get('bedrooms', 0))
                except:
                    bedrooms = 0

                finishing = str(row.get('finishing_type', 'Core & Shell'))
                
                description = (
                    f"Luxury {row.get('property_type', 'property')} in {row.get('compound_name', '')}, {location}. "
                    f"Size: {size_sqm} sqm, Bedrooms: {bedrooms}, Finishing: {finishing}. "
                    f"Price: {price:,.0f} EGP."
                )

                # Generate Embedding
                embedding = await get_embedding(description)
                
                # Create Property Object
                prop = Property(
                    title=title,
                    description=description,
                    location=location,
                    price=price,
                    size_sqm=size_sqm,
                    bedrooms=bedrooms,
                    finishing=finishing,
                    embedding=embedding,
                    is_available=True
                )
                
                session.add(prop)
                count += 1
                
                if count % 10 == 0:
                    print(f"Processed {count} properties...")
                    await session.commit()
                    
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        await session.commit()
        print(f"Migration complete. Imported {count} properties.")

async def main():
    await init_models()
    await migrate_data()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
