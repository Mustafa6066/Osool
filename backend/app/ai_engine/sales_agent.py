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
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents"
    )
else:
    print("⚠️ Supabase Credentials Missing. RAG will fail.")

class PostgresHistory:
    """Chat History manager using 'chat_messages' table."""
    def __init__(self, session_id: str):
        self.session_id = session_id

    def add_message(self, role: str, content: str):
        if not supabase: return
        try:
            supabase.table("chat_messages").insert({
                "session_id": self.session_id,
                "role": role,
                "content": content
            }).execute()
        except Exception as e:
            print(f"History Error: {e}")

    def get_messages(self) -> List[BaseMessage]:
        if not supabase: return []
        try:
            res = supabase.table("chat_messages").select("*") \
                .eq("session_id", self.session_id) \
                .order("created_at", desc=False).execute()
            messages = []
            for msg in res.data:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            return messages
        except Exception as e:
            print(f"Fetch History Error: {e}")
            return []

# ---------------------------------------------------------------------------
# 1. SESSION-BASED RESULT STORAGE (Concurrency Safe)
# ---------------------------------------------------------------------------

# Thread-local context for passing session_id to tools
import contextvars
_current_session_id: contextvars.ContextVar[str] = contextvars.ContextVar('session_id', default='default')

def store_session_results(session_id: str, results: list):
    """Store search results in Supabase keyed by session_id."""
    if not supabase:
        return
    try:
        supabase.table("session_search_results").upsert({
            "session_id": session_id,
            "results": json.dumps(results)
        }, on_conflict="session_id").execute()
    except Exception as e:
        print(f"Session Store Error: {e}")

def get_session_results(session_id: str) -> list:
    """Retrieve search results for a specific session."""
    if not supabase:
        return []
    try:
        res = supabase.table("session_search_results").select("results").eq("session_id", session_id).execute()
        if res.data:
            return json.loads(res.data[0]["results"])
    except Exception as e:
        print(f"Session Fetch Error: {e}")
    return []

# ---------------------------------------------------------------------------
# 2. TOOLS (STRICT RAG)
# ---------------------------------------------------------------------------

@tool
def search_properties(query: str) -> str:
    """
    Searches the property database using semantic search.
    Returns REAL properties from the Supabase vector store.
    YOU MUST USE THIS TOOL before recommending any property.
    """
    global _last_search_results
    _last_search_results = []
    
    if not vector_store:
        return "ERROR: Property database is not available. Please try again later."
    
    try:
        docs = vector_store.similarity_search(query, k=5)
    except Exception as e:
        return f"Search Error: {e}"
    
    if not docs:
        return "No properties found matching your criteria. Try adjusting your search."
    
    results_text = []
    results_json = []
    
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        
        # Human-readable card
        card = (
            f"**{i}. {meta.get('title', 'Property')}** (ID: {meta.get('id', 'N/A')})\n"
            f"📍 {meta.get('location', 'Unknown')} - {meta.get('compound', 'N/A')}\n"
            f"🏠 Type: {meta.get('type', 'N/A')} | Area: {meta.get('area', 0)} sqm | 🛌 {meta.get('bedrooms', 0)} beds\n"
            f"💰 **{meta.get('price', 0):,.0f} EGP** ({meta.get('pricePerSqm', 0):,.0f} EGP/sqm)\n"
            f"📅 Delivery: {meta.get('deliveryDate', 'N/A')}\n"
        )
        results_text.append(card)
        
        # JSON for frontend rendering
        results_json.append({
            "id": meta.get("id", ""),
            "title": meta.get("title", ""),
            "type": meta.get("type", ""),
            "location": meta.get("location", ""),
            "compound": meta.get("compound", ""),
            "price": meta.get("price", 0),
            "pricePerSqm": meta.get("pricePerSqm", 0),
            "area": meta.get("area", 0),
            "bedrooms": meta.get("bedrooms", 0),
            "bathrooms": meta.get("bathrooms", 0),
            "deliveryDate": meta.get("deliveryDate", ""),
            "image": meta.get("image", ""),
            "url": meta.get("url", ""),
            "developer": meta.get("developer", "")
        })
    
    # Store for API retrieval (session-scoped)
    session_id = _current_session_id.get()
    store_session_results(session_id, results_json)
    
    return "\n\n".join(results_text)

