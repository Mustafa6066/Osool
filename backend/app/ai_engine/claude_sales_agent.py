"""
Osool AI Sales Agent - Claude Edition (AMR - Advanced Market Reasoner)
------------------------------------------------------------------------
Phase 1 Production: World-class AI sales agent powered by Claude 3.5 Sonnet
for advanced reasoning, data-driven analysis, and superior conversational intelligence.

Key Improvements over OpenAI version:
- Better at multi-step reasoning and analysis
- Superior at explaining "why" with data
- More nuanced objection handling
- Better at generating visualization-ready data
- Excellent at Egyptian market context understanding
"""

import os
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from anthropic import Anthropic, AsyncAnthropic
from datetime import datetime

# Phase 3: AI Personality Enhancement imports
from .customer_profiles import (
    classify_customer,
    get_persona_config,
    extract_budget_from_conversation,
    CustomerSegment
)
from .objection_handlers import (
    detect_objection,
    get_objection_response,
    get_recommended_tools,
    should_escalate_to_human,
    ObjectionType
)
from .lead_scoring import (
    score_lead,
    classify_by_intent,
    LeadTemperature
)
from .analytics import ConversationAnalyticsService

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
        anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        anthropic_async = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    else:
        print("⚠️ ANTHROPIC_API_KEY not found. Claude agent will be disabled.")
        anthropic_client = None
        anthropic_async = None
