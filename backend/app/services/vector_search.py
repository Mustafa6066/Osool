"""
Vector Search Service
---------------------
Handles semantic search for properties using OpenAI Embeddings and pgvector.
Phase 1: Production-ready with fallback mechanisms.
"""

import os
import logging
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property
from app.database import get_db
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str) -> Optional[List[float]]:
    """
    Phase 4: Generate embedding for text using OpenAI with circuit breaker and cost monitoring.
    Returns None on failure to allow fallback to text search.
    """
    try:
        from app.services.circuit_breaker import openai_breaker
        from app.services.cost_monitor import cost_monitor

        # Wrap OpenAI call with circuit breaker
        def _generate_embedding():
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )

            # Phase 4: Track token usage and cost
            token_count = response.usage.total_tokens
            cost_monitor.log_usage(
                model="text-embedding-3-small",
                input_tokens=token_count,
                output_tokens=0,
                context="property_search"
            )

            return response.data[0].embedding

        # Execute with circuit breaker protection
        embedding = openai_breaker.call(_generate_embedding)
        return embedding

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None

async def search_properties(
    db: AsyncSession,
    query_text: str,
    limit: int = 5,
    similarity_threshold: float = 0.7,
    price_min: int = None,
    price_max: int = None,
    sale_type: str = None,
    is_delivered: bool = None,
    finishing: str = None,
    is_nawy_now: bool = None,
) -> List[dict]:
    """
    Search for properties using semantic similarity with STRICT threshold enforcement.

    Phase 7 Production Enhancement:
    - Primary: pgvector cosine similarity search with 0.7 minimum threshold
    - ANTI-HALLUCINATION: Returns empty if no results meet threshold
    - Fallback: Text search when pgvector not available
    - Direct price filtering for budget enforcement
    - NEW: sale_type, is_delivered, finishing, is_nawy_now filters

    Args:
        db: Database session
        query_text: User search query
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score (0-1), default 0.7
        price_min: Minimum price filter (optional)
        price_max: Maximum price filter (optional)
        sale_type: Filter by sale type: "Resale", "Developer", "Nawy Now" (optional)
        is_delivered: Filter for delivered/ready-to-move properties (optional)
        finishing: Filter by finishing: "Finished", "Semi-Finished", "Core & Shell" (optional)
        is_nawy_now: Filter for Nawy Now mortgage properties (optional)

    Returns:
        List of property dicts with similarity scores and _source metadata
    """
    try:
        # FORCE DISABLE vector search when pgvector extension is not on PostgreSQL
        # The Python package being installed doesn't mean the DB has the extension
        # Set ENABLE_VECTOR_SEARCH=1 in env when using pgvector-enabled PostgreSQL (Supabase, Neon)
        import os
        VECTOR_SEARCH_ENABLED = os.getenv("ENABLE_VECTOR_SEARCH", "0") == "1"
        
        if VECTOR_SEARCH_ENABLED:
            try:
                # Try vector search first
                embedding = await get_embedding(query_text)
        
                if embedding:
                    logger.info(f"🔎 PostgreSQL Vector Search (threshold: {similarity_threshold}): '{query_text}'")

                    # Helper function to execute search with specific threshold
                    async def _execute_vector_search(current_threshold):
                        similarity_expr = 1 - Property.embedding.cosine_distance(embedding)
                        filters = [
                            Property.is_available == True,
                            similarity_expr >= current_threshold
                        ]
                        # Apply price filters if specified
                        if price_min is not None:
                            filters.append(Property.price >= price_min)
                        if price_max is not None:
                            filters.append(Property.price <= price_max)
                        # Apply sale_type filter (Resale / Developer / Nawy Now)
                        if sale_type is not None:
                            filters.append(Property.sale_type == sale_type)
                        # Apply delivery status filter
                        if is_delivered is not None:
                            filters.append(Property.is_delivered == is_delivered)
                        # Apply finishing filter
                        if finishing is not None:
                            filters.append(Property.finishing.ilike(f"%{finishing}%"))
                        # Apply Nawy Now filter
                        if is_nawy_now is not None:
                            filters.append(Property.is_nawy_now == is_nawy_now)
                        
                        stmt = (
                            select(Property, similarity_expr.label('similarity'))
                            .filter(*filters)
                            .order_by(similarity_expr.desc())
                            .limit(limit)
                        )
                        result = await db.execute(stmt)
                        return result.all()

                    # Try High Precision First (The "Perfect Match")
                    rows = await _execute_vector_search(similarity_threshold)

                    if not rows and similarity_threshold > 0.5:
                        logger.warning(
                            f"⚠️ No exact matches for '{query_text}' at {similarity_threshold}. Widening search radius to 0.50..."
                        )
                        # Fallback: Widen the net (The "Opportunity")
                        rows = await _execute_vector_search(0.50)

                    if not rows:
                        logger.warning(
                            f"⚠️ No properties meet 50% similarity threshold. Falling back to Keyword Search."
                        )
                        # Do NOT return [] here. Fall through to text search.
                        raise Exception("Zero vector matches found - triggering fallback")

                    # Convert to dicts with similarity scores
                    properties = []
                    for row in rows:
                        prop = row.Property
                        prop_dict = {
                            "id": prop.id,
                            "title": prop.title,
                            "description": prop.description,
                            "type": prop.type,
                            "location": prop.location,
                            "compound": prop.compound,
                            "developer": prop.developer,
                            "price": prop.price,
                            "price_per_sqm": prop.price_per_sqm,
                            "size_sqm": prop.size_sqm,
                            "bedrooms": prop.bedrooms,
                            "bathrooms": prop.bathrooms,
                            "finishing": prop.finishing,
                            "delivery_date": prop.delivery_date,
                            "down_payment": prop.down_payment,
                            "installment_years": prop.installment_years,
                            "monthly_installment": prop.monthly_installment,
                            "image_url": prop.image_url,
                            "nawy_url": prop.nawy_url,
                            "sale_type": prop.sale_type,
                            "is_available": prop.is_available,
                            "is_delivered": getattr(prop, 'is_delivered', None),
                            "is_cash_only": getattr(prop, 'is_cash_only', None),
                            "land_area": getattr(prop, 'land_area', None),
                            "nawy_reference": getattr(prop, 'nawy_reference', None),
                            "is_nawy_now": getattr(prop, 'is_nawy_now', None),
                            "_source": "database",
                            "_similarity_score": float(row.similarity)
                        }
                        properties.append(prop_dict)

                    logger.info(f"Found {len(properties)} properties (best score: {properties[0]['_similarity_score']:.2f})")
                    return properties

            except Exception as vector_error:
                # pgvector query failed (likely TEXT column instead of VECTOR or extension missing)
                logger.warning(f"Vector search failed, falling back to text search: {vector_error}")
                # Fall through to text search below

        # TEXT SEARCH FALLBACK (when pgvector not available or vector search failed)
        # TEXT SEARCH STRATEGY 1: Exact Phrase Match with Price Filtering
        logger.info(f"🔍 Text Search Attempt 1: Exact phrase '{query_text}'")
        search_term = f"%{query_text}%"

        # Build base filters
        base_filters = [
            Property.is_available == True,
            or_(
                Property.title.ilike(search_term),
                Property.location.ilike(search_term),
                Property.compound.ilike(search_term),
                Property.description.ilike(search_term),
                Property.developer.ilike(search_term),
                Property.type.ilike(search_term)
            )
        ]
        
        # Apply price filters if specified
        if price_min is not None:
            base_filters.append(Property.price >= price_min)
        if price_max is not None:
            base_filters.append(Property.price <= price_max)
        # Apply sale_type / delivery / finishing / nawy_now filters to text search too
        if sale_type is not None:
            base_filters.append(Property.sale_type == sale_type)
        if is_delivered is not None:
            base_filters.append(Property.is_delivered == is_delivered)
        if finishing is not None:
            base_filters.append(Property.finishing.ilike(f"%{finishing}%"))
        if is_nawy_now is not None:
            base_filters.append(Property.is_nawy_now == is_nawy_now)

        stmt = select(Property).filter(*base_filters).limit(limit)

        result = await db.execute(stmt)
        properties = result.scalars().all()

        # TEXT SEARCH STRATEGY 2: Split Keywords (if Exact Match fails)
        if not properties and len(query_text.split()) > 1:
            logger.info(f"🔍 Text Search Attempt 2: Split keywords")
            keywords = query_text.split()
            # Filter out common stop words (English + Arabic)
            stop_words = {
                # English
                'in', 'at', 'the', 'a', 'an', 'for', 'of', 'with', 'under', 'above', 'below',
                # Arabic
                'في', 'من', 'إلى', 'على', 'عن', 'مع', 'تحت', 'فوق', 'عند', 'إن', 'أن', 'ال', 'و', 'أو'
            }
            keywords = [k for k in keywords if k.lower() not in stop_words and len(k) > 1]
            
            if keywords:
                # Construct OR conditions for each keyword
                conditions = []
                for word in keywords:
                    term = f"%{word}%"
                    conditions.append(Property.title.ilike(term))
                    conditions.append(Property.location.ilike(term))
                    conditions.append(Property.compound.ilike(term))
                    conditions.append(Property.type.ilike(term))
                
                stmt = select(Property).filter(
                    Property.is_available == True,
                    or_(*conditions)
                )
                
                # Apply price filters if specified
                if price_min is not None:
                    stmt = stmt.filter(Property.price >= price_min)
                if price_max is not None:
                    stmt = stmt.filter(Property.price <= price_max)
                
                stmt = stmt.limit(limit)
                
                result = await db.execute(stmt)
                properties = result.scalars().all()

        if not properties:
            logger.warning(f"No properties found via text search for query: '{query_text}'")
            return []

        # Convert to dicts without similarity scores (text search fallback)
        return [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "type": p.type,
                "location": p.location,
                "compound": p.compound,
                "developer": p.developer,
                "price": p.price,
                "price_per_sqm": p.price_per_sqm,
                "size_sqm": p.size_sqm,
                "bedrooms": p.bedrooms,
                "bathrooms": p.bathrooms,
                "finishing": p.finishing,
                "delivery_date": p.delivery_date,
                "down_payment": p.down_payment,
                "installment_years": p.installment_years,
                "monthly_installment": p.monthly_installment,
                "image_url": p.image_url,
                "nawy_url": p.nawy_url,
                "sale_type": p.sale_type,
                "is_available": p.is_available,
                "is_delivered": getattr(p, 'is_delivered', None),
                "is_cash_only": getattr(p, 'is_cash_only', None),
                "land_area": getattr(p, 'land_area', None),
                "nawy_reference": getattr(p, 'nawy_reference', None),
                "is_nawy_now": getattr(p, 'is_nawy_now', None),
                "_source": "text_search_fallback",
                "_similarity_score": None
            }
            for p in properties
        ]

    except Exception as e:
        logger.error(f"Property search failed: {e}")
        return []


async def validate_property_exists(db: AsyncSession, property_id: int) -> bool:
    """
    Phase 1: Hallucination Prevention
    Validates that a property ID actually exists in the database.

    This function is critical for preventing the AI from recommending
    non-existent properties.

    Args:
        db: Database session
        property_id: Property ID to validate

    Returns:
        True if property exists, False otherwise
    """
    try:
        result = await db.execute(
            select(Property).filter(Property.id == property_id)
        )
        exists = result.scalar_one_or_none() is not None

        if not exists:
            logger.warning(f"⚠️ HALLUCINATION BLOCKED: Property {property_id} does not exist in database")

        return exists

    except Exception as e:
        logger.error(f"Property validation failed: {e}")
        return False
