"""
Osool AI Sales Agent (LangChain)
--------------------------------
The "Wolf of Wall Street" Engine.
Powered by LangChain, GPT-4o, and Custom Tools.
"""

import os
from typing import Optional, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import tool, AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage
import pandas as pd

load_dotenv()

# Load Data (Fallback until Postgres is up)
EXCEL_PATH = "../nawy_final_refined.xlsx"
try:
    df_properties = pd.read_excel(EXCEL_PATH)
    print(f"Loaded {len(df_properties)} properties from Excel.")
except Exception as e:
    print(f"Warning: Could not load Excel data: {e}")
    df_properties = pd.DataFrame()

# ---------------------------------------------------------------------------
# 1. DEFINE TOOLS
# ---------------------------------------------------------------------------

@tool
def search_properties(query: str) -> str:
    """
    Searches for properties based on user requirements.
    Useful when user asks for "villa in New Cairo", "apartment under 5M", etc.
    """
    if df_properties.empty:
        return "I'm sorry, my property database is currently offline. Please check back later."
        
    # Simple keyword search (mocking vector search)
    # In production, this call would go to PGVector
    
    query = query.lower()
    results = []
    
    # Filter constraints (simple logic for MVP fallback)
    max_price = 100_000_000 # Default max
    if "under" in query:
        import re
        nums = re.findall(r'\d+', query)
        if nums:
            # simple guess: if user says "under 5 million", nums=['5'] -> 5000000
            # handling 'million' is complex with regex alone, simplifying for now
            pass 

    # Scan top 50 rows for matches (simple optimization)
    # This is rough but effective for a "Wolf" demo without DB
    for _, row in df_properties.head(100).iterrows():
        # Construct text representation to match against
        compound = str(row.get('compound_name', '')).lower()
        location = str(row.get('city_name', '')).lower()
        ptype = str(row.get('property_type', '')).lower()
        
        match_score = 0
        if any(w in compound for w in query.split()): match_score += 1
        if any(w in location for w in query.split()): match_score += 1
        if any(w in ptype for w in query.split()): match_score += 1
        
        if match_score > 0:
            price = row.get('final_price', 0)
            try:
                price_fmt = f"{float(price):,.0f}"
            except:
                price_fmt = str(price)
                
            results.append(
                f"- **{row.get('property_type')}** in {row.get('compound_name')}, {row.get('city_name')}. "
                f"Price: {price_fmt} EGP. Size: {row.get('unit_area')} sqm."
            )
            
        if len(results) >= 5:
            break
            
    if not results:
        return "I searched our exclusive listings but couldn't find an exact match right now. I have many other off-market options—what is your budget?"
        
    return "Here are some premium options I found for you:\n" + "\n".join(results)

@tool
def calculate_mortgage(price: int, down_payment: int, years: int, interest_rate: float = 25.0) -> str:
    """
    Calculates monthly mortgage installments.
    Args:
        price: Total property price in EGP.
        down_payment: Down payment amount in EGP.
        years: Loan duration in years (standard is 5-10).
        interest_rate: Annual interest rate (default 25% for 2026).
    """
    if down_payment >= price:
        return "Down payment covers the full price! No mortgage needed."
        
    principal = price - down_payment
    monthly_rate = (interest_rate / 100) / 12
    num_payments = years * 12
    
    # Mortgage formula: M = P [ i(1 + i)^n ] / [ (1 + i)^n – 1]
    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    return (
        f"💰 **Mortgage Calculation**:\n"
        f"- Property Value: {price:,.0f} EGP\n"
        f"- Down Payment: {down_payment:,.0f} EGP\n"
        f"- Loan Amount: {principal:,.0f} EGP\n"
        f"- Interest Rate: {interest_rate}%\n"
        f"- Duration: {years} Years\n"
        f"----------------------------------------\n"
        f"**Monthly Installment: {monthly_payment:,.2f} EGP**"
    )

@tool
def check_availability(property_id: int) -> str:
    """
    Checks if a property is still available for sale.
    Queries the Blockchain/Database status.
    """
    # TODO: Connect to actual Postgres/Blockchain when Docker is up.
    # Mocking for now as per plan.
    if property_id % 2 == 0:
        return f"✅ Property #{property_id} is AVAILABLE and ready for instant blockchain reservation."
    else:
        return f"❌ Property #{property_id} is SOLD (Reserved on Blockchain)."

@tool
def generate_reservation_link(property_id: int) -> str:
    """
    Generates a secure payment link for reservation.
    Only use this when the user explicitly says they want to buy/reserve.
    """
    return f"https://pay.osool.eg/reserve/{property_id}?ref=ai_agent"

# ---------------------------------------------------------------------------
# 2. AGENT SETUP
# ---------------------------------------------------------------------------

class OsoolAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        # Added search_properties to tools
        self.tools = [search_properties, calculate_mortgage, check_availability, generate_reservation_link]
        
        # System Prompt - The "Wolf" Persona
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are **Amr**, the Senior AI Consultant at **Osool**.
                
                **Your Mission**:
                You are not just a chatbot. You are a top-tier Real Estate Consultant (The "Wolf of Wall Street" of Cairo).
                You sell TRUST, not just properties.
                
                **Directives**:
                1. **Sell the Dream, Secure the Deal**: Be professional, confident, and persuasive. 
                2. **Blockchain is Safety**: Always explain that Osool uses Blockchain to prevent fraud (double-sales).
                3. **Legal Guardian**: Quote **Law 114** (Registration) to build authority. Warn against "Urfi" contracts.
                4. **Use Tools**:
                   - **SEARCH FIRST**: If a user asks for a property ("villa", "apartment", "New Cairo"), Use `search_properties` immediately.
                   - If a user asks about monthly payments, use `calculate_mortgage`.
                   - If a user likes a unit, use `check_availability`.
                   - If they are ready to buy, give them the link with `generate_reservation_link`.
                
                **Tone**:
                - Professional but high-energy.
                - Use Egyptian Market terminology (Tawkil, Rasmy, New Capital, ROI).
                - Respond in the SAME language as the user (Arabic or English).
                """
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        
        # Chat History Memory
        self.memory = {}  # In-memory session store (SessionID -> History)

    def chat(self, user_input: str, session_id: str = "default") -> str:
        """
        Main chat function.
        """
        # Retrieve or initialize memory (Simple List for now, ideally Redis)
        if session_id not in self.memory:
            self.memory[session_id] = []
            
        chat_history = self.memory[session_id]
        
        response = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        output = response["output"]
        
        # Update history
        from langchain_core.messages import HumanMessage, AIMessage
        self.memory[session_id].extend([
            HumanMessage(content=user_input),
            AIMessage(content=output)
        ])
        
        return output

# Singleton
sales_agent = OsoolAgent()

if __name__ == "__main__":
    # Test Interaction
    print("--- Osool Sales Agent Test ---")
    print(sales_agent.chat("I want to buy a villa in New Capital, price around 10 Million EGP. Can I pay over 10 years?"))
