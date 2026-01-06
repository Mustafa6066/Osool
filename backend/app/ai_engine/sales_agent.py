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

@tool
def search_properties(query: str) -> str:
    """
    Semantic search for properties. 
    Finds properties based on meaning (e.g., "luxury villa with a view", "investment near AUC").
    """
    if not vector_store:
        return "System Error: Property Database Offline."

    try:
        # RAG RPC Call
        # Assuming we have an RPC function 'match_documents' in Supabase
        docs = vector_store.similarity_search(query, k=5)
    except Exception as e:
        return f"Database Search Error: {e}"
    
    results = []
    for doc in docs:
        details = doc.metadata
        price = details.get('price', 0)
        location = details.get('location', 'Unknown')
        area = details.get('area', 0)
        
        # Dynamic ROI based on location (Wolf Logic)
        growth = "Stable"
        roi = "12%"
        if isinstance(location, str) and ("New Cairo" in location or "Capital" in location):
            roi = "20-25%"
            growth = "High Growth Zone"
            
        card = (
            f"🏠 **{details.get('title', 'Property')}**\n"
            f"📍 {location} | 📏 {area} sqm | 🛌 {details.get('bedrooms', 3)} Beds\n"
            f"💰 **{float(price):,.0f} EGP**\n"
            f"📈 **Wolf Insight:** {growth}. Potential ROI: {roi}.\n"
        )
        results.append(card)

    if not results:
        return "I checked the vault, but no exact matches found. Ask for something broader?"

    return "\n\n".join(results)

@tool
def calculate_mortgage(price: int, down_payment: int, years: int, interest_rate: float = 25.0) -> str:
    """
    Calculates monthly mortgage installments.
    """
    if down_payment >= price:
        return "Cash Deal! No mortgage needed."
        
    principal = price - down_payment
    monthly_rate = (interest_rate / 100) / 12
    num_payments = years * 12
    
    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    return f"**Monthly Installment: {monthly_payment:,.2f} EGP** (over {years} years)"

@tool
def generate_payment_link(property_id: str) -> str:
    """
    Generates a secure reservation link.
    USE THIS TOOL if the user shows buying intent > 80%.
    """
    intent_id = str(uuid.uuid4())
    # In production, this would call Paymob to create a real order
    return f"https://pay.osool.eg/checkout/{property_id}?intent={intent_id}&ref=wolf_agent"

# ---------------------------------------------------------------------------
# 2. AGENT SETUP
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3) # Low temp for precision
        self.tools = [search_properties, calculate_mortgage, generate_payment_link]
        
        # S.P.I.N Selling + Wolf Persona + Objection Handling
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, the 'Wolf of Cairo' Real Estate Consultant at **Osool**.

                **CORE IDENTITY**:
                - You are a CLOSER. You speak with authority and confidence.
                - You do not apologize. You offer solutions.
                
                **OBJECTION HANDLING (CRITICAL)**:
                1. **Safety/Trust**: If user asks "Is this safe?" or mentions fraud:
                   - Quote **Egyptian Civil Law No. 114**.
                   - Explain **Blockchain Immutability** ("Your ownership is etched in code, not just paper").
                2. **Price**: If user says "Too expensive":
                   - Pivot to **ROI** and **Inflation** ("Every day you keep cash, you lose value").
                
                **CLOSING ALGORITHM**:
                - If User Interest > 80% (asks about payment, contract, or steps):
                - **MUST USE** `generate_payment_link` tool immediately.
                - Say: "I've generated your reservation link. Secure this unit before it's gone."
                
                **TOOLS**:
                - Property lookup? -> `search_properties`.
                - Payment plan? -> `calculate_mortgage`.
                - Read to buy? -> `generate_payment_link`.

                **TONE**:
                - "Let's talk business."
                - "This is a rare opportunity."
                - Mix English with "Ya Basha", "Tawkil".
                """
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)

    def chat(self, user_input: str, session_id: str) -> str:
        """
        Main chat loop with History.
        """
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
