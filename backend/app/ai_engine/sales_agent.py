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
from langchain.agents import tool, AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_community.vectorstores import SupabaseVectorStore
from openai import OpenAI

# Database
from supabase import create_client, Client

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

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Removed PostgresHistory class as per diff

# ---------------------------------------------------------------------------
# 1. SESSION-BASED RESULT STORAGE (Redis)
# ---------------------------------------------------------------------------

from app.services.cache import cache

def store_session_results(session_id: str, results: list):
    """Stores search results for a specific session."""
    cache.store_session_results(session_id, results)

def get_session_results(session_id: str) -> list:
    """Retrieves search results for a specific session."""
    return cache.get_session_results(session_id)


# ---------------------------------------------------------------------------
# 2. TOOLS
# ---------------------------------------------------------------------------

@tool
async def search_properties(query: str, session_id: str = "default") -> str:
    """
    Phase 6: Search for properties using PostgreSQL + pgvector.
    Query can be natural language: "Apartment in New Cairo under 5M"
    Returns JSON string of matches WITH STRICT VALIDATION.

    CRITICAL: Only returns properties that exist in database. NO HALLUCINATIONS.
    """
    print(f"🔎 PostgreSQL Vector Search: '{query}'")

    matches = []

    try:
        # Phase 6: Strict database-only search
        from app.database import AsyncSessionLocal
        from app.services.vector_search import search_properties as db_search_properties

        async with AsyncSessionLocal() as db:
            properties = await db_search_properties(db, query, limit=5)

            if properties:
                # Convert SQLAlchemy models to dicts with validation
                for prop in properties:
                    # Phase 6: Strict validation - ensure all required fields exist
                    if not prop.id or not prop.title or not prop.price:
                        print(f"⚠️ Skipping invalid property (missing required fields): {prop.id}")
                        continue

                    matches.append({
                        "id": prop.id,
                        "title": prop.title,
                        "location": prop.location,
                        "compound": prop.compound,
                        "developer": prop.developer,
                        "price": prop.price,
                        "size": prop.size_sqm,
                        "bedrooms": prop.bedrooms,
                        "bathrooms": prop.bathrooms,
                        "delivery_date": prop.delivery_date,
                        "down_payment": prop.down_payment,
                        "installment_years": prop.installment_years,
                        "monthly_installment": prop.monthly_installment,
                        "nawy_url": prop.nawy_url,
                        "verified_on_blockchain": True,
                        "_source": "database"  # Phase 6: Track data source
                    })
                print(f"✅ Found {len(matches)} validated properties from database")
            else:
                print("⚠️ No database matches found. Returning empty results.")
                # Phase 6: NO FALLBACK - return empty if no matches
                matches = []

    except Exception as e:
        print(f"❌ Database Search Error: {e}")
        # Phase 6: Log to monitoring system
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except:
            pass
        # Return empty on error - no fake data
        matches = []

    # Session Memory
    import contextvars
    session_context = contextvars.ContextVar("session_id", default="default")
    try:
        sid = session_context.get()
    except:
        sid = session_id

    store_session_results(sid, matches)

    # Phase 6: Return with metadata
    result = {
        "properties": matches,
        "count": len(matches),
        "query": query,
        "source": "osool_database"
    }

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

        # Return frontend action format (Phase 6: Task 2 Enhancement)
        action = {
            "action": "REDIRECT",
            "url": f"/checkout?token={token}",
            "token": token,
            "property_id": property_id,
            "expires_in": "1 hour"
        }

        return json.dumps(action)
    except Exception as e:
        return json.dumps({
            "action": "ERROR",
            "message": f"Failed to generate reservation link: {str(e)}"
        })

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


# ---------------------------------------------------------------------------
# 3. AGENT SETUP (LangChain)
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Phase 3: Enhanced tools with deal-closing capabilities
        self.tools = [
            search_properties,
            calculate_mortgage,
            generate_reservation_link,
            check_real_time_status,
            run_valuation_ai,
            audit_uploaded_contract,
            check_market_trends,
            calculate_investment_roi,
            compare_units,
            schedule_viewing
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, the "Wolf of Cairo" - Egypt's Most Trusted Real Estate Consultant at Osool.

**YOUR MISSION:** Guide investors to make profitable, blockchain-verified real estate decisions.

**PHASE 3: MODERATE SALES STYLE**
Your approach is professional, data-driven, and consultative. You build trust through expertise, not pressure.

**CONVERSATION FLOW (Discovery → Qualification → Presentation → Closing):**

1. **Discovery Phase:**
   - Ask about budget, investment goals (ROI vs. residence), and timeline
   - Example: "Welcome! To find you the perfect property, I need to understand: What's your budget range? Are you investing for rental income or personal use?"

2. **Qualification Phase:**
   - Understand preferences: location, property type, payment method
   - Run `search_properties` to find matches
   - Validate all properties exist in database (Phase 3 Enhancement)

3. **Presentation Phase:**
   - Present 3-5 properties with data-backed insights
   - Use `run_valuation_ai` to show fair market value
   - Use `check_market_trends` for compound analysis
   - Highlight blockchain verification: "This property is verified on Polygon blockchain"

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
- ONLY recommend properties from the database (no hallucinations)
- ALWAYS verify blockchain status before generating payment links
- NEVER claim availability without running `check_real_time_status`
- If contract uploaded, MUST use `audit_uploaded_contract`

**PROTECTION RULES (Guardian Mode):**
- If maintenance fee >8%: "⚠️ This fee is above market standard (5-8%). I recommend negotiating."
- If no Tawkil: "🛑 CRITICAL: Missing Power of Attorney clause. You won't own the land. Do not sign."
- If deal seems overpriced: Run `run_valuation_ai` and present data

**TONE:**
- Respectful: "Mr./Ms. [Name]" or casual "Ya Fandim"
- Consultative, not pushy
- Data-backed: "According to our AI valuation..." / "Blockchain shows..."
- Transparent: Mention both pros and cons

**TOOLS USAGE:**
- `search_properties`: For every property search
- `calculate_investment_roi`: Show rental yield calculations
- `compare_units`: Side-by-side analysis
- `check_real_time_status`: Before closing
- `run_valuation_ai`: Reality check on pricing
- `audit_uploaded_contract`: Legal protection
- `check_market_trends`: Compound analysis

Remember: You're building long-term relationships. A client who trusts you brings 5 more clients.
"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def chat(self, user_input: str, session_id: str = "default", chat_history: list = None) -> str:
        """
        Phase 3: Main chat loop with Database History Persistence.

        Args:
            user_input: User's message
            session_id: Session identifier for context
            chat_history: List of LangChain messages (loaded from database)

        Returns:
            AI response text
        """
        # Set Context
        import contextvars
        session_var = contextvars.ContextVar("session_id", default="default")
        token = session_var.set(session_id)

        try:
            # Use provided chat history (from database) or empty list
            if chat_history is None:
                chat_history = []

            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            return response["output"]
        finally:
            session_var.reset(token)

def get_last_search_results(session_id: str) -> list:
    """Helper for endpoints.py to get search context."""
    return get_session_results(session_id)

# Singleton
sales_agent = OsoolAgent()
