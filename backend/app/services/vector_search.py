"""
Vector Search Service
---------------------
Handles semantic search for properties using OpenAI Embeddings and pgvector.
"""

import os
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property
from app.database import get_db
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

async def search_properties(db: AsyncSession, query_text: str, limit: int = 5):
    """
    Search for properties using semantic similarity.
    """
    embedding = await get_embedding(query_text)
    if not embedding:
        return []

    # Cosine distance search using pgvector
    # Note: operator <-> is L2 distance, <=> is cosine distance, <#> is negative inner product
    # We use <=> for cosine distance (lower is better)
    stmt = select(Property).order_by(
        Property.embedding.cosine_distance(embedding)
    ).limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()
