import os
import logging
from typing import Dict, Any, List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

# Import the unified Wolf Brain
from app.ai_engine.wolf_orchestrator import wolf_brain
# Import ConversationMemory for loop detection
from app.ai_engine.conversation_memory import ConversationMemory

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
        self.memory_utils = ConversationMemory()  # Utility for loop detection

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

            # --- LOOP DETECTION FIX ---
            # Check if the response is identical or highly similar to the last AI message
            response_text = result.get("response", "")
            if self.memory_utils.check_repetitive_loop(chat_history_dicts, response_text):
                logger.warning(f"🔄 Loop detected for session {session_id}. Applying pivot strategy.")
                
                # Heuristic: Check language to append appropriate pivot message
                is_arabic = any("\u0600" <= char <= "\u06FF" for char in response_text)
                
                if is_arabic:
                    pivot = "\n\n(يبدو أننا نكرر نفس النقاط. هل هناك تفاصيل محددة بخصوص الموقع أو الميزانية تود تغييرها؟)"
                else:
                    pivot = "\n\n(It seems we are going in circles. Is there a specific detail regarding location or budget you'd like to adjust?)"
                
                # Append pivot to break the user out of the loop
                result["response"] = response_text + pivot
            # --------------------------

            # 3. Map result to API response structure
            # We map 'ui_actions' to 'charts' to maintain frontend compatibility
            # while delivering the richer Wolf visualizations.
            return {
                "response": result.get("response", ""), # Now potentially modified
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
