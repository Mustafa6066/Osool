"""
Osool AI Sales Agent - Claude Edition (AMR - Advanced Market Reasoner)
------------------------------------------------------------------------
Phase 2 Production: World-class AI sales agent powered by Claude 3.5 Sonnet
with Parallel Hybrid Brain (Claude + GPT-4o + XGBoost).

The Wolf of Egyptian Real Estate - State of the Art Implementation.

Key Features:
- Parallel processing with Claude, GPT-4o, and XGBoost
- Data-first protocol - never assumes, always verifies
- Language-adaptive responses (Arabic/English)
- Egyptian market psychology and buyer personas
- Strict tool enforcement before claims
"""

import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from anthropic import AsyncAnthropic
from datetime import datetime

# Phase 3: AI Personality Enhancement imports
from .customer_profiles import (
    classify_customer,
    extract_budget_from_conversation,
    CustomerSegment
)
from .lead_scoring import score_lead
from .analytics import ConversationAnalyticsService

# Phase 4: Data-First Protocol and Parallel Brain
from .data_first_enforcer import data_first_enforcer
from .amr_master_prompt import get_wolf_system_prompt

# Import tools from existing sales_agent
from .sales_agent import (
    search_properties,
    calculate_mortgage,
    generate_reservation_link,
    check_real_time_status,
    run_valuation_ai,
    check_market_trends,
    calculate_investment_roi,
    compare_units,
    schedule_viewing,
    escalate_to_human,
    explain_osool_advantage,
    store_session_results,
    get_last_search_results
)

load_dotenv()

# ---------------------------------------------------------------------------
# CLAUDE CONFIGURATION
# ---------------------------------------------------------------------------

from app.config import config

# Check for API key to prevent startup/import crashes
try:
    if config.ANTHROPIC_API_KEY:
        anthropic_async = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    else:
        print("⚠️ ANTHROPIC_API_KEY not found. Claude agent will be disabled.")
        anthropic_async = None
except Exception as e:
    print(f"⚠️ Failed to initialize Anthropic client: {e}")
    anthropic_async = None

# Cost tracking
COST_PER_1M_INPUT_TOKENS = 3.0  # USD per 1M input tokens (Claude 3.5 Sonnet)
COST_PER_1M_OUTPUT_TOKENS = 15.0  # USD per 1M output tokens


# ---------------------------------------------------------------------------
# TOOL DEFINITIONS FOR CLAUDE
# ---------------------------------------------------------------------------

