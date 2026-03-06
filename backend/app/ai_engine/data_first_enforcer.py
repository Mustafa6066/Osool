"""
Data-First Enforcer - The Wolf's Discipline
--------------------------------------------
Ensures CoInvestor never assumes, always verifies with data.
This is the backbone of trustworthy AI responses.

Rules:
1. Property mention -> search_properties must be called first
2. Price quote -> run_valuation_ai must be called first
3. Availability claim -> check_real_time_status must be called first
4. Unknown budget/location/purpose -> ASK, don't assume
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum


class ConversationPhase(Enum):
    """Phases of the sales conversation."""
    DISCOVERY = "discovery"       # First contact, need to gather info
    QUALIFICATION = "qualification"  # Have some info, qualifying needs
    PRESENTATION = "presentation"   # Showing properties
    ANALYSIS = "analysis"          # Deep dive into specific properties
    OBJECTION = "objection"        # Handling concerns
    CLOSING = "closing"            # Ready to close the deal


class MissingContext(Enum):
    """Critical information that must be gathered."""
    BUDGET = "budget"
    PURPOSE = "purpose"      # Investment vs residence
    LOCATION = "location"
    TIMELINE = "timeline"


class DataFirstEnforcer:
    """
    Intercepts AI responses and enforces tool usage before claims.
    The Wolf doesn't guess - the Wolf KNOWS.
    """

    # Tools that MUST be called before certain types of claims
    REQUIRED_TOOLS_BY_INTENT = {
        "property_request": ["search_properties"],
        "property_mention": ["search_properties"],
        "price_discussion": ["run_valuation_ai"],
        "price_quote": ["run_valuation_ai", "calculate_mortgage"],
        "availability_check": ["check_real_time_status"],
        "reservation": ["check_real_time_status", "generate_reservation_link"],
        "comparison": ["compare_units"],
        "investment_analysis": ["calculate_investment_roi"],
        "market_trends": ["check_market_trends"],
    }

    # Intent detection patterns
    INTENT_PATTERNS = {
        "property_request": [
            r"(عايز|عاوز|ابغى|محتاج)\s*(شقة|فيلا|بيت|عقار|وحدة)",
            r"(show|find|search|looking for).*(apartment|villa|property|unit)",
            r"(ابحث|دور|شوف).*(شقة|فيلا|عقار)",
            r"(i want|i need).*(apartment|villa|property)",
        ],
        "price_discussion": [
            r"(كام|سعر|بكام|ثمن|price|cost|how much)",
            r"(غالي|رخيص|expensive|cheap|affordable)",
            r"(ميزانية|budget|range)",
            # Franco-Arabic patterns (Latin transliteration of Egyptian Arabic)
            r"\b(kam|bekam|be kam|b kam|sa3r|se3r)\b",
            r"\b(ghaly|r5ees|re5ees)\b",
        ],
        "availability_check": [
            r"(متاح|موجود|available|in stock)",
            r"(لسه|still).*(متاح|available)",
        ],
        "reservation": [
            r"(احجز|اشتري|خد|reserve|book|buy)",
            r"(عايز احجز|i want to reserve|i want to book)",
        ],
        "comparison": [
            r"(قارن|compare|مقارنة|versus|vs|ولا)",
            r"(أحسن|better|افضل|which one)",
        ],
        "investment_analysis": [
            r"(استثمار|investment|roi|عائد|ربح|return)",
            r"(هيزيد|appreciation|قيمة|value)",
        ],
    }

    # Discovery questions in both Arabic and English
    DISCOVERY_QUESTIONS = {
        MissingContext.BUDGET: {
            "ar": "يا باشا، قبل ما أفتحلك الـ black book - إيه الـ budget range اللي مريحك؟ عشان أجيبلك أحسن الفرص.",
            "en": "Boss, before I open my black book - what's your budget range? I want to show you the best opportunities.",
        },
        MissingContext.PURPOSE: {
            "ar": "سكن ولا استثمار؟ عشان أعرف أفلترلك صح - الاستثمار ليه حسابات مختلفة.",
            "en": "Is this for living or investment? Different game requires different strategy.",
        },
        MissingContext.LOCATION: {
            "ar": "أي منطقة تفكر فيها؟ تجمع؟ زايد؟ أكتوبر؟ العاصمة؟ كل منطقة ليها character مختلف.",
            "en": "Which area are you considering? New Cairo? Sheikh Zayed? October? New Capital? Each has its own vibe.",
        },
        MissingContext.TIMELINE: {
            "ar": "ناوي تشتري قريب ولا بتستكشف السوق؟ عشان أعرف أركز معاك على إيه.",
            "en": "Looking to buy soon or exploring the market? Helps me focus on what matters to you.",
        },
    }

    # Patterns to detect if context is already known
    CONTEXT_DETECTION_PATTERNS = {
        MissingContext.BUDGET: [
            r"(\d+)\s*(مليون|million|M|م)",
            r"(budget|ميزانية).{0,20}(\d+)",
            r"(من|from).{0,10}(\d+).{0,10}(لـ|to|إلى).{0,10}(\d+)",
            r"(تحت|under|فوق|over|around|حوالي|في حدود).{0,10}(\d+)",
            r"(\d+).{0,5}(مليون|million)",  # Catch "2 مليون" with slight spacing
            r"(حوالي|في حدود).{0,15}(\d+)",  # "around/approximately" + number
        ],
        MissingContext.PURPOSE: [
            r"(استثمار|investment|invest)",
            r"(سكن|للسكن|residence|live|living|أسكن)",
            r"(للعيلة|family|عيلة|أولاد|kids)",
        ],
        MissingContext.LOCATION: [
            r"(التجمع|new cairo|تجمع|القاهرة الجديدة)",
            r"(زايد|sheikh zayed|الشيخ زايد)",
            r"(أكتوبر|october|6 أكتوبر)",
            r"(العاصمة|new capital|capital|الإدارية)",
            r"(المعادي|maadi)",
            r"(مدينتي|madinaty)",
        ],
        MissingContext.TIMELINE: [
            r"(قريب|soon|immediately|فوراً|دلوقتي|now)",
            r"(بعد سنة|next year|السنة الجاية)",
            r"(بستكشف|exploring|just looking|بدور)",
        ],
    }

    def __init__(self):
        self.known_context: Dict[MissingContext, bool] = {
            MissingContext.BUDGET: False,
            MissingContext.PURPOSE: False,
            MissingContext.LOCATION: False,
            MissingContext.TIMELINE: False,
        }
        self.tools_called_this_session: List[str] = []

    def detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        arabic_chars = len(arabic_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))

        if total_chars == 0:
            return "en"

        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"

    def detect_intent(self, user_input: str) -> List[str]:
        """Detect user's intent from their message."""
        detected_intents = []
        user_input_lower = user_input.lower()

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    detected_intents.append(intent)
                    break

        return detected_intents

    def get_required_tools(self, user_input: str) -> List[str]:
        """Get list of tools that MUST be called based on user intent."""
        intents = self.detect_intent(user_input)
        required_tools = []

        for intent in intents:
            if intent in self.REQUIRED_TOOLS_BY_INTENT:
                for tool in self.REQUIRED_TOOLS_BY_INTENT[intent]:
                    if tool not in required_tools:
                        required_tools.append(tool)

        return required_tools

    def update_known_context(self, conversation_history: List[Dict[str, str]]) -> None:
        """Update what context we already know from conversation history."""
        full_text = " ".join([
            msg.get("content", "")
            for msg in conversation_history
        ])

        for context_type, patterns in self.CONTEXT_DETECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    self.known_context[context_type] = True
                    break

    def check_missing_context(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        intents: List[str]
    ) -> Optional[MissingContext]:
        """
        Check if we're missing critical context that we need before proceeding.

        Priority order for property requests:
        1. Budget (most important for filtering)
        2. Purpose (investment vs residence changes everything)
        3. Location (if not specified in query)
        """
        # Update known context from conversation
        self.update_known_context(conversation_history + [{"content": user_input}])

        # For property requests, we need budget first
        if "property_request" in intents or "property_mention" in intents:
            if not self.known_context[MissingContext.BUDGET]:
                return MissingContext.BUDGET
            if not self.known_context[MissingContext.PURPOSE]:
                return MissingContext.PURPOSE

        # For investment analysis, we need purpose
        if "investment_analysis" in intents:
            if not self.known_context[MissingContext.PURPOSE]:
                return MissingContext.PURPOSE

        return None

    def generate_discovery_question(
        self,
        missing: MissingContext,
        language: str = "ar"
    ) -> str:
        """Generate appropriate discovery question based on missing context."""
        return self.DISCOVERY_QUESTIONS[missing][language]

    def should_ask_discovery(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Main method to check if we should ask a discovery question.

        Returns:
            Tuple of (should_ask: bool, question: Optional[str])
        """
        intents = self.detect_intent(user_input)

        # If no property-related intent, no need to ask
        if not intents:
            return False, None

        missing = self.check_missing_context(user_input, conversation_history, intents)

        if missing:
            language = self.detect_language(user_input)
            question = self.generate_discovery_question(missing, language)
            return True, question

        return False, None

    def get_tool_enforcement_prompt(self, required_tools: List[str]) -> str:
        """
        Generate a prompt injection to enforce tool usage.
        This is added to the system prompt before Claude processes.
        """
        if not required_tools:
            return ""

        tool_list = ", ".join([f"`{t}`" for t in required_tools])

        return f"""
<mandatory_tool_enforcement>
## CRITICAL: YOU MUST CALL THESE TOOLS FIRST

Before responding to this message, you MUST call: {tool_list}

## PROTOCOL: DATA-FIRST INTEGRITY
1. **NO GUESSING:** Do NOT mention any property, price, or availability without first getting results from these tools.
2. **STRICT VISIBILITY checks:**
    - If the tool result says "payment_plan: null", YOU MUST SAY: "I need to confirm the latest payment plan with the developer."
    - DO NOT hallucinate "5% down" or "8 years" if it's not in the JSON.
3. **EMPTY RESULTS:**
    - If tools return [], say: "حالياً مفيش حاجة متاحة بالمواصفات دي بالظبط، بس في بدائل..." (Currently nothing matches exactly, but here are alternatives...).
    - NEVER invent a property to fill the gap.
</mandatory_tool_enforcement>
"""

    def validate_response_has_data(
        self,
        response: str,
        tool_results: List[Dict[str, Any]]
    ) -> bool:
        """
        Validate that the AI response is backed by tool data.
        Returns True if response seems to use tool data, False if it might be hallucinating.
        """
        # Check if response mentions specific properties
        property_patterns = [
            r"(EGP|جنيه)\s*[\d,]+",  # Price mention
            r"\d+\s*(sqm|م²|متر)",    # Size mention
            r"\d+\s*(bedroom|غرف)",   # Bedroom mention
        ]

        has_specific_data = any(
            re.search(p, response, re.IGNORECASE)
            for p in property_patterns
        )

        # If response has specific data, check if tools were called
        if has_specific_data:
            has_property_tool = any(
                "search_properties" in str(r) or "properties" in str(r)
                for r in tool_results
            )
            return has_property_tool

        return True  # No specific claims, so no validation needed

    def reset_session(self) -> None:
        """Reset context for new session."""
        self.known_context = {
            MissingContext.BUDGET: False,
            MissingContext.PURPOSE: False,
            MissingContext.LOCATION: False,
            MissingContext.TIMELINE: False,
        }
        self.tools_called_this_session = []


# Singleton instance
data_first_enforcer = DataFirstEnforcer()

# Export
__all__ = [
    "DataFirstEnforcer",
    "data_first_enforcer",
    "ConversationPhase",
    "MissingContext"
]
