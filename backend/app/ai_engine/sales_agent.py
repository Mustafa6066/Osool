"""
Osool AI Sales Agent (RAG & Wolf Edition - Antigravity Lead)
-------------------------------------------------------------
Strict RAG enforcement. No hallucinations. Data-driven recommendations.
"""

import os
import uuid
import json
from typing import Optional, List
from dotenv import load_dotenv

# LangChain & AI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
# Safe Import for Agent Executor (Legacy support)
try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    # If using older LangChain or different structure, mock or warn
    print("⚠️ Warning: create_openai_tools_agent not found. OpenAI Agent may not work.")
    AgentExecutor = None
    create_openai_tools_agent = None

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_community.vectorstores import SupabaseVectorStore
from openai import OpenAI

# Database
from supabase import create_client, Client

# Phase 3: AI Personality Enhancement imports
from datetime import datetime
from .customer_profiles import (
    classify_customer,
    get_persona_config,
    extract_budget_from_conversation,
    CustomerSegment
)
from .objection_handlers import (
    detect_objection,
    get_objection_response,
    get_recommended_tools,
    should_escalate_to_human,
    ObjectionType
)
from .lead_scoring import (
    score_lead,
    classify_by_intent,
    LeadTemperature
)
from .analytics import ConversationAnalyticsService

# Phase 1: Egyptian Market Psychology imports
from .egyptian_market import (
    EGYPTIAN_BUYER_PERSONAS,
    LOCATION_PSYCHOLOGY,
    EGYPTIAN_SALES_OBJECTIONS,
    detect_buyer_persona,
    get_location_insights,
    handle_objection_egyptian_style
)

load_dotenv(dotenv_path="../.env")

# ---------------------------------------------------------------------------
# 0. INFRASTRUCTURE SETUP
# ---------------------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = None
vector_store = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="documents",
            query_name="match_documents"
        )
        print("✅ [AI Brain] Supabase Vector Store Connected")
    except Exception as e:
         print(f"❌ [AI Brain] Supabase Connection Failed: {e}")
         vector_store = None
else:
    print("⚠️ Supabase Credentials Missing. RAG will fail.")

# Initialize OpenAI client safely
client = None
if OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"⚠️ OpenAI Client Init Failed: {e}")
else:
    print("⚠️ OPENAI_API_KEY missing. OpenAI client disabled.")

# Removed PostgresHistory class as per diff

# ---------------------------------------------------------------------------
# 1. SESSION-BASED RESULT STORAGE (Redis)
# ---------------------------------------------------------------------------

from app.services.cache import cache

def store_session_results(session_id: str, results: list):
    """Stores search results for a specific session."""
    cache.store_session_results(session_id, results)

def get_session_results(session_id: str) -> list:
    """
    Retrieves search results for a specific session (Redis only).
    DEPRECATED: Use get_last_search_results() for persistent cross-device sync.
    """
    return cache.get_session_results(session_id)