CLAUDE_TOOLS = [
    {
        "name": "search_properties",
        "description": "Search for properties using semantic AI search with 70% similarity threshold. Returns database-verified properties only. Query can be natural language like 'Apartment in New Cairo under 5M EGP'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query for properties"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session identifier for result storage"
                }
            },
            "required": ["query", "session_id"]
        }
    },
    {
        "name": "calculate_mortgage",
        "description": "Calculate monthly mortgage payments using live CBE (Central Bank of Egypt) interest rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "principal": {
                    "type": "integer",
                    "description": "Loan amount in EGP"
                },
                "years": {
                    "type": "integer",
                    "description": "Loan duration in years (default: 20)"
                }
            },
            "required": ["principal"]
        }
    },
    {
        "name": "run_valuation_ai",
        "description": "Run hybrid AI valuation (XGBoost ML + GPT-4o reasoning) to determine fair market price. Returns predicted price, market status, and reasoning bullets for visualization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Property location (e.g., 'New Cairo', 'Sheikh Zayed')"
                },
                "size_sqm": {
                    "type": "integer",
                    "description": "Property size in square meters"
                },
                "finishing": {
                    "type": "string",
                    "description": "Finishing level: 'Core & Shell', 'Semi Finished', 'Fully Finished', 'Ultra Lux'"
                }
            },
            "required": ["location", "size_sqm", "finishing"]
        }
    },
    {
        "name": "compare_units",
        "description": "Compare multiple properties side-by-side with best value analysis. Returns comparison data suitable for visualization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of property IDs to compare (max 4)"
                }
            },
            "required": ["property_ids"]
        }
    },
    {
        "name": "calculate_investment_roi",
        "description": "Calculate detailed ROI analysis including rental yield, break-even timeline, and annual returns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID for ROI analysis"
                },
                "purchase_price": {
                    "type": "number",
                    "description": "Purchase price in EGP"
                },
                "monthly_rent": {
                    "type": "number",
                    "description": "Expected monthly rent in EGP (optional, will estimate if not provided)"
                }
            },
            "required": ["property_id", "purchase_price"]
        }
    },
    {
        "name": "check_real_time_status",
        "description": "Check blockchain-verified availability status of a property in real-time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to check"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "generate_reservation_link",
        "description": "Generate secure JWT-signed reservation link for property checkout. ONLY call after confirming availability via check_real_time_status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to reserve"
                }
            },
            "required": ["property_id"]
        }
    },
    {
        "name": "check_market_trends",
        "description": "Get current market trends and sentiment for a specific compound or location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "compound_name": {
                    "type": "string",
                    "description": "Compound or location name"
                }
            },
            "required": ["compound_name"]
        }
    },
    {
        "name": "schedule_viewing",
        "description": "Schedule a property viewing appointment for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to view"
                },
                "preferred_date": {
                    "type": "string",
                    "description": "Preferred viewing date (YYYY-MM-DD format)"
                },
                "contact_phone": {
                    "type": "string",
                    "description": "User's contact phone number"
                }
            },
            "required": ["property_id", "preferred_date", "contact_phone"]
        }
    },
    {
        "name": "explain_osool_advantage",
        "description": "Explain Osool's competitive advantages over competitors (Nawy, Aqarmap) with respectful comparison.",
        "input_schema": {
            "type": "object",
            "properties": {
                "competitor_name": {
                    "type": "string",
                    "description": "Competitor name to compare against (e.g., 'Nawy', 'Aqarmap')"
                }
            },
            "required": ["competitor_name"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate conversation to human support agent when AI cannot help further.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation"
                },
                "user_contact": {
                    "type": "string",
                    "description": "User contact information"
                }
            },
            "required": ["reason", "user_contact"]
        }
    }
]


