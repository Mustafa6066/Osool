"""
Parallel Brain Orchestrator - State-of-the-Art Hybrid AI
--------------------------------------------------------
The Wolf's Hybrid Brain runs Claude, GPT-4o, and XGBoost
in parallel for maximum intelligence and speed.

Architecture:
1. User query arrives
2. PARALLEL: Claude reasoning + GPT-4o insights + XGBoost predictions
3. Claude synthesizes all insights into final Wolf response

This is what makes Amr one-of-a-kind.
"""

import asyncio
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import config
from .amr_master_prompt import get_wolf_system_prompt, get_synthesis_prompt
from .data_first_enforcer import DataFirstEnforcer, data_first_enforcer
from .xgboost_predictor import OsoolXGBoostPredictor


class ParallelBrainOrchestrator:
    """
    State-of-the-art hybrid brain using parallel model collaboration.

    The Wolf's Secret Weapon:
    - Claude: Strategic reasoning, conversation flow, Egyptian psychology
    - GPT-4o: Fast market insights, creative angles, quick facts
    - XGBoost: Price prediction, deal scoring, urgency detection

    All run in parallel, then Claude synthesizes the final response.
    """

    def __init__(self):
        # Initialize AI clients
        self.claude_client = None
        self.openai_client = None

        if config.ANTHROPIC_API_KEY:
            self.claude_client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

        if config.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

        # XGBoost predictor
        self.xgb_predictor = OsoolXGBoostPredictor()

        # Data-first enforcer
        self.data_enforcer = data_first_enforcer

        # Configuration
        self.claude_model = config.CLAUDE_MODEL
        self.gpt_model = "gpt-4o"
        self.claude_max_tokens = config.CLAUDE_MAX_TOKENS
        self.claude_temperature = config.CLAUDE_TEMPERATURE

        # Token tracking
        self.total_claude_tokens = 0
        self.total_gpt_tokens = 0

    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        arabic_chars = len(arabic_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))

        if total_chars == 0:
            return "en"

        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"

    async def process_parallel(
        self,
        user_input: str,
        session_id: str,
        chat_history: List[Dict[str, str]],
        user: Optional[Dict] = None,
        customer_segment: Optional[str] = None,
        lead_temperature: Optional[str] = None,
        lead_score: Optional[int] = None,
        tools: List[Dict] = None,
        execute_tool_func: callable = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Main entry point for parallel brain processing.

        Args:
            user_input: User's message
            session_id: Session identifier
            chat_history: Previous conversation messages
            user: User object if authenticated
            customer_segment: Detected customer type
            lead_temperature: hot/warm/cold
            lead_score: 0-100 score
            tools: List of available tools for Claude
            execute_tool_func: Function to execute tools

        Returns:
            Tuple of (response_text, metadata)
        """
        detected_language = self.detect_language(user_input)

        # Check for missing context - if missing, ask discovery question
        should_ask, question = self.data_enforcer.should_ask_discovery(
            user_input, chat_history
        )

        if should_ask and question:
            # Return discovery question instead of processing
            return question, {
                "type": "discovery_question",
                "language": detected_language,
                "phase": "discovery"
            }

        # Build context for all models
        context = {
            "user_input": user_input,
            "session_id": session_id,
            "chat_history": chat_history,
            "user": user,
            "customer_segment": customer_segment,
            "lead_temperature": lead_temperature,
            "lead_score": lead_score,
            "detected_language": detected_language,
        }

        # Launch all three models in parallel
        tasks = [
            self._claude_reasoning(context, tools, execute_tool_func),
            self._gpt_analysis(context),
            self._xgboost_scoring(context)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Extract results (handle exceptions gracefully)
        claude_result = results[0] if not isinstance(results[0], Exception) else {"response": "", "tool_results": []}
        gpt_insights = results[1] if not isinstance(results[1], Exception) else {}
        xgb_scores = results[2] if not isinstance(results[2], Exception) else {}

        # If Claude already produced a good response with tools, use it
        # Otherwise, synthesize with all insights
        if claude_result.get("response") and claude_result.get("tool_results"):
            # Claude used tools - enhance with XGBoost data
            final_response = await self._enhance_with_insights(
                claude_result["response"],
                gpt_insights,
                xgb_scores,
                detected_language
            )
        elif claude_result.get("response"):
            # Claude responded without tools - synthesize all
            final_response = await self._claude_synthesize(
                claude_result["response"],
                gpt_insights,
                xgb_scores,
                detected_language
            )
        else:
            # Fallback to GPT insights if Claude failed
            final_response = self._generate_fallback_response(
                gpt_insights, detected_language
            )

        metadata = {
            "type": "parallel_brain",
            "language": detected_language,
            "claude_tokens": claude_result.get("tokens", 0),
            "gpt_tokens": gpt_insights.get("tokens", 0),
            "xgb_scores": xgb_scores,
            "tools_used": claude_result.get("tools_used", []),
            "properties": claude_result.get("properties", [])
        }

        return final_response, metadata

    async def _claude_reasoning(
        self,
        context: Dict[str, Any],
        tools: List[Dict] = None,
        execute_tool_func: callable = None
    ) -> Dict[str, Any]:
        """
        Claude handles strategic reasoning, conversation flow, and tool execution.
        This is the primary brain for complex interactions.
        """
        if not self.claude_client:
            return {"response": "", "tool_results": [], "tokens": 0}

        # Build system prompt with context
        system_prompt = get_wolf_system_prompt(
            customer_segment=context.get("customer_segment"),
            lead_temperature=context.get("lead_temperature"),
            lead_score=context.get("lead_score"),
            detected_language=context.get("detected_language", "ar"),
            conversation_phase="qualification"  # Will be dynamic later
        )

        # Get required tools based on user intent
        required_tools = self.data_enforcer.get_required_tools(context["user_input"])
        if required_tools:
            tool_enforcement = self.data_enforcer.get_tool_enforcement_prompt(required_tools)
            system_prompt = tool_enforcement + "\n" + system_prompt

        # Convert chat history to Claude format
        messages = []
        for msg in context.get("chat_history", []):
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                content = msg.content if hasattr(msg, "content") else str(msg)

            messages.append({"role": role, "content": content})

        # Add current user message
        messages.append({"role": "user", "content": context["user_input"]})

        try:
            # Call Claude with tools
            response = await self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=self.claude_max_tokens,
                temperature=self.claude_temperature,
                system=system_prompt,
                messages=messages,
                tools=tools or []
            )

            total_tokens = response.usage.input_tokens + response.usage.output_tokens
            tool_results = []
            tools_used = []
            properties = []

            # Handle tool use loop
            while response.stop_reason == "tool_use" and execute_tool_func:
                assistant_content = []
                new_tool_results = []

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({
                            "type": "text",
                            "text": block.text
                        })
                    elif block.type == "tool_use":
                        # Execute tool
                        tool_result = await execute_tool_func(block.name, block.input)
                        tools_used.append(block.name)

                        # Track properties from search
                        if block.name == "search_properties":
                            try:
                                result_data = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                                if isinstance(result_data, list):
                                    properties.extend(result_data)
                                elif isinstance(result_data, dict) and "properties" in result_data:
                                    properties.extend(result_data["properties"])
                            except:
                                pass

                        tool_results.append({
                            "tool": block.name,
                            "input": block.input,
                            "result": tool_result
                        })
                        new_tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })

                # Continue conversation with tool results
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": new_tool_results})

                # Get next response
                response = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=self.claude_max_tokens,
                    temperature=self.claude_temperature,
                    system=system_prompt,
                    messages=messages,
                    tools=tools or []
                )

                total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Extract final text response
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text

            self.total_claude_tokens += total_tokens

            return {
                "response": final_text,
                "tool_results": tool_results,
                "tools_used": tools_used,
                "properties": properties,
                "tokens": total_tokens
            }

        except Exception as e:
            print(f"Claude reasoning error: {e}")
            return {"response": "", "tool_results": [], "tokens": 0, "error": str(e)}

    async def _gpt_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        GPT-4o provides fast market insights, creative angles, and quick facts.
        Runs in parallel with Claude to add market color.
        """
        if not self.openai_client:
            return {}

        detected_lang = context.get("detected_language", "ar")
        lang_instruction = (
            "Respond in Arabic (Egyptian dialect)" if detected_lang == "ar"
            else "Respond in English"
        )

        prompt = f"""
You are a market analyst supporting a real estate AI agent in Egypt.
The user said: "{context['user_input']}"

Provide quick market insights in JSON format:
{{
    "market_sentiment": "bullish/bearish/stable",
    "key_insight": "One sentence about current market conditions",
    "alternative_angles": ["angle1", "angle2"],
    "quick_facts": ["fact1", "fact2"],
    "urgency_factors": ["factor1", "factor2"]
}}

Focus on Egyptian real estate market (New Cairo, Sheikh Zayed, October, New Capital).
{lang_instruction}
Keep insights brief and actionable.
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": "You are a concise market analyst. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            tokens = response.usage.total_tokens if response.usage else 0
            self.total_gpt_tokens += tokens

            content = response.choices[0].message.content
            insights = json.loads(content) if content else {}
            insights["tokens"] = tokens

            return insights

        except Exception as e:
            print(f"GPT analysis error: {e}")
            return {"error": str(e)}

    async def _xgboost_scoring(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        XGBoost provides deal probability, price predictions, and urgency scoring.
        Fast ML predictions to augment AI responses with data.
        """
        try:
            # Build features from context
            chat_history = context.get("chat_history", [])
            user_input = context.get("user_input", "")

            # Session features for deal scoring
            session_features = {
                "messages_count": len(chat_history),
                "budget_mentioned": self._has_budget_mention(chat_history, user_input),
                "location_specified": self._has_location_mention(chat_history, user_input),
                "properties_viewed": 0,  # Will be updated from session
                "objections_raised": self._count_objections(chat_history),
                "closing_language": self._has_closing_intent(user_input),
                "lead_score": context.get("lead_score", 50)
            }

            # Get predictions
            deal_probability = self.xgb_predictor.predict_deal_probability(session_features)
            urgency_score = self.xgb_predictor.predict_urgency(session_features)

            # Determine market status based on conversation
            market_status = "stable"
            if deal_probability > 0.7:
                market_status = "hot"
            elif deal_probability < 0.3:
                market_status = "cold"

            return {
                "deal_probability": deal_probability,
                "urgency_score": urgency_score,
                "market_status": market_status,
                "predicted_price": None,  # Set when specific property discussed
                "confidence": 0.75
            }

        except Exception as e:
            print(f"XGBoost scoring error: {e}")
            return {
                "deal_probability": 0.5,
                "urgency_score": 0.5,
                "market_status": "stable",
                "error": str(e)
            }

    def _has_budget_mention(self, history: List, current: str) -> bool:
        """Check if budget was mentioned in conversation."""
        patterns = [
            r"(\d+)\s*(مليون|million|M|م)",
            r"(budget|ميزانية)",
            r"\d{6,}",  # 6+ digit numbers
        ]
        text = " ".join([m.get("content", "") for m in history if isinstance(m, dict)])
        text += " " + current

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _has_location_mention(self, history: List, current: str) -> bool:
        """Check if location was mentioned."""
        locations = [
            "التجمع", "new cairo", "زايد", "sheikh zayed",
            "أكتوبر", "october", "العاصمة", "new capital",
            "المعادي", "maadi", "مدينتي", "madinaty"
        ]
        text = " ".join([m.get("content", "") for m in history if isinstance(m, dict)])
        text = (text + " " + current).lower()

        return any(loc.lower() in text for loc in locations)

    def _count_objections(self, history: List) -> int:
        """Count objection signals in conversation."""
        objection_patterns = [
            r"(غالي|expensive|مكلف)",
            r"(محتاج وقت|need time|أفكر|think)",
            r"(مش متأكد|not sure|hesitant)",
        ]
        text = " ".join([m.get("content", "") for m in history if isinstance(m, dict)])
        count = 0
        for pattern in objection_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count

    def _has_closing_intent(self, text: str) -> bool:
        """Check for closing intent signals."""
        closing_patterns = [
            r"(احجز|reserve|book)",
            r"(اشتري|buy|purchase)",
            r"(خلاص|okay|let's do)",
            r"(موافق|agree|deal)",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in closing_patterns)

    async def _enhance_with_insights(
        self,
        claude_response: str,
        gpt_insights: Dict[str, Any],
        xgb_scores: Dict[str, Any],
        detected_language: str
    ) -> str:
        """
        Enhance Claude's tool-based response with XGBoost and GPT insights.
        Light touch - just add data authority if appropriate.
        """
        # If deal probability is high, the response is probably good as-is
        if xgb_scores.get("deal_probability", 0.5) > 0.6:
            # Add subtle data authority to existing response
            if detected_language == "ar":
                if "%" not in claude_response and xgb_scores.get("deal_probability"):
                    # Could add XGB insight, but keep response clean for now
                    pass
            return claude_response

        return claude_response

    async def _claude_synthesize(
        self,
        claude_draft: str,
        gpt_insights: Dict[str, Any],
        xgb_scores: Dict[str, Any],
        detected_language: str
    ) -> str:
        """
        Claude synthesizes all insights into final Wolf response.
        Used when Claude didn't use tools or needs enhancement.
        """
        if not self.claude_client:
            return claude_draft or self._generate_fallback_response(gpt_insights, detected_language)

        if not claude_draft:
            return self._generate_fallback_response(gpt_insights, detected_language)

        synthesis_prompt = get_synthesis_prompt(
            claude_draft, gpt_insights, xgb_scores, detected_language
        )

        try:
            response = await self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=1000,
                temperature=0.5,
                messages=[{"role": "user", "content": synthesis_prompt}]
            )

            self.total_claude_tokens += response.usage.input_tokens + response.usage.output_tokens

            for block in response.content:
                if block.type == "text":
                    return block.text

            return claude_draft

        except Exception as e:
            print(f"Synthesis error: {e}")
            return claude_draft

    def _generate_fallback_response(
        self,
        gpt_insights: Dict[str, Any],
        detected_language: str
    ) -> str:
        """Generate fallback response if primary models fail."""
        if detected_language == "ar":
            return "يا باشا، حصل مشكلة تقنية صغيرة. ممكن تعيد السؤال تاني؟"
        else:
            return "Boss, had a small technical hiccup. Could you repeat that?"

    def get_token_summary(self) -> Dict[str, Any]:
        """Get token usage summary."""
        return {
            "claude_tokens": self.total_claude_tokens,
            "gpt_tokens": self.total_gpt_tokens,
            "total_tokens": self.total_claude_tokens + self.total_gpt_tokens
        }


# Singleton instance
parallel_brain = ParallelBrainOrchestrator()

# Export
__all__ = ["ParallelBrainOrchestrator", "parallel_brain"]