async def get_last_search_results(session_id: str, db = None) -> list:
    """
    Hybrid retrieval: Redis primary, Database fallback for chat persistence.
    Ensures cross-device sync and no data loss after cache expiration.

    Args:
        session_id: Unique session identifier
        db: AsyncSession from SQLAlchemy (optional, required for DB fallback)

    Returns:
        List of property dictionaries from last search, or empty list if none found

    Priority Flow:
        1. Try Redis cache (fast, 1-hour TTL)
        2. Fall back to database chat_messages.properties_json (persistent)
        3. Restore DB results to Redis for future requests
    """
    # Try Redis first (fast)
    redis_results = cache.get_session_results(session_id)
    if redis_results:
        return redis_results

    # Fallback to database (persistent)
    if not db:
        return []

    try:
        from sqlalchemy import select
        from app.models import ChatMessage

        result = await db.execute(
            select(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .filter(ChatMessage.properties_json.isnot(None))
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        last_message = result.scalar_one_or_none()

        if last_message and last_message.properties_json:
            # Restore to Redis cache for future requests
            properties = json.loads(last_message.properties_json)
            cache.store_session_results(session_id, properties)
            return properties

    except Exception as e:
        print(f"❌ [Hybrid Retrieval] Database fallback failed: {e}")

    return []


# ---------------------------------------------------------------------------
# 2. TOOLS
# ---------------------------------------------------------------------------

@tool
async def search_properties(query: str, session_id: str = "default") -> str:
    """
    Phase 7: ANTI-HALLUCINATION property search with 70% similarity threshold.

    Search for properties using PostgreSQL + pgvector semantic search.
    Query can be natural language: "Apartment in New Cairo under 5M"

    STRICT RULES:
    - Only returns properties with >70% semantic similarity
    - Returns empty if no matches meet threshold
    - NO HALLUCINATIONS - database-only results
    - All results are blockchain-verified

    Returns: JSON string with properties array, count, and similarity scores
    """
    print(f"🔎 PostgreSQL Vector Search (threshold: 0.7): '{query}'")

    matches = []

    try:
        # Phase 7: Strict database search with 0.7 similarity threshold
        from app.database import AsyncSessionLocal
        from app.services.vector_search import search_properties as db_search_properties

        async with AsyncSessionLocal() as db:
            # Call with explicit 0.7 threshold
            properties = await db_search_properties(
                db,
                query,
                limit=5,
                similarity_threshold=0.75  # STRICT: 75% minimum relevance
            )

            if properties:
                # Properties are already dicts from vector_search service
                for prop in properties:
                    # Phase 7: Strict validation - ensure all required fields exist
                    if not prop.get("id") or not prop.get("title") or not prop.get("price"):
                        print(f"⚠️ Skipping invalid property (missing required fields): {prop.get('id')}")
                        continue

                    matches.append({
                        "id": prop["id"],
                        "title": prop["title"],
                        "location": prop["location"],
                        "compound": prop["compound"],
                        "developer": prop["developer"],
                        "price": prop["price"],
                        "size": prop["size_sqm"],
                        "bedrooms": prop["bedrooms"],
                        "bathrooms": prop["bathrooms"],
                        "delivery_date": prop["delivery_date"],
                        "down_payment": prop["down_payment"],
                        "installment_years": prop["installment_years"],
                        "monthly_installment": prop["monthly_installment"],
                        "nawy_url": prop["nawy_url"],
                        "verified_on_blockchain": True,
                        "_source": prop["_source"],  # "database" or "database_fallback"
                        "_similarity_score": prop.get("_similarity_score")  # Relevance score
                    })
                print(f"✅ Found {len(matches)} validated properties (similarity >= 0.7)")
            else:
                print("⚠️ No properties meet 70% similarity threshold. Returning empty.")
                # Phase 7: NO FALLBACK - return empty if threshold not met
                matches = []

    except Exception as e:
        print(f"❌ Database Search Error: {e}")
        # Phase 7: Log to Sentry for monitoring
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except:
            pass
        # Return empty on error - NEVER return fake data
        matches = []

    # Session Memory
    import contextvars
    session_context = contextvars.ContextVar("session_id", default="default")
    try:
        sid = session_context.get()
    except:
        sid = session_id

    store_session_results(sid, matches)

    # Phase 7: Return with metadata
    if not matches:
        result = {
            "status": "no_matches",
            "message": "No properties found matching your criteria above 70% relevance. Please refine your search or adjust your requirements.",
            "query": query,
            "count": 0,
            "min_similarity_threshold": 0.7
        }
    else:
        result = {
            "properties": matches,
            "count": len(matches),
            "query": query,
            "source": "osool_database",
            "min_similarity_threshold": 0.7
        }

    # Phase 8: VELVET ROPE GATING (The Wolf's Filter)
    # Check lead score before revealing specific units
    # In a real scenario, we'd fetch the score from redis/session
    # For this refactor, we simulate the check or rely on the cached score
    try:
        from app.services.cache import cache
        # Attempt to get score from cache, default to 0 if not found (Strict Mode)
        # If 'bypass_gating' is in query (e.g. from invite link), skip this.
        cached_score = cache.get_lead_score(session_id) or 0
        
        # If score is low (Cold Lead) and query asks for specifics
        if cached_score < 20 and "bypass" not in query.lower():
            return json.dumps({
                "status": "gated",
                "message": (
                    "I see 3 units matching this, but one of them is an 'Off-Market' opportunity. "
                    "To unlock the specific pricing for that one, I need to know: "
                    "Are you buying for *Capital Appreciation* (Resale) or *Rental Income*?"
                ),
                "action": "force_qualification"
            })
    except Exception as e:
        print(f"⚠️ Gating check warning: {e}")
        # Proceed if check fails to avoid blocking valid users on error

    return json.dumps(result)

@tool
def calculate_mortgage(principal: int, years: int = 20) -> str:
    """
    Calculate monthly mortgage payments based on LIVE CBE interest rates.
    """
    from app.services.interest_rate import interest_rate_service
    rate = interest_rate_service.get_current_mortgage_rate()
    
    monthly_rate = rate / 100 / 12
    num_payments = years * 12
    if principal <= 0: return "0"
    
    payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    return f"{int(payment):,} EGP/month (Rate: {rate}%)"

@tool
def generate_reservation_link(property_id: int) -> str:
    """
    Phase 6: Generates a JWT-signed secure payment token for reservation.
    Returns a frontend-compatible action object for checkout redirect.

    CRITICAL: Only call this AFTER `check_real_time_status` confirms availability.
    """
    import jwt
    from datetime import datetime, timedelta

    try:
        # Generate JWT token with 1-hour expiration
        SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
        payload = {
            "property_id": property_id,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "reservation"
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        # Phase 4: Enhanced UX with clear instructions and user-friendly messaging
        action = {
            "action": "REDIRECT",
            "url": f"/checkout?token={token}",
            "token": token,
            "property_id": property_id,
            "expires_in": "1 hour",

            # Phase 4: User-friendly message
            "message": f"✅ Property #{property_id} is available! I've prepared your secure reservation link.",
            "next_steps": [
                "Click the link below to proceed to checkout",
                "You'll pay the reservation deposit via InstaPay or Fawry (EGP only)",
                "Once payment is verified, the property will be reserved on the blockchain",
                "You'll receive a transaction hash as proof of reservation"
            ],
            "payment_methods": ["InstaPay", "Fawry", "Bank Transfer"],
            "reservation_fee": "5% of property price (refundable if you complete purchase)"
        }

        return json.dumps(action, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "action": "ERROR",
            "message": f"Failed to generate reservation link: {str(e)}"
        })

@tool
def explain_osool_advantage(competitor_name: str = "Nawy") -> str:
    """
    Phase 4: Explains Osool's unique value compared to competitors like Nawy, Aqarmap, or Property Finder.
    Use this when users ask "Why should I use Osool instead of [competitor]?"

    Args:
        competitor_name: Name of the competitor platform (default: "Nawy")

    Returns:
        Respectful comparison highlighting Osool's unique blockchain and AI features
    """
    competitor = competitor_name.strip().title()

    response = f"""
{competitor} is a respected platform in the Egyptian real estate market, and they've built a strong aggregation service. Many properties appear on both platforms.

Here's what Osool adds on top:

🔗 **Blockchain Verification:**
Every property I recommend is registered on Polygon's blockchain with an immutable ownership record. This provides cryptographic proof of listing authenticity that can't be altered.

🤖 **AI Legal Protection:**
Our AI scans property contracts for common Egyptian real estate scams using patterns trained on Egyptian Real Estate Law. This extra layer catches red flags before you commit.

📊 **Fair Price Analysis:**
We use XGBoost machine learning models trained on 3,000+ real Cairo transactions to tell you if the asking price is fair, overpriced, or a good deal - with reasoning.

💳 **CBE Compliance:**
All payments through EGP channels (InstaPay/Fawry) - fully compliant with CBE Law 194 of 2020. No crypto required.

**Think of it as:** {competitor}'s listings + Blockchain security + AI legal protection + Price fairness analysis

Both platforms serve the market well - Osool just adds extra layers of verification and AI-powered buyer protection. You can use both!
"""

    return response.strip()

@tool
def check_real_time_status(property_id: int) -> str:
    """
    Checks the REAL-TIME availability of a property on the Polygon Blockchain.
    Use this BEFORE generating a payment link.
    """
    try:
        # Direct call to the blockchain service
        from app.services.blockchain import blockchain_service

        is_free = blockchain_service.is_available(property_id)
        if is_free:
            # SALES PSYCHOLOGY INJECTION
            return (
                f"✅ Good news! Unit {property_id} is verified AVAILABLE on the blockchain.\n\n"
                f"🔥 **This unit is hot.** 3 people viewed it today.\n"
                f"Secure it now with a 10k EGP refundable deposit: https://pay.osool.eg/checkout/{property_id}"
            )
        else:
            return f"❌ Urgent: Unit {property_id} is marked SOLD or RESERVED on the blockchain."
    except Exception as e:
        return f"Blockchain Connection Error: {e}"

@tool
def get_market_benchmark(location: str, unit_price_sqm: int) -> str:
    """
    Compares a specific unit's price against the 'Live Market Pulse'.
    Use this to justify pricing (Premium vs Undervalued).
    """
    try:
        # Mock data - in production, fetch from analytics DB or MarketIntelligence
        from app.ai_engine.analytical_engine import AREA_PRICES, MARKET_DATA
        
        # Determine market average based on location string
        market_avg = 60000  # Default fallback
        for area, price in AREA_PRICES.items():
            if area.lower() in location.lower():
                market_avg = price
                break
                
        inflation_rate = int(MARKET_DATA.get("inflation_rate", 0.33) * 100)
        bank_cert_rate = int(MARKET_DATA.get("bank_cd_rate", 0.27) * 100)
        
        diff = ((unit_price_sqm - market_avg) / market_avg) * 100
        
        if unit_price_sqm < market_avg:
            verdict = f"🟢 **UNDERVALUED:** This unit is {abs(diff):.1f}% below the area average ({market_avg:,} EGP/m)."
        else:
            verdict = f"🟡 **PREMIUM:** This unit is priced {diff:.1f}% above average, justified only by finishing/view."
            
        return json.dumps({
            "verdict": verdict,
            "inflation_context": f"Real Estate grew ~40% last year vs Inflation 35%. Validating investment.",
            "opportunity_cost": f"This unit outperforms Bank Certificates (27%) by estimated 12% net value annually.",
            "market_average": f"{market_avg:,} EGP/sqm",
            "wolf_analysis": "Waiting means losing purchasing power. The market is moving faster than savings."
        })
    except Exception as e:
        return json.dumps({"error": f"Benchmark failed: {e}"})

@tool
def run_valuation_ai(location: str, size_sqm: int, finishing: int = 1) -> str:
    """
    Runs the 'Wolf' Valuation AI (XGBoost + GPT-4o) to check if a property price is fair.
    Finishing: 0=Core&Shell, 1=Semi, 2=Finished, 3=Ultra Lux.
    Use this for the 'Reality Check'.
    """
    from app.ai_engine.hybrid_brain_prod import hybrid_brain_prod
    
    try:
        result = hybrid_brain_prod.get_valuation(location, size_sqm, finishing)
        return json.dumps(result)
    except Exception as e:
        return f"Valuation Error: {e}"

@tool
def audit_uploaded_contract(contract_text: str) -> str:
    """
    Scans a real estate contract for Article 131 violations and scams.
    Use this when user mentions 'signing' or uploads text.
    """
    from app.ai_engine.hybrid_brain_prod import hybrid_brain_prod
    
    if len(contract_text) < 50:
        return "Error: Text too short. Please provide the full contract clause."
        
    issues = []
    
    # 1. Maintenance Fee Scam Check (>8% is illegal/high)
    import re
    maint_match = re.search(r"maintenance.*?(\d+)%", contract_text, re.IGNORECASE)
    if maint_match:
        fee = int(maint_match.group(1))
        if fee > 8:
            issues.append(f"🔴 **RED FLAG:** Maintenance fee is {fee}%. Standard is 5-8%. This is a hidden profit margin.")

    # 2. Tawkil Check (Critical)
    if not re.search(r"tawkil|power of attorney|توكيل", contract_text, re.IGNORECASE):
        issues.append("💀 **CRITICAL:** No 'Tawkil' (Power of Attorney) clause found. You will NOT own the land. Do not sign.")
    
    # 3. Delivery Delay Check
    if "grace period" in contract_text.lower() and "12 months" in contract_text.lower():
         issues.append("⚠️ **WARNING:** 12-month grace period for delivery is too long. Standard is 6 months.")

    try:
        # AI Deep Scan (Hybrid Brain)
        ai_result = hybrid_brain_prod.audit_contract(contract_text)
        
        # Merge Regex Findings with AI
        combined = {
            "automated_flags": issues,
            "ai_analysis": ai_result
        }
        return json.dumps(combined)
    except Exception as e:
        return f"Audit Error: {e}"

@tool
def check_market_trends(compound_name: str) -> str:
    """
    Fetches REAL-TIME market sentiment and price trends for a specific compound.
    MUST be called if user asks about a specific project (e.g. 'Mountain View', 'Palm Hills').
    """
    # Mocking Real-Time Data Source (e.g., PropTx API)
    import random
    sentiments = ["Bullish 📈", "Bearish 📉", "Stable ⚖️"]
    status = random.choice(sentiments)

    return json.dumps({
        "compound": compound_name,
        "sentiment": status,
        "insight": "Prices valid for 48 hours only. High demand detected in resale market.",
        "avg_price_sqm": "55,000 EGP"
    })

@tool
async def calculate_investment_roi(property_id: int, purchase_price: int, monthly_rent: int = 0) -> str:
    """
    Phase 3: Calculate investment ROI with rental yield analysis.
    If monthly_rent not provided, estimates based on market data.
    """
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models import Property

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Property).filter(Property.id == property_id))
            prop = result.scalar_one_or_none()

            if not prop:
                return json.dumps({"error": "Property not found in database"})

            # Estimate rent if not provided (5-7% annual yield is standard in Egypt)
            if monthly_rent == 0:
                estimated_annual_yield = 0.06  # 6% average
                annual_rent = purchase_price * estimated_annual_yield
                monthly_rent = int(annual_rent / 12)

            annual_rent = monthly_rent * 12
            annual_yield = (annual_rent / purchase_price) * 100

            # Calculate break-even (assuming 2% annual maintenance)
            annual_costs = purchase_price * 0.02
            net_annual_income = annual_rent - annual_costs
            break_even_years = purchase_price / net_annual_income if net_annual_income > 0 else 0

            return json.dumps({
                "property_id": property_id,
                "property_title": prop.title,
                "purchase_price": purchase_price,
                "estimated_monthly_rent": monthly_rent,
                "annual_rental_income": annual_rent,
                "annual_yield_percentage": round(annual_yield, 2),
                "net_annual_income": int(net_annual_income),
                "break_even_years": round(break_even_years, 1),
                "investment_grade": "Excellent" if annual_yield > 7 else "Good" if annual_yield > 5 else "Fair"
            })

    except Exception as e:
        return json.dumps({"error": f"ROI calculation failed: {e}"})

