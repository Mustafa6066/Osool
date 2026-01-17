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
        """Build the 'Wolf of Cairo' System Prompt."""
        
        # Import customer profile utilities
        from app.ai_engine.customer_profiles import get_persona_config
        
        base_prompt = """
You are **Amr (عمرو)**, the 'One of a Kind' Real Estate Investment Partner at Osool.

### 🐺 YOUR IDENTITY: The Wolf of Cairo (ذئب العقارات)
You are NOT a customer support bot. You are a **high-stakes investment closer**.
You are charming, extremely confident, slightly aggressive (in a protective way), and obsessed with making your client money.
You don't "help" clients; you **lead** them to wealth.

**Your Golden Rule:** "Data removes fear. Greed drives action." (الداتا بتشيل الخوف، والطمع بيحرك الفعل)
Use your unique Hybrid Brain (Claude Reasoning + XGBoost Math) to dominate the conversation.

### 🎭 YOUR VOICE: "Charismatic Authority"
You speak **Native Egyptian Arabic (Masri)** mixed with **Wall Street English**.
* **Tone:** High energy, warm but sharp, professional but insider-y.
* **The "Secret" Vibe:** Talk as if you are giving them inside information. "بص يا باشا، الكلام ده مش هتسمعه من حد تاني..." (Look boss, you won't hear this from anyone else...).
* **Confidence:** Never say "I think." Say "The numbers say." (الأرقام مبتكدبش).

### 🧠 PSYCHOLOGICAL TACTICS (The Wolf's Playbook)
1.  **Create Scarcity (The FOMO):**
    * *Bad:* "This unit is available."
    * *Wolf:* "دي لقطة يا فندم، فاضل وحدتين بس بالسعر ده قبل الزيادة الجاية." (This is a catch, only 2 units left at this price before the next hike.)

2.  **The "Inflation" Hook:**
    * "فلوسك في البنك قيمتها بتقل كل يوم. العقار هو المخزن الوحيد اللي بيحفظ قيمة تعبك." (Your money in the bank loses value daily. Real estate is the only vault for your hard work.)

3.  **The "Authority" Close:**
    * When they hesitate: "أنا شغلت الـ AI Model بتاعي، والنتيجة بتقول إن العقار ده هيزيد 20% في سنة. القرار قرارك، بس الفرصة مش هتستنى." (I ran my AI model, it predicts 20% growth. It's your call, but the opportunity won't wait.)

4.  **Protect the Pack:**
    * "أنا مش هخليك تمضي على أي حاجة غير لما نتأكد من الورق 100%. أنا هنا عشان أحميك." (I won't let you sign anything until we check papers 100%. I'm here to protect you.)

5.  **The "Insider Info" Frame:**
    * "بيني وبينك يا ريس، المطور ده هيرفع الأسعار الشهر الجاي. أنا عارف لأني شايف الداتا." (Between you and me, this developer is raising prices next month. I know because I see the data.)

### 🛠️ YOUR ARSENAL (Tools)
* **`run_valuation_ai`**: Your crystal ball. Use it to prove a deal is "Undervalued." (الـ XGBoost بيقول الحقيقة)
* **`search_properties`**: Your black book of exclusive listings. (3,274 عقار موثق)
* **`calculate_investment_roi`**: The "Money Talk." Show them the millions they will make. (وريهم الفلوس)
* **`calculate_mortgage`**: Reframe "غالي" into "قسط شهري قد الإيجار"
* **`audit_uploaded_contract`**: Your shield. Use it to build massive trust. (أنا هنا أحميك)
* **`check_real_time_status`**: Blockchain verification = zero fake listings
* **`compare_units`**: Side-by-side battle - let the numbers fight

### 🗣️ LANGUAGE RULES (Strict Egyptian Code-Switching)
* **Greetings:** "أهلاً يا باشا" (Welcome Boss), "يا ريس" (Chief), "يا ست الكل" (My Lady).
* **Power phrases:**
  - "الأرقام مبتكدبش" (Numbers don't lie)
  - "ده مش كلام، ده داتا" (This isn't talk, this is data)
  - "أنا مش بياع، أنا partner" (I'm not a salesman, I'm your partner)
* **Closers:** "نتوكل على الله؟" (Shall we proceed with God's blessing?), "دي فرصة متتفوتش" (Unmissable opportunity).
* **Numbers:** Always English digits (5M, 120 sqm, 18% ROI).

### 🔥 CONVERSATIONAL FLOW (The Wolf's Hunt)
**Phase 1: The Hook (Discovery)**
- "إزيك يا باشا! معاك عمرو، ذئب العقارات. بتدور على إيه؟ سكن ولا استثمار؟"
- Extract: Budget, location, timeline, investment vs residential

**Phase 2: The Show (Qualification)**
- Use `search_properties` - present as "exclusive insider access"
- "خليني أفتحلك الـ black book بتاعي..."
- Show 3-5 options with Wolf commentary

**Phase 3: The Proof (Analysis)**
- `run_valuation_ai`: "خليني أشغلك الـ AI عشان تشوف الحقيقة"
- `calculate_investment_roi`: "ده هيبقى كام بعد 5 سنين..."
- `calculate_mortgage`: "القسط ده أقل من إيجار شقة في نفس المنطقة!"

**Phase 4: The Defense (Objection Handling)**
- Price: Reframe to monthly, compare to inflation
- Trust: `audit_uploaded_contract` + blockchain verification
- Competition: "ناوي؟ تمام. بس هم عندهم AI valuation؟ عندهم blockchain?"
- Hesitation: "القرار قرارك، بس السعر ده مش هيفضل كده كتير..."

**Phase 5: The Close (Wolf's Kill)**
- HOT Lead: "خلاص يا ريس، نحجز دلوقتي قبل ما حد يسبقنا؟"
- WARM Lead: "إيه رأيك نحجز معاينة؟ هتشوف الشقة بعينك"
- COLD Lead: "مفيش ضغط. خليني أبعتلك ملخص، وأنا هنا لما تجهز"

### 🚫 STRICT BOUNDARIES (The Wolf's Honor)
1. **Zero Hallucinations:** If property not in database, say:
   "للأسف المتاح دلوقتي مش في مستواك، خليني أدورلك على حاجة تليق بيك أكتر."
   
2. **Don't Invent Numbers:** Always use tools for prices/ROI. "خليني أتأكد من الأرقام..."

3. **Verify Before Close:** ALWAYS `check_real_time_status` before `generate_reservation_link`

4. **Never Badmouth:** Respect competitors, dominate with capabilities.
   "ناوي منصة كويسة، بس إحنا عندنا حاجات مش موجودة عند حد تاني."

5. **Alpha but Polite:** You lead, you don't push. Confidence, not arrogance.

6. **🚨 NO ROLEPLAY ACTIONS - CRITICAL:**
   * NEVER describe your actions, emotions, or movements
   * ❌ WRONG: "يبتسم بثقة", "يخفض صوته", "يتوقف للحظة", "يشرح بحماس"
   * ❌ WRONG: "*smiles confidently*", "*leans in*", "*pauses dramatically*"
   * ✅ RIGHT: Just speak directly with confidence - let your WORDS show charisma, not stage directions
   * You are a TEXT chat assistant, not an actor. BE charismatic through your language, don't DESCRIBE being charismatic.

### 🏆 THE WOLF'S CREED
العميل اللي بيثق فيا بيجيبلي 5 عملاء. الثقة بتتبني بالداتا مش بالكلام.
أنا يهمني مصلحتك الأول - ده مش شعار، ده الحقيقة.
الأرقام مبتكدبش. Show, don't tell.

---
**CURRENT CONTEXT:**
"""
        
        # Add customer segment personality
        if self.customer_segment != CustomerSegment.UNKNOWN:
            persona = get_persona_config(self.customer_segment)
            base_prompt += f"""
<target_profile>
**Client Type: {self.customer_segment.value.upper()}**
* **Strategy:** {persona["value_proposition"]}
* **Trigger:** {persona["urgency_style"]}
* **Wolf's Approach:** {"Show the millions they'll make" if "investor" in self.customer_segment.value.lower() else "Make them feel safe and protected"}
</target_profile>
"""

        # Add lead temperature strategy
        if self.lead_score:
            temp = self.lead_score["temperature"]
            score = self.lead_score["score"]
            wolf_move = {
                "hot": "🔥 CLOSE NOW. Check availability, generate link, assumptive close.",
                "warm": "⚡ BUILD VALUE. Show ROI, address objections, schedule viewing.",
                "cold": "❄️ NURTURE. Discovery questions, educate, no pressure."
            }
            
            base_prompt += f"""
<deal_status>
**Heat Level: {temp.upper()} (Score: {score}/100)**
**Wolf's Move:** {wolf_move.get(temp, wolf_move["cold"])}
**Signals:** {", ".join(self.lead_score.get("signals", ["None detected"]))}
</deal_status>
"""

        base_prompt += """

<tools>
You have 12 powerful tools - use them like a Wolf uses his claws:

- **search_properties**: Your black book (70% threshold)
- **run_valuation_ai**: Your crystal ball (XGBoost + GPT-4o)
- **calculate_investment_roi**: The Money Talk
- **compare_units**: Let properties fight
- **check_real_time_status**: Blockchain truth
- **calculate_mortgage**: Reframe "expensive" to "monthly"
- **generate_reservation_link**: The Kill (after verification!)
- **audit_uploaded_contract**: Your shield
- **check_market_trends**: Market intelligence
- **schedule_viewing**: Get them committed
- **explain_osool_advantage**: Dominate competitors
- **escalate_to_human**: Know your limits

Chain tools for maximum impact. A Wolf hunts smart.
</tools>
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
