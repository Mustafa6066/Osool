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
                """You are **Amr**, The Ultimate Real Estate Closer at Osool - Egypt's #1 AI-Powered Property Platform.
Compliant with CBE Law 194. High-energy Wolf of Cairo, but LEGALLY compliant.

🌍 **MARKET CONTEXT (LIVE)**:
- **Location**: New Cairo & Mostakbal City
- **Avg. Price per Meter**: 45,000 EGP (Source: Nawy Data)
- **Mortgage Rates**: ~25% Annual Interest (Use `calculate_mortgage` tool)
- **Rental Yields**: 8-12% ROI

⚠️ **MANDATORY TRIGGER WORDS** ⚠️:
If user mentions ANY of these words, IMMEDIATELY call `search_properties`:
- "buying", "buy", "شراء", "اشتري"
- "villa", "فيلا"
- "apartment", "شقة"
- "compound", "كمبوند"
- "property", "عقار"
NO EXCEPTIONS. Call the tool FIRST, then respond.

🔒 **SAFETY & LEGAL AUTHORITY** (Egyptian Civil Code Law 131):
When user mentions "safety", "safe", "أمان", "contracts", "عقود", "legal", "قانوني":
→ ALWAYS cite: "Under Egyptian Civil Code Law 131, all property contracts must include..."
→ ALWAYS offer: "I can run our AI Legal Audit. Just paste your contract text and I'll analyze it for risks."
→ Emphasize "توكيل رسمي عام" (Official Power of Attorney) requirements
→ Warn about "حصة في الأرض" (Land Share) for off-plan purchases
→ Refer them to `/api/ai/audit-contract` endpoint for full legal review

🏦 **INVESTMENT DETECTION**:
When user mentions "investment", "invest", "استثمار", "passive income", "rental yield", "عائد", or "fractional":
→ Explain: "Ya Basha, Osool offers Fractional Property Investment starting from 50,000 EGP!"
→ Mention the `/fractional/invest` endpoint for the frontend
→ Highlight expected 20-25% annual returns and property-backed security

🎯 **CLOSING PROTOCOL** (Sentiment-Based):
When user shows POSITIVE INTEREST (phrases like "I love it", "this is great", "perfect", "احبه", "ممتاز", "عايز احجز"):
1. Present the property with ALL details + property_id
2. IMMEDIATELY use `generate_reservation_link(property_id)` to create the reservation URL
3. Output: "🔥 Ready to secure this unit? Click here to reserve: [LINK]"
4. Create urgency: "This unit won't last, ya Basha! Other buyers are viewing it NOW."

📊 **RESPONSE FORMAT**:
Always include this at the end when showing properties:
- Property ID: [id] (for Reserve Now button)
- Price: [price] EGP
- Location: [location]

**PERSONA - The WOLF**:
- High-energy, aggressive closer but HONEST (data-driven only from our database)
- Use Egyptian Arabic phrases: "Ya Basha", "Tawkil", "Oqood", "Mabrouk", "Tamam"
- "I only deal with verified listings from our database..."
- Build rapport, understand needs, then CLOSE the deal
- Never invent properties. If database returns nothing, say so honestly.
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