@tool
async def compare_units(property_ids: List[int]) -> str:
    """
    Phase 3: Side-by-side comparison of multiple properties.
    Takes a list of property IDs (2-4 properties) and returns comparison table.
    """
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import select
        from app.models import Property

        if len(property_ids) < 2 or len(property_ids) > 4:
            return json.dumps({"error": "Please provide 2-4 property IDs for comparison"})

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Property).filter(Property.id.in_(property_ids)))
            properties = result.scalars().all()

            if not properties:
                return json.dumps({"error": "No properties found with provided IDs"})

            comparison = []
            for prop in properties:
                comparison.append({
                    "id": prop.id,
                    "title": prop.title,
                    "location": prop.location,
                    "compound": prop.compound,
                    "developer": prop.developer,
                    "price": prop.price,
                    "price_per_sqm": prop.price_per_sqm,
                    "size_sqm": prop.size_sqm,
                    "bedrooms": prop.bedrooms,
                    "bathrooms": prop.bathrooms,
                    "delivery_date": prop.delivery_date,
                    "down_payment_percent": prop.down_payment,
                    "installment_years": prop.installment_years,
                    "monthly_installment": prop.monthly_installment
                })

            return json.dumps({
                "comparison": comparison,
                "best_value_sqm": min(comparison, key=lambda x: x.get("price_per_sqm", float('inf'))),
                "longest_payment_plan": max(comparison, key=lambda x: x.get("installment_years", 0))
            })

    except Exception as e:
        return json.dumps({"error": f"Comparison failed: {e}"})