@tool
def calculate_mortgage(price: int, down_payment: int, years: int) -> str:
    """Calculates monthly installment @ 25% interest (Egyptian bank average)."""
    r = 0.25 / 12
    n = years * 12
    p = price - down_payment
    if p <= 0:
        return "Cash deal! No mortgage needed."
    m = p * (r * (1 + r)**n) / ((1 + r)**n - 1)
    return f"**{m:,.0f} EGP/month** over {years} years (Loan: {p:,.0f} EGP)"

@tool
def generate_reservation_link(property_id: str) -> str:
    """Generates a secure reservation link for payment."""
    intent = str(uuid.uuid4())
    return f"https://pay.osool.eg/checkout/{property_id}?intent={intent}"

def get_last_search_results(session_id: str = "default") -> list:
    """API helper to get search results for a specific session."""
    return get_session_results(session_id)

# ---------------------------------------------------------------------------
# 2. AGENT SETUP
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.tools = [search_properties, calculate_mortgage, generate_reservation_link]
        
        # ULTIMATE REAL ESTATE CLOSER PROMPT - V1.0 PRODUCTION
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, The "Antigravity" Senior Consultant at Osool.
You are NOT a support bot. You are a high-stakes Real Estate Investment Banker for the Egyptian market (New Cairo, Sheikh Zayed, North Coast).
Your goal is to PROTECT the client and CLOSE the deal.

**CORE DIRECTIVES**:
1. **"No Fluff" Policy**: Never say "I hope you are well." Start immediately with value.
2. **The "Wolf" Radar**:
   - IF user mentions "New Cairo" -> PITCH ROI & Rental Yields (Avg 45k/sqm).
   - IF user mentions "Safety" -> PITCH Law 131 & Blockchain Verification.
3. **Strict Data Adherence**: You only sell what is in the `search_properties` tool. If not there, say: "That isn't in my verified vault yet, but I have something better..."

⚠️ **MANDATORY TRIGGER WORDS** ⚠️:
- "buying", "villa", "apartment", "compound", "property" -> CALL `search_properties` IMMEDIATELY.

⚖️ **LEGAL GUARDIAN MODE (Trigger: "Contract", "Safe", "Scam")**:
- Cite **Egyptian Civil Code Article 131**: "A contract for a non-existent thing is void." Warn about off-plan without permits.
- Demand to see **"Tawkil Rasmi"** (Power of Attorney) before they sign.
- Refuse to let them buy if contract lacks **"Penalty Clause"** (Short-shart) for delays.

⚔️ **THE "NAWY KILLER" SCRIPT (Trigger: "Shares", "Investment", "Nawy")**:
- "Nawy Shares is good, but your money is locked until 2029. With Osool, you own **Tokens**. You can sell your tokens next week if you need cash. Why lock your liquidity?"

🎯 **CLOSING LOOPS**:
- **Soft Close**: "Shall I generate a payment link for the 50k EGP down payment?" (Use `generate_reservation_link`)
- **Hard Close**: "This unit has 3 other viewers today. I can lock it on the blockchain for 24 hours if you transfer the reservation fee now."

**TONE**:
- Professional, assertive, "Street-Smart" Egyptian (use: "Ya Basha", "Tamam", "Mabrouk").
- Speak English but understand Arabic/Franco.
"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def chat(self, user_input: str, session_id: str) -> str:
        """Main chat loop with History."""
        # Set session context for thread-safe result storage
        _current_session_id.set(session_id)
        
        history_manager = PostgresHistory(session_id)
        chat_history = history_manager.get_messages()
        
        response = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        output = response["output"]
        history_manager.add_message("user", user_input)
        history_manager.add_message("assistant", output)
        return output

# Singleton
sales_agent = OsoolAgent()
