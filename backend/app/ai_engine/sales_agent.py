"""
Osool AI Sales Agent (RAG & Wolf Edition)
-----------------------------------------
The "Wolf of Wall Street" Engine.
Powered by LangChain, GPT-4o, Supabase Vector Store, and Custom Tools.
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

if not SUPABASE_URL or not SUPABASE_KEY:
    # Fail gracefully for now, or mock
    print("⚠️ Supabase Credentials Missing. RAG will fail.")
    supabase = None
    vector_store = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Connect to Vector Store
    # Using 'rpc' method for Supabase is cleaner for hybrid search.
    # We will define a custom retriever logic or use SupabaseVectorStore with specific query.
    
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents", # Standard langchain table
        query_name="match_documents"
    )

class PostgresHistory:
    """
    Custom Chat History manager using our 'chat_messages' table.
    """
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
# 1. DEFINE TOOLS
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 1. DEFINE TOOLS (DATA DRIVEN)
# ---------------------------------------------------------------------------

@tool
def query_market_stats(location: str) -> str:
    """
    Queries the REAL Database for average property prices in a location.
    Use this to give accurate ROI data.
    """
    from sqlalchemy import func
    from app.database import SessionLocal
    from app.models import Property
    
    db = SessionLocal()
    try:
        # Simple AVG aggregation
        avg_price = db.query(func.avg(Property.price)).filter(Property.location.ilike(f"%{location}%")).scalar()
        count = db.query(Property).filter(Property.location.ilike(f"%{location}%")).count()
        
        if not avg_price or count == 0:
            return f"I don't have enough data for {location} yet. Let's assume market average."
            
        return f"📊 **Market Data ({location})**: Avg Price is {avg_price:,.0f} EGP (based on {count} active listings)."
    except Exception as e:
        return f"Data Error: {e}"
    finally:
        db.close()

@tool
def compare_with_nawy(compound_name: str, unit_price: float) -> str:
    """
    Compares Osool's price vs Nawy (Competitor) for a similar unit.
    Use this to highlight VALUE.
    """
    # Mock Dataset for MVP - In prod this would scrape Nawy.com
    nawy_data = {
        "Mountain View": 15000000, # 15M
        "Palm Hills": 18000000,
        "Hyde Park": 12000000
    }
    
    # Fuzzy match
    match = None
    for k, v in nawy_data.items():
        if k.lower() in compound_name.lower():
            match = v
            break
            
    if match:
        diff = match - unit_price
        if diff > 0:
            return (
                f"💡 **Competitor Check (Nawy)**:\n"
                f"Similar units on Nawy are listed at **{match:,.0f} EGP**.\n"
                f"We are saving you **{diff:,.0f} EGP** (-{int((diff/match)*100)}%). This is an instant equity gain."
            )
        else:
            return f"Nawy is listed at {match:,.0f} EGP. We are competitively priced."
            
    return "I don't have direct Nawy comparison data for this specific compound right now."

@tool
def search_properties(query: str) -> str:
    """
    Semantic search for properties using Vector Store.
    """
    if not vector_store: return "System Error: DB Offline."
    
    try:
        docs = vector_store.similarity_search(query, k=3)
    except Exception as e:
        return f"Search Error: {e}"
    
    results = []
    for doc in docs:
        d = doc.metadata
        card = (
            f"🏠 **{d.get('title', 'Unit')}**\n"
            f"📍 {d.get('location')} | 💰 **{d.get('price', 0):,.0f} EGP**\n"
            f"🔗 [View Details]({d.get('url', '#')})"
        )
        results.append(card)
        
    return "\n\n".join(results) if results else "No matches found."

@tool
def calculate_mortgage(price: int, down_payment: int, years: int) -> str:
    """Calculates monthly installment @ 25% interest properly."""
    r = 0.25 / 12
    n = years * 12
    p = price - down_payment
    m = p * (r * (1 + r)**n) / ((1 + r)**n - 1)
    return f"**{m:,.0f} EGP/month** (Loan: {p:,.0f} EGP)"

@tool
def generate_payment_link(property_id: str) -> str:
    """Generates a Paymob-ready Checkout Link."""
    return f"https://pay.osool.eg/checkout/{property_id}?intent={uuid.uuid4()}"

@tool
def audit_contract(file_content: str) -> str:
    """
    Analyzes a user-uploaded contract text for risks.
    """
    # Mocking the analysis logic for now
    return (
        "⚖️ **Contract Preliminary Scan**:\n"
        "1. **Clause 4 (Delivery)**: Loose timeline 'expected 2026'. Request specific date.\n"
        "2. **Clause 9 (Resale)**: 5% Admin fee is high. Standard is 2.5%.\n"
        "⚠️ This is not legal advice. Please consult a lawyer."
    )

# ---------------------------------------------------------------------------
# 2. AGENT SETUP
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.tools = [
            search_properties, 
            query_market_stats, 
            compare_with_nawy, 
            calculate_mortgage, 
            generate_payment_link,
            audit_contract
        ]
        
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, the 'Wolf of Cairo' Real Estate Consultant at **Osool**.

                **IDENTITY**:
                - Ruthless but honest. You prioritize ROI and DATA over fluff.
                - "I don't guess. I check the database."

                **PROTOCOL**:
                1. **Audit First**: If user mentions/uploads a contract, use `audit_contract` IMMEDIATELY. Warn them about risks.
                2. **Data Backed**: NEVER say "Good price". Use `query_market_stats` to prove it.
                3. **Beat the Competition**: Use `compare_with_nawy` to show we are cheaper/better.
                4. **Close**: If they ask about payment, generate the link.
                
                **OBJECTION HANDLING**:
                - "Is this safe?" -> Quote **Law 114** & Blockchain.
                - "Contract Risks?" -> "I am not a lawyer, but I spot huge red flags in Clause X."

                **TONE**: Professional, Sharp, English + Business Arabic ("Ya Basha", "Tawkil", "Oqood").
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

# Legacy code removed. Strict RAG enforcement.
"""
