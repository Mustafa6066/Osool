import os
import logging
from typing import Dict, Any, List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

# Import the unified Wolf Brain
from app.ai_engine.wolf_orchestrator import wolf_brain

# Load environment variables
load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AmrAgent")

class AmrAgent:
    """
    Amr - The Elite Real Estate Agent.
    
    Architecture (Updated v2):
    - CORE: Wolf Brain Orchestrator (wolf_orchestrator.py)
    - ROUTING: Handled internally by Wolf Logic
    - TOOLS: Integrated via 'Smart Hunt' & Analytical Engine
    """
    
    def __init__(self):
        # WolfBrain initializes its own clients (Anthropic/OpenAI) internally
        # We just act as the API wrapper here.
        logger.info("🚀 AmrAgent initialized with Wolf Brain V7")

    async def process_message(self, user_input: str, session_id: str, history: List[BaseMessage] = []) -> Dict[str, Any]:
        """
        Main entry point.
        
        Delegates strict processing to the Wolf Brain Orchestrator to ensure:
        1. Psychology Analysis (Trust/Skepticism detection)
        2. Smart Hunt (Reflexion & Pivoting)
        3. Market Data Injection (Live DB stats)
        4. Narrative Control (Claude 3.5 Sonnet via Wolf Master Prompt)
        """
        logger.info(f"📨 Processing message for session {session_id}")

        # 1. Convert LangChain history to Wolf Brain format (List[Dict])
        chat_history_dicts = self._convert_history(history)

        # 2. Execute Wolf Brain Logic
        try:
            result = await wolf_brain.process_turn(
                query=user_input,
                history=chat_history_dicts,
                session_id=session_id,
                language="auto"  # Wolf Brain has internal strict detection
            )

            # 3. Map result to API response structure
            # We map 'ui_actions' to 'charts' to maintain frontend compatibility
            # while delivering the richer Wolf visualizations.
            return {
                "response": result.get("response", ""),
                "source_model": result.get("model_used", "Wolf Brain V7"),
                "charts": result.get("ui_actions", []),
                "properties": result.get("properties", []),
                "strategy": result.get("strategy", {}),
                "psychology": result.get("psychology", {}),
                "showing_strategy": result.get("showing_strategy"),
                "hunt_strategy": result.get("hunt_strategy"),
            }

        except Exception as e:
            logger.error(f"❌ Wolf Brain Execution Failed: {e}", exc_info=True)
            return {
                "response": "عذراً، حدث خطأ في الاتصال بالشبكة العصبية. يرجى المحاولة مرة أخرى. (System Error)",
                "source_model": "Error Fallback",
                "charts": [],
                "error": str(e)
            }

    def _convert_history(self, history: List[BaseMessage]) -> List[Dict[str, str]]:
        """Converts LangChain message objects to simple dicts for Wolf Brain."""
        converted = []
        for msg in history:
            if isinstance(msg, HumanMessage):
                converted.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                converted.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                # Skip system messages as Wolf Brain sets its own context
                pass
            else:
                # Handle dict format passed directly
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    converted.append(msg)
        
        logger.info(f"📋 Converted {len(history)} messages -> {len(converted)} dicts for Wolf Brain")
        return converted


# Singleton
amr_agent = AmrAgent()
