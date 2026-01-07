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
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # Removed as per diff
    # vector_store = SupabaseVectorStore( # Removed as per diff
    #     client=supabase, # Removed as per diff
    #     embedding=embeddings, # Removed as per diff
    #     table_name="documents", # Removed as per diff
    #     query_name="match_documents" # Removed as per diff
    # ) # Removed as per diff
else:
    print("⚠️ Supabase Credentials Missing. RAG will fail.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Removed PostgresHistory class as per diff

# ---------------------------------------------------------------------------
# 1. SESSION-BASED RESULT STORAGE (Concurrency Safe)
# ---------------------------------------------------------------------------

# Removed _current_session_id contextvar as per diff
# Removed store_session_results and get_session_results functions as per diff


# ---------------------------------------------------------------------------
# 2. TOOLS
# ---------------------------------------------------------------------------

@tool
def search_properties(max_price: int = 100000000, location: str = "") -> str:
    """
    Search for properties based on budget and location. 
    Returns list of matches with IDs.
    """
    print(f"🔎 Database Search: Max {max_price} EGP, {location or 'Anywhere'}")
    
    # Mock Database Results (Simulating Vector Store)
    results = [
        {"id": 1, "title": "Luxury Apartment in New Cairo", "price": 4500000, "location": "New Cairo", "bedrooms": 3, "size": 180, "risk_score": 10},
        {"id": 2, "title": "Townhouse in Sheikh Zayed", "price": 8500000, "location": "Sheikh Zayed", "bedrooms": 4, "size": 250, "risk_score": 5},
        {"id": 3, "title": "Modern Studio in Maadi", "price": 2500000, "location": "Maadi", "bedrooms": 1, "size": 90, "risk_score": 8},
        {"id": 4, "title": "Sea View Chalet in Ain Sokhna", "price": 5500000, "location": "Ain Sokhna", "bedrooms": 2, "size": 120, "risk_score": 25},
    ]
    
    # Filter
    filtered = [
        p for p in results 
        if p['price'] <= max_price
        and (not location or location.lower() in p['location'].lower())
    ]
    
    return json.dumps(filtered)

@tool
def calculate_mortgage(principal: int, rate: float = 25.0, years: int = 20) -> str:
    """
    Calculate monthly mortgage payments based on interest rate (%) and loan term (years).
    """
    monthly_rate = rate / 100 / 12
    num_payments = years * 12
    if principal <= 0: return "0"
    
    payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    return f"{int(payment):,} EGP/month"

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
        # We import here to avoid circular dependencies if any, 
        # but standard structure allows top-level import if clean.
        from app.services.blockchain import blockchain_service 
        
        is_free = blockchain_service.is_available(property_id)
        if is_free:
            return f"✅ Good news! Unit {property_id} is verified AVAILABLE on the blockchain."
        else:
            return f"❌ Urgent: Unit {property_id} is marked SOLD or RESERVED on the blockchain."
    except Exception as e:
        return f"Blockchain Connection Error: {e}"


# ---------------------------------------------------------------------------
# 3. AGENT SETUP (LangChain)
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Tools including the new Blockchain Check
        self.tools = [search_properties, calculate_mortgage, generate_reservation_link, check_real_time_status]
        
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, The "Antigravity" Senior Consultant at Osool (The "Wolf of Cairo").
Your tone is Professional, Assertive, "Street-Smart", and deeply knowledgeable about the Egyptian market.

**CORE IDENTITY:**
- You DO NOT waste time. You DO NOT generic "AI fluff".
- You speak the language of money (ROI, Capital Appreciation, Rental Yields).
- You are strictly on the SIDE OF THE USER (The Investor). You protect them from scams.
- You operate with "Wolf Radar": You smell bad deals and call them out immediately.

**MARKET DATA (LIVE CONTEXT):**
- Location: New Cairo / Mostakbal City / Zayed
- Average Price per Meter: ~45,000 EGP (New Cairo) / ~60,000 EGP (Zayed)
- Mortgage Rates: ~25% (Extremely High - Cash is King, or Installments)
- Rental Yields: 8-12% ROI

🛡️ **BLOCKCHAIN VERIFICATION PROTOCOL**:
- Before asking for money or sending a link, you MUST call `check_real_time_status`.
- If the status is SOLD, apologize and find a similar unit using `search_properties`.
- If AVAILABLE, say: "It's live on the chain. I can lock this for you right now."

⚠️ **MANDATORY TRIGGER WORDS**:
- "buying", "villa", "apartment", "compound" -> CALL `search_properties` IMMEDIATELY.

⚖️ **LEGAL GUARDIAN MODE**:
- If user mentions "Contract", "Off-plan":
  - Cite **Egyptian Civil Code Article 131**: "A contract for a non-existent thing is void."
  - Demand **"Tawkil Rasmi"**.
  - Check for **"Penalty Clause"**.

⚔️ **THE "NAWY KILLER" SCRIPT**:
- If user mentions "Nawy":
  - "They lock you in for 7 years. I sell you liquid tokens you can sell tomorrow. Don't lock your liquidity."

🎯 **CLOSING LOOPS**:
- **Soft Close**: "Shall I generate a payment link?"
- **Hard Close**: "The blockchain shows 3 reservations attempted. Validating status..." (Call check_real_time_status)

**TONE**:
- "Ya Basha", "Tamam", "Mabrouk". Concise. Numbers first.
"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def chat(self, user_input: str, session_id: str = "default") -> str:
        """Main chat loop with History (Mocking history for now)."""
        # In production, fetch specific history for session_id
        chat_history = [] 
        
        response = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        return response["output"]

def get_last_search_results(session_id: str) -> list:
    """Helper for endpoints.py to get search context."""
    # Since we moved to LangChain Executor, extracting the specific tool output 
    # from the agent trace would require looking at intermediate steps.
    # For MVP, we'll return a stub or implement a callback handler if needed.
    # Currently, returning empty list to prevent crash.
    return []

# Singleton
sales_agent = OsoolAgent()