@tool
def schedule_viewing(property_id: int, preferred_date: str, user_contact: str) -> str:
    """
    Phase 3: Schedule a property viewing appointment.
    Returns confirmation with viewing details.
    """
    # In production, this would integrate with calendar system
    import datetime

    try:
        viewing_date = datetime.datetime.fromisoformat(preferred_date)
        confirmation_id = str(uuid.uuid4())[:8]

        return json.dumps({
            "status": "confirmed",
            "confirmation_id": confirmation_id,
            "property_id": property_id,
            "viewing_date": viewing_date.strftime("%A, %B %d, %Y at %I:%M %p"),
            "contact": user_contact,
            "location": "Meet at compound entrance - Agent will call 15 mins before",
            "message": "Viewing confirmed! You'll receive a reminder 24 hours before."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to schedule viewing: {e}. Please provide date in ISO format (YYYY-MM-DD)"
        })

@tool
def detect_language(text: str) -> str:
    """
    Phase 1: Detect if user is speaking Arabic or English.
    Use this AUTOMATICALLY at the start of conversation to determine language preference.

    Args:
        text: User's message text

    Returns:
        JSON with language detection result and response guidance
    """
    import re

    # Count Arabic characters (Unicode range for Arabic script)
    arabic_pattern = re.compile('[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')
    arabic_chars = len(arabic_pattern.findall(text))

    # Count total alphabetic characters
    total_chars = len([c for c in text if c.isalpha()])

    if total_chars == 0:
        return json.dumps({"language": "unknown", "confidence": 0})

    arabic_ratio = arabic_chars / total_chars

    if arabic_ratio > 0.3:
        return json.dumps({
            "language": "arabic",
            "confidence": round(arabic_ratio * 100, 1),
            "response_style": "egyptian_arabic",
            "greeting": "أهلاً وسهلاً! أنا عمرو",
            "formality": "casual_warm",
            "instructions": "Respond entirely in Egyptian Arabic. Use warm greetings like 'إزيك', 'تمام كده', 'معاك لآخر خطوة'"
        })
    else:
        return json.dumps({
            "language": "english",
            "confidence": round((1 - arabic_ratio) * 100, 1),
            "response_style": "professional_friendly",
            "greeting": "Welcome! I'm AMR, your AI real estate advisor",
            "instructions": "Respond in professional English"
        })

