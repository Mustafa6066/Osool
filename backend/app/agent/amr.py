import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from dotenv import load_dotenv

from app.ai_engine.hybrid_brain import hybrid_brain
from app.ai_engine.sales_agent import (
    search_properties,
    calculate_mortgage,
    generate_reservation_link,
    explain_osool_advantage,
    check_real_time_status,
    audit_uploaded_contract,
    check_market_trends,
    calculate_investment_roi,
    compare_units,
    schedule_viewing,
    detect_language
)

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AmrAgent")

class AmrAgent:
    """
    Amr - The Elite Real Estate Agent.
    
    Architecture:
    - BRAIN (Reasoning & Persona): Claude 3 Sonnet (Anthropic)
    - REFLEX (Tools & Speed): GPT-4o (OpenAI)
    - SUB-CORTEX (Valuation): XGBoost (OsoolHybridBrain)
    """
    
    def __init__(self):
        # 1. Initialize Models
        self.sonnet = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.gpt4o = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 2. Load Market Memory
        self.market_knowledge = self._load_market_research()
        
        # 3. Define Tools (Handled by GPT-4o for reliability/function calling standard)
        self.tools = [
            search_properties,
            calculate_mortgage,
            generate_reservation_link,
            explain_osool_advantage,
            check_real_time_status,
            audit_uploaded_contract,
            check_market_trends,
            calculate_investment_roi,
            compare_units,
            schedule_viewing
        ]
        
        # 4. Create Tool Binding
        self.gpt_with_tools = self.gpt4o.bind_tools(self.tools)

    def _load_market_research(self) -> Dict:
        """Loads static market research to inject into context."""
        try:
            path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "market_research.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load market research: {e}")
        return {}

    async def process_message(self, user_input: str, session_id: str, history: List[BaseMessage] = []) -> Dict[str, Any]:
        """
        Main entry point.
        
        Strategy:
        1. Detect Language & Intent.
        2. If "Tool Use" is needed (search, calc) -> Route to GPT-4o (Agent execution).
        3. If "Advice/Consultation" -> Route to Sonnet (Persona/Wisdom).
        4. If "Valuation" -> Invoke XGBoost directly via Tool or HybridBrain.
        """
        
        # Step 1: Language Detection (Fast Check)
        # We assume the frontend might pass this, but we check here if needed.
        # For now, we'll let the prompt handle language mirroring, or use the tool if explicitly asked.
        
        # Step 2: Intent Classification (Heuristic or simple LLM call)
        # We'll use a simple heuristic: if keywords imply database fetch, use GPT Tools.
        tool_keywords = ["find", "search", "apartment", "villa", "price", "location", "calculate", "mortgage", "audit", "contract", "check", "compare"]
        is_tool_query = any(k in user_input.lower() for k in tool_keywords)
        
        if is_tool_query:
            return await self._run_gpt_tools(user_input, session_id, history)
        else:
            return await self._run_sonnet_persona(user_input, session_id, history)

    async def _run_gpt_tools(self, user_input: str, session_id: str, history: List[BaseMessage]) -> Dict[str, Any]:
        """Executes the standard tool-using agent loop with GPT-4o."""
        logger.info(f"Routing to GPT-4o (Tool Use): {user_input[:50]}")
        
        # Construct Prompt
        system_prompt = """You are Amr, Osool's AI Agent.
        Your goal is to execute the user's request using your tools.
        Return the tool output directly or a summary.
        Do not be overly chatty, just get the job done.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.gpt4o, self.tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        
        try:
            response = await agent_executor.ainvoke({
                "input": user_input,
                "history": history
            })
            return {
                "response": response["output"],
                "source_model": "GPT-4o + Tools",
                "charts": self._extract_charts(response["output"]) # Attempt to extract chart data if any
            }
        except Exception as e:
            logger.error(f"GPT Tool Execution Failed: {e}")
            return {"response": "I encountered an error accessing my tools. Please try again.", "error": str(e)}

    async def _run_sonnet_persona(self, user_input: str, session_id: str, history: List[BaseMessage]) -> Dict[str, Any]:
        """Executes the High-EQ, Culturally Aware Persona using Claude 3.5 Sonnet."""
        logger.info(f"Routing to Sonnet (Persona): {user_input[:50]}")
        
        # Inject Market Research into Context
        market_context = json.dumps(self.market_knowledge, indent=2, ensure_ascii=False)
        
        system_prompt = f"""You are **Amr (عمرو)**, the 'One of a Kind' Real Estate Agent at Osool.
        
        **IDENTITY:**
        - You are NOT a robot. You are a highly intelligent, top-tier consultant.
        - You speak concise, premium language.
        - You switch seamlessly between "Egyptian Arabic (Warm, Smart)" and "English (Professional, Global)".
        - You are "The Wolf of Real Estate" but Ethical. Confident, Knowledgeable, Sharp.
        
        **KNOWLEDGE BASE (Strict):**
        Use the following Market Research data to inform your answers. 
        If the user asks something NOT in your data or general knowledge, steer them back to Real Estate.
        
        [MARKET DATA START]
        {market_context}
        [MARKET DATA END]
        
        **RULES:**
        1. **Mirror Language**: If user speaks Arabic, speak Arabic. If English, speak English.
        2. **Be Visual**: If you are describing numbers, say "[Visual: Graph of X]" to indicate where a chart should be.
        3. **Trust**: Mention "Blockchain Verification" casually as a standard feature.
        4. **Adaptive**: If the user seems like an Investor, talk ROI. If a Family, talk Security.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
        ] + history + [HumanMessage(content=user_input)]
        
        try:
            response = await self.sonnet.ainvoke(messages)
            return {
                "response": response.content,
                "source_model": "Claude 3 Sonnet",
                "charts": self._extract_charts(response.content)
            }
        except Exception as e:
            logger.error(f"Sonnet Execution Failed: {e}")
            # Fallback to GPT
            return await self._run_gpt_tools(user_input, session_id, history)

    def _extract_charts(self, text: str) -> List[Dict]:
        """
        Parses the text for special tokens or context to generate chart JSONs for the frontend.
        Simple heuristic implementation.
        """
        charts = []
        if "ROI" in text or "yield" in text or "appreciation" in text.lower():
            # Example: Generate a dummy chart for ROI
            charts.append({
                "type": "bar",
                "title": "Estimated ROI (5 Years)",
                "data": [
                    {"label": "Year 1", "value": 12},
                    {"label": "Year 2", "value": 25},
                    {"label": "Year 3", "value": 38},
                    {"label": "Year 4", "value": 52},
                    {"label": "Year 5", "value": 68},
                ],
                "color": "#10B981"
            })
        return charts

# Singleton
amr_agent = AmrAgent()
