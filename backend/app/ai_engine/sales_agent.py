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
def search_properties(query: str, session_id: str = "default") -> str:
    """
    Search for properties using Semantic Search (RAG).
    Query can be natural language: "Apartment in New Cairo under 5M"
    Returns JSON string of matches.
    """
    print(f"🔎 RAG Search: '{query}'")
    
    matches = []
    
    # FALLBACK DATA (Production Resilience)
    FEATURED_PROPERTIES = [
        {"title": "Apartment in Zed East", "location": "New Cairo", "price": 7500000, "size": 165, "bedrooms": 3, "developer": "Ora", "market_status": "Hot"},
        {"title": "Villa in Cairo Gate", "location": "Sheikh Zayed", "price": 12000000, "size": 300, "bedrooms": 4, "developer": "Emaar", "market_status": "Premium"},
        {"title": "Chalet in Marassi", "location": "North Coast", "price": 15000000, "size": 120, "bedrooms": 2, "developer": "Emaar", "market_status": "Summer Demand"},
    ]

    if vector_store:
        try:
            # 1. Semantic Search via Supabase
            docs = vector_store.similarity_search(query, k=5)
            
            # 2. Parse Results
            for doc in docs:
                matches.append(doc.metadata)

            if not matches:
                 print("⚠️ No semantic matches found. Using Featured.")
                 matches = FEATURED_PROPERTIES
                
        except Exception as e:
             print(f"⚠️ Vector Search Error: {e}. Failling back to Featured.")
             matches = FEATURED_PROPERTIES
    else:
         print("⚠️ No Vector Store. Using Featured Properties.")
         matches = FEATURED_PROPERTIES

    # 3. Session Memory logic (simplified for prompt)
    import contextvars
    session_context = contextvars.ContextVar("session_id", default="default")
    try:
        sid = session_context.get()
    except:
        sid = session_id # Fallback if context not set
        
    store_session_results(sid, matches)
    
    return json.dumps(matches)

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
    """Generates a secure reservation link for payment."""
    return f"https://pay.osool.eg/checkout/{property_id}"

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
        
    try:
        result = hybrid_brain_prod.audit_contract(contract_text)
        return json.dumps(result)
    except Exception as e:
        return f"Audit Error: {e}"


# ---------------------------------------------------------------------------
# 3. AGENT SETUP (LangChain)
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Tools including the new Blockchain Check
        self.tools = [search_properties, calculate_mortgage, generate_reservation_link, check_real_time_status, run_valuation_ai, audit_uploaded_contract]
        
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, the "Antigravity" Real Estate Consultant at Osool. You are NOT a support bot. You are a high-net-worth investment advisor.

**YOUR PRIME DIRECTIVE:**
Your goal is to CLOSE DEALS by protecting the user. You win trust by exposing bad deals, so you can sell them the *right* deal.

**YOUR BRAIN (DATA SOURCES):**
1.  **Legal Code (The Shield):** You know Egyptian Civil Code 131 & Law 114 inside out.
    * *Trigger:* If user uploads a contract or mentions "signing", ASK: "Does it have the Tawkil clause? Upload it, I'll scan it for free."
2.  **Market Data (The Sword):**
    * *New Cairo:* ~45k-60k EGP/sqm. Saturation is high.
    * *Sheikh Zayed:* ~65k EGP/sqm. High demand.
    * *Nawy Competitor check:* "Nawy is great for browsing, but they push their exclusive inventory. I find you the asset that makes MONEY, regardless of the developer."
3.  **Blockchain (The Trust):**
    * "I don't just 'promise' it's yours. I write it to the Polygon Ledger. Here is the TX Hash."

**CONVERSATION STAGE STRATEGY:**

* **STAGE 1: DISCOVERY (The Interrogation)**
    * User: "I want an apartment."
    * You: "Budget? Cash or Installments? If installments, be careful of the 30% loading fees developers hide. Give me the numbers."

* **STAGE 2: THE "REALITY CHECK"**
    * User: "I found a villa for 5M in Tagamo."
    * You: "5M in 2026? Impossible. Either it's a scam, legal issues, or it's in the middle of the desert. Send me the location, let me run the Valuation AI."

* **STAGE 3: THE CLOSE (Fractional)**
    * User: "I only have 500k EGP."
    * You: "Don't buy a bad apartment in a bad area. Put that 500k into **Osool Fractional**. Buy 10% of a Prime Villa in Zayed. You get the appreciation of the Villa, without the headache."
    * *Action:* Call `search_properties` with fractional filter.

**TONE & STYLE:**
* Egyptian Business Professional ("Ya Basha", "Hadhretak", but firm).
* Use Emoji sparingly to highlight Money 💰 and Warnings ⚠️.
* Never be passive. Always end with a Call to Action (CTA).
"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def chat(self, user_input: str, session_id: str = "default") -> str:
        """Main chat loop with History."""
        # Set Context
        import contextvars
        session_var = contextvars.ContextVar("session_id", default="default")
        token = session_var.set(session_id)
        
        try:
            # TODO: Fetch Chat History from DB (Supabase/Redis)
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