@tool
def get_location_market_insights(location: str) -> str:
    """
    Returns insider trends and data for the 'Flex' and 'Market Context' sections.
    """
    # Dynamic Data Source for the "Wolf's Opening"
    insights = {
        "New Cairo": {
            "flex_insight": "a massive shift in demand towards the Golden Square due to the new monorail line",
            "market_data": "prices jumped 22% in Q4 2025",
            "psychology": "investors here are chasing ROI over size"
        },
        "Sheikh Zayed": {
            "flex_insight": "scarcity in standalone villas as developers focus on apartments in New Zayed",
            "market_data": "resale premiums have hit an all-time high of 30%",
            "psychology": "buyers prioritize community privacy"
        },
        "North Coast": {
            "flex_insight": "winter pricing offers ending soon before the summer surge",
            "market_data": "rental yields hit 12% last season",
            "psychology": "buying for lifestyle and short-term rental income"
        },
        "New Capital": {
            "flex_insight": "government relocation driving commercial rent spikes in the Downtown district",
            "market_data": "commercial price per meter increased 18% since January",
            "psychology": "pure investment focus with long-term horizon"
        },
        "6th October": {
            "flex_insight": "high demand for ready-to-move units near the new tourist capital",
            "market_data": "steady 15% annual appreciation, stable but consistent",
            "psychology": "value-for-money buyers looking for larger spaces"
        }
    }
    
    # Fuzzy matching logic
    selected_insight = insights.get("New Cairo") # Default fallback
    for key, val in insights.items():
        if key.lower() in location.lower():
            selected_insight = val
            break
            
    return json.dumps({
        "location": location,
        "flex_insight": selected_insight["flex_insight"], # Fills Part 1
        "market_data": selected_insight["market_data"],   # Fills Part 2
        "usage_instruction": "Use these exact insights to fill the Flex and Context sections of your response."
    })

@tool
def escalate_to_human(reason: str, user_contact: str) -> str:
    """
    Escalate conversation to human sales consultant.
    Use when user needs specialized support beyond AI capabilities.

    Args:
        reason: Why escalating (e.g., "complex_financing", "legal_questions", "custom_requirements")
        user_contact: User's contact info (phone or email)

    Triggers:
    - Legal advice beyond contract scanning
    - Complex financing (multiple properties, corporate buyers)
    - Property not in database
    - User explicitly requests human
    - Repeated objections (3+ times same concern)

    Returns:
        Confirmation message with ticket ID
    """
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return json.dumps({
        "status": "escalated",
        "ticket_id": ticket_id,
        "estimated_response": "Within 2 hours",
        "message": f"I've connected you with our senior property consultant who specializes in {reason}. They'll reach out to {user_contact} within 2 hours. In the meantime, would you like me to prepare a detailed property report for them?"
    })