# ---------------------------------------------------------------------------
# TOOL EXECUTION MAPPING
# ---------------------------------------------------------------------------

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return its result as a string."""
    try:
        if tool_name == "search_properties":
            return await search_properties.ainvoke(tool_input)
        elif tool_name == "calculate_mortgage":
            return calculate_mortgage.invoke(tool_input)
        elif tool_name == "run_valuation_ai":
            return run_valuation_ai.invoke(tool_input)
        elif tool_name == "compare_units":
            return await compare_units.ainvoke(tool_input)
        elif tool_name == "calculate_investment_roi":
            return await calculate_investment_roi.ainvoke(tool_input)
        elif tool_name == "check_real_time_status":
            return check_real_time_status.invoke(tool_input)
        elif tool_name == "generate_reservation_link":
            return generate_reservation_link.invoke(tool_input)
        elif tool_name == "check_market_trends":
            return check_market_trends.invoke(tool_input)
        elif tool_name == "schedule_viewing":
            return schedule_viewing.invoke(tool_input)
        elif tool_name == "explain_osool_advantage":
            return explain_osool_advantage.invoke(tool_input)
        elif tool_name == "escalate_to_human":
            return escalate_to_human.invoke(tool_input)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# CLAUDE SALES AGENT CLASS
# ---------------------------------------------------------------------------

class ClaudeSalesAgent:
    """
    AMR (Advanced Market Reasoner) - Claude-powered sales agent.

    World-class AI sales agent that uses Claude 3.5 Sonnet for:
    - Advanced multi-step reasoning
    - Data-driven property analysis
    - Statistical comparisons with visual data
    - Nuanced objection handling
    - Egyptian market expertise
    """

    def __init__(self):
        self.model = config.CLAUDE_MODEL
        self.max_tokens = config.CLAUDE_MAX_TOKENS
        self.temperature = config.CLAUDE_TEMPERATURE

        # Phase 3: Customer Intelligence
        self.customer_segment = CustomerSegment.UNKNOWN
        self.lead_score = None
        self.conversation_history = []

        # Analytics tracking
        self.analytics = ConversationAnalyticsService()

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        import re
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        arabic_chars = len(arabic_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return "en"
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"

    def build_system_prompt(self, user_input: str = "") -> str:
        """Build the 'Wolf of Cairo' System Prompt using the new prompt system."""

        # Detect language from user input
        detected_language = self.detect_language(user_input) if user_input else "ar"

        # Get lead temperature
        lead_temp = None
        lead_score_val = None
        if self.lead_score:
            lead_temp = self.lead_score.get("temperature", "cold")
            lead_score_val = self.lead_score.get("score", 50)

        # Get customer segment
        segment = None
        if self.customer_segment and self.customer_segment != CustomerSegment.UNKNOWN:
            segment = self.customer_segment.value

        # Use the new Wolf prompt system
        base_prompt = get_wolf_system_prompt(
            customer_segment=segment,
            lead_temperature=lead_temp,
            lead_score=lead_score_val,
            detected_language=detected_language,
            conversation_phase="qualification"
        )

        # Add tool enforcement if needed based on user input
        required_tools = data_first_enforcer.get_required_tools(user_input)
        if required_tools:
            tool_enforcement = data_first_enforcer.get_tool_enforcement_prompt(required_tools)
            base_prompt = tool_enforcement + "\n" + base_prompt

        return base_prompt

    async def chat(
        self,
        user_input: str,
        session_id: str = "default",
        chat_history: list = None,
        user: Optional[dict] = None
    ) -> str:
        """
        Main chat method - Now with Reasoning Loop Architecture.

        Args:
            user_input: User's message
            session_id: Session identifier
            chat_history: Previous conversation messages
            user: User object if authenticated

        Returns:
            AI response text
        """
        
        # Feature flag for safe rollback
        REASONING_LOOP_ENABLED = os.getenv("ENABLE_REASONING_LOOP", "true").lower() == "true"
        
        try:
            if REASONING_LOOP_ENABLED:
                # NEW ARCHITECTURE: Reasoning Loop (Hunt → Analyze → Speak)
                from app.ai_engine.hybrid_brain import hybrid_brain
                
                # Convert chat history to simple dict format
                history_for_loop = []
                if chat_history:
                    for msg in chat_history:
                        if hasattr(msg, "content"):
                            role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                            history_for_loop.append({"role": role, "content": msg.content})
                        elif isinstance(msg, dict):
                            history_for_loop.append(msg)
                
                # Delegate to reasoning loop
                response = await hybrid_brain.process_turn(
                    query=user_input,
                    history=history_for_loop,
                    profile=user
                )
                
                return response
                
            else:
                # OLD ARCHITECTURE: Direct Claude (fallback)
                return await self._legacy_claude_chat(user_input, session_id, chat_history, user)
                
        except Exception as e:
            logger.error(f"❌ Reasoning loop failed: {e}", exc_info=True)
            # Auto-fallback to legacy system
            logger.warning("⚠️ Falling back to legacy Claude chat")
            return await self._legacy_claude_chat(user_input, session_id, chat_history, user)
    
    async def _legacy_claude_chat(
        self,
        user_input: str,
        session_id: str,
        chat_history: list,
        user: Optional[dict]
    ) -> str:
        """Legacy Claude-only chat method (pre-reasoning loop)."""

        # Initialize chat history
        if chat_history is None:
            chat_history = []

        # Phase 4: Data-First Protocol - Check if we need to ask discovery questions
        # Convert chat history to list of dicts for enforcer
        history_for_enforcer = []
        for msg in chat_history:
            if hasattr(msg, "content"):
                role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                history_for_enforcer.append({"role": role, "content": msg.content})

        should_ask, discovery_question = data_first_enforcer.should_ask_discovery(
            user_input, history_for_enforcer
        )

        if should_ask and discovery_question:
            # Return discovery question instead of processing with AI
            # This ensures we never assume - we always ask first
            return discovery_question

        # Phase 3: Customer Intelligence
        # Classify customer segment after 2+ messages
        full_conversation = "\n".join([
            f"{'User' if i % 2 == 0 else 'Assistant'}: {msg.content if hasattr(msg, 'content') else str(msg)}"
            for i, msg in enumerate(chat_history[-10:])  # Last 10 messages
        ]) + f"\nUser: {user_input}"

        if len(chat_history) >= 2:
            budget = extract_budget_from_conversation(full_conversation)
            self.customer_segment = classify_customer(budget, full_conversation, user)

        # Lead scoring
        # Prepare conversation history for scoring (List[Dict])
        conversation_list_for_scoring = []
        for msg in chat_history:
            if hasattr(msg, "content"):
                role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                conversation_list_for_scoring.append({"role": role, "content": msg.content})
        
        # Add current message
        conversation_list_for_scoring.append({"role": "user", "content": user_input})

        # Prepare session metadata
        properties_viewed_count = len(await get_last_search_results(session_id))
        session_metadata = {
            "properties_viewed": properties_viewed_count,
            "session_start_time": datetime.now(), # Approximation since we don't persist start time
            "duration_minutes": (len(chat_history) * 0.5) # Rough estimate: 30s per message
        }

        self.lead_score = score_lead(
            conversation_history=conversation_list_for_scoring,
            session_metadata=session_metadata,
            user_profile=user
        )

        # Build system prompt with user input for language detection
        system_prompt = self.build_system_prompt(user_input)

        # Convert chat history to Claude format
        claude_messages = []
        for msg in chat_history:
            if hasattr(msg, 'content'):
                role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                claude_messages.append({
                    "role": role,
                    "content": msg.content
                })

        # Add current user message
        claude_messages.append({
            "role": "user",
            "content": user_input
        })

        # Call Claude API with tool use
        try:
            if not anthropic_async:
                return "I apologize, but my AI brain is currently offline (Missing API Key). Please check the backend configuration."

            response = await anthropic_async.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=claude_messages,
                tools=CLAUDE_TOOLS
            )

            # Track token usage
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            # Handle tool use loop
            while response.stop_reason == "tool_use":
                # Extract tool calls
                tool_results = []
                assistant_content = []

                for block in response.content:
                    if block.type == "text":
                        # Convert text block to proper dict format
                        assistant_content.append({
                            "type": "text",
                            "text": block.text
                        })
                    elif block.type == "tool_use":
                        # Execute tool
                        tool_result = await execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })
                        # Convert tool_use block to proper dict format
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })

                # Continue conversation with tool results
                claude_messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                claude_messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Get next response
                response = await anthropic_async.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=claude_messages,
                    tools=CLAUDE_TOOLS
                )

                # Track tokens
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

            # Extract final text response
            final_response = ""
            for block in response.content:
                if block.type == "text":
                    final_response += block.text

            return final_response

        except Exception as e:
            print(f"❌ Claude API Error: {e}")
            # Fallback error message
            return f"I apologize, but I'm experiencing technical difficulties. Please try again in a moment. Error: {str(e)}"

    def get_cost_summary(self) -> dict:
        """Get cost summary for current session."""
        input_cost = (self.total_input_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 4)
        }


# ---------------------------------------------------------------------------
# SINGLETON INSTANCE
# ---------------------------------------------------------------------------

claude_sales_agent = ClaudeSalesAgent()

# Export
__all__ = ["claude_sales_agent", "ClaudeSalesAgent", "get_last_search_results"]