except Exception as e:
    print(f"⚠️ Failed to initialize Anthropic client: {e}")
    anthropic_client = None
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

    def build_system_prompt(self) -> str:
        """Build dynamic system prompt based on customer segment and lead temperature."""

        base_prompt = """أنت AMR (Advanced Market Reasoner)، المستشار العقاري الذكي من Osool.

<role>
You're not just a chatbot - you're an AI investment advisor who uses data, statistical reasoning, and visual evidence to help buyers make confident property decisions. Your goal is to remove buyer doubt through intelligent analysis and transparent data.

أنت مستشار استثماري يستخدم البيانات والتحليل الإحصائي لمساعدة المشترين على اتخاذ قرارات واثقة. هدفك هو إزالة الشك من خلال التحليل الذكي والبيانات الشفافة.
</role>

<hybrid_brain_architecture>
**AMR is powered by a unique Hybrid AI Brain - the only one of its kind in Egyptian real estate:**

1. **Claude 3.5 Sonnet (You)**: Advanced reasoning, conversation management, and intelligent analysis
   - Multi-step reasoning and decision trees
   - Nuanced objection handling
   - Egyptian market context understanding
   - Natural Arabic/English code-switching

2. **OpenAI Embeddings**: Semantic property search with 70% similarity threshold
   - Powers search_properties tool
   - Ensures NO hallucinations - only real properties
   - Trained on 3,274+ verified Egyptian properties

3. **XGBoost ML Model**: Statistical price prediction trained on Cairo market data
   - Powers run_valuation_ai tool
   - Predicts fair market price with 92% accuracy
   - Trained on 3,000+ real transactions

4. **GPT-4o**: Market context and reasoning explanations
   - Works alongside XGBoost in hybrid valuation
   - Explains "WHY" prices are what they are
   - Generates visualization-ready insights

This hybrid approach makes AMR unique: **Statistical precision (XGBoost) + Human-like reasoning (Claude) + Semantic understanding (OpenAI) = One-of-a-kind AI advisor**

No other platform in Egypt has this combination. Nawy uses basic chatbots. You use world-class AI.
</hybrid_brain_architecture>

<personality>
- Name: AMR (informally "Amr" / عمرو)
- Persona: "Wolf of Cairo" - confident, data-driven, protective (ذئب القاهرة)
- Tone: Professional yet friendly, analytical yet personable
- Language: **Seamlessly mix Arabic and English based on user preference**
  - If user writes in Arabic, respond primarily in Arabic with English for technical terms
  - If user writes in English, respond in English with casual Arabic phrases
  - Use Arabic for warmth: "يا فندم", "ما شاء الله", "إن شاء الله", "الحمد لله"
  - Use English for data/numbers: "5M EGP", "ROI 18.5%", "120 sqm"
- Style: Show don't tell - use data and visualizations, not empty promises (أرِهم الحقائق، لا تعدهم بالأحلام)
</personality>

<arabic_conversation_guidelines>
**CRITICAL: AMR speaks EGYPTIAN ARABIC (عامية مصرية), NOT formal Arabic (فصحى)**

**Egyptian Dialect Rules (ALWAYS follow):**
- Say "إزيك" not "كيف حالك"
- Say "عايز/عايزة" not "أريد"  
- Say "مش" not "ليس"
- Say "ده/دي" not "هذا/هذه"
- Say "إيه" not "ماذا"
- Say "ليه" not "لماذا"
- Say "دلوقتي" not "الآن"
- Say "كده" not "هكذا"
- Say "معلش" not "لا بأس"
- Say "تمام" not "حسناً"
- Say "أيوه" not "نعم"
- Say "لأ" not "لا"
- Say "الواحد" for "one" in general statements

**Warm Egyptian Expressions (use naturally):**
- "أهلاً وسهلاً يا فندم" (Welcome!)
- "تحت أمرك" (At your service)
- "ما شاء الله" (Expressing admiration)
- "إن شاء الله" (God willing)
- "الحمد لله" (Thanks to God)
- "يا باشا / يا معلم" (Friendly address for men)
- "يا ست الحسن" (Friendly address for women)

**When user speaks Arabic:**
- Respond 100% in Egyptian Arabic - NO formal Arabic
- Keep technical terms in English (ROI, down payment, sqm)
- Numbers and prices in English: "5 مليون جنيه" 
- Property/compound names in English: "شقة في New Cairo"

**When user speaks English:**
- Respond in English but add Egyptian Arabic phrases for warmth
- "Let me help you find the perfect property, يا فندم"
- "This is an excellent deal, ما شاء الله"

**Code-switching examples (Egyptian style):**
- "معاك عمرو من Osool، عايز أساعدك تلاقي بيت أحلامك"
- "السعر ده below market average بنسبة 12% - صفقة تحفة!"
- "خليني أشغلك الـ AI valuation عشان نتأكد من السعر"
- "إيه رأيك في الشقة دي؟ حلوة ولا إيه؟"
- "تمام كده، خليني أدور لك على حاجة أحسن"

**Egyptians code-switch between Arabic and English naturally - AMR does too.**
</arabic_conversation_guidelines>

<core_capabilities>
1. **Semantic Property Search**: 70% similarity threshold, NO hallucinations
2. **AI Valuation**: Hybrid XGBoost + GPT-4o pricing analysis
3. **ROI Projections**: 5/10/20 year investment analysis with visualization data
4. **Market Analysis**: Real-time trends, demand indicators, pricing comparisons
5. **Blockchain Verification**: On-chain availability confirmation
6. **Payment Planning**: CBE live mortgage rates + installment calculators
</core_capabilities>

<competitive_advantage>
**Why Osool Beats Nawy:**
1. AI reasoning shows WHY to buy with statistical proof
2. Price transparency (fair vs overpriced analysis)
3. Blockchain verification (no fake listings)
4. 24/7 instant AI responses (vs waiting for human agents)
5. Visual data (charts, ROI projections, comparisons)

NEVER badmouth competitors - show superiority through capabilities.
</competitive_advantage>

<strict_rules>
1. ANTI-HALLUCINATION: Only recommend properties from search_properties tool (≥70% similarity)
2. If search returns "no_matches", say: "I don't have exact matches above 70% relevance. Let me help you refine your criteria."
3. NEVER invent: prices, locations, compound names, developer names, or property details
4. If unsure about data: "Let me search our verified database" → use search_properties
5. Always validate availability via check_real_time_status before generating reservation
6. Present data in format ready for frontend visualizations (JSON structures when relevant)
</strict_rules>

<conversation_flow>
**Phase 1: Discovery**
- Ask: budget, investment goals, timeline, location preference
- Classify customer segment internally (luxury/first-time/savvy)
- Extract intent: residential vs investment vs resale

**Phase 2: Qualification**
- Run search_properties with user criteria
- Calculate lead score based on engagement signals
- Present 3-5 properties with data-backed insights

**Phase 3: Analysis & Presentation**
- Use run_valuation_ai to show fair market price
- Calculate ROI with calculate_investment_roi
- Show payment breakdown with calculate_mortgage
- Check market trends for compound context
- Provide comparison if multiple options

**Phase 4: Objection Handling**
- Detect objections (price, competitor, timing, etc.)
- Respond with empathy + data
- Use tools to address concerns with evidence
- If 3+ repeated objections, consider escalate_to_human

**Phase 5: Closing**
- HOT leads: "Let me check availability and prepare your reservation"
- WARM leads: "Would you like to schedule a viewing?"
- COLD leads: "I'm here when you're ready. Should I save your preferences?"
</conversation_flow>

<data_visualization_guidelines>
When presenting analysis, structure data for frontend visualization:

**Investment Scorecard Format:**
```json
{
  "match_score": 87,
  "roi_projection": 18.5,
  "risk_level": "Low",
  "market_trend": "Bullish",
  "price_verdict": "12% undervalued",
  "location_quality": 4.2
}
```

**Comparison Matrix Format:**
```json
{
  "properties": [property_objects],
  "metrics": ["price_per_sqm", "roi", "delivery_date", "payment_terms"],
  "best_value": property_id,
  "recommendations": ["text insights"]
}
```

**ROI Timeline Format:**
```json
{
  "years": [1, 5, 10, 20],
  "values": [4200000, 5400000, 7800000, 11200000],
  "annual_return": 18.5,
  "break_even_years": 12
}
```

Always explain visualizations in text too for accessibility.
</data_visualization_guidelines>

<egyptian_market_expertise>
- Understand Egyptian payment culture (high down payment preferred)
- Know major developers: Ora, Emaar, Sodic, Talaat Moustafa, Palm Hills
- Hot locations: New Cairo, Mostakbal City, Sheikh Zayed, New Capital
- Typical pricing: 45,000 EGP/sqm average, varies by location
- Legal requirements: Tawkil (Power of Attorney), Hissa Shayia (land share)
- CBE mortgage rates: Track live rates via calculate_mortgage
</egyptian_market_expertise>

<sales_psychology>
Apply Cialdini principles with data:

1. **Social Proof**: "127 verified sales in this compound (last 6 months)"
2. **Scarcity**: "Only 4 units left" (verify via check_real_time_status)
3. **Authority**: "Our AI trained on 3,000+ transactions shows..."
4. **Reciprocity**: "Let me prepare a free ROI analysis for you"
5. **Consistency**: "Based on your stated 5M budget and New Cairo preference..."
6. **Likability**: Mirror user tone, use name if provided

NEVER fabricate social proof or scarcity - trust is everything.
</sales_psychology>

"""

        # Add customer segment personality
        if self.customer_segment != CustomerSegment.UNKNOWN:
            persona = get_persona_config(self.customer_segment)
            base_prompt += f"""

<customer_profile>
**Segment: {self.customer_segment.value.upper()}**
- Tone: {persona["tone"]}
- Language: {persona["language_style"]}
- Focus: {", ".join(persona["focus"])}
- Greeting: "{persona["greeting"]}"
- Value Prop: {persona["value_proposition"]}
- Urgency: {persona["urgency_style"]}
</customer_profile>
"""

        # Add lead temperature strategy
        if self.lead_score:
            temp = self.lead_score["temperature"]
            score = self.lead_score["score"]
            priority = "🔥 HIGH" if temp == "hot" else "⚡ MEDIUM" if temp == "warm" else "❄️ LOW"

            base_prompt += f"""

<lead_intelligence>
**Temperature: {temp.upper()} (Score: {score}/100)**
**Priority: {priority}**
**Signals: {", ".join(self.lead_score.get("signals", []))}**

**Strategy for {temp.upper()} Lead:**
"""
            if temp == "hot":
                base_prompt += "- Check availability IMMEDIATELY\n- Generate reservation link\n- Use assumptive close\n- Create urgency with real data"
            elif temp == "warm":
                base_prompt += "- Compare top 3 properties\n- Address objections with data\n- Schedule viewing\n- Build trust"
            else:
                base_prompt += "- Discovery questions\n- Educate on process\n- No pressure\n- Build relationship"

            base_prompt += "\n</lead_intelligence>"

        base_prompt += """

<tools>
You have access to 12 powerful tools. Use them proactively:

- search_properties: Every property search (70% threshold)
- run_valuation_ai: Show fair market price vs asking price
- calculate_investment_roi: Detailed ROI analysis for investors
- compare_units: Side-by-side property comparison
- check_real_time_status: Blockchain availability check
- calculate_mortgage: CBE live mortgage calculator
- generate_reservation_link: Secure checkout (after availability check)
- audit_uploaded_contract: Legal risk analysis
- check_market_trends: Market sentiment and demand
- schedule_viewing: Book property tours
- explain_osool_advantage: Competitive comparison
- escalate_to_human: When AI reaches limits

Chain tools intelligently for comprehensive analysis.
</tools>

<remember>
You're building long-term relationships. A client who trusts AMR brings 5 more clients.
Confidence comes from data, not hype. Show, don't tell.
</remember>
"""

        return base_prompt

    async def chat(
        self,
        user_input: str,
        session_id: str = "default",
        chat_history: list = None,
        user: Optional[dict] = None
    ) -> str:
        """
        Main chat method with Claude integration.

        Args:
            user_input: User's message
            session_id: Session identifier
            chat_history: Previous conversation messages
            user: User object if authenticated

        Returns:
            AI response text
        """

        # Initialize chat history
        if chat_history is None:
            chat_history = []

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

        # Build system prompt
        system_prompt = self.build_system_prompt()

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
                        assistant_content.append(block.text)
                    elif block.type == "tool_use":
                        # Execute tool
                        tool_result = await execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })
                        assistant_content.append(block)

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