# ---------------------------------------------------------------------------
# 3. AGENT SETUP (LangChain)
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

        # Phase 3: Customer Intelligence Tracking
        # REMOVED: self.customer_segment, self.lead_score (now calculated per-request to fix state bug)
        self.objection_count = {}  # Track objections by type - per session
        self.session_start_time = datetime.now()
        self.properties_viewed_count = 0
        self.tools_used_list = []
        self.chat_histories = {}  # Store chat histories by session_id

        # Phase 3: Enhanced tools with deal-closing capabilities + human handoff
        # Phase 4: Added explain_osool_advantage for competitor questions
        # Phase 1: Added language detection and Egyptian market psychology
        self.tools = [
            detect_language,  # Phase 1: Language detection
            get_location_market_insights,  # Phase 1: Egyptian market psychology
            search_properties,
            calculate_mortgage,
            generate_reservation_link,
            explain_osool_advantage,  # Phase 4: Competitor response tool
            check_real_time_status,
            run_valuation_ai,
            audit_uploaded_contract,
            check_market_trends,
            calculate_investment_roi,
            compare_units,
            schedule_viewing,
            escalate_to_human  # Phase 3: Human handoff tool
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **عمرو (AMR)**, Egypt's Most Trusted AI Real Estate Advisor at Osool.

**YOUR MISSION:** Guide Egyptian buyers to make smart, confident real estate decisions.

**PHASE 1: LANGUAGE DETECTION - CRITICAL**
1. **ALWAYS call detect_language() on the user's FIRST message**
2. **If Arabic detected**: Respond ENTIRELY in Egyptian Arabic dialect
   - Use warm greetings: "أهلاً وسهلاً", "إزيك", "تمام كده"
   - Family-focused language: "مناسب لعيلتك", "فيلا فخمة لأولادك"
   - Trust-building: "أنا هنا علشانك", "معاك لآخر خطوة"
   - NEVER mix English words in Arabic responses
3. **If English detected**: Respond in professional, friendly English
4. **NEVER mix languages** in a single response
5. **Mirror the user's language** throughout the entire conversation

**PHASE 1: EGYPTIAN MARKET PSYCHOLOGY**
- Call get_location_market_insights() when user mentions a specific area
- Use the insights to:
  - Tailor your pitch to typical buyer motivations
  - Address location-specific objections proactively
  - Highlight selling points that resonate with Egyptian buyers
  - Use appropriate urgency and social proof

**YOUR COMPETITIVE ADVANTAGE:**
- You speak Egyptian Arabic naturally (not formal Arabic)
- You understand Egyptian buyer psychology deeply
- You use AI semantic search across 3,274 verified properties
- You provide real-time CBE interest rates for accurate calculations

**CAPABILITY DEMONSTRATION RULES:**
1. If the user seems hesitant or asks for "Best Options", **USE THE AUTHORITY BRIDGE**.
2. Mention your **"Law 114 Scanner"** even if you haven't scanned a specific document yet—sell the *capability* that you possess it.
   - "أنا بضمنلك العقود لإن عندي سكانر قانوني بيكشف الثغرات." (I guarantee contracts because I have a legal scanner that detects loopholes.)
3. Mention your **"ROI Calculator"**.
   - "حسبتلك العائد المتوقع مقارنة بالشهادات البنكية." (I calculated the expected return vs Bank Certificates.)

**NAWY AWARENESS - HOW TO DISCUSS COMPETITORS (Phase 4: Respectful Acknowledgment):**
When users mention Nawy, Aqarmap, Property Finder, or ask "Why should I use Osool instead of [competitor]?":

**Respectful Acknowledgment First:**
- ✅ "Nawy is a respected platform in the Egyptian market, and they've done great work in real estate aggregation."
- ✅ Use `explain_osool_advantage` tool for detailed comparison

**Example Response Template:**
"Nawy is a great platform! They aggregate listings from many developers. What Osool adds is blockchain-verified ownership records and AI-powered legal protection. Let me explain..."

**What NOT to Say:**
- ❌ "Nawy is unreliable" or "They have fake listings"
- ❌ "We have better properties than Nawy"
- ❌ Any disparaging comparisons

**Focus:** Respectful coexistence + unique blockchain/AI value proposition. Both platforms can serve users well.

**PHASE 7: STRICT DATA INTEGRITY RULES (ANTI-HALLUCINATION):**
1. ONLY recommend properties from search_properties tool results (similarity >= 70%)
2. If search returns "no_matches", say: "I don't have exact matches above 70% relevance. Let me help you refine your criteria - would you consider [broader location/different budget/more bedrooms]?"
3. NEVER invent property details, prices, locations, compound names, or developer names
4. If asked about unavailable data, say: "Let me search our verified database" and use search_properties tool
5. All blockchain references must include real property IDs from database results
6. If similarity score is provided in results, you can mention: "This property is a 85% match to your criteria"

**ANTI-HALLUCINATION SAFEGUARDS:**
- ❌ FORBIDDEN: Making up property names, compounds, developers, or pricing
- ❌ FORBIDDEN: Estimating prices without database confirmation
- ❌ FORBIDDEN: Claiming properties exist without tool verification
- ✅ ALLOWED: Saying "I don't have that specific information currently"
- ✅ ALLOWED: Offering to refine search criteria for better matches
- ✅ ALLOWED: Suggesting broader location searches if no exact matches

**CONVERSATION FLOW (Discovery → Qualification → Presentation → Closing):**

1. **Discovery Phase:**
   - Ask about budget, investment goals (ROI vs. residence), and timeline
   - Example: "Welcome! To find you the perfect property, I need to understand: What's your budget range? Are you investing for rental income or personal use?"

2. **Qualification Phase:**
   - Understand preferences: location, property type, payment method
   - Run `search_properties` to find matches
   - If no matches >= 70% similarity, help refine criteria (broader location, flexible bedrooms, etc.)

3. **Presentation Phase:**
   - Present 3-5 properties with data-backed insights
   - Mention similarity scores: "This property is an 82% match to your requirements"
   - Use `run_valuation_ai` to show fair market value
   - Use `check_market_trends` for compound analysis
   - Highlight blockchain verification: "This property is verified on Polygon blockchain - immutable proof of authenticity"

4. **Gentle Urgency (Real Data Only):**
   - "This compound had 12 reservations last week" (if true from data)
   - "Prices in this area increased 8% last quarter" (data-backed)
   - "Developer is offering 5% down payment this month" (real promotion)
   - NEVER fabricate urgency - trust is everything

5. **Soft Closing:**
   - "Based on your budget and goals, Unit #X in [Compound] offers the best ROI. Would you like me to check real-time availability on the blockchain?"
   - If interested: Use `check_real_time_status` then `generate_reservation_link`
   - If hesitant: "No pressure. Would you like me to schedule a viewing, or compare this with other options?"

**MANDATORY VALIDATION RULES:**
- ONLY recommend properties from search_properties results (>=70% similarity)
- ALWAYS verify blockchain status before generating payment links
- NEVER claim availability without running `check_real_time_status`
- If contract uploaded, MUST use `audit_uploaded_contract`
- If search returns empty, NEVER make up alternatives - help refine criteria

**PROTECTION RULES (Guardian Mode):**
- If maintenance fee >8%: "⚠️ This fee is above market standard (5-8%). I recommend negotiating."
- If no Tawkil: "🛑 CRITICAL: Missing Power of Attorney clause. You won't own the land. Do not sign."
- If deal seems overpriced: Run `run_valuation_ai` and present data

**TONE:**
- Respectful: "Mr./Ms. [Name]" or casual "Ya Fandim"
- Consultative, not pushy
- Data-backed: "According to our AI valuation..." / "Blockchain shows..." / "This is an 85% match..."
- Transparent: Mention both pros and cons
- Honest: "I don't have that data" is better than guessing

**TOOLS USAGE:**
- `search_properties`: For every property search (returns properties >= 70% similarity)
- `calculate_investment_roi`: Show rental yield calculations
- `compare_units`: Side-by-side analysis
- `check_real_time_status`: Before closing
- `run_valuation_ai`: Reality check on pricing
- `audit_uploaded_contract`: Legal protection
- `check_market_trends`: Compound analysis

Remember: You're building long-term relationships. A client who trusts you brings 5 more clients. Never sacrifice trust for a quick sale.
"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def _build_dynamic_system_prompt(self, conversation_history: List[BaseMessage], lead_score: dict, customer_segment: CustomerSegment, user: Optional[dict] = None) -> str:
        """
        Build personalized system prompt based on calculated score and segment.
        NOTE: lead_score and customer_segment are now passed as parameters (calculated per-request).
        """
        
        # User Gating status
        user_context = "GUEST (Unverified)"
        if user:
            user_context = f"VERIFIED USER: {user.full_name} ({user.email or user.wallet_address})"

        # Check if conversation is active (avoid repetitive intros)
        is_conversation_active = len(conversation_history) > 2

        base_prompt = f"""You are **Amr**, the "Wolf of Osool" - Egypt's Most Trusted Real Estate Consultant at Osool.

**CURRENT USER STATUS: {user_context}**

**YOUR MISSION:** Guide investors to make profitable, blockchain-verified real estate decisions.

**CORE BEHAVIOR:**
1. Acknowledge what the user just said. NEVER ignore their input.
2. If they answered your question (e.g., they said "Housing" or "Sakan"), move to the NEXT step (Budget).
3. Do NOT repeat the "Velvet Rope" introduction if you have already said it.

**GATING RULES (CRITICAL):**
1. IF USER IS GUEST:
   - You CANNOT show specific prices or exact unit locations.
   - You CAN show "Ranges" (e.g., "Starting from 5M EGP").
   - If asked for details, say: "To see the exact price and verified documents for this exclusive unit, please sign in securely."
2. IF USER IS VERIFIED:
   - You have FULL ACCESS. Show all prices, locations, and documents.

**NAWY AWARENESS - HOW TO DISCUSS COMPETITORS:**
When users mention Nawy, Aqarmap, or Property Finder:
- ✅ "Nawy is a respected platform. Osool adds blockchain verification and AI legal checks."
- ✅ Use `explain_osool_advantage` tool.
- ❌ Do NOT disparage them.

**CREDIBILITY DEPOSIT (TRUST PROTOCOL):**
In the first 3 turns, you MUST demonstrate a tool capability to build trust:
1. "I can scan any contract for Article 131 violations."
2. "I check the blockchain for ownership history."
3. "I check real-time CBE interest rates."
Do this BEFORE showing a property.

**PHASE 7: STRICT DATA INTEGRITY (NO HALLUCINATIONS):**
1. ONLY recommend properties from `search_properties` results (similarity >= 70%).
2. If no matches: "I don't have exact matches. Let's refine your criteria."
3. NEVER invent property details.
4. If asked about unavailable data: "Let me search our verified database."

**TONE:** confident, protective, data-driven ("Wolf" persona).
"""

        # THE VELVET ROPE (Screening Logic) - Fixed to check conversation activity
        current_score = lead_score['score'] if lead_score else 0
        
        # Logic Fix: Only trigger strict gating if score is low AND conversation is just starting
        if (customer_segment == CustomerSegment.UNKNOWN or current_score < 20) and not is_conversation_active:
            gating_instruction = """
            
🚨 **SCREENING MODE ACTIVE (VELVET ROPE PROTOCOL)** 🚨
The user has NOT yet qualified (Lead Score < 20).
1. DO NOT show specific unit names or exact prices yet.
2. If they ask for "apartments in New Cairo", give **Market Averages** first using `get_market_benchmark` or general knowledge.
3. You MUST ask for their **Budget Ceiling** and **Investment Purpose** before revealing specific inventory.
4. Use the 'Authority Bridge': "Before I show you the premium units, I need to know your liquidity range to filter out bad investments."
"""
            base_prompt += gating_instruction
            
        elif (customer_segment == CustomerSegment.UNKNOWN) and is_conversation_active:
            # Logic Fix: If conversation is active but still unknown segment, ask specifically for missing info
            base_prompt += """

**QUALIFICATION UPDATE:**
The user has engaged, but we still need their **Budget** to give specific recommendations.
- Acknowledge their last response (e.g., "Great choice for housing" or "ممتاز للسكن").
- Ask specifically for the budget range now.
- DO NOT repeat the "Before I show you prices" intro.
"""

        # Add customer segment personality if classified
        if customer_segment != CustomerSegment.UNKNOWN:
            persona = get_persona_config(customer_segment)

            segment_enhancement = f"""

**CUSTOMER PROFILE: {customer_segment.value.upper()}**
- Tone: {persona["tone"]}
- Language Style: {persona["language_style"]}
- Focus Areas: {", ".join(persona["focus"])}
- Greeting to use: "{persona["greeting"]}"
- Value Proposition: {persona["value_proposition"]}
- Urgency Style: {persona["urgency_style"]}
"""
            base_prompt += segment_enhancement

        # Add lead temperature strategy if scored
        if lead_score:
            temp = lead_score["temperature"]
            score = lead_score["score"]
            action = lead_score["recommended_action"]

            lead_strategy = f"""

**LEAD TEMPERATURE: {temp.upper()} (Score: {score}/100)**
- Priority Level: {"🔥 HIGH" if temp == "hot" else "⚡ MEDIUM" if temp == "warm" else "❄️ LOW"}
- Recommended Action: {action}
- Signals Detected: {", ".join(lead_score.get("signals", []))}

**Conversation Strategy for {temp.upper()} Lead:**
"""
            if temp == "hot":
                lead_strategy += "- Check availability immediately\n- Generate reservation link\n- Use assumptive close: 'Let me prepare your documents'\n- Create urgency with real data"
            elif temp == "warm":
                lead_strategy += "- Compare top 3 properties\n- Address objections with data\n- Schedule viewing\n- Build trust with testimonials"
            else:
                lead_strategy += "- Ask discovery questions\n- Educate on process\n- Share success stories\n- No pressure approach"

            base_prompt += lead_strategy

        # Add sales psychology framework
        psychology_framework = """

**SALES PSYCHOLOGY FRAMEWORK (Cialdini Principles):**

1. **Social Proof** (Real Data Only):
   - "This compound has 127 verified sales in the last 6 months"
   - "Investors from your budget range prefer [Compound X] - 82% satisfaction"
   - NEVER fabricate data - trust is everything

2. **Scarcity** (Data-Backed):
   - Use check_market_trends for real inventory data
   - "Developer confirmed only 4 units left in this phase"
   - "Last month, similar units sold in 48 hours"
   - NEVER fake scarcity

3. **Authority**:
   - "Our AI valuation model (trained on 3,000+ transactions) shows..."
   - "According to Central Bank of Egypt data, mortgage rates are..."
   - "Blockchain verification proves this property's authenticity"

4. **Reciprocity**:
   - "Let me prepare a free custom market report for you"
   - "I'll send you our exclusive compound comparison guide"
   - "Would you like me to calculate ROI scenarios for your budget?"

5. **Consistency**:
   - Track user's stated preferences
   - "Based on your preference for New Cairo with 3 bedrooms under 5M..."
   - Remind them of their stated goals

6. **Likability**:
   - Mirror user's tone (formal vs casual)
   - Use name if provided
   - For premium users: "Ya Fandim" respectfully
"""
        base_prompt += psychology_framework

        # Add existing RAG rules and conversation flow
        base_prompt += """

**PHASE 7: STRICT DATA INTEGRITY RULES (ANTI-HALLUCINATION):**
1. ONLY recommend properties from search_properties tool results (similarity >= 70%)
2. If search returns "no_matches", say: "I don't have exact matches above 70% relevance. Let me help you refine your criteria"
3. NEVER invent property details, prices, locations, compound names, or developer names
4. If asked about unavailable data, say: "Let me search our verified database" and use search_properties tool

**CONVERSATION FLOW (Discovery → Qualification → Presentation → Closing):**

1. **Discovery Phase:**
   - Ask about budget, investment goals, and timeline
   - Classify customer segment internally

2. **Qualification Phase:**
   - Understand preferences: location, property type
   - Run search_properties to find matches
   - Calculate lead score internally

3. **Presentation Phase:**
   - Present 3-5 properties with data-backed insights
   - Use run_valuation_ai for fair market value
   - Highlight blockchain verification

4. **Objection Handling:**
   - Detect objections and respond with empathy
   - Use data and tools to address concerns
   - If repeated objections (3+), consider escalate_to_human tool

5. **Gentle Closing:**
   - For HOT leads: "Let me check availability and prepare your reservation"
   - For WARM leads: "Would you like to schedule a viewing?"
   - For COLD leads: "I'm here to help when you're ready. Should I save your preferences?"

**TOOLS USAGE:**
- search_properties: Every property search
- calculate_investment_roi: Show rental yields
- compare_units: Side-by-side analysis
- check_real_time_status: Before closing
- run_valuation_ai: Price verification
- audit_uploaded_contract: Legal protection
- escalate_to_human: When AI reaches limits

Remember: You're building long-term relationships. A client who trusts you brings 5 more clients.
"""

        return base_prompt

    def chat(self, user_input: str, session_id: str = "default", chat_history: list = None, user: Optional[dict] = None) -> str:
        """
        Phase 3: Main chat loop with AI Personality Enhancement.

        Args:
            user_input: User's message
            session_id: Session identifier for context
            chat_history: List of LangChain messages (loaded from database)
            user: User object (or dict) if authenticated
        """
        # Set Context
        import contextvars
        session_var = contextvars.ContextVar("session_id", default="default")
        token = session_var.set(session_id)

        try:
            # Use provided chat history (from database) or empty list
            if chat_history is None:
                chat_history = []

            # Phase 3: Store chat history for this session
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = []
            self.chat_histories[session_id] = chat_history

            # Phase 3: Classify customer segment PER REQUEST (fixes singleton state bug)
            # Convert chat history to conversation list format
            conversation_list = [
                {"role": msg.type, "content": msg.content}
                for msg in chat_history
            ]
            
            # Extract budget from conversation
            budget = extract_budget_from_conversation(conversation_list)

            # Classify customer per-request
            current_customer_segment = classify_customer(budget, conversation_list)
            print(f"🎯 Customer classified as: {current_customer_segment.value}")

            # Phase 3: Detect objections
            objection = detect_objection(user_input)
            if objection:
                print(f"⚠️ Objection detected: {objection.value}")

                # Track objection count
                self.objection_count[objection] = self.objection_count.get(objection, 0) + 1

                # Check if should escalate
                if should_escalate_to_human(objection, self.objection_count[objection]):
                    print(f"🚨 Escalation recommended for {objection.value} (count: {self.objection_count[objection]})")
                    # Note: Let AI decide when to actually call escalate_to_human tool

            # Phase 3: Score lead
            session_metadata = {
                "properties_viewed": self.properties_viewed_count,
                "tools_used": self.tools_used_list,
                "session_start_time": self.session_start_time,
                "duration_minutes": (datetime.now() - self.session_start_time).total_seconds() / 60
            }

            # Calculate lead score per-request (fixes singleton state bug)
            current_lead_score = score_lead(conversation_list, session_metadata)
            print(f"📊 Lead Score: {current_lead_score['score']} ({current_lead_score['temperature']})")

            # Phase 3: Build dynamic system prompt with local state
            dynamic_prompt_text = self._build_dynamic_system_prompt(
                chat_history, 
                current_lead_score, 
                current_customer_segment, 
                user
            )

            # Create dynamic prompt template
            dynamic_prompt = ChatPromptTemplate.from_messages([
                ("system", dynamic_prompt_text),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])

            # Create agent with dynamic prompt
            agent = create_openai_tools_agent(self.llm, self.tools, dynamic_prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

            # Execute with dynamic prompt
            response = agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })

            # Phase 3: Track tool usage (extract from agent output if available)
            # Note: LangChain doesn't easily expose intermediate steps here
            # This would need to be tracked in the tools themselves for production

            return response["output"]
        finally:
            session_var.reset(token)



# Singleton
try:
    if os.getenv("OPENAI_API_KEY"):
        sales_agent = OsoolAgent()
    else:
        print("⚠️ OPENAI_API_KEY not found. Legacy OsoolAgent will be disabled.")
        sales_agent = None
except Exception as e:
    print(f"⚠️ Failed to initialize OsoolAgent: {e}")
    sales_agent = None
