"""
Wolf Orchestrator - The Unified Wolf Brain
-------------------------------------------
The main reasoning loop that orchestrates all components:
1. PERCEPTION (GPT-4o) - Intent extraction
2. PSYCHOLOGY (Pattern Match) - Emotional state detection
3. HUNT (Database) - Property search
4. ANALYZE (XGBoost/Math) - Deal scoring
5. UI ACTIONS (Visuals) - Chart triggers
6. STRATEGY (Psychology-Aware) - Pitch angle selection
7. SPEAK (Claude 3.5 Sonnet) - Narrative generation

This replaces the monolithic hybrid_brain.py with a clean, modular design.
"""

import os
import json
import logging
import asyncio
import hashlib
import re
from typing import Dict, List, Any, Optional, AsyncIterator
from datetime import datetime
from anthropic import AsyncAnthropic
import anthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Internal modules
from .wolf_router import wolf_router, RouteType, RouteDecision
from .perception_layer import perception_layer, Intent
from .psychology_layer import (
    analyze_psychology,
    determine_strategy,
    get_psychology_context_for_prompt,
    PsychologyProfile,
    PsychologicalState,
    UrgencyLevel,
    DecisionStage,
    BuyerPersona,
    ObjectionResolutionTracker,
)
from .reasoning_engine import reasoning_engine, ReasoningChain
from .analytical_engine import (
    analytical_engine, market_intelligence, OsoolScore,
    AREA_BENCHMARKS, MARKET_SEGMENTS, DEVELOPER_GRAPH,
    payment_plan_analyzer, developer_trust_scorer, resale_intelligence, trade_up_advisor,
)
from app.config import config
from .market_analytics_layer import MarketAnalyticsLayer
from .analytical_actions import generate_analytical_ui_actions
from .amr_master_prompt import get_wolf_system_prompt, AMR_SYSTEM_PROMPT, is_discount_request, FRAME_CONTROL_EXAMPLES
from .hybrid_brain_prod import hybrid_brain_prod  # The Specialist Tools
from .conversation_memory import ConversationMemory, CrossSessionIntelligence
from .lead_scoring import score_lead, LeadTemperature, BehaviorSignal
from .wolf_checklist import validate_checklist, WolfChecklistResult
from .verifier_agent import verifier_agent
from .suggestion_engine import generate_suggestions_from_turn
from .proactive_insights import proactive_engine

# V2 Enhancement Imports
from .social_proof_engine import social_proof_engine, community_sell_engine
from .fear_clock import fear_clock


# Database
from app.database import AsyncSessionLocal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_search import search_properties as db_search_properties
from app.services.cache import cache
from app.models import UserMemory

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# V2: COMMITMENT LADDER (Micro-Commitment Funnel)
# Each step earns commitment points — enables early close detection
# ═══════════════════════════════════════════════════════════════════════
COMMITMENT_LADDER = {
    "shared_budget": 10,       # User told us their budget
    "shared_area": 10,         # User specified an area
    "shared_purpose": 10,      # Investment vs living
    "asked_about_specific": 15, # Asked about a specific property/compound  
    "asked_payment_plan": 15,  # Asked about installments/financing
    "asked_developer": 10,     # Inquired about developer reputation
    "liked_property": 20,      # Expressed liking for a property
    "asked_visit": 25,         # Asked about site visit / viewing
    "asked_legal": 10,         # Asked about contract/legal (engaged)
    "asked_booking": 30,       # Asked about booking/reservation
    "shared_timeline": 10,     # Told us when they want to buy
    "returned_session": 15,    # Came back for another session
}


# ═══════════════════════════════════════════════════════════════════════
# V2: CLOSING SEQUENCE TRIGGERS
# Activate when commitment >= threshold
# ═══════════════════════════════════════════════════════════════════════
CLOSING_THRESHOLDS = {
    "soft_close": 50,    # Hint at booking, test readiness
    "medium_close": 70,  # Present booking as natural next step
    "hard_close": 85,    # Direct ask to reserve/pay
}


# ═══════════════════════════════════════════════════════════════════════
# V2: FAMILY COMMITTEE MODE TRIGGERS
# Egyptian market: 60%+ of buying decisions involve family consultation
# ═══════════════════════════════════════════════════════════════════════
FAMILY_CONSULT_TRIGGERS = [
    "أشاور", "أسأل", "مراتي", "زوجتي", "أبويا", "والدي", "أخويا",
    "wife", "husband", "father", "mother", "brother", "family",
    "العيلة", "العائلة", "أهلي", "خطيبتي", "خطيبي",
    "هسأل", "لازم أشاور", "need to ask", "consult",
]


def _calculate_commitment_from_memory(memory: ConversationMemory, intent: Intent) -> int:
    """Calculate commitment score from memory state and current intent.
    
    NOTE: Uses SET semantics — computes from scratch each turn, not accumulative.
    This prevents commitment from saturating to 100 within 2-3 turns.
    """
    score = 0  # Start from zero each turn — compute from current memory state
    
    if memory.budget_range:
        score += COMMITMENT_LADDER["shared_budget"]
    if memory.preferred_areas:
        score += COMMITMENT_LADDER["shared_area"]
    if memory.investment_vs_living:
        score += COMMITMENT_LADDER["shared_purpose"]
    if memory.timeline:
        score += COMMITMENT_LADDER["shared_timeline"]
    if memory.visit_scheduled:
        score += COMMITMENT_LADDER["asked_visit"]
    if memory.liked_properties:
        score += COMMITMENT_LADDER["liked_property"]
    if memory.preferred_payment:
        score += COMMITMENT_LADDER["asked_payment_plan"]
    if memory.session_count > 1:
        score += COMMITMENT_LADDER["returned_session"]

    # Intent-based boosts
    bucket = intent.intent_bucket if hasattr(intent, 'intent_bucket') else ""
    if bucket == "closing_intent":
        score += COMMITMENT_LADDER["asked_booking"]
    elif bucket == "installment_inquiry":
        score += COMMITMENT_LADDER["asked_payment_plan"]
    elif bucket == "developer_inquiry":
        score += COMMITMENT_LADDER["asked_developer"]
    elif bucket == "legal_inquiry":
        score += COMMITMENT_LADDER["asked_legal"]

    return min(score, 100)


def _predict_objections(psychology: PsychologyProfile, memory, intent, properties: list) -> list:
    """
    V3: Objection Pre-Emption Engine.
    Predicts top 2 likely objections based on psychology + persona + stage + properties.
    Returns counter-arguments for Claude to weave in naturally BEFORE the user asks.
    """
    predictions = []
    state = psychology.primary_state
    persona = getattr(psychology, 'buyer_persona', None)
    stage = getattr(psychology, 'decision_stage', None)
    already_resolved = set(memory.objections_resolved.keys()) if memory and hasattr(memory, 'objections_resolved') else set()

    # Prediction rules (order = priority)
    _PREDICTIONS = [
        {
            "type": "delivery_risk",
            "triggers": lambda: (state in (PsychologicalState.RISK_AVERSE, PsychologicalState.DELIVERY_FEAR, PsychologicalState.FAMILY_SECURITY)
                                 or (persona and persona.value == "first_timer")),
            "counter_ar": "المطور ده تسليمه 95%+ في الوقت — وعندنا Law 114 بيحمي فلوسك لو حصل أي تأخير.",
            "counter_en": "This developer has 95%+ on-time delivery — and our Law 114 Scanner protects your money against delays.",
        },
        {
            "type": "price_will_drop",
            "triggers": lambda: state in (PsychologicalState.MACRO_SKEPTIC, PsychologicalState.SKEPTICISM, PsychologicalState.ANALYSIS_PARALYSIS),
            "counter_ar": "الأسعار مش هتنزل — تكلفة البناء النهاردة أعلى من سعر البيع. الـ downside risk شبه صفر.",
            "counter_en": "Prices won't drop — today's construction cost exceeds selling price. Downside risk is near zero.",
        },
        {
            "type": "installment_burden",
            "triggers": lambda: (state == PsychologicalState.INSTALLMENT_ANXIETY
                                 or (memory and memory.budget_range and memory.budget_range.get('max', 0) < 5_000_000)),
            "counter_ar": "القسط الشهري أقل من إيجار شقة في نفس المنطقة — ومع التضخم القسط بيخف مع الوقت.",
            "counter_en": "Monthly installment is less than rent in the same area — and inflation makes installments lighter over time.",
        },
        {
            "type": "legal_safety",
            "triggers": lambda: state in (PsychologicalState.LEGAL_ANXIETY, PsychologicalState.TRUST_DEFICIT),
            "counter_ar": "كل وحدة بنعرضها بتعدي على Law 114 Scanner — لو الورق مش نضيف بنستبعدها قبل ما توصلك.",
            "counter_en": "Every unit we show passes our Law 114 Scanner — if papers aren't clean, we filter it out before it reaches you.",
        },
        {
            "type": "wrong_timing",
            "triggers": lambda: stage and stage.value in ("awareness", "research"),
            "counter_ar": "أنا مش بقولك اشتري دلوقتي — بس الأرقام بتقول إن كل شهر تأخير بيكلفك فلوس حقيقية.",
            "counter_en": "I'm not saying buy now — but the numbers show every month of delay costs real money.",
        },
        {
            "type": "remote_trust",
            "triggers": lambda: state == PsychologicalState.EXPATRIATE_ANXIETY,
            "counter_ar": "كل حاجة ممكن تتعمل عن بُعد — من المعاينة الفيديو للتوكيل الرسمي. عملنا كده مع عملاء كتير في الخليج.",
            "counter_en": "Everything can be done remotely — from video viewing to legal proxy. We've done this with many Gulf-based clients.",
        },
    ]

    for pred in _PREDICTIONS:
        if pred["type"] in already_resolved:
            continue
        try:
            if pred["triggers"]():
                predictions.append(pred)
                if len(predictions) >= 2:
                    break
        except Exception:
            continue

    return predictions


def _get_response_length_instruction(psychology: PsychologyProfile, memory: ConversationMemory) -> str:
    """
    V2: Emotion-Aware Response Length Calibration.
    
    Returns instruction for Claude to calibrate response length based on
    user's emotional state and engagement level.
    """
    state = psychology.primary_state
    intensity = getattr(psychology, 'emotional_intensity', 0.5)
    stage = getattr(psychology, 'decision_stage', DecisionStage.AWARENESS)
    turn_count = len(memory.shown_properties) + len(memory.liked_properties)

    # Short responses (2-4 sentences)
    if state == PsychologicalState.IMPULSE_BUYER:
        return "\n[RESPONSE_LENGTH: SHORT (2-4 sentences). User is ready to act. Skip explanations, give action steps only.]"
    if stage == DecisionStage.ACTION:
        return "\n[RESPONSE_LENGTH: SHORT (2-4 sentences). Closing stage. Booking info only. No new data.]"

    # Medium responses (4-8 sentences)
    if state in (PsychologicalState.FOMO, PsychologicalState.GREED_DRIVEN):
        return "\n[RESPONSE_LENGTH: MEDIUM (4-8 sentences). User is engaged. Give key numbers + one closing push.]"
    if stage == DecisionStage.DECISION:
        return "\n[RESPONSE_LENGTH: MEDIUM (4-8 sentences). Decision stage. Clear recommendation + supporting data.]"

    # Long responses (8-15 sentences) — for education and trust building
    if state in (PsychologicalState.ANALYSIS_PARALYSIS, PsychologicalState.MACRO_SKEPTIC, PsychologicalState.RISK_AVERSE):
        return "\n[RESPONSE_LENGTH: LONG (8-15 sentences). User needs education/reassurance. Provide thorough data-backed analysis.]"
    if stage in (DecisionStage.AWARENESS, DecisionStage.RESEARCH):
        return "\n[RESPONSE_LENGTH: LONG (8-12 sentences). Early stage. Educate with market data, area comparison, developer info.]"

    # Default: medium
    return "\n[RESPONSE_LENGTH: MEDIUM (5-8 sentences). Balanced response.]"


def _get_closing_sequence_context(commitment_level: int, language: str = "ar") -> str:
    """
    V2: Intelligent Closing Sequence injection.
    Returns context for Claude based on commitment level.
    """
    if commitment_level >= CLOSING_THRESHOLDS["hard_close"]:
        if language == "ar":
            return """
[🔴 CLOSING SEQUENCE: HARD CLOSE]
Commitment level is HIGH (85%+). The user is ready.
MANDATORY: End your response with a direct booking call-to-action:
- "خلينا نحجز الوحدة دي دلوقتي. محتاج بس [المقدم] وأنا هتابع معاك كل الورق."
- "أنا شايف إنك جاهز. الخطوة الجاية: حجز مبدئي بمبلغ [X] جنيه. أبعتلك اللينك؟"
DO NOT introduce new options. Focus on closing the current interest.
"""
        else:
            return """
[🔴 CLOSING SEQUENCE: HARD CLOSE]
Commitment level is HIGH (85%+). The user is ready.
MANDATORY: End with a direct booking CTA:
- "Let's reserve this unit now. You just need [down payment] and I'll handle all the paperwork."
- "You seem ready. Next step: initial reservation of [X] EGP. Shall I send you the link?"
DO NOT introduce new options. Close the current interest.
"""
    elif commitment_level >= CLOSING_THRESHOLDS["medium_close"]:
        if language == "ar":
            return """
[🟡 CLOSING SEQUENCE: MEDIUM CLOSE]
Commitment level is HIGH (70%+). Test their readiness.
- Mention booking as a natural next step, not as pressure
- "لو عجبتك الوحدة دي، نقدر نعمل حجز مبدئي من غير التزام."
- "حابب نرتب معاينة؟ دي أفضل طريقة تاخد قرارك."
"""
        else:
            return """
[🟡 CLOSING SEQUENCE: MEDIUM CLOSE]
Commitment level is HIGH (70%+). Test readiness.
- Frame booking as natural next step
- "If you like this unit, we can do a preliminary reservation with no obligation."
- "Would you like to schedule a viewing? That's the best way to decide."
"""
    elif commitment_level >= CLOSING_THRESHOLDS["soft_close"]:
        if language == "ar":
            return """
[🟢 CLOSING SEQUENCE: SOFT CLOSE]
Commitment level is MODERATE (50%+). Plant the seed.
- Hint at scarcity: "الوحدات دي بتخلص بسرعة"
- Suggest a timeline: "لو قررت الأسبوع ده، هتلحق السعر الحالي"
"""
        else:
            return """
[🟢 CLOSING SEQUENCE: SOFT CLOSE]
Commitment level is MODERATE (50%+). Plant the seed.
- Hint at scarcity: "Units like this sell quickly"
- Suggest timeline: "Deciding this week locks in the current price"
"""
    return ""


def _get_family_committee_context(query: str, memory: ConversationMemory, language: str = "ar") -> str:
    """
    V2: Family Committee Mode.
    When user mentions family consultation, adapt strategy to address
    the invisible decision-makers.
    """
    query_lower = query.lower()
    is_family_consult = any(trigger in query_lower for trigger in FAMILY_CONSULT_TRIGGERS)
    has_family_members = bool(memory.family_members_mentioned)

    if not is_family_consult and not has_family_members:
        return ""

    members = memory.family_members_mentioned or ["family"]
    members_str = ", ".join(members)

    if language == "ar":
        return f"""
[👨‍👩‍👧‍👦 FAMILY COMMITTEE MODE ACTIVATED]
The user is consulting with: {members_str}

CRITICAL PIVOT: You are no longer selling to ONE person. You are selling to a COMMITTEE.

RULES:
1. Acknowledge the family role: "ده قرار كبير وطبيعي تشاور العيلة."
2. Arm the user with SHAREABLE DATA they can present to family:
   - Summary with key numbers (price, ROI, payment plan)
   - "ممكن أبعتلك ملخص تشاركه مع [المرات/والدك]؟"
3. Address the invisible objectors:
   - Father/Father-in-law: Trust + Legal safety → "الورق سليم 100%"
   - Wife: Lifestyle + Community → "الكمباوند فيه مدارس ونادي"
   - Brother: ROI + Market data → "العائد 7% + نمو 30%"
4. Offer a family viewing: "تحبوا تنزلوا كلكم مع بعض؟ أحجزلكم معاينة."
5. Set a follow-up timeline: "خد وقتك. نتكلم بكرة بعد ما تشاوروا؟"
"""
    else:
        return f"""
[👨‍👩‍👧‍👦 FAMILY COMMITTEE MODE ACTIVATED]
The user is consulting with: {members_str}

CRITICAL PIVOT: You are selling to a COMMITTEE, not one person.

RULES:
1. Validate: "This is a big decision. It's smart to involve the family."
2. Provide shareable data: summary with prices, ROI, payment plan.
3. Address invisible objectors:
   - Father: Legal safety, developer reputation
   - Wife/Partner: Lifestyle, community, schools
   - Sibling: ROI, market data, growth
4. Offer family viewing: "Would everyone like to visit together?"
5. Set follow-up: "Take your time. Let's reconnect after you discuss."
"""


class WolfBrain:
    """
    The Wolf of Osool - Unified Hybrid Intelligence Engine.
    
    Combines GPT-4o (Speed), Claude 3.5 Sonnet (Nuance), and 
    XGBoost/Python (Precision) into a deal-closing machine.
    """
    
    def __init__(self):
        """Initialize all AI clients and components."""
        self.anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Memory store (session_id -> ConversationMemory)
        self._memory_store: Dict[str, ConversationMemory] = {}
        
        # Stats tracking
        self.stats = {
            "turns_processed": 0,
            "claude_calls": 0,
            "gpt_calls": 0,
            "searches": 0,
            "errors": 0,
        }
        
        logger.info("🐺 Wolf Brain initialized (Reloaded for Protocol 6)")
    
    async def process_turn(
        self,
        query: str,
        history: List[Dict],
        profile: Optional[Dict] = None,
        language: str = "auto",
        session_id: Optional[str] = None,
        streaming: bool = False,
    ) -> Dict[str, Any]:
        """
        The Main Thinking Loop - Wrapper for Session Management.
        When streaming=True, returns _stream_context for real SSE streaming.
        """
        async with AsyncSessionLocal() as session:
            return await self._process_turn_logic(
                query=query,
                history=history,
                session=session,
                profile=profile,
                language=language,
                session_id=session_id,
                streaming=streaming,
            )

    async def _process_turn_logic(
        self,
        query: str,
        history: List[Dict],
        session: AsyncSession,
        profile: Optional[Dict] = None,
        language: str = "auto",
        session_id: Optional[str] = None,
        streaming: bool = False,
    ) -> Dict[str, Any]:
        """
        The Core Thinking Loop.
        """
        start_time = datetime.now()
        
        # === CRITICAL DEBUG (Remove after fixing session issue) ===
        logger.info(f"🐺 WOLF BRAIN START: session={session_id}, history_len={len(history)}, query={query[:50]}...")
        self.stats["turns_processed"] += 1
        
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 0: LANGUAGE DETECTION (Strict)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Detect language from query content, overriding the passed hint
            detected_lang = self._detect_user_language(query)
            if detected_lang != "auto":
                language = detected_lang
            else:
                # Fallback to passed language or default to Arabic (primary market)
                language = language if language != "auto" else "ar"
            
            logger.info(f"🗣️ Language: {language} (detected from: '{query[:20]}...')")
            
            # Initialize Market Analytics Layer (Session Scope)
            market_layer = MarketAnalyticsLayer(session)
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 1: FAST ROUTE (Regex Gate - 0ms Latency)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Check for price asks without context EARLY to save tokens & time
            if self._needs_screening(query, history):
                 logger.info("🛡️ FAST GATE: Intercepted vague price query")
                 return self._get_screening_script(language)

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 2: PARALLEL COGNITION (The Brain - Speed Upgrade)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Run Intent (LLM), Psychology (Regex), and Lead Scoring (Logic) in parallel
            
            # wrapper for async psychology
            async def run_psychology():
                # We pass None for intent initially to run in parallel
                return analyze_psychology(query, history, None)

            # wrapper for async lead scoring
            async def run_scoring():
                session_meta = {
                    "session_start_time": datetime.now(), 
                    "properties_viewed": len(history) // 3,
                    "tools_used": []
                }
                # Lead scoring is fast, but wrapping ensures it doesn't block if we add complexity
                return score_lead(history + [{"role": "user", "content": query}], session_meta, profile)

            # Launch tasks
            perception_task = asyncio.create_task(perception_layer.analyze(query, history))
            psychology_task = asyncio.create_task(run_psychology())
            lead_score_task = asyncio.create_task(run_scoring())
            
            # Routing (can also run parallel, but fast enough to run here or inside perception?)
            # Let's keep routing separate or assume perception handles it. 
            # The original code had wolf_router. Let's run that too if needed, but the user plan omitted it.
            # I will keep wolf_router as a check for "General" queries if I want to maintain that path.
            # But for "Superhuman", we might want to process everything through the main flow unless typical FAQ.
            # Let's run router quickly first? No, user wants parallelism.
            # Actually, let's keep the Router check before parallel tasks if it's very fast, 
            # OR run it in parallel.
            # For now, I'll stick to the user's plan: 
            # Router -> Perception... 
            # The user's plan showed "Fast Route (Regex)" then "Parallel Perception".
            
            # Wait for all results
            intent, psychology, lead_data = await asyncio.gather(
                perception_task, 
                psychology_task, 
                lead_score_task
            )
            
            self.stats["gpt_calls"] += 1 # Perception used GPT
            logger.info(f"🎯 Intent: {intent.action}, Filters: {intent.filters}")
            logger.info(f"🧠 Psychology: {psychology.primary_state.value}")
            
            lead_score = lead_data["score"]
            logger.info(f"📊 Lead Score: {lead_score} ({lead_data['temperature']})")

            # Persist score
            if session_id:
                cache.set_lead_score(session_id, lead_score)

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # MEMORY: Hydrate from DB (cross-session) + history (current session)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 1. Load cross-session memory from DB (if user is logged in)
            user_id = profile.get("id") or profile.get("user_id") if profile else None
            db_memory = await self._load_user_memory(session, user_id) if user_id else None
            
            # 2. Build session memory from current conversation history
            memory = ConversationMemory()
            for msg in history:
                if msg.get("role") == "user":
                    memory.extract_from_message(msg.get("content", ""))
            # Extract from current query with AI-detected filters
            memory.extract_from_message(query, {"filters": intent.filters})
            
            # 3. Merge: DB memory fills gaps, current session wins on conflicts
            if db_memory:
                memory.merge(db_memory)
                logger.info("🧠 Cross-session memory loaded and merged")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: CROSS-SESSION INTELLIGENCE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            cross_session_context = None
            try:
                return_analysis = CrossSessionIntelligence.analyze_return_behavior(
                    last_session_time=memory.last_session_time,
                    previous_sessions_count=memory.session_count,
                )
                if return_analysis["return_type"] != "fresh_start":
                    cross_session_context = return_analysis
                    logger.info(f"🔄 Return type: {return_analysis['return_type']} ({return_analysis.get('hours_since', 0):.0f}h ago)")
            except Exception as e:
                logger.debug(f"Cross-session intelligence skipped: {e}")

            logger.info(f"🧠 Memory: {memory.to_dict()}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V2 ENHANCEMENT: EMOTIONAL TRACKING + COMMITMENT SCORING
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                turn_count = len([m for m in history if m.get("role") == "user"]) + 1
                memory.record_emotional_state(
                    turn_count,
                    psychology.primary_state.value,
                    psychology.emotional_intensity
                )
                commitment = _calculate_commitment_from_memory(memory, intent)
                memory.commitment_level = commitment  # SET semantics, not additive
                logger.info(f"💎 V2: Emotion recorded (turn {turn_count}), commitment={commitment}/100")
            except Exception as e:
                logger.debug(f"V2 emotional tracking skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: OBJECTION RESOLUTION TRACKER
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            objection_tracker = ObjectionResolutionTracker()
            try:
                # Load tracker from memory if exists
                if memory.objections_resolved:
                    prev_tracker_data = {
                        obj_type: {"raised_turn": 0, "trigger_text": "", "attempts": [],
                                   "resolved": resolved, "effective_tactic": None, "re_raised_count": 0}
                        for obj_type, resolved in memory.objections_resolved.items()
                    }
                    objection_tracker = ObjectionResolutionTracker.from_dict(prev_tracker_data)

                # Map current psychology state → objection type
                _STATE_TO_OBJECTION = {
                    PsychologicalState.RISK_AVERSE: "financial",
                    PsychologicalState.TRUST_DEFICIT: "trust",
                    PsychologicalState.SKEPTICISM: "market",
                    PsychologicalState.LEGAL_ANXIETY: "legal",
                    PsychologicalState.DELIVERY_FEAR: "trust",
                    PsychologicalState.INSTALLMENT_ANXIETY: "financial",
                    PsychologicalState.MACRO_SKEPTIC: "market",
                }

                state = psychology.primary_state
                turn_count_for_obj = len([m for m in history if m.get("role") == "user"]) + 1
                if state in _STATE_TO_OBJECTION:
                    obj_type = _STATE_TO_OBJECTION[state]
                    objection_tracker.raise_objection(obj_type, turn_count_for_obj, query[:100])
                    logger.info(f"🚨 Objection detected: {obj_type} (state={state.value})")

                # Check for resolved objections (state shifted away from previous objection)
                for prev_obj in objection_tracker.get_unresolved():
                    inverse_states = [s for s, o in _STATE_TO_OBJECTION.items() if o == prev_obj]
                    if state not in inverse_states:
                        objection_tracker.resolve_objection(prev_obj, f"state_shift_to_{state.value}")
                        memory.objections_resolved[prev_obj] = True
                        logger.info(f"✅ Objection resolved: {prev_obj}")
            except Exception as e:
                logger.debug(f"V3 objection tracker skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 3: LOGIC GATES (Loop Detection & Feasibility)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Pre-initialize card_readiness (computed fully in Step 4A.2 below)
            card_readiness = {"readiness_score": 0, "recommendation": "pending"}

            # HUMAN HANDOFF CHECK
            if "loop_detected" in lead_data.get("signals", []):
                return {
                    "response": "لقد لاحظت تكرار الأسئلة، وهذا يتطلب تدخلاً من خبير بشري لتحليل الوضع بدقة.\n\n"
                                "سأقوم بتحويلك الآن لمستشار أول (Senior Consultant) لمراجعة حالتك.\n"
                                "تم فتح تذكرة #URGENT-882.",
                    "properties": [],
                    "ui_actions": [{"type": "handoff_alert", "priority": "high"}],
                    "psychology": psychology.to_dict(),
                    "handoff": True,
                    "suggestions": ["تواصل مع مستشار", "ابدأ محادثة جديدة", "عرض ملخص المحادثة"],
                    "detected_language": "ar",
                    "lead_score": lead_score,
                    "card_readiness": card_readiness,
                    "intent": intent.intent if hasattr(intent, 'intent') else "handoff"
                }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4: CONFIDENCE CHECK (The "No-Sell" Zone)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if psychology.primary_state == PsychologicalState.TRUST_DEFICIT:
                logger.info("🛑 TRUST DEFICIT: Halting sales to run Law 114 Scan")
                
                if language == "ar":
                    resp = (
                        "أنا حاسس إنك قلقان من وضع السوق، وعندك حق. مشاريع كتير بتتأخر في التسليم.\n\n"
                        "عشان كدة أنا مش هرشحلك أي حاجة دلوقتي.\n"
                        "أنا هشغل **فحص قانوني (Law 114)** على أي مطور بتفكر فيه عشان نضمن تسلسل الملكية.\n\n"
                        "قولي، مين المطور اللي قلقان منه؟"
                    )
                else:
                    resp = (
                        "I sense you are worried about the market risks, and you are right. "
                        "Many projects are delayed. Forget about buying for a moment.\n\n"
                        "I want to run a **Legal Scan** on any developer you are considering. "
                        "I use a Law 114 Checklist to ensure ownership chains are clean. "
                        "What developer are you worried about?"
                    )

                trust_suggestions_ar = ["اسم المطور؟", "عايز أعرف عن مشروع معين", "إيه أكتر حاجة قلقانك؟"]
                trust_suggestions_en = ["Which developer?", "Tell me about a project", "What worries you most?"]
                return {
                    "response": resp,
                    "ui_actions": [{
                        "type": "law_114_guardian",
                        "status": "active"
                    }],
                    "strategy": {"strategy": "confidence_building", "route": "legal"},
                    "psychology": psychology.to_dict(),
                    "suggestions": trust_suggestions_ar if language == "ar" else trust_suggestions_en,
                    "detected_language": language,
                    "lead_score": lead_score,
                    "card_readiness": card_readiness,
                    "intent": intent.intent if hasattr(intent, 'intent') else "trust_building"
                }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4: DISCOVERY CHECK
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            is_discovery_complete = self._is_discovery_complete(intent.filters, history, query)

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4A: ANALYTICS ENRICHMENT (Always-On Market Intelligence)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            analytics_context = await self._build_analytics_context(intent, session, market_layer)
            if analytics_context.get("has_analytics"):
                logger.info(f"📊 ANALYTICS ENRICHMENT: Built context for {analytics_context.get('location', 'N/A')}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4A.1: CHAIN-OF-THOUGHT REASONING (V3)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            reasoning_chain: Optional[ReasoningChain] = None
            try:
                location = intent.filters.get('location', '')
                budget = intent.filters.get('max_price') or intent.filters.get('budget', 0)
                property_type = intent.filters.get('property_type', '')

                if location and analytics_context.get("has_analytics"):
                    # Full investment analysis when we have location + analytics
                    reasoning_chain = reasoning_engine.analyze_investment_opportunity(
                        location=location,
                        budget=int(budget) if budget else 5_000_000,
                        property_type=property_type or "apartment",
                        analytics_context=analytics_context,
                        market_data=None,
                    )
                    logger.info(f"🧠 CoT: {len(reasoning_chain.steps)} steps, conf={reasoning_chain.total_confidence:.0%}, verdict={reasoning_chain.final_verdict}")
                else:
                    # Dynamic reasoning based on query type
                    reasoning_chain = reasoning_engine.reason_about_query(
                        query=query,
                        intent=intent.to_dict() if hasattr(intent, 'to_dict') else {"action": intent.action, "filters": intent.filters},
                        psychology=psychology.to_dict(),
                        analytics_context=analytics_context,
                        history=history,
                    )
                    if reasoning_chain and reasoning_chain.steps:
                        logger.info(f"🧠 CoT (dynamic): {len(reasoning_chain.steps)} steps, verdict={reasoning_chain.final_verdict}")
            except Exception as e:
                logger.warning(f"⚠️ Reasoning engine error (non-fatal): {e}")
                reasoning_chain = None

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4A.2: CARD READINESS SCORE (Psychology-Driven)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            from .psychology_layer import calculate_card_readiness
            card_readiness = calculate_card_readiness(psychology, history, memory, lead_score)
            logger.info(f"🎯 Card Readiness: score={card_readiness['readiness_score']}, rec={card_readiness['recommendation']}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4B: DEEP ANALYSIS TRIGGER (Market Context Queries)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # If user asks "How is the market in X?" without wanting to search,
            # trigger analytical_engine.get_area_context() to show benchmark data
            market_context_keywords = [
                "السوق", "متوسط", "أسعار", "market", "average", "prices", 
                "benchmark", "ماشي ازاي", "الأسعار", "سعر المتر", "كام المتر"
            ]
            
            is_market_context_query = (
                intent.action == "general" and 
                intent.filters.get("location") and
                any(kw in query.lower() for kw in market_context_keywords)
            )
            
            if is_market_context_query:
                location = intent.filters.get("location")
                logger.info(f"📊 DEEP ANALYSIS: Triggered for market context query about {location}")
                
                # Get comprehensive area context from analytical engine (unified truth)
                area_context = market_intelligence.get_area_context(location)
                market_segment = market_intelligence.get_market_segment(location)
                
                if area_context.get("found"):
                    avg_price_sqm = area_context.get("avg_price_sqm", 50000)
                    growth_rate = area_context.get("growth_rate", 0.12)
                    rental_yield = area_context.get("rental_yield", 0.065)
                    
                    if language == "ar":
                        resp = (
                            f"📊 **تحليل السوق في {area_context.get('ar_name', location)}:**\n\n"
                            f"• **متوسط سعر المتر:** {avg_price_sqm:,} جنيه/متر\n"
                            f"• **نمو سنوي:** {int(growth_rate * 100)}%\n"
                            f"• **عائد إيجاري:** {rental_yield * 100:.1f}%\n\n"
                        )
                        
                        if market_segment.get("found"):
                            class_a = market_segment.get("class_a", {})
                            class_b = market_segment.get("class_b", {})
                            resp += (
                                f"**تقسيم السوق:**\n"
                                f"🏆 **الفئة الأولى:** {class_a.get('price_range_ar', 'غير محدد')}\n"
                                f"⭐ **الفئة الثانية:** {class_b.get('price_range_ar', 'غير محدد')}\n\n"
                                "لو عايز تشوف وحدات معينة، قولي ميزانيتك وأنا أرشحلك الأنسب."
                            )
                    else:
                        resp = (
                            f"📊 **Market Analysis for {location}:**\n\n"
                            f"• **Avg Price/sqm:** {avg_price_sqm:,} EGP\n"
                            f"• **Annual Growth:** {int(growth_rate * 100)}%\n"
                            f"• **Rental Yield:** {rental_yield * 100:.1f}%\n\n"
                        )
                        
                        if market_segment.get("found"):
                            class_a = market_segment.get("class_a", {})
                            class_b = market_segment.get("class_b", {})
                            resp += (
                                f"**Market Tiers:**\n"
                                f"🏆 **Tier 1 (Premium):** {class_a.get('price_range_en', 'N/A')}\n"
                                f"⭐ **Tier 2 (Value):** {class_b.get('price_range_en', 'N/A')}\n\n"
                                "If you'd like to see specific units, let me know your budget."
                            )
                    
                    market_suggestions_ar = ["عايز أشوف وحدات", "إيه أحسن مطور هناك؟", "قارن مع مناطق تانية"]
                    market_suggestions_en = ["Show me units", "Best developer there?", "Compare with other areas"]
                    return {
                        "response": resp,
                        "properties": [],
                        "ui_actions": [{
                            "type": "market_benchmark",
                            "priority": "high",
                            "title": f"📊 أسعار السوق في {area_context.get('ar_name', location)}",
                            "title_en": f"📊 Market Prices in {location}",
                            "data": {
                                "market_segment": market_segment,
                                "area_context": area_context,
                                "avg_price_sqm": avg_price_sqm,
                                "rental_yield": rental_yield,
                                "growth_rate": growth_rate,
                            }
                        }],
                        "strategy": {"strategy": "market_education", "area": location},
                        "psychology": psychology.to_dict(),
                        "suggestions": market_suggestions_ar if language == "ar" else market_suggestions_en,
                        "detected_language": language,
                        "lead_score": lead_score,
                        "card_readiness": card_readiness,
                        "analytics_context": analytics_context,
                        "intent": intent.intent if hasattr(intent, 'intent') else "market_education"
                    }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 5: INTELLIGENT SCREENING (The "Give-to-Get" Protocol)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # If user wants price/search but we don't know their budget/purpose yet
            # CRITICAL FIX: Don't show this if user ALREADY stated Purpose (e.g. "Sakan A'eli" -> Living)
            p_val = intent.filters.get("purpose") or intent.filters.get("intended_use") or ""
            has_explicit_purpose = str(p_val).lower() in ["living", "investment"]
            
            if intent.action in ["search", "price_check"] and not is_discovery_complete and not has_explicit_purpose:
                
                # 1. Identify the Area they asked about
                # FIX: Do NOT default to New Cairo. If unknown, skip.
                location = intent.filters.get('location')
                
                # 2. Get Market Intelligence safely (The "Value" we give)
                market_segment = {}
                if location:
                    market_segment = market_intelligence.get_market_segment(location)
                
                if market_segment.get("found"):
                    logger.info(f"🧱 GIVE-TO-GET: Screening user for {location}")
                    
                    if language == "ar":
                        # UPDATED PROFESSIONAL SCRIPT (Markt Insider)
                        resp = (
                            f"قبل ما ندخل في تفاصيل الأسعار، خليني أوضحلك 'خريطة السوق' الحقيقية في {market_segment.get('name_ar', location)} عشان تضمن إنك بتشتري بالقيمة العادلة.\n\n"
                            f"البيانات بتقول إن المنطقة دي فيها مستويين:\n\n"
                            f"🏆 **المستوى الأول (Premium)**: متوسط {market_segment['class_a']['min_price']/1000000:.1f} مليون (مطورين زي {', '.join(market_segment['class_a']['developers_ar'][:2])}).\n"
                            f"⭐ **المستوى الثاني (Value)**: فرص بتبدأ من {market_segment['class_b']['min_price']/1000000:.1f} مليون.\n\n"
                            "عشان أوجهك للفرصة الأنسب: **هل هدفك الأساسي تعظيم العائد (ROI) ولا السكن الفاخر؟**"
                        )
                    else:
                        # Improved English Script
                        resp = (
                            f"Before we dive into prices, let me clarify the 'Market Map' in {location} to ensure you get fair value.\n\n"
                            f"The data shows two distinct tiers here:\n"
                            f"🏆 **Tier 1 (Premium):** Avg {market_segment['class_a']['min_price']/1000000:.1f}M (Developers like {market_segment['class_a']['developers'][0]}).\n"
                            f"⭐ **Tier 2 (Value):** Opportunities starting from {market_segment['class_b']['min_price']/1000000:.1f}M.\n\n"
                            "To guide you correctly: **Is your primary goal High ROI or Luxury Living?**"
                        )

                    # Generate screening suggestions in correct language
                    if language == "ar":
                        gate_suggestions = [
                            "عايز أستثمر مش أسكن",
                            "أنا بدور على سكن عائلي",
                            f"ميزانيتي حوالي {market_segment['class_b']['min_price']/1000000:.0f} مليون جنيه",
                        ]
                    else:
                        gate_suggestions = [
                            "I want to invest, not live",
                            "I'm looking for a family home",
                            f"My budget is around {market_segment['class_b']['min_price']/1000000:.0f}M EGP",
                        ]
                    return {
                        "response": resp,
                        "properties": [],
                        "ui_actions": [{"type": "market_trend_chart", "data": market_segment}],
                        "strategy": {"strategy": "screening_gate", "market_segment": market_segment},
                        "psychology": psychology.to_dict(),
                        "suggestions": gate_suggestions,
                        "detected_language": language,
                        "lead_score": lead_score,
                        "card_readiness": card_readiness,
                        "showing_strategy": "ANALYTICS_ONLY",
                        "analytics_context": None,
                        "intent": intent.to_dict(),
                    }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 5B: FEASIBILITY SCREENING (Budget Negotiation)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # If user has budget + location + property_type, check if request is realistic
            # Handles "Villa in Zayed for 5M" → "5M won't get a villa, but here's a townhouse"
            feasibility_location = intent.filters.get('location', '')
            feasibility_type = intent.filters.get('property_type', '')
            feasibility_budget = intent.filters.get('budget_max', 0)
            
            if feasibility_location and feasibility_type and feasibility_budget and feasibility_budget > 0:
                feasibility_result = market_intelligence.screen_feasibility(
                    location=feasibility_location,
                    property_type=feasibility_type,
                    budget=feasibility_budget
                )
                if not feasibility_result.is_feasible:
                    logger.info(f"🛑 FEASIBILITY: {feasibility_type} in {feasibility_location} for {feasibility_budget/1e6:.1f}M is NOT feasible")
                    # Don't block — inject the feasibility message and still search with alternatives
                    feasibility_msg = feasibility_result.message_ar if language == 'ar' else feasibility_result.message_en
                    alternatives = feasibility_result.alternatives
                    
                    # Build negotiation response
                    alt_text = ""
                    if alternatives:
                        if language == 'ar':
                            alt_text = "\n\nبس أنا لقيتلك بدائل ممتازة:\n"
                            for alt in alternatives[:3]:
                                alt_text += f"• **{alt.get('type_ar', alt.get('type', ''))}** في {alt.get('location_ar', alt.get('location', ''))} — من {alt.get('min_price', 0)/1e6:.1f} مليون\n"
                        else:
                            alt_text = "\n\nBut I found excellent alternatives:\n"
                            for alt in alternatives[:3]:
                                alt_text += f"• **{alt.get('type', '')}** in {alt.get('location', '')} — from {alt.get('min_price', 0)/1e6:.1f}M\n"
                    
                    feasibility_suggestions_ar = ["عايز أشوف البدائل", "ممكن أزود الميزانية", "منطقة تانية أرخص؟"]
                    feasibility_suggestions_en = ["Show alternatives", "I can increase budget", "Cheaper area?"]
                    return {
                        "response": feasibility_msg + alt_text,
                        "properties": [],
                        "ui_actions": [{"type": "feasibility_alert", "priority": "high", "data": feasibility_result.to_dict()}],
                        "strategy": {"strategy": "budget_negotiation", "feasibility": feasibility_result.to_dict()},
                        "psychology": psychology.to_dict(),
                        "suggestions": feasibility_suggestions_ar if language == "ar" else feasibility_suggestions_en,
                        "detected_language": language,
                        "lead_score": lead_score,
                        "card_readiness": card_readiness,
                        "intent": intent.intent if hasattr(intent, 'intent') else "feasibility"
                    }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 6: THE SMART HUNT (Agentic Search with Reflexion)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            properties = []
            scored_properties = []
            hunt_strategy = "none"
            pivot_message = None
            
            # Determine "Smart Display" Strategy (Psychology-Driven Card Gate v4 — Readiness-First)
            showing_strategy = self._psychology_card_gate(intent, psychology, is_discovery_complete, lead_score=lead_score, memory=memory, history=history, card_readiness=card_readiness)

            # ── OVERRIDE: Explicit price-range query → always show properties ──
            # When user says "I want from 3M to 5M" or "عايز من 3 ل 5 مليون"
            has_budget_range = bool(
                intent.filters.get('budget_max') or intent.filters.get('budget_min')
                or intent.filters.get('max_price') or intent.filters.get('min_price')
            )
            has_location = bool(intent.filters.get('location'))
            is_search_intent = intent.action in ['search', 'price_check']

            # Budget-range override — respects readiness ceiling.
            # Having a budget does NOT auto-show cards; psychology must agree.
            engagement_turns = len([m for m in history if m.get('role') == 'user'])
            cr_score = card_readiness.get("readiness_score", 0) if card_readiness else 0
            if has_budget_range and showing_strategy in ['NONE', 'ANALYTICS_ONLY']:
                if engagement_turns >= 4 and cr_score >= 45:
                    showing_strategy = 'FULL_LIST'
                    logger.info(f"🔓 Budget override → FULL_LIST (depth={engagement_turns}, readiness={cr_score})")
                elif engagement_turns >= 3 and cr_score >= 20:
                    showing_strategy = 'TEASER'
                    logger.info(f"🔓 Budget override → TEASER (depth={engagement_turns}, readiness={cr_score})")
                else:
                    showing_strategy = 'ANALYTICS_ONLY'
                    logger.info(f"📊 Budget present but gated: ANALYTICS_ONLY (depth={engagement_turns}, readiness={cr_score})")

            # Safety net: readiness < 20 → always cap at ANALYTICS_ONLY
            if card_readiness and card_readiness.get("readiness_score", 0) < 20 and showing_strategy in ['TEASER', 'FULL_LIST']:
                showing_strategy = 'ANALYTICS_ONLY'
                logger.info(f"🛡️ Psychology safety net: readiness={card_readiness.get('readiness_score', 0)}, forced ANALYTICS_ONLY")
            logger.info(f"👁️ Visual Strategy: {showing_strategy} (readiness={card_readiness.get('readiness_score', 0) if card_readiness else 0})")

            # Only search if strategy is TEASER or FULL_LIST
            if showing_strategy in ['TEASER', 'FULL_LIST']:
                # Use SMART HUNT with Reflexion (auto-pivot on failure)
                properties, hunt_strategy, pivot_message = await self._smart_hunt(
                    intent, session, language
                )
                self.stats["searches"] += 1
                
                # If TEASER mode, only keep the "Median" property to anchor expectations
                if showing_strategy == 'TEASER' and properties:
                    # Sort by price and pick the middle one (the "anchor")
                    properties.sort(key=lambda x: x.get('price', 0))
                    mid_index = len(properties) // 2
                    properties = [properties[mid_index]]  # Keep only one anchor property
                    logger.info(f"🎯 TEASER: Showing 1 anchor property at index {mid_index}")
            
            logger.info(f"🎯 Hunt Strategy: {hunt_strategy}, Pivot: {pivot_message is not None}")
        
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 7: BENCHMARKING & SCORING (Async with DB)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Pass session for real-time benchmarking
            if properties:
                scored_properties = await analytical_engine.score_properties(properties, session=session)
            
            # 7b. Fetch Dynamic Economic Data (Inflation, Bank Rates)
            market_economic_data = await analytical_engine.get_live_market_data(session)

            # Augment with Wolf Analysis
            for prop in scored_properties:
                # Pass dynamic market data for accurate/live ROI
                roi = analytical_engine.calculate_true_roi(prop, market_data=market_economic_data)
                prop["roi_analysis"] = roi.to_dict()
                benchmark = market_intelligence.benchmark_property(prop)
                prop["wolf_analysis"] = benchmark.wolf_analysis
                prop["wolf_benchmark"] = benchmark.to_dict()

            top_verdict = scored_properties[0].get("verdict", "FAIR") if scored_properties else "FAIR"

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 7: STRATEGY & UI
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 1. Determine Verbal Strategy FIRST (so UI can match it)
            strategy = determine_strategy(
                psychology,
                has_properties=len(scored_properties) > 0 and is_discovery_complete,
                top_property_verdict=top_verdict
            )
            
            # 2. Determine UI Actions (Charts must back up the strategy)
            ui_actions = await self._determine_ui_actions(
                psychology, 
                scored_properties, 
                intent, 
                query,
                showing_strategy,
                wolf_strategy=strategy # Pass the strategy to force matching charts
            )# PRICE DEFENSE (The "Wolf" Logic)
            no_discount_mode = False
            top_wolf_analysis = "FAIR_VALUE"
            if is_discount_request(query):
                 strategy["strategy"] = "price_defense" # Override strategy
                 no_discount_mode = True
                 if scored_properties:
                     top_wolf_analysis = scored_properties[0].get("wolf_analysis", "FAIR_VALUE")

            logger.info(f"🎭 Strategy: {strategy['strategy']}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # FETCH REAL-TIME MARKET PULSE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            market_pulse = None
            if intent.filters.get("location"):
                # Fetch live stats for the requested location
                market_pulse = await market_layer.get_real_time_market_pulse(intent.filters.get("location"))

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 7B: DEVELOPER INSIGHT INJECTION
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Auto-detect developer mentions and inject graph-backed context
            developer_insight = None
            for dev_key, dev_data in DEVELOPER_GRAPH.items():
                # Check English name, Arabic name, and key in the query
                dev_names = [dev_key, dev_data.get('name_en', '').lower(), dev_data.get('name_ar', '')]
                if any(name and name.lower() in query.lower() for name in dev_names):
                    developer_insight = analytical_engine.get_developer_insight(dev_key, language)
                    if developer_insight:
                        logger.info(f"📊 DEVELOPER GRAPH: Injecting insight for {dev_data.get('name_en')}")
                    break

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 8: SPEAK (Narrative Generation)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            suggestions = []  # initialized early for streaming path
            _narrative_kwargs = dict(
                query=query,
                properties=scored_properties,
                psychology=psychology,
                strategy=strategy,
                ui_actions=ui_actions,
                history=history,
                language=language,
                profile=profile,
                is_discovery=not is_discovery_complete,
                intent=intent,
                feasibility=None,
                no_discount_mode=no_discount_mode,
                market_segment=strategy.get("market_segment"),
                market_pulse=market_pulse,
                showing_strategy=showing_strategy,
                pivot_message=pivot_message,
                hunt_strategy=hunt_strategy,
                memory=memory,
                analytics_context=analytics_context,
                developer_insight=developer_insight,
                reasoning_chain=reasoning_chain,
                db_session=session,
            )

            # ── STREAMING MODE: return context for real SSE streaming ──
            if streaming and config.ENABLE_REAL_STREAMING:
                stream_context = await self._generate_wolf_narrative(
                    **_narrative_kwargs, _return_context=True,
                )
                # Skip verification & return immediately with stream context
                elapsed = (datetime.now() - start_time).total_seconds()
                return {
                    "response": "",  # Will be filled by streaming
                    "_stream_context": stream_context,
                    "properties": scored_properties[:5] if showing_strategy == 'FULL_LIST' else (scored_properties[:1] if showing_strategy == 'TEASER' else []),
                    "ui_actions": ui_actions,
                    "analytics_context": analytics_context,
                    "card_readiness": card_readiness,
                    "psychology": psychology.to_dict(),
                    "strategy": strategy,
                    "intent": intent.to_dict(),
                    "processing_time_ms": int(elapsed * 1000),
                    "model_used": "wolf_brain_v10_streaming",
                    "showing_strategy": showing_strategy,
                    "hunt_strategy": hunt_strategy,
                    "suggestions": suggestions,
                    "verification": {},
                    "proactive_alerts": [],
                    "xp_awarded": 0,
                    "detected_language": language,
                    "lead_score": lead_score,
                }

            # ── NON-STREAMING: full pipeline ──
            response_text = await self._generate_wolf_narrative(**_narrative_kwargs)
            self.stats["claude_calls"] += 1

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # POST-SPEAK: Verification (Anti-Hallucination Layer)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            verification = {}
            try:
                properties_for_verify = scored_properties[:5] if showing_strategy == 'FULL_LIST' else (scored_properties[:1] if showing_strategy == 'TEASER' else [])
                verification = await verifier_agent.verify_response(
                    response_text=response_text,
                    properties_mentioned=properties_for_verify,
                    session=session,
                )
                if verification.get("corrections"):
                    logger.info(f"🔍 VERIFIER: Found {len(verification['corrections'])} corrections (confidence: {verification.get('confidence', 'N/A')})")
            except Exception as e:
                logger.warning(f"Verifier agent skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # POST-SPEAK: Smart Follow-Up Suggestions
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            suggestions = []
            try:
                suggestions = generate_suggestions_from_turn(
                    language=language,
                    lead_score=lead_score,
                    history=history,
                    ui_actions=ui_actions,
                    properties=scored_properties,
                )
                if suggestions:
                    logger.info(f"💡 SUGGESTIONS: Generated {len(suggestions)} follow-up suggestions")
            except Exception as e:
                logger.warning(f"Suggestion engine skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # POST-SPEAK: Proactive Intelligence Alerts
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            proactive_alerts = []
            try:
                tools_used_list = [a.get("type", "") for a in ui_actions] if ui_actions else []
                insights = proactive_engine.analyze(
                    history=history,
                    properties_viewed=scored_properties,
                    tools_used=tools_used_list,
                    lead_score=lead_score,
                    user_memory=memory.to_dict() if memory else None,
                    session_count=len([m for m in history if m.get("role") == "user"]),
                )
                proactive_alerts = [ins.to_dict(language) for ins in insights]
                if proactive_alerts:
                    logger.info(f"🔮 PROACTIVE: {proactive_alerts[0].get('type', 'unknown')} alert generated")
            except Exception as e:
                logger.warning(f"Proactive insights skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # POST-SPEAK: Gamification XP Award
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            xp_awarded = 0
            try:
                if user_id:
                    from app.services.gamification import GamificationEngine
                    gam_engine = GamificationEngine()

                    # Base XP for asking a question
                    result = await gam_engine.award_xp(user_id, "ask_question", session)
                    xp_awarded += result.get("xp_awarded", 0)

                    # Bonus XP for using analysis tools
                    analysis_tools = ["certificates_vs_property", "bank_vs_property", "roi_calculator", "area_analysis", "comparison_matrix"]
                    tools_in_turn = [a.get("type", "") for a in ui_actions] if ui_actions else []
                    if any(t in analysis_tools for t in tools_in_turn):
                        result = await gam_engine.award_xp(user_id, "use_analysis_tool", session)
                        xp_awarded += result.get("xp_awarded", 0)

                    # Check achievements
                    await gam_engine.check_achievements(user_id, session)

                    if xp_awarded > 0:
                        logger.info(f"🎮 GAMIFICATION: Awarded {xp_awarded} XP to user {user_id}")
            except Exception as e:
                logger.warning(f"Gamification XP skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # SAVE MEMORY: Persist to DB for cross-session recall
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if user_id:
                await self._save_user_memory(session, user_id, memory)

            # Calculate processing time
            elapsed = (datetime.now() - start_time).total_seconds()

            return {
                "response": response_text,
                "properties": scored_properties[:5] if showing_strategy == 'FULL_LIST' else (scored_properties[:1] if showing_strategy == 'TEASER' else []),
                "ui_actions": ui_actions,
                "analytics_context": analytics_context,
                "card_readiness": card_readiness,
                "psychology": psychology.to_dict(),
                "strategy": strategy,
                "intent": intent.to_dict(),
                "processing_time_ms": int(elapsed * 1000),
                "model_used": "wolf_brain_v10_full_pipeline",
                "showing_strategy": showing_strategy,
                "hunt_strategy": hunt_strategy,
                "suggestions": suggestions,
                "verification": verification,
                "proactive_alerts": proactive_alerts,
                "xp_awarded": xp_awarded,
                "detected_language": language,
                "lead_score": lead_score,
                "commitment_level": memory.commitment_level if memory else 0,
            }
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Wolf Brain error: {e}", exc_info=True)
            
            # Fallback response
            return {
                "response": "عذراً حصل خطأ فني. ممكن تحاول تاني؟ 🙏 (Sorry, technical error. Can you try again?)",
                "properties": [],
                "ui_actions": [],
                "psychology": {"primary_state": "neutral"},
                "error": str(e)
            }
    
    def _detect_user_language(self, text: str) -> str:
        """
        Detect if text is Arabic or English.
        Returns 'ar', 'en', or 'auto' (if mixed/unclear).
        """
        if not text:
            return "auto"
            
        # Check for Arabic unicode range
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', text))
        
        if has_arabic:
            return "ar"
        return "en"

    async def _load_user_memory(self, session: AsyncSession, user_id: int) -> Optional[ConversationMemory]:
        """Load cross-session memory from DB for a logged-in user."""
        try:
            result = await session.execute(
                select(UserMemory).where(UserMemory.user_id == user_id)
            )
            record = result.scalar_one_or_none()
            if record and record.memory_json:
                import json
                data = json.loads(record.memory_json)
                return ConversationMemory.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load user memory for user {user_id}: {e}")
        return None

    async def _save_user_memory(self, session: AsyncSession, user_id: int, memory: ConversationMemory):
        """Save/update cross-session memory to DB for a logged-in user."""
        try:
            import json
            memory_dict = memory.to_dict()
            memory_json = json.dumps(memory_dict, ensure_ascii=False)
            
            result = await session.execute(
                select(UserMemory).where(UserMemory.user_id == user_id)
            )
            record = result.scalar_one_or_none()
            
            if record:
                record.memory_json = memory_json
                record.budget_min = memory.budget_range.get('min') if memory.budget_range else None
                record.budget_max = memory.budget_range.get('max') if memory.budget_range else None
                record.preferred_areas = ','.join(memory.preferred_areas) if memory.preferred_areas else None
                record.investment_vs_living = memory.investment_vs_living
                record.preferences_text = '; '.join(memory.preferences) if memory.preferences else None
            else:
                new_record = UserMemory(
                    user_id=user_id,
                    memory_json=memory_json,
                    budget_min=memory.budget_range.get('min') if memory.budget_range else None,
                    budget_max=memory.budget_range.get('max') if memory.budget_range else None,
                    preferred_areas=','.join(memory.preferred_areas) if memory.preferred_areas else None,
                    investment_vs_living=memory.investment_vs_living,
                    preferences_text='; '.join(memory.preferences) if memory.preferences else None
                )
                session.add(new_record)
            
            await session.commit()
            logger.info(f"💾 User memory saved for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to save user memory for user {user_id}: {e}")

    def _needs_screening(self, query: str, history: List[Dict]) -> bool:
        """
        Check if we need to trigger the 'Velvet Rope' screening gate.
        Criteria:
        1. Vague price query ("How much", "Price", "Prices", "سعر", "بكام")
        2. No previous context (history length < 2)
        3. No budget mentioned in query (simple regex check)
        """
        if len(history) >= 2:
            return False
            
        query_lower = query.lower()
        price_keywords = ["price", "much", "cost", "سعر", "بكام", "اسعار", "أسعار", "تكلفة"]
        
        is_price_query = any(kw in query_lower for kw in price_keywords)
        
        if not is_price_query:
            return False
            
        # Check if they already gave a budget (e.g. "Price under 5M")
        budget_indicators = ["million", "mil", "k", "000", "مليون", "الف", "ألف"]
        has_budget = any(ind in query_lower for ind in budget_indicators)
        
        return not has_budget

    def _get_screening_script(self, language: str) -> Dict[str, Any]:
        """Return the pre-baked Velvet Rope script."""
        script_ar = (
            "قبل ما أقولك أرقام ممكن تكون مش مناسبة ليك، قولي الأول:\n\n"
            "حضرتك بتشتري **سكن** (Living) ولا **استثمار** (Investment)؟\n"
            "وميزانيتك في حدود كام؟\n\n"
            "الإجابة دي هتفرق جداً في الترشيحات."
        )
        script_en = (
            "Before I quote prices that might not fit your goals, I need to know:\n\n"
            "Are you buying for **Living** or **Investment**?\n"
            "And what is your approximate budget?\n\n"
            "This will help me filter 90% of the market for you."
        )
        
        # Generate language-aware suggestions for the screening
        screening_suggestions_ar = [
            "عايز أستثمر مش أسكن",
            "أنا بدور على شقة للسكن العائلي",
            "ميزانيتي حوالي 5 مليون جنيه",
        ]
        screening_suggestions_en = [
            "I want to invest, not live",
            "I'm looking for a family home",
            "My budget is around 5M EGP",
        ]
        return {
            "response": script_ar if language != "en" else script_en,
            "ui_actions": [],
            "properties": [],
            "psychology": {"primary_state": "neutral"},
            "strategy": {"strategy": "fast_gate"},
            "model_used": "wolf_fast_gate",
            "suggestions": screening_suggestions_ar if language != "en" else screening_suggestions_en,
            "detected_language": language,
            "lead_score": 0,
            "card_readiness": {"readiness_score": 0, "recommendation": "NONE"},
            "showing_strategy": "NONE",
            "analytics_context": None,
            "intent": {},
        }

    async def _handle_general_query(
        self,
        query: str,
        history: List[Dict],
        language: str
    ) -> Dict[str, Any]:
        """Handle simple queries with fast GPT-4o response."""
        # ... logic remains if needed, or we can rely on main flow. 
        # For now, keeping it as fallback.
        try:
             # Just use main flow fallback logic or simple return 
             # ...
             pass
        except:
             pass
        return {} # Placeholder if called

    async def _search_database(self, filters: Dict, db_session: Optional[AsyncSession] = None) -> List[Dict]:
        """
        Search database for properties matching filters.
        """
        try:
            # Use passed session or create new one context
            if db_session:
                return await self._execute_search_query(filters, db_session)
            
            async with AsyncSessionLocal() as db:
                return await self._execute_search_query(filters, db)
        except Exception as e:
            logger.error(f"Database search failed: {e}", exc_info=True)
            return []

    async def _execute_search_query(self, filters: Dict, db: AsyncSession) -> List[Dict]:
        """Execute the actual search logic with full filter support including resale/delivery."""
        # Build query text
        query_parts = []
        if 'location' in filters:
            query_parts.append(filters['location'])
        if 'bedrooms' in filters:
            query_parts.append(f"{filters['bedrooms']} bedrooms")
        if 'property_type' in filters:
            query_parts.append(filters['property_type'])
        if 'keywords' in filters:
            query_parts.append(filters['keywords'])
        if 'budget_max' in filters and filters['budget_max']:
            budget_mil = filters['budget_max'] / 1_000_000
            query_parts.append(f"under {budget_mil} million")
        # Include sale_type in query text for semantic search
        if 'sale_type' in filters and filters['sale_type']:
            sale_type_map = {"resale": "Resale", "developer": "Developer", "nawy_now": "Nawy Now"}
            query_parts.append(sale_type_map.get(filters['sale_type'], filters['sale_type']))
        if filters.get('is_delivered'):
            query_parts.append("delivered ready to move")
        if 'finishing' in filters and filters['finishing']:
            query_parts.append(f"{filters['finishing']} finishing")
            
        query_text = " ".join(query_parts) if query_parts else "property"
        
        # Map filter values to DB column values
        sale_type_db = None
        if 'sale_type' in filters and filters['sale_type']:
            sale_type_map = {"resale": "Resale", "developer": "Developer", "nawy_now": "Nawy Now"}
            sale_type_db = sale_type_map.get(filters['sale_type'].lower(), filters['sale_type'])
        
        finishing_db = None
        if 'finishing' in filters and filters['finishing']:
            fin_map = {"finished": "Finished", "semi-finished": "Semi-Finished", "semi_finished": "Semi-Finished",
                       "core": "Core & Shell", "unfinished": "Core & Shell", "lux": "Finished", "ready": "Finished"}
            finishing_db = fin_map.get(filters['finishing'].lower(), filters['finishing'])

        # Vector search with full filter support
        results = await db_search_properties(
            db=db,
            query_text=query_text,
            limit=50,
            similarity_threshold=0.50,
            price_min=filters.get('budget_min'),
            price_max=filters.get('budget_max'),
            sale_type=sale_type_db,
            is_delivered=filters.get('is_delivered'),
            finishing=finishing_db,
            is_nawy_now=filters.get('is_nawy_now'),
        )
        
        # Apply additional filters (belt & suspenders post-filter)
        if 'budget_max' in filters and filters['budget_max']:
            results = [r for r in results if r.get('price', 0) <= filters['budget_max']]
        
        if 'budget_min' in filters and filters['budget_min']:
            results = [r for r in results if r.get('price', 0) >= filters['budget_min']]
        
        if 'bedrooms' in filters and filters['bedrooms']:
            results = [r for r in results if r.get('bedrooms', 0) >= filters['bedrooms']]
        
        if 'property_type' in filters and filters['property_type']:
            ptype = filters['property_type'].lower()
            results = [r for r in results if ptype in r.get('type', '').lower()]
        
        return results[:10]  # Top 10

    async def _smart_hunt(
        self, 
        intent: Intent, 
        session: AsyncSession,
        language: str = "ar"
    ) -> tuple[List[Dict], str, Optional[str]]:
        """
        SOTA: Agentic Search with Reflexion (Fallback Strategies)
        
        Instead of returning empty results, this method automatically pivots:
        1. Location Pivot: Zayed → 6th October (cheaper neighbor)
        2. Type Pivot: Villa → Townhouse (downgrade type)
        
        Returns: (properties, strategy_used, pivot_message)
        - strategy_used: 'direct_match', 'location_pivot', 'type_pivot', 'budget_pivot', 'failed'
        - pivot_message: Explanation for the user about the pivot (None if direct match)
        """
        filters = intent.filters
        
        # 1. Primary Search
        results = await self._search_database(filters, db_session=session)
        if results:
            logger.info(f"🎯 SMART HUNT: Direct match found ({len(results)} results)")
            return results, "direct_match", None

        logger.info("🔄 SMART HUNT: No direct match, entering Reflexion mode...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REFLEXION: Location Pivot (Keep budget, move to cheaper area)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        location = filters.get("location", "").lower()
        location_pivots = {
            "sheikh zayed": ("6th October", "أكتوبر", "زايد"),
            "zayed": ("6th October", "أكتوبر", "زايد"),
            "الشيخ زايد": ("6th October", "أكتوبر", "زايد"),
            "new cairo": ("Mostakbal City", "المستقبل", "التجمع"),
            "التجمع": ("Mostakbal City", "المستقبل", "التجمع"),
            "التجمع الخامس": ("Mostakbal City", "المستقبل", "التجمع"),
            "madinaty": ("Mostakbal City", "المستقبل", "مدينتي"),
            "مدينتي": ("Mostakbal City", "المستقبل", "مدينتي"),
        }
        
        for loc_key, (new_loc, new_loc_ar, old_loc_ar) in location_pivots.items():
            if loc_key in location:
                new_filters = filters.copy()
                new_filters["location"] = new_loc
                alternatives = await self._search_database(new_filters, db_session=session)
                
                if alternatives:
                    logger.info(f"🔄 SMART HUNT: Location pivot success ({loc_key} → {new_loc})")
                    if language == "ar":
                        pivot_msg = f"مفيش نتائج في {old_loc_ar}، بس لقيت فرص في {new_loc_ar} بنفس الميزانية."
                    else:
                        pivot_msg = f"No exact match in {loc_key.title()}, but I found options in {new_loc} within your budget."
                    return alternatives, "location_pivot", pivot_msg
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REFLEXION: Type Pivot (Keep location, downgrade property type)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        property_type = filters.get("property_type", "").lower()
        type_pivots = {
            "villa": ("townhouse", "تاون هاوس", "فيلا"),
            "فيلا": ("townhouse", "تاون هاوس", "فيلا"),
            "standalone": ("twin house", "توين هاوس", "ستاند الون"),
            "twin house": ("townhouse", "تاون هاوس", "توين هاوس"),
            "townhouse": ("apartment", "شقة", "تاون هاوس"),
            "duplex": ("apartment", "شقة", "دوبلكس"),
        }
        
        for type_key, (new_type, new_type_ar, old_type_ar) in type_pivots.items():
            if type_key in property_type:
                new_filters = filters.copy()
                new_filters["property_type"] = new_type
                alternatives = await self._search_database(new_filters, db_session=session)
                
                if alternatives:
                    logger.info(f"🔄 SMART HUNT: Type pivot success ({type_key} → {new_type})")
                    if language == "ar":
                        pivot_msg = f"الـ{old_type_ar} بالميزانية دي صعب، بس لقيت {new_type_ar} ممتاز في نفس المنطقة."
                    else:
                        pivot_msg = f"A {type_key} at this budget is tough, but I found an excellent {new_type} in the same area."
                    return alternatives, "type_pivot", pivot_msg
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REFLEXION: Budget Pivot (Increase budget by 20% if too low)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        budget_max = filters.get("budget_max")
        if budget_max and budget_max > 0:
            new_filters = filters.copy()
            new_budget = int(budget_max * 1.25)  # 25% increase
            new_filters["budget_max"] = new_budget
            alternatives = await self._search_database(new_filters, db_session=session)
            
            if alternatives:
                budget_diff = (new_budget - budget_max) / 1_000_000
                logger.info(f"🔄 SMART HUNT: Budget pivot success ({budget_max/1e6:.1f}M → {new_budget/1e6:.1f}M)")
                if language == "ar":
                    pivot_msg = f"بزيادة بسيطة ({budget_diff:.1f} مليون)، لقيت خيارات ممتازة."
                else:
                    pivot_msg = f"With a small stretch (+{budget_diff:.1f}M), I found excellent options."
                return alternatives, "budget_pivot", pivot_msg
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REFLEXION: Relaxed Search (Keep only location, drop all other filters)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        location = filters.get("location", "")
        if location:
            relaxed_filters = {"location": location}
            alternatives = await self._search_database(relaxed_filters, db_session=session)
            if alternatives:
                logger.info(f"🔄 SMART HUNT: Relaxed search success (location only: {location}, {len(alternatives)} results)")
                if language == "ar":
                    pivot_msg = f"المواصفات المحددة مش متاحة دلوقتي، بس دي أفضل الخيارات المتاحة في {location}."
                else:
                    pivot_msg = f"Those exact specs aren't available, but here are the best options in {location}."
                return alternatives, "relaxed_search", pivot_msg

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REFLEXION: Any Area Search (Keep only budget, drop everything)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        budget_max = filters.get("budget_max")
        budget_min = filters.get("budget_min")
        if budget_max or budget_min:
            any_area_filters = {}
            if budget_max:
                any_area_filters["budget_max"] = budget_max
            if budget_min:
                any_area_filters["budget_min"] = budget_min
            alternatives = await self._search_database(any_area_filters, db_session=session)
            if alternatives:
                logger.info(f"🔄 SMART HUNT: Any-area search success ({len(alternatives)} results)")
                if language == "ar":
                    pivot_msg = "مفيش في المنطقة دي بالميزانية دي، بس لقيت فرص في مناطق تانية تستاهل تشوفها."
                else:
                    pivot_msg = "Nothing in that area at this budget, but I found opportunities in other areas worth checking."
                return alternatives, "any_area_search", pivot_msg

        # All strategies failed — graceful message with suggestions
        logger.info("❌ SMART HUNT: All reflexion strategies failed")
        filter_desc_parts = []
        if filters.get("location"):
            filter_desc_parts.append(filters["location"])
        if filters.get("property_type"):
            filter_desc_parts.append(filters["property_type"])
        if filters.get("budget_max"):
            filter_desc_parts.append(f"{filters['budget_max']/1e6:.1f}M budget")
            
        if language == "ar":
            pivot_msg = (
                "للأسف مفيش وحدات متاحة بالمواصفات دي حالياً.\n\n"
                "ممكن نجرب:\n"
                "• تغيير المنطقة (مثلاً المستقبل أو أكتوبر)\n"
                "• تعديل الميزانية بزيادة بسيطة\n"
                "• نوع مختلف (شقة بدل فيلا مثلاً)\n\n"
                "قولي إيه اللي تحب نعدله وأنا أبحثلك تاني 💪"
            )
        else:
            pivot_msg = (
                "Unfortunately, no units match these exact criteria right now.\n\n"
                "Let's try:\n"
                "• A different area (e.g., Mostakbal City or October)\n"
                "• Stretching the budget slightly\n"
                "• A different property type\n\n"
                "Tell me what you'd like to adjust and I'll search again."
            )
        return [], "failed", pivot_msg

                    
    def _is_discovery_complete(self, filters: Dict, history: List[Dict], query: str = "") -> bool:
        """
        Check if discovery phase is complete.
        Uses AI-extracted context to break the loop.
        """
        # 1. Check if AI successfully extracted the Purpose context
        #    This solves the "exact match" issue. If GPT says purpose is "living", we trust it.
        ai_extracted_purpose = filters.get('purpose')
        if ai_extracted_purpose in ['living', 'investment', 'commercial']:
            logger.debug(f"Discovery complete: AI extracted purpose '{ai_extracted_purpose}'")
            return True

        # 2. Check for Budget (AI extraction or manual check)
        has_budget = bool(filters.get('budget_max') or filters.get('budget_min'))
        
        # 3. Check history length
        has_context = len(history) >= 2
        
        # 4. Fallback: Manual Keyword Check (Safety Net)
        #    Only needed if the AI failed to extract the purpose
        history_text = " ".join([
            msg.get('content', '').lower() 
            for msg in history[-6:] 
            if isinstance(msg, dict)
        ])
        full_text = f"{history_text} {query.lower()}"
        
        manual_purpose_keywords = [
            # English
            "invest", "live", "rent", "buy", "roi", "yield", "profit", 
            "home", "house", "family", "kids", "resale", "flip", "living",
            "stay", "return", "capital", "income",
            # Arabic
            "سكن", "استثمار", "ايجار", "عائد", "ارباح", "بيت", "اسكن",
            "عيلة", "اولاد", "منزل", "اعيش", "شقة", "فيلا"
        ]
        has_manual_purpose = any(kw in full_text for kw in manual_purpose_keywords)
        
        # 5. SAFETY NET: Check for manual budget in query 
        budget_keywords = ["million", "mil", "k", "000", "مليون", "الف", "ألف", "مليار"]
        has_manual_budget = any(kw in query.lower() for kw in budget_keywords) and any(c.isdigit() for c in query)
        has_budget = has_budget or has_manual_budget
        
        # Check for location
        has_location = bool(filters.get('location'))
        
        # Also check for location keywords in context
        location_keywords = [
            "new cairo", "zayed", "october", "capital", "shorouk", "future city", 
            "coastal", "التجمع", "زايد", "اكتوبر", "العاصمة", "الشروق", "مدينتي",
            "6 october", "6th october", "الساحل", "north coast"
        ]
        if not has_location:
            has_location = any(kw in full_text for kw in location_keywords)

        # 6. Decision Logic
        if has_budget:
            logger.debug("Discovery complete: Has budget info")
            return True
        
        if has_context and has_manual_purpose:
            logger.debug("Discovery complete: Has context + manual purpose")
            return True
        
        if has_location and has_manual_purpose:
            logger.debug("Discovery complete: Has location + manual purpose")
            return True
            
        # If user explicitly asks to SEE something, assume discovery is done
        show_keywords = ["show", "see", "list", "what do you have", "وريني", "عايز اشوف", "ايه المتاح", "ورجيني", "اعرض"]
        if any(kw in query.lower() for kw in show_keywords):
            logger.debug("Discovery complete: User explicitly asked to see properties")
            return True
        
        logger.debug(f"Discovery incomplete: budget={has_budget}, context={has_context}, purpose={has_manual_purpose}, location={has_location}")
        return False
    
    def _psychology_card_gate(
        self,
        intent: Intent,
        psychology: PsychologyProfile,
        is_discovery_complete: bool,
        lead_score: int = 0,
        memory: Optional[Any] = None,
        history: Optional[List[Dict]] = None,
        card_readiness: Optional[Dict] = None
    ) -> str:
        """
        Psychology-Driven Card Display Gate v4 — Readiness-First.

        Card readiness score is the PRIMARY signal. Discovery status can only
        UPGRADE within readiness bounds; it cannot bypass psychology.

        Hard rules:
        - < 3 user turns  → max ANALYTICS_ONLY (no exceptions except hard blocks)
        - < 4 user turns  → max TEASER
        - readiness < 20   → max ANALYTICS_ONLY
        - readiness 20-44  → max TEASER
        - readiness >= 45  → FULL_LIST allowed

        Returns: 'NONE', 'ANALYTICS_ONLY', 'TEASER', 'FULL_LIST'
        """
        history = history or []
        state = psychology.primary_state
        trust_level = self._calculate_trust_level(psychology, history)
        engagement_depth = len([m for m in history if m.get("role") == "user"])
        has_location = bool(intent.filters.get("location"))
        has_budget = bool(intent.filters.get("budget_max"))

        # Extract readiness score
        readiness_score = card_readiness.get("readiness_score", 0) if card_readiness else 0
        readiness_rec = card_readiness.get("recommendation", "NONE") if card_readiness else "NONE"

        # ── CEILING FUNCTION: Hard cap based on readiness + engagement depth ──
        tier_order = ['NONE', 'ANALYTICS_ONLY', 'TEASER', 'FULL_LIST']

        def apply_ceiling(proposed: str) -> str:
            """Cap proposed strategy by readiness score AND engagement depth."""
            # Max by engagement depth
            if engagement_depth < 3:
                depth_max = 'ANALYTICS_ONLY'
            elif engagement_depth < 4:
                depth_max = 'TEASER'
            else:
                depth_max = 'FULL_LIST'

            # Max by readiness score
            if readiness_score < 20:
                readiness_max = 'ANALYTICS_ONLY'
            elif readiness_score < 45:
                readiness_max = 'TEASER'
            else:
                readiness_max = 'FULL_LIST'

            # Ceiling = stricter of the two
            ceiling = tier_order[min(tier_order.index(depth_max), tier_order.index(readiness_max))]

            if tier_order.index(proposed) > tier_order.index(ceiling):
                logger.info(f"🔒 Ceiling: {proposed} → {ceiling} (depth={engagement_depth}, readiness={readiness_score})")
                return ceiling
            return proposed

        # ── HARD BLOCKS (never show cards — bypass ceiling) ──
        if state == PsychologicalState.TRUST_DEFICIT:
            logger.info("👁️ Gate: NONE (Trust Deficit — build confidence first)")
            return 'NONE'

        if state == PsychologicalState.LEGAL_ANXIETY and trust_level < 0.5:
            logger.info("👁️ Gate: NONE (Legal Anxiety + low trust)")
            return 'NONE'

        if intent.action in ["investment", "general", "legal"] and not has_location and not has_budget:
            logger.info("👁️ Gate: NONE (Educational query without location or budget)")
            return 'NONE'

        # ── ANALYTICS_ONLY tier (psychology-specific gates) ──
        if state == PsychologicalState.ANALYSIS_PARALYSIS:
            if engagement_depth < 5:
                result = apply_ceiling('ANALYTICS_ONLY')
                logger.info(f"👁️ Gate: {result} (Analysis Paralysis, depth={engagement_depth})")
                return result
            result = apply_ceiling('TEASER')
            logger.info(f"👁️ Gate: {result} (Analysis Paralysis resolved after 5+ turns)")
            return result

        if state == PsychologicalState.RISK_AVERSE and trust_level < 0.6:
            result = apply_ceiling('ANALYTICS_ONLY')
            logger.info(f"👁️ Gate: {result} (Risk Averse, trust={trust_level:.2f})")
            return result

        if state in [PsychologicalState.MACRO_SKEPTIC, PsychologicalState.SKEPTICISM]:
            if engagement_depth < 4:
                result = apply_ceiling('ANALYTICS_ONLY')
                logger.info(f"👁️ Gate: {result} (Skeptic, depth={engagement_depth})")
                return result

        if state == PsychologicalState.INFLATION_REFUGEE and not has_budget:
            result = apply_ceiling('ANALYTICS_ONLY')
            logger.info(f"👁️ Gate: {result} (Inflation Refugee — show economic data first)")
            return result

        # Cold leads → analytics first
        if lead_score < 20 and not is_discovery_complete:
            if intent.action not in ["search", "price_check"]:
                if has_location:
                    result = apply_ceiling('ANALYTICS_ONLY')
                    logger.info(f"👁️ Gate: {result} (Cold lead={lead_score}, has location)")
                    return result
                logger.info(f"👁️ Gate: NONE (Cold lead={lead_score}, no location)")
                return 'NONE'

        # ── FAST-TRACK tier (psychology says eager — still ceiling-gated) ──
        if state == PsychologicalState.IMPULSE_BUYER and has_location:
            if is_discovery_complete or has_budget:
                result = apply_ceiling('FULL_LIST')
                logger.info(f"👁️ Gate: {result} (Impulse Buyer + qualified)")
                return result
            result = apply_ceiling('TEASER')
            logger.info(f"👁️ Gate: {result} (Impulse Buyer — quick anchor)")
            return result

        if state in [PsychologicalState.GREED_DRIVEN, PsychologicalState.FOMO]:
            if lead_score >= 30 and has_location:
                result = apply_ceiling('FULL_LIST')
                logger.info(f"👁️ Gate: {result} ({state.value} + warm lead)")
                return result
            if has_location:
                result = apply_ceiling('TEASER')
                logger.info(f"👁️ Gate: {result} ({state.value} + location)")
                return result
            return apply_ceiling('ANALYTICS_ONLY')

        # ── Explicit show request — still respect engagement ceiling ──
        show_keywords = ["show", "أوريني", "ورجيني", "best", "أفضل", "options", "خيارات", "وريني", "عايز اشوف"]
        if any(kw in intent.raw_query.lower() for kw in show_keywords):
            result = apply_ceiling('FULL_LIST')
            logger.info(f"👁️ Gate: {result} (Explicit show request, ceiling-adjusted)")
            return result

        # ── Discovery complete → upgrade ONE level from readiness base ──
        if is_discovery_complete:
            base_idx = tier_order.index(readiness_rec) if readiness_rec in tier_order else 0
            upgraded = tier_order[min(base_idx + 1, len(tier_order) - 1)]
            result = apply_ceiling(upgraded)
            logger.info(f"👁️ Gate: {result} (Discovery complete, base={readiness_rec} → upgraded={upgraded})")
            return result

        # ── Warm/hot lead upgrade ──
        if lead_score >= 60 and has_location:
            result = apply_ceiling('FULL_LIST')
            logger.info(f"👁️ Gate: {result} (Hot lead upgrade: {lead_score})")
            return result

        # ── Has location but no budget → analytics then teaser ──
        if has_location and not has_budget:
            if engagement_depth >= 3:
                result = apply_ceiling('TEASER')
                logger.info(f"👁️ Gate: {result} (Location + engagement ≥ 3)")
                return result
            result = apply_ceiling('ANALYTICS_ONLY')
            logger.info(f"👁️ Gate: {result} (Location only, early conversation)")
            return result

        # ── Default: analytics if location, else none ──
        if has_location:
            result = apply_ceiling('ANALYTICS_ONLY')
            logger.info(f"👁️ Gate: {result} (Default with location)")
            return result

        logger.info("👁️ Gate: NONE (Default fallback)")
        return 'NONE'

    def _calculate_trust_level(self, psychology: PsychologyProfile, history: List[Dict]) -> float:
        """Calculate trust 0.0-1.0 based on psychology + conversation depth."""
        base = 0.3
        if psychology.emotional_momentum == "warming_up":
            base += 0.2
        elif psychology.emotional_momentum == "cooling_down":
            base -= 0.1
        if psychology.urgency_level in [UrgencyLevel.EVALUATING, UrgencyLevel.READY_TO_ACT, UrgencyLevel.URGENT]:
            base += 0.15
        # Longer conversations build trust
        turn_count = len([m for m in history if m.get("role") == "user"])
        turn_bonus = min(turn_count / 20, 0.3)
        return max(0.0, min(base + turn_bonus, 1.0))

    async def _build_analytics_context(self, intent: Intent, session: AsyncSession, market_layer: MarketAnalyticsLayer) -> Dict[str, Any]:
        """Build comprehensive analytics context from DB before any property search."""
        context: Dict[str, Any] = {"has_analytics": False}
        location = intent.filters.get("location", "")
        if not location:
            return context

        try:
            # Sequential fetch: both use the same async session, so we CANNOT
            # run them concurrently (SQLAlchemy async sessions forbid it).
            pulse = None
            econ = {}
            try:
                pulse = await market_layer.get_real_time_market_pulse(location)
            except Exception as e:
                logger.warning(f"Market pulse fetch failed: {e}")
                pulse = None

            try:
                econ = await analytical_engine.get_live_market_data(session)
            except Exception as e:
                logger.warning(f"Economic data fetch failed: {e}")
                econ = MARKET_DATA.copy() if 'MARKET_DATA' in dir() else {}

            # Sync fetch: area context + market segment
            area_ctx = market_intelligence.get_area_context(location)
            segment = market_intelligence.get_market_segment(location)

            # Format economic context for prompt injection
            economic_brief = analytical_engine.format_economic_context(econ) if econ else ""

            context = {
                "has_analytics": True,
                "location": location,
                "market_pulse": pulse if isinstance(pulse, dict) else None,
                "area_context": area_ctx,
                "market_segment": segment,
                "economic_data": econ if isinstance(econ, dict) else {},
                "economic_brief": economic_brief,
                "avg_price_sqm": area_ctx.get("avg_price_sqm", 0),
                "growth_rate": area_ctx.get("growth_rate", 0),
                "rental_yield": area_ctx.get("rental_yield", 0),
            }
        except Exception as e:
            logger.warning(f"Analytics context build failed: {e}")

        return context
    

    async def _determine_ui_actions(
        self,
        psychology: PsychologyProfile,
        properties: List[Dict],
        intent: Intent,
        query: str,
        showing_strategy: str = 'NONE',
        wolf_strategy: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Determine which UI visualizations to trigger.
        SELECTIVE: Only show charts when they add real value to the conversation.
        The AI text itself should carry the statistics — charts are supplementary.
        Deduplicates by type to prevent the same chart appearing twice.
        """
        ui_actions = []
        seen_types = set()  # Prevent duplicate chart types
        query_lower = query.lower()

        def add_action(action: Dict):
            """Add ui_action only if its type hasn't been added yet."""
            atype = action.get("type", "")
            if atype not in seen_types:
                seen_types.add(atype)
                ui_actions.append(action)

        location = intent.filters.get('location', '')
        
        # ═══════════════════════════════════════════════════════════════
        # ANALYTICS_ONLY: Show area_analysis (text-rich) instead of market_benchmark
        # The AI text carries the statistics. Only one chart per message.
        # ═══════════════════════════════════════════════════════════════
        if showing_strategy == 'ANALYTICS_ONLY' and location:
            area_ctx = market_intelligence.get_area_context(location)
            if area_ctx.get('found'):
                # Build rich area data from AREA_BENCHMARKS
                loc_key = market_intelligence._normalize_location(location)
                raw_bench = AREA_BENCHMARKS.get(loc_key, {})
                growth_raw = area_ctx.get('growth_rate', 0)
                # Convert growth to percentage (some benchmarks store as 1.57 = 157%)
                growth_pct = growth_raw * 100 if growth_raw < 5 else growth_raw
                rental_yield = area_ctx.get('rental_yield', 0)
                yield_pct = rental_yield * 100 if rental_yield < 1 else rental_yield
                avg_sqm = area_ctx.get('avg_price_sqm', 0)
                tier1 = area_ctx.get('tier1_developers', [])
                tier2 = raw_bench.get('tier2_developers', [])
                minimums = raw_bench.get('property_minimums', {})

                # Build pros/cons from real data
                pros_list = []
                cons_list = []
                if growth_pct > 20:
                    pros_list.append(f"نمو سعري قوي ({growth_pct:.0f}% سنوياً)")
                if yield_pct > 6:
                    pros_list.append(f"عائد إيجاري مرتفع ({yield_pct:.1f}%)")
                if len(tier1) >= 3:
                    pros_list.append(f"تواجد {len(tier1)} مطورين درجة أولى")
                if minimums.get('apartment', 0) < 4_000_000:
                    pros_list.append("نقطة دخول معقولة للشقق")
                if avg_sqm > 60000:
                    cons_list.append("متوسط سعر المتر مرتفع نسبياً")
                if growth_pct > 100:
                    cons_list.append("أسعار قد تكون في ذروة الارتفاع")
                if len(tier1) <= 1:
                    cons_list.append("عدد محدود من المطورين الكبار")

                # Build best_for from data characteristics
                best_for = []
                if yield_pct > 7:
                    best_for.append("الاستثمار الإيجاري")
                if growth_pct > 30:
                    best_for.append("زيادة رأس المال")
                if minimums.get('apartment', 99_000_000) < 5_000_000:
                    best_for.append("المشترين لأول مرة")
                if minimums.get('villa', 0) > 0:
                    best_for.append("العائلات")

                add_action({
                    "type": "area_analysis",
                    "priority": "high",
                    "title": f"تحليل منطقة {location}",
                    "title_en": f"Area Analysis: {location}",
                    "data": {
                        "area": {
                            "name": area_ctx.get('ar_name', location),
                            "avg_price_sqm": avg_sqm,
                            "avg_price_per_sqm": avg_sqm,
                            "price_growth_ytd": growth_pct,
                            "growth_rate": growth_raw,
                            "rental_yield": rental_yield,
                            "demand_level": "عالي" if growth_pct > 50 else "متوسط" if growth_pct > 15 else "منخفض",
                            "supply_level": "محدود" if avg_sqm > 60000 else "متوسط",
                            "market_trend": "صاعد" if growth_pct > 20 else "مستقر",
                            "tier1_developers": tier1,
                            "top_developers": tier1 + tier2[:2],
                            "best_for": best_for,
                            "pros": pros_list,
                            "cons": cons_list,
                            "property_minimums": minimums,
                        }
                    }
                })

            # ALWAYS inject price growth chart with area analysis (line chart)
            # The user explicitly requested: "make the AI show a line chart about growth with analysis"
            growth_data = analytical_engine.calculate_price_growth_history(location, include_developers=True)
            if growth_data.get('found') and growth_data.get('data_points'):
                add_action({
                    "type": "price_growth_chart",
                    "priority": "high",
                    "title": f"📈 تطور الأسعار في {growth_data.get('location_ar', location)} (2021–2026)",
                    "title_en": f"📈 Price Growth in {location} (2021–2026)",
                    "data": growth_data
                })

            # Auto-inject inflation chart for investment/economic queries
            investment_keywords = ["invest", "استثمار", "عائد", "roi", "return", "bank", "بنك", "فايدة", "شهادات"]
            if any(kw in query_lower for kw in investment_keywords):
                investment_amount = 5_000_000
                inflation_data = analytical_engine.calculate_inflation_hedge(investment_amount, years=5)
                if inflation_data and inflation_data.get('projections'):
                    add_action({
                        "type": "inflation_killer",
                        "priority": "high",
                        "title": "العقار vs التضخم vs البنك",
                        "title_en": "Property vs Inflation vs Bank",
                        "data": {
                            **inflation_data,
                            "initial_investment": investment_amount,
                            "years": 5
                        }
                    })

        # ═══════════════════════════════════════════════════════════════
        # PSYCHOLOGY-DRIVEN CHARTS (Automatic triggers based on emotional state)
        # ═══════════════════════════════════════════════════════════════
        # FAMILY_SECURITY -> Always show inflation protection chart
        if psychology.primary_state == PsychologicalState.FAMILY_SECURITY:
            investment_amount = properties[0].get('price', 5_000_000) if properties else 5_000_000
            inflation_data = analytical_engine.calculate_inflation_hedge(investment_amount, years=5)
            if inflation_data and inflation_data.get('projections'):
                add_action({
                    "type": "inflation_killer",
                    "priority": 8,
                    "title": "حماية العيلة من التضخم",
                    "title_en": "Family Inflation Protection",
                    "data": {
                        **inflation_data,
                        "initial_investment": investment_amount,
                        "years": 5
                    }
                })

        # LEGAL_ANXIETY -> Always show Law 114 Guardian
        if psychology.primary_state == PsychologicalState.LEGAL_ANXIETY:
            add_action({
                "type": "law_114_guardian",
                "priority": 9,
                "status": "active",
                "title": "فحص قانون 114",
                "title_en": "Law 114 Legal Scan",
                "data": {
                    "status": "active",
                    "capabilities": [
                        "فحص تسلسل الملكية",
                        "التحقق من رخص البناء",
                        "مراجعة شروط العقد",
                        "كشف البنود المخفية"
                    ],
                    "cta": "ارفع العقد وأنا أفحصه مجاناً"
                }
            })

        # ═══════════════════════════════════════════════════════════════
        # STRATEGY-DRIVEN CHARTS (Must match script)
        # ═══════════════════════════════════════════════════════════════
        strategy_name = wolf_strategy.get("strategy", "") if wolf_strategy else ""

        # 1. Inflation Hedge Chart (Certificates vs Property)
        # Triggered by: Investment intent OR Specific Strategies (Family Safety, Liquidity Shift)
        force_inflation_chart = strategy_name in ["FAMILY_SAFETY_PITCH", "LIQUIDITY_SHIFT", "TRUST_BUILDING"]
        
        property_keywords = ["شقة", "فيلا", "عقار", "apartment", "villa", "property", "بيت", "unit", "سكن"] # Added "سكن"
        has_property_intent = any(kw in query_lower for kw in property_keywords) or intent.action in ["search", "price_check", "investment"]
        
        if has_property_intent or force_inflation_chart:
            investment_amount = 5_000_000  # Default 5M
            if properties:
                investment_amount = properties[0].get('price', 5_000_000)

            inflation_data = analytical_engine.calculate_inflation_hedge(investment_amount, years=5)
            if inflation_data and inflation_data.get('projections'):
                add_action({
                    "type": "inflation_killer",
                    "priority": "high",
                    "title": "العقار vs شهادات البنك (22% فايدة)",
                    "title_en": "Property vs Bank CDs (22% Interest)",
                    "data": {
                        **inflation_data,
                        "initial_investment": investment_amount,
                        "years": 5
                    }
                })
        
        # 2. Bank Comparison Chart (The Truth)
        # Triggered by: Bank keywords OR Macro Skeptic strategy
        force_bank_chart = strategy_name in ["MACRO_SKEPTIC", "FEAR_OF_LOSS"]
        
        bank_keywords = ["bank", "بنك", "فايدة", "22%", "27%", "شهادات", "certificates"]
        if any(kw in query_lower for kw in bank_keywords) or force_bank_chart:
            investment_amount = 5_000_000
            if properties:
                investment_amount = properties[0].get('price', 5_000_000)

            bank_data = analytical_engine.calculate_bank_vs_property(investment_amount, years=5)
            if bank_data:
                add_action({
                    "type": "certificates_vs_property",  # Use type that frontend supports
                    "priority": "high",
                    "title": "شهادات البنك vs العقار (الحقيقة)",
                    "title_en": "Bank CDs vs Property (The Truth)",
                    "data": {
                        **bank_data,
                        "initial_investment": investment_amount,
                        "years": 5
                    }
                })
        
        # Property cards for search results (Strategy-aware)
        if properties and showing_strategy in ['TEASER', 'FULL_LIST']:
            # Determine card title based on strategy
            if showing_strategy == 'TEASER':
                card_title_ar = "💡 مثال من السوق (متوسط الأسعار)"
                card_title_en = "💡 Market Example (Average Pricing)"
                display_properties = properties[:1]  # Only 1 anchor
            else:
                card_title_ar = "🏠 وحدات تناسب احتياجاتك"
                card_title_en = "🏠 Units Matching Your Criteria"
                display_properties = properties[:5]  # Full list
            
            add_action({
                "type": "property_cards",
                "priority": "medium" if showing_strategy == 'FULL_LIST' else "low",
                "title": card_title_ar,
                "title_en": card_title_en,
                "properties": display_properties,
                "is_teaser": showing_strategy == 'TEASER'  # Flag for frontend styling
            })
        
        # Bargain alert if found
        if properties:
            bargains = await analytical_engine.detect_bargains(properties, threshold_percent=10)
            if bargains:
                add_action({
                    "type": "la2ta_alert",
                    "priority": "high",
                    "title": "🔥 لقطة",
                    "title_en": "🔥 Bargain Found",
                    "property": bargains[0],
                    "discount": bargains[0].get("la2ta_score", 0)
                })
        
        # Growth chart: ALWAYS inject when a location exists — the price
        # history chart is minimal and always adds value to the conversation.
        if location:
            growth_data = analytical_engine.calculate_price_growth_history(location, include_developers=True)
            if growth_data.get('found') and growth_data.get('data_points'):
                add_action({
                    "type": "price_growth_chart",
                    "priority": "high",
                    "title": f"📈 تطور الأسعار في {growth_data.get('location_ar', location)} (2021–2026)",
                    "title_en": f"📈 Price Growth in {location} (2021–2026)",
                    "data": growth_data
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        ui_actions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))

        return ui_actions
    
    async def _generate_wolf_narrative(
        self,
        query: str,
        properties: List[Dict],
        psychology: PsychologyProfile,
        strategy: Dict,
        ui_actions: List[Dict],
        history: List[Dict],
        language: str,
        profile: Optional[Dict] = None,
        is_discovery: bool = False,
        intent: Optional[Intent] = None,
        feasibility: Optional[Any] = None,
        no_discount_mode: bool = False,
        market_segment: Optional[Dict] = None,
        market_pulse: Optional[Dict] = None,
        showing_strategy: str = 'NONE',
        pivot_message: Optional[str] = None,
        hunt_strategy: str = 'none',
        memory: Optional[Any] = None,
        developer_insight: Optional[Dict] = None,
        analytics_context: Optional[Dict] = None,
        reasoning_chain: Optional[ReasoningChain] = None,
        db_session: Optional[Any] = None,
        _return_context: bool = False,
    ):
        """
        STEP 8: SPEAK (Claude 3.5 Sonnet)
        Generate the Wolf's response using ONLY verified data.
        Now with psychology-aware context injection and Smart Display strategy.
        """
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # INSIGHT INJECTION (The "Wolf" Edge)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            wolf_insight_instruction = ""
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # DEVELOPER GRAPH INSIGHT (Wolf 2.0)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if developer_insight:
                dev_name = developer_insight.get('developer', '')
                insight_text = developer_insight.get('insight_text', '')
                wolf_insight_instruction += f"""
[DEVELOPER GRAPH DATA - VERIFIED]
{insight_text}

IMPORTANT: Use this verified data to answer the user's question about {dev_name}.
Do NOT make up statistics. Use ONLY the numbers above.
Frame it as insider market intelligence: "My data shows..."
"""
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # REFLEXION CONTEXT (Search Pivot Explanation)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if hunt_strategy != 'direct_match' and pivot_message:
                # We had to pivot the search - inject explanation
                pivot_type_names = {
                    'location_pivot': 'Location Alternative',
                    'type_pivot': 'Property Type Alternative',
                    'budget_pivot': 'Budget Stretch',
                    'relaxed_search': 'Relaxed Criteria Match',
                    'any_area_search': 'Cross-Area Match',
                    'failed': 'No Match Found'
                }
                pivot_type = pivot_type_names.get(hunt_strategy, 'Alternative')
                
                wolf_insight_instruction += f"""
[REFLEXION: {pivot_type.upper()}]
IMPORTANT: The user's EXACT criteria returned zero results.
I used intelligent reasoning to find alternatives.
START your response with this explanation: "{pivot_message}"
Then present the alternatives as helpful suggestions, NOT as the user's original request.
"""
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # SMART DISPLAY STRATEGY CONTEXT
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if showing_strategy == 'ANALYTICS_ONLY':
                # ANALYTICS-FIRST MODE: Embed stats in TEXT, not just charts
                # Build a data brief string from analytics context
                data_brief_lines = []
                if analytics_context:
                    ac = analytics_context
                    loc_name = ac.get('location', '')
                    avg_p = ac.get('avg_price_sqm', 0)
                    growth = ac.get('growth_rate', 0)
                    ryield = ac.get('rental_yield', 0)
                    if avg_p > 0:
                        data_brief_lines.append(f"- متوسط سعر المتر في {loc_name}: {avg_p:,.0f} جنيه/م²" if language == 'ar' else f"- Avg price/sqm in {loc_name}: {avg_p:,.0f} EGP/m²")
                    if growth > 0:
                        pct = growth * 100 if growth < 1 else growth
                        data_brief_lines.append(f"- نسبة النمو السنوي: +{pct:.0f}%" if language == 'ar' else f"- YoY Growth: +{pct:.0f}%")
                    if ryield > 0:
                        ypct = ryield * 100 if ryield < 1 else ryield
                        data_brief_lines.append(f"- العائد الإيجاري: {ypct:.1f}%" if language == 'ar' else f"- Rental Yield: {ypct:.1f}%")
                    # Add area context details
                    area_ctx = ac.get('area_context', {})
                    if area_ctx.get('tier1_developers'):
                        devs = ', '.join(area_ctx['tier1_developers'][:4])
                        data_brief_lines.append(f"- أبرز المطورين: {devs}" if language == 'ar' else f"- Top developers: {devs}")
                    # Add economic data
                    econ = ac.get('economic_data', {})
                    if econ.get('inflation_rate'):
                        inf_val = econ['inflation_rate']
                        inf_pct = inf_val * 100 if inf_val < 1 else inf_val
                        data_brief_lines.append(f"- معدل التضخم: {inf_pct:.1f}%" if language == 'ar' else f"- Inflation rate: {inf_pct:.1f}%")
                    if econ.get('usd_egp'):
                        data_brief_lines.append(f"- سعر الدولار: {econ['usd_egp']:.2f} جنيه" if language == 'ar' else f"- USD/EGP: {econ['usd_egp']:.2f}")
                    if econ.get('bank_cd_rate'):
                        cd_val = econ['bank_cd_rate']
                        cd_pct = cd_val * 100 if cd_val < 1 else cd_val
                        data_brief_lines.append(f"- عائد شهادات البنك: {cd_pct:.0f}%" if language == 'ar' else f"- Bank CD rate: {cd_pct:.0f}%")

                data_brief = "\n".join(data_brief_lines) if data_brief_lines else ""

                if language == 'ar':
                    wolf_insight_instruction += f"""
[STRATEGY: ANALYTICS_FIRST]
أنت في وضع "المستشار البيانات" — أظهر ذكاءك بالأرقام:
1. لازم تكتب الأرقام دي في كلامك مباشرة (مش بس في الرسوم):
{data_brief}
2. قارن بين المناطق أو المطورين بالبيانات الحقيقية
3. لا تذكر أي وحدات أو عقارات محددة — بيانات فقط
4. اكتب الأرقام والإحصائيات كجزء أساسي من الرد مش مجرد إشارة للرسوم
5. اختم بسؤال استكشافي يساعدك تفهم احتياجاته أكتر
6. خلي المستخدم يحس إنه في جلسة استشارية خاصة مع خبير سوق
"""
                else:
                    wolf_insight_instruction += f"""
[STRATEGY: ANALYTICS_FIRST]
You are in DATA CONSULTANT mode — embed these numbers DIRECTLY in your text:
{data_brief}
1. WRITE these exact numbers in your response text (not just in charts)
2. Compare areas, developers, market segments with REAL data in your message
3. DO NOT mention any specific properties or units — data only
4. The statistics must appear in your text message, not hidden in visualizations
5. End with a strategic qualifying question to narrow their needs
6. Make them feel like they're getting a private market briefing from an insider
"""
            elif properties and showing_strategy == 'TEASER':
                # TEASER MODE: Show 1 anchor property to test price sensitivity
                anchor_price = properties[0].get('price', 0)
                anchor_location = properties[0].get('location', 'المنطقة')
                if language == 'ar':
                    wolf_insight_instruction += f"""
[STRATEGY: TEASER_ANCHOR]
أنت بتعرض وحدة واحدة بس كـ "مثال من السوق" لاختبار الميزانية.
لا تبيع الوحدة دي دلوقتي. استخدمها لتثبيت السعر.
قول: "مثلاً، ده متوسط سعر الوحدات في {anchor_location} ({anchor_price:,.0f} جنيه). ده في نطاق ميزانيتك؟"
بعد كده اسأل عن الميزانية المحددة عشان تقدر ترشح بدقة.
"""
                else:
                    wolf_insight_instruction += f"""
[STRATEGY: TEASER_ANCHOR]
You are showing ONLY ONE property as a "Market Example" to test their budget.
DO NOT sell this specific unit yet. Use it to anchor the price.
Say: "For example, this is what the average unit in {anchor_location} costs ({anchor_price:,.0f} EGP). Is this within your comfort zone?"
Then ask for their specific budget so you can recommend precisely.
"""
            elif properties and showing_strategy == 'FULL_LIST':
                # FULL MODE: Group properties and show them intelligently
                # Detect grouping mode: by developer (if area given) or by area (if no area)
                user_loc = (intent.filters.get("location", "") if intent else "").strip()
                has_user_area = bool(user_loc)

                # Build grouping summary for the AI
                if has_user_area:
                    # User chose an area → group by developer
                    dev_groups = {}
                    for p in properties:
                        dev = p.get("developer", "أخرى") or "أخرى"
                        dev_groups.setdefault(dev, []).append(p)
                    group_lines = []
                    for dev, props in dev_groups.items():
                        prices = [p.get('price', 0) for p in props if p.get('price')]
                        avg_p = sum(prices) / len(prices) if prices else 0
                        group_lines.append(f"  • {dev}: {len(props)} وحدة — متوسط {avg_p/1e6:.1f}M" if language == 'ar' else f"  • {dev}: {len(props)} units — avg {avg_p/1e6:.1f}M")
                    grouping_text = "\n".join(group_lines)

                    if language == 'ar':
                        wolf_insight_instruction += f"""
[STRATEGY: FULL_INVENTORY — مجمّعة حسب المطور]
أنت بتعرض أفضل الخيارات في {user_loc}. رتّب الوحدات حسب المطور:
{grouping_text}

لكل مطور: اذكر اسم المطور، عدد الوحدات المتاحة، ومتوسط السعر.
ركز على مقارنة المطورين ببعض: مين أرخص ومين أجود.
أختم بتوصية واضحة: "لو بتدور على أفضل قيمة، {dev_groups and list(dev_groups.keys())[0] or 'X'} هو الأنسب."
"""
                    else:
                        wolf_insight_instruction += f"""
[STRATEGY: FULL_INVENTORY — Grouped by Developer]
Showing best matches in {user_loc}. Present grouped by developer:
{grouping_text}

For each developer: mention name, available units, avg price.
Compare developers against each other: who's cheapest, who's best quality.
End with a clear recommendation.
"""
                else:
                    # No area chosen → group by area/location
                    area_groups = {}
                    for p in properties:
                        area = p.get("location", "غير محدد") or "غير محدد"
                        area_groups.setdefault(area, []).append(p)
                    group_lines = []
                    for area, props in area_groups.items():
                        prices = [p.get('price', 0) for p in props if p.get('price')]
                        avg_p = sum(prices) / len(prices) if prices else 0
                        group_lines.append(f"  • {area}: {len(props)} وحدة — متوسط {avg_p/1e6:.1f}M" if language == 'ar' else f"  • {area}: {len(props)} units — avg {avg_p/1e6:.1f}M")
                    grouping_text = "\n".join(group_lines)

                    if language == 'ar':
                        wolf_insight_instruction += f"""
[STRATEGY: FULL_INVENTORY — مجمّعة حسب المنطقة]
المستخدم محددش منطقة، فأنت بتعرض الفرص حسب المنطقة:
{grouping_text}

لكل منطقة: اذكر اسمها، عدد الوحدات المتاحة، ومتوسط السعر.
قارن المناطق ببعض: أسعار + نمو + عائد إيجاري.
أختم بسؤال: "حضرتك تفضل منطقة معينة ولا أختارلك الأنسب؟"
"""
                    else:
                        wolf_insight_instruction += f"""
[STRATEGY: FULL_INVENTORY — Grouped by Area]
User hasn't chosen an area. Present options grouped by location:
{grouping_text}

For each area: mention name, available units, avg price.
Compare areas: prices, growth, rental yield.
End with: "Do you prefer a specific area, or shall I pick the best value?"
"""
            
            # 0. Inject Economic Context (Always-On from Analytics Enrichment)
            if analytics_context and analytics_context.get("economic_brief"):
                wolf_insight_instruction += analytics_context["economic_brief"]

            # 1. Inject Live Market Pulse (Real-Time DB Data)
            # This overrides hardcoded assumptions with fresh data
            if market_pulse:
                wolf_insight_instruction += f"""
[LIVE MARKET DATA - FROM DATABASE]
- Location: {market_pulse['location']}
- Real Average Price: {market_pulse['avg_price_sqm']:,} EGP/sqm
- Active Inventory: {market_pulse['inventory_count']} listings
- Market Heat: {market_pulse['market_heat_index']}
"""

            if properties and len(properties) > 0:
                top_prop = properties[0]
                wolf_score = top_prop.get('wolf_score', 0)
                price_sqm = top_prop.get('price_per_sqm', 0)
                location = top_prop.get('location', '')
                
                # Fetch Real Market Average (The "Price Sandwich" Anchor)
                # Ensure we use the Live DB average if available, otherwise fallback
                area_avg = market_pulse['avg_price_sqm'] if market_pulse else market_intelligence.get_avg_price_per_sqm(location)
                if area_avg == 0:
                     area_avg = top_prop.get('wolf_benchmark', {}).get('market_avg', 0)

                # Inject Benchmarking Protocol (The Sandwich)
                wolf_insight_instruction += f"""
[BENCHMARKING_PROTOCOL]
- The Market Average Price in {location} is: **{area_avg:,.0f} EGP/sqm**
- The Property you are recommending is: **{price_sqm:,.0f} EGP/sqm**

MANDATORY INSTRUCTION:
You MUST compare these two numbers to justify the value.
- If property < market: "This is entering at {price_sqm:,.0f} vs market average of {area_avg:,.0f}. That is instant equity."
- If property > market: "It is above market average ({area_avg:,.0f}) because it is a Premium Class A asset."
"""
                
                # Logic to force the AI to be "Remarkable" (Market Anomaly)
                if wolf_score > 85:
                    
                    if language == 'ar':
                         wolf_insight_instruction += f"""
[MANDATORY OPENER]
You MUST start your response with this EXACT sentence (in Egyptian Arabic):
"🐺 أنا لقيت لقطة في السوق. الوحدة دي سعر مترها {price_sqm:,.0f} جنيه، في حين إن متوسط المنطقة {area_avg:,.0f} جنيه."
"""
                    else:
                         wolf_insight_instruction += f"""
[MANDATORY OPENER]
You MUST start your response with this EXACT sentence:
"🐺 I found a market anomaly. This unit is priced at {price_sqm:,.0f} EGP/sqm, while the area average is {area_avg:,.0f} EGP/sqm."
"""
            
            if psychology.primary_state == PsychologicalState.RISK_AVERSE:
                 if language == 'ar':
                     wolf_insight_instruction += f"""
[MANDATORY OPENER]
Start with: "أنا عملت فحص (Law 114) على المطور ده. معندوش أي تأخيرات في التسليم آخر 5 سنين."
"""
                 else:
                     wolf_insight_instruction += f"""
[MANDATORY OPENER]
Start with: "I've run the Law 114 check on this developer. They have 0 recorded delivery delays in the last 5 years."
"""

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # PROTOCOL E: SKEPTICISM DESTROYER (Data Anchoring)
            # When user doubts "Is this real?" or "Is it a good time?"
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            skepticism_keywords = [
                "حقيقي", "ده صحيح", "هل ده", "وقت مناسب", "أصدق", "مضمون",
                "is this real", "good time to buy", "are these numbers real", 
                "can i trust", "is it safe", "should i believe"
            ]
            is_skeptical = any(kw in query.lower() for kw in skepticism_keywords)
            
            if is_skeptical or psychology.primary_state == PsychologicalState.SKEPTICISM:
                # Get area-specific growth rate from market pulse or default
                growth_rate = 18  # Default: New Cairo average
                if market_pulse:
                    growth_rate = market_pulse.get('growth_rate', 18)
                elif intent and intent.filters.get('location'):
                    # Try to get from AREA_GROWTH
                    location = intent.filters.get('location', '')
                    from .analytical_engine import AREA_GROWTH
                    for area, rate in AREA_GROWTH.items():
                        if area.lower() in location.lower() or location.lower() in area.lower():
                            growth_rate = int(rate * 100)
                            break
                
                # Economic constants (from canonical MARKET_DATA)
                from .analytical_engine import MARKET_DATA as _mdata
                inflation_rate = int(_mdata["inflation_rate"] * 100)    # 13.6 → 14
                bank_rate = int(_mdata["bank_cd_rate"] * 100)            # 22
                negative_yield = inflation_rate - bank_rate  # Negative means bank loses to inflation
                
                wolf_insight_instruction += f"""
[PROTOCOL_E_SKEPTICISM_DESTROYER_ACTIVATED]
The user is questioning the market data. You MUST:
1. DROP the sales pitch immediately
2. Switch to "auditor" mode
3. Use these EXACT numbers:
   - GROWTH_RATE: {growth_rate}%
   - INFLATION_RATE: {inflation_rate}%
   - BANK_RATE: {bank_rate}%
   - NEGATIVE_YIELD: {negative_yield}%

MANDATORY RESPONSE PATTERN:
Start with: "سؤال ممتاز. سيبك من كلام البيع وخلينا نتكلم بالأرقام..."
Then use the Inflation vs Bank equation to prove your point.
End with: "تحب أوريك الرسم البياني للمقارنة دي؟"
"""

            # Build context for Claude
            context_parts = []
            
            # Inject the insight instruction first
            if wolf_insight_instruction:
                context_parts.append(wolf_insight_instruction)
            
            # Discovery phase context - provide market insights with REAL DATA
            if is_discovery:
                location = intent.filters.get('location', '') if intent else ''
                
                # Get market segment data (Class A vs Class B)
                segment_data = market_intelligence.get_market_segment(location) if location else None
                
                if segment_data and segment_data.get('found'):
                    ar_name = segment_data.get('name_ar', location)
                    
                    # Class A developer data
                    class_a = segment_data.get('class_a', {})
                    class_a_devs = class_a.get('developers_ar', [])
                    class_a_avg = class_a.get('avg_price', 0) / 1_000_000
                    class_a_min = class_a.get('min_price', 0) / 1_000_000
                    class_a_max = class_a.get('max_price', 0) / 1_000_000
                    
                    # Class B developer data
                    class_b = segment_data.get('class_b', {})
                    class_b_devs = class_b.get('developers_ar', [])
                    class_b_min = class_b.get('min_price', 0) / 1_000_000
                    class_b_max = class_b.get('max_price', 0) / 1_000_000
                    
                    # Market floor/ceiling
                    market_floor = segment_data.get('market_floor', 0) / 1_000_000
                    market_ceiling = segment_data.get('market_ceiling', 0) / 1_000_000
                    
                    # Format developer lists
                    class_a_devs_str = '، '.join(class_a_devs[:3]) if class_a_devs else 'إعمار، سوديك، مراكز'
                    class_b_devs_str = '، '.join(class_b_devs[:3]) if class_b_devs else 'ماونتن فيو، بالم هيلز، صبور'
                    
                    context_parts.append(f"""
[MARKET_EDUCATION_PROTOCOL]
The user asked about: {ar_name}

DO NOT ask for budget yet. EDUCATE them first using this EXACT script:

══════════════════════════════════════════════════════
ARABIC SCRIPT (USE THIS EXACT FORMAT):
══════════════════════════════════════════════════════

"اهلا بيك في اصول!

متوسط أسعار الشقق في {ar_name} للغرفتين والصالة من أول {market_floor:.0f} مليون إلى {market_ceiling:.0f} مليون.
وده بيختلف حسب المطور والموقع:

1️⃣ **مطورين الفئة الأولى (Class A)** زي {class_a_devs_str}...
الشقة دي بتوصل لـ {class_a_avg:.0f} مليون.

2️⃣ **مطورين الفئة الثانية (Class B)** زي {class_b_devs_str}...
والسعر بيبدأ من {class_b_min:.0f} مليون لغاية {class_b_max:.0f} مليون.

تحب نشوف شقة في متوسط معين ولا لمطور معين؟"

══════════════════════════════════════════════════════
ENGLISH SCRIPT (if user speaks English):
══════════════════════════════════════════════════════

"Welcome to Osool!

Average 2-bedroom apartments in {segment_data.get('name_en', location)} range from {market_floor:.0f}M to {market_ceiling:.0f}M EGP.
This varies by developer and location:

1️⃣ **Tier 1 Developers** ({class_a_devs_str}) - apartments reach {class_a_avg:.0f}M.
2️⃣ **Tier 2 Developers** ({class_b_devs_str}) - prices from {class_b_min:.0f}M to {class_b_max:.0f}M.

Would you like to explore a specific price range or a specific developer?"

══════════════════════════════════════════════════════
CRITICAL RULES:
1. DO NOT ask "what's your budget?" directly - the education REPLACES that question
2. The question at the end forces them to self-categorize
3. Use ONLY the numbers provided above - no made-up prices
4. DO NOT show property cards yet
══════════════════════════════════════════════════════
""")
                else:
                    # Generic discovery for unknown area
                    context_parts.append(f"""
[DISCOVERY_PHASE]
The user asked about: {location if location else 'unspecified area'}

Provide general market context and ask:
1. Which specific area interests them
2. Budget range
3. Residence or investment purpose

Be welcoming: "اهلا بيك! خليني أفهم احتياجاتك..."
""")
            
            if feasibility and not feasibility.is_feasible:
                context_parts.append(f"""
[REALITY_CHECK - CRITICAL]
The user's request is NOT FEASIBLE given market realities!

{feasibility.message_ar}

Use the **Universal Response Protocol** Part 2 (Market Context) to explain why:
"السوق دلوقتي بدأ من X... الانتظار هيخسرك..."

ALTERNATIVES TO OFFER:

ALTERNATIVES TO OFFER:
{chr(10).join('- ' + alt.get('message_ar', '') for alt in feasibility.alternatives[:3])}

YOUR APPROACH:
1. Be TRANSPARENT but TACTFUL: "خليني أكون صريح معاك..."
2. Show you are PROTECTING them from wasted time
3. Pivot to realistic alternatives they CAN afford
4. Frame it as insider knowledge: "السوق دلوقتي الشقق في..."
""")
            
            # Property context with wolf benchmarking (only when not in discovery)
            if properties:
                context_parts.append(self._format_property_context(properties))

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # DATABASE STATISTICS INJECTION (Phase 5C)
            # Reuse existing db_session to avoid creating extra connections
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                from app.services.market_statistics import compute_detailed_qa_statistics, format_qa_stats_for_ai
                if db_session:
                    qa_stats = await compute_detailed_qa_statistics(db_session)
                    qa_stats_text = format_qa_stats_for_ai(qa_stats)
                    if qa_stats_text:
                        context_parts.append(f"\n[LIVE_DATABASE_STATISTICS]\n{qa_stats_text}\nUse ONLY these numbers. Never invent statistics.\n")
            except Exception as e:
                logger.warning(f"Could not inject QA stats: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # INTELLIGENCE: Family Housing Detection (Phase 6B)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            family_kws = ["سكن عائلي", "عيلة", "عائلي", "family", "أطفال", "kids", "سكن"]
            is_family = any(kw in query.lower() for kw in family_kws)
            if is_family or (intent and intent.filters.get("purpose") == "living"):
                context_parts.append("""
[FAMILY_HOUSING_INTELLIGENCE]
User is looking for family housing. Apply these rules:
- Minimum 3 bedrooms for families (suggest upgrading if they asked for 2)
- Prioritize compounds (أمان، خدمات، مساحات خضراء)
- Mention school proximity, medical facilities, and community features
- Use emotional language: "المكان ده هينفع عيلتك" / "This is perfect for your family"
""")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # INTELLIGENCE: Capital Preservation Psychology (Phase 6C)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            capital_kws = ["حافظ", "أمان", "آمن", "safe", "preserve", "protect", "ضمان", "مضمون"]
            is_capital = any(kw in query.lower() for kw in capital_kws)
            if is_capital or psychology.primary_state == PsychologicalState.RISK_AVERSE:
                context_parts.append("""
[CAPITAL_PRESERVATION_PSYCHOLOGY]
User cares about SAFETY of their capital. Apply:
- Lead with Tier 1 developers (delivery guarantee, resale premium)
- Mention Law 114 protection immediately
- Use replacement cost argument: "سعر الوحدة أقل من تكلفة بناءها"
- Frame property as inflation hedge, not speculation
- Highlight compound security features
""")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # INTELLIGENCE: FOMO Triggers for Hot Markets (Phase 6D)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            hot_markets = ["new cairo", "التجمع", "6th october", "أكتوبر", "zayed", "زايد", "mostakbal", "المستقبل"]
            user_location = (intent.filters.get("location", "") if intent else "").lower()
            is_hot_market = any(hm in user_location for hm in hot_markets)
            if is_hot_market and properties:
                avg_price = sum(p.get('price', 0) for p in properties) / len(properties)
                context_parts.append(f"""
[FOMO_TRIGGER - HOT MARKET]
This area is experiencing HIGH demand. Use scarcity tactics:
- "المنطقة دي الأسعار فيها بتزيد كل شهر" (Prices increase monthly)
- "الوحدات المتاحة بالسعر ده مش هتلاقيها بعد كام شهر"
- Mention average price ({avg_price/1e6:.1f}M) as benchmark
- Create urgency WITHOUT lying about availability
""")
                
                # Add wolf analysis for each property
                wolf_verdicts = []
                for i, prop in enumerate(properties[:5]):
                    benchmark = prop.get("wolf_benchmark", {})
                    wolf_analysis = prop.get("wolf_analysis", "FAIR_VALUE")
                    verdict = benchmark.get("verdict_ar", "")
                    
                    if wolf_analysis == "BARGAIN_DEAL":
                        wolf_verdicts.append(f"🔥 العقار #{i+1}: {verdict}")
                    elif wolf_analysis == "PREMIUM":
                        wolf_verdicts.append(f"💎 العقار #{i+1}: {verdict}")
                    elif wolf_analysis == "OVERPRICED":
                        wolf_verdicts.append(f"⚠️ العقار #{i+1}: {verdict}")
                
                if wolf_verdicts:
                    context_parts.append(f"""
[WOLF_VALUE_ANCHORING]
For each property, you MUST mention its value vs market:
{chr(10).join(wolf_verdicts)}

Use phrases like:
- "ده أقل من السوق بـ X%" (This is X% below market)
- "ده Premium بس المكان يستاهل" (Premium but location justifies)
""")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V2 ENHANCEMENT: SOCIAL PROOF ENGINE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                sp_location = (intent.filters.get('location', '') if intent else '') or (memory.preferred_areas[0] if memory and memory.preferred_areas else '')
                if sp_location:
                    social_signals = await social_proof_engine.get_social_signals(sp_location, db_session=db_session)
                    sp_context = social_proof_engine.format_for_prompt(social_signals, language)
                    if sp_context:
                        context_parts.append(sp_context)
                    scarcity_msg = social_proof_engine.get_scarcity_signal(social_signals, language)
                    if scarcity_msg:
                        context_parts.append(f"\n[SCARCITY_SIGNAL]\n{scarcity_msg}\n")
            except Exception as e:
                logger.debug(f"Social proof injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: COMMUNITY SELL (Family-Focused Lifestyle Data)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                _community_states = (PsychologicalState.FAMILY_SECURITY, PsychologicalState.SOCIAL_PRESSURE,
                                     PsychologicalState.LIFE_EVENT_URGENCY)
                if psychology.primary_state in _community_states or (hasattr(psychology, 'buyer_persona') and psychology.buyer_persona and psychology.buyer_persona.value == "end_user"):
                    _cs_compound = ""
                    _cs_location = (intent.filters.get('location', '') if intent else '') or (memory.preferred_areas[0] if memory and memory.preferred_areas else '')
                    if properties:
                        _cs_compound = properties[0].get('compound', properties[0].get('project_name', ''))
                    cs_ctx = community_sell_engine.get_community_context(compound_name=_cs_compound, location=_cs_location, language=language)
                    if cs_ctx:
                        context_parts.append(cs_ctx)
                        logger.info(f"🏘️ Community Sell injected (compound={_cs_compound or _cs_location})")
            except Exception as e:
                logger.debug(f"Community Sell injection skipped: {e}")
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                fc_location = (intent.filters.get('location', '') if intent else '') or (memory.preferred_areas[0] if memory and memory.preferred_areas else '')
                fc_budget = intent.filters.get('budget_max', 0) if intent else 0
                if fc_location and psychology.decision_stage in (DecisionStage.RESEARCH, DecisionStage.CONSIDERATION, DecisionStage.DECISION):
                    erosion = fear_clock.calculate_daily_erosion(budget=fc_budget or 5_000_000, location=fc_location)
                    if erosion:
                        fc_context = fear_clock.format_for_prompt(erosion, language)
                        if fc_context:
                            context_parts.append(fc_context)
            except Exception as e:
                logger.debug(f"Fear clock injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V2 ENHANCEMENT: PAYMENT PLAN CALCULATOR
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                pp_bucket = intent.intent_bucket if intent else ""
                if pp_bucket == "installment_inquiry" or (properties and memory and memory.preferred_payment):
                    pp_price = properties[0].get('price', 0) if properties else (memory.budget_range.get('max', 5_000_000) if memory and memory.budget_range else 5_000_000)
                    pp_location = (intent.filters.get('location', '') if intent else '') or (memory.preferred_areas[0] if memory and memory.preferred_areas else '')
                    pp_result = payment_plan_analyzer.calculate_installment_plan(total_price=pp_price, location=pp_location)
                    pp_context = payment_plan_analyzer.format_for_prompt(pp_result, language)
                    if pp_context:
                        context_parts.append(pp_context)
                        # V3: Installment Inflation Gift — show how installments get cheaper
                        if psychology.primary_state == PsychologicalState.INSTALLMENT_ANXIETY or pp_bucket == "installment_inquiry":
                            _monthly = pp_result.get('monthly_installment', 0)
                            _years = pp_result.get('plan_years', 7)
                            if _monthly > 0:
                                ig_result = fear_clock.calculate_installment_deflation(_monthly, _years)
                                ig_ctx = fear_clock.format_installment_gift_for_prompt(ig_result, language)
                                if ig_ctx:
                                    context_parts.append(ig_ctx)
                                    logger.info(f"🎁 Installment Inflation Gift injected ({_monthly:,}/mo × {_years}y)")
            except Exception as e:
                logger.debug(f"Payment plan injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V2 ENHANCEMENT: DEVELOPER TRUST SCORE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                dt_bucket = intent.intent_bucket if intent else ""
                # V3: Widened trigger — fire when showing properties with a developer, not just on explicit inquiry
                dt_should_fire = (
                    dt_bucket == "developer_inquiry"
                    or psychology.primary_state == PsychologicalState.DELIVERY_FEAR
                    or psychology.primary_state == PsychologicalState.TRUST_DEFICIT
                    or (properties and showing_strategy in ('TEASER', 'FULL_LIST'))
                )
                if dt_should_fire:
                    dt_dev = intent.filters.get('developer', '') if intent else ''
                    if not dt_dev and properties:
                        dt_dev = properties[0].get('developer', '')
                    if dt_dev:
                        trust_result = developer_trust_scorer.calculate_trust_score(dt_dev)
                        trust_context = developer_trust_scorer.format_for_prompt(trust_result, language)
                        if trust_context:
                            context_parts.append(trust_context)
            except Exception as e:
                logger.debug(f"Developer trust injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V2 ENHANCEMENT: RESALE INTELLIGENCE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                ri_bucket = intent.intent_bucket if intent else ""
                if ri_bucket == "resale_inquiry" or (intent and intent.action == "investment"):
                    ri_price = properties[0].get('price', 0) if properties else 5_000_000
                    ri_dev = properties[0].get('developer', '') if properties else ''
                    ri_loc = intent.filters.get('location', '') if intent else ''
                    ri_result = resale_intelligence.calculate_resale_projection(developer=ri_dev, total_price=ri_price)
                    ri_context = resale_intelligence.format_for_prompt(ri_result, language)
                    if ri_context:
                        context_parts.append(ri_context)
            except Exception as e:
                logger.debug(f"Resale intelligence injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: TRADE-UP CALCULATOR
            # For inheritance/upgrade users: current property + cash → what to buy
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                _tu_states = (PsychologicalState.INHERITANCE_CONFUSION, PsychologicalState.DOWNGRADE_SHAME)
                _tu_persona = getattr(psychology, 'buyer_persona', None)
                _tu_is_upgrader = _tu_persona and _tu_persona.value in ("upgrader", "portfolio")
                if psychology.primary_state in _tu_states or _tu_is_upgrader:
                    _tu_location = (intent.filters.get('location', '') if intent else '') or (memory.preferred_areas[0] if memory and memory.preferred_areas else '')
                    _tu_budget = (intent.filters.get('budget_max', 0) if intent else 0) or (memory.budget_range.get('max', 5_000_000) if memory and memory.budget_range else 5_000_000)
                    _tu_result = trade_up_advisor.calculate_trade_up(
                        cash_available=_tu_budget,
                        target_location=_tu_location or "New Cairo",
                    )
                    _tu_ctx = trade_up_advisor.format_for_prompt(_tu_result, language)
                    if _tu_ctx:
                        context_parts.append(_tu_ctx)
                        logger.info(f"📊 Trade-Up Calculator injected (budget={_tu_budget:,})")
            except Exception as e:
                logger.debug(f"Trade-Up Calculator skipped: {e}")
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            response_length_hint = _get_response_length_instruction(psychology, memory)
            if response_length_hint:
                context_parts.append(response_length_hint)

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V2 ENHANCEMENT: MICRO-COMMITMENT + CLOSING SEQUENCE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                commitment = _calculate_commitment_from_memory(memory, intent)
                memory.commitment_level = commitment
                closing_ctx = _get_closing_sequence_context(commitment, language)
                if closing_ctx:
                    context_parts.append(closing_ctx)
                    logger.info(f"🎯 Commitment: {commitment}/100, Closing sequence injected")
            except Exception as e:
                logger.debug(f"Closing sequence injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: TWO-UNIT TRAP (Forced Choice Close)
            # When showing ≥3 properties + commitment ≥50, narrow to 2 best
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                _commitment = memory.commitment_level if memory else 0
                if (showing_strategy == 'FULL_LIST' and _commitment >= 50
                        and properties and len(properties) >= 3):
                    # Keep only top 2 by Osool Score — force binary choice
                    properties = sorted(properties, key=lambda p: p.get('osool_score', p.get('score', 0)), reverse=True)[:2]
                    if language == "ar":
                        context_parts.append("""
[TWO_UNIT_TRAP — استراتيجية الاختيار بين اثنين]
أنت بتعرض وحدتين بس. استخدم "أنت مع أنهي واحدة؟" لا تعرض خيار ثالث.
- قارن بينهم بشكل مباشر: المساحة، السعر، الموقع، العائد
- اسأل: "الوحدة A ولا الوحدة B؟ أنا شايف إن B أحسن ليك عشان..."
- الهدف: تحويل القرار من "هشتري ولا لأ" ل "هشتري أنهي"
""")
                    else:
                        context_parts.append("""
[TWO_UNIT_TRAP — Binary Choice Strategy]
You are showing EXACTLY 2 units. Use "Which one are you leaning towards?" Do NOT offer a third option.
- Compare them directly: size, price, location, ROI
- Ask: "Unit A or Unit B? I think B suits you better because..."
- Goal: Shift from "should I buy?" to "which should I buy?"
""")
                    logger.info(f"🎯 Two-Unit Trap activated (commitment={_commitment}, narrowed to 2)")
            except Exception as e:
                logger.debug(f"Two-Unit Trap skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: VIEWING CLOSE PROTOCOL
            # Push towards a specific viewing appointment within 48h
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                _intent_bucket = intent.intent_bucket if hasattr(intent, 'intent_bucket') else ""
                _visit_scheduled = memory.visit_scheduled if memory else False
                _commitment_vc = memory.commitment_level if memory else 0
                _viewing_keywords = ["معاينة", "أشوف", "أزور", "viewing", "visit", "see the unit", "زيارة", "نشوف"]
                _wants_viewing = any(kw in query.lower() for kw in _viewing_keywords)

                if (_wants_viewing or _intent_bucket == "closing_intent" or _commitment_vc >= 65) and not _visit_scheduled:
                    # Calculate next 2 available viewing slots
                    from datetime import timedelta
                    _now = datetime.now()
                    _slot_1 = _now + timedelta(days=1)
                    _slot_2 = _now + timedelta(days=2)
                    _day1 = _slot_1.strftime("%A")
                    _day2 = _slot_2.strftime("%A")

                    if language == "ar":
                        _day_map = {"Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين",
                                    "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", "Thursday": "الخميس", "Friday": "الجمعة"}
                        context_parts.append(f"""
[VIEWING_CLOSE — حجز معاينة]
العميل مستعد — ادفعه ناحية معاينة محددة:
- اقترح: "إيه رأيك نحجز معاينة يوم {_day_map.get(_day1, _day1)} أو {_day_map.get(_day2, _day2)}؟"
- NEVER say "في أي وقت يناسبك" — حدد وقت: "الساعة 11 الصبح أو 4 العصر"
- لو قال "هفكر" — رد: "طب خلينا نحجز مبدئي ولو عايز تلغي عندك وقت"
- الهدف: تحويل الاهتمام ل commitment حقيقي بتاريخ ووقت
""")
                    else:
                        context_parts.append(f"""
[VIEWING_CLOSE — Schedule Viewing]
Client is ready — push towards a specific viewing:
- Suggest: "How about we schedule a viewing on {_day1} or {_day2}?"
- NEVER say "whenever suits you" — offer specific times: "11 AM or 4 PM"
- If they say "I'll think" — respond: "Let's book tentatively, you can cancel anytime"
- Goal: Convert interest into real commitment with date and time
""")
                    logger.info(f"📅 Viewing Close activated (commitment={_commitment_vc})")
            except Exception as e:
                logger.debug(f"Viewing Close skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                family_ctx = _get_family_committee_context(query, memory, language)
                if family_ctx:
                    context_parts.append(family_ctx)
                    logger.info("👨‍👩‍👧‍👦 Family Committee Mode activated")
            except Exception as e:
                logger.debug(f"Family mode injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: OBJECTION RESOLUTION TRACKER CONTEXT
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                obj_ctx = objection_tracker.get_prompt_context(language)
                if obj_ctx:
                    context_parts.append(obj_ctx)
            except Exception as e:
                logger.debug(f"Objection tracker context skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: OBJECTION PRE-EMPTION ENGINE
            # Predict top 2 likely objections BEFORE user raises them
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                _pre_empt = _predict_objections(psychology, memory, intent, properties if 'properties' in dir() else [])
                if _pre_empt:
                    if language == "ar":
                        pe_lines = ["[PRE_EMPT_OBJECTIONS — اعتراضات متوقعة: عالجها قبل ما العميل يسأل]"]
                        for obj in _pre_empt:
                            pe_lines.append(f"• {obj['type']}: {obj['counter_ar']}")
                        pe_lines.append("STRATEGY: أدخل الرد بشكل طبيعي — 'أنا عارف ممكن يكون في بالك...'")
                    else:
                        pe_lines = ["[PRE_EMPT_OBJECTIONS — Predicted objections: address before user asks]"]
                        for obj in _pre_empt:
                            pe_lines.append(f"• {obj['type']}: {obj['counter_en']}")
                        pe_lines.append("STRATEGY: Weave naturally — 'I know you might be thinking...'")
                    context_parts.append("\n".join(pe_lines))
                    logger.info(f"🛡️ Pre-emption: {[o['type'] for o in _pre_empt]}")
            except Exception as e:
                logger.debug(f"Objection pre-emption skipped: {e}")
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                if cross_session_context and len(history) <= 1:
                    # Only inject on first turn of a returning user's session
                    ret_type = cross_session_context["return_type"]
                    ret_msg = cross_session_context.get(f"message_{language}", cross_session_context.get("message_en", ""))
                    ret_hint = cross_session_context.get("strategy_hint", "")
                    sessions = cross_session_context.get("sessions_count", 0)
                    context_parts.append(f"""
[RETURN_VISITOR]
Return Type: {ret_type} (session #{sessions + 1})
Suggested Greeting: {ret_msg}
Strategy Hint: {ret_hint}
- Reference previous conversation if possible
- Do NOT restart discovery from scratch
- For hot_return: Push towards closing
- For comparison_return: Differentiate against competitors
- For cold_return: Re-engage gently, offer market update
""")
                    logger.info(f"🔄 Return visitor context injected: {ret_type}")
            except Exception as e:
                logger.debug(f"Return visitor context skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3 ENHANCEMENT: WAITING COST (Fear Clock Extension)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                _need_time_keywords = ["محتاج أفكر", "هفكر", "need time", "later", "maybe", "مش متأكد", "not sure", "بكرة", "tomorrow"]
                _is_stalling = any(kw in query.lower() for kw in _need_time_keywords)
                if _is_stalling:
                    wc_location = (intent.filters.get('location', '') if intent else '') or (memory.preferred_areas[0] if memory.preferred_areas else '')
                    wc_budget = (intent.filters.get('budget_max', 0) if intent else 0) or (memory.budget_range.get('max', 5_000_000) if memory.budget_range else 5_000_000)
                    if wc_location and wc_budget:
                        for wait_m in [1, 3, 6]:
                            wc_result = fear_clock.calculate_waiting_cost(wc_budget, wc_location, wait_m)
                            if wc_result.get("available"):
                                if language == "ar":
                                    context_parts.append(f"""
[WAITING_COST — {wait_m} شهور]
⏳ لو استنيت {wait_m} شهور:
- سعر المتر هيزيد من {wc_result['price_today']:,} ل {wc_result['price_after']:,} جنيه
- هتقدر تشتري {wc_result['sqm_after']:.0f} متر بدل {wc_result['sqm_today']:.0f} (خسارة {wc_result['sqm_lost']:.0f} متر²)
- خسارة مالية تعادل: {wc_result['equivalent_money_lost']:,} جنيه
USE: "لو استنيت {wait_m} شهور بس، هتدفع {wc_result['equivalent_money_lost']:,} جنيه زيادة على نفس الشقة"
""")
                                else:
                                    context_parts.append(f"""
[WAITING_COST — {wait_m} months]
⏳ If you wait {wait_m} months:
- Price/sqm rises from {wc_result['price_today']:,} to {wc_result['price_after']:,} EGP
- You can buy {wc_result['sqm_after']:.0f} sqm instead of {wc_result['sqm_today']:.0f} ({wc_result['sqm_lost']:.0f} sqm lost)
- Equivalent money lost: {wc_result['equivalent_money_lost']:,} EGP
USE: "Waiting just {wait_m} months would cost you {wc_result['equivalent_money_lost']:,} EGP more for the same unit"
""")
                        logger.info("⏳ Waiting cost calculator injected (user stalling)")
            except Exception as e:
                logger.debug(f"Waiting cost injection skipped: {e}")

            # Psychology context
            context_parts.append(get_psychology_context_for_prompt(psychology))
            
            # Strategy context
            context_parts.append(f"""
[STRATEGY: {strategy['strategy'].upper()}]
Angle: {strategy['angle']}
Momentum: {strategy.get('emotional_momentum', 'static')}
Objection: {strategy.get('specific_objection', 'none')}
Primary Message: {strategy['primary_message']}
Key Points: {', '.join(strategy['talking_points'][:3])}
""")
            
            # UI Actions context (tell Claude what visuals are showing)
            if ui_actions:
                visual_hints = []
                for action in ui_actions:
                    if action['type'] == 'certificates_vs_property':
                        visual_hints.append("📊 Inflation chart is visible - reference it")
                    elif action['type'] == 'bank_vs_property':
                        visual_hints.append("📊 Bank comparison chart is visible - reference it")
                    elif action['type'] == 'la2ta_alert':
                        visual_hints.append("🔥 Bargain alert is visible - highlight it")
                
                if visual_hints:
                    context_parts.append(f"""
[VISUAL_INTEGRATION]
The following visualizations are being shown to the user:
{chr(10).join('- ' + h for h in visual_hints)}

Reference these in your response:
- "بص على الشاشة دلوقتي..." (Look at the screen now...)
- "الرسم البياني ده بيوضح..." (This chart shows...)
""")
            
            # User personalization
            user_name = profile.get('first_name') if profile else None
            if user_name:
                context_parts.append(f"""
[USER]
Name: {user_name}
Address them occasionally: "يا {user_name}" or "{user_name}، خليني أقولك..."
""")
            
            # No Discount Protocol Injection
            if no_discount_mode:
                context_parts.append("""
[PRICE_INTEGRITY_PROTOCOL - CRITICAL]
The user may be fishing for a discount or negotiation.
RULE 1: NEVER offer a discount.
RULE 2: NEVER apologize for the price.
RULE 3: Pivot to the "Takeaway Close":
   "This unit is priced for value. If this budget is tight, we can look at a smaller unit or a different location (downgrade), but I cannot touch the price of THIS asset."
RULE 4: Anchor the price to the ROI: "You are not spending X, you are securing an asset that grows Y% annually."
""")

            # Inject conversation memory summary (budget, areas, purpose, objections)
            if memory:
                memory_summary = memory.get_context_summary()
                if memory_summary:
                    context_parts.append(f"\n{memory_summary}\n")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V5: USER INTELLIGENCE DOSSIER — Wire memory into Claude context
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                dossier_parts = []
                mem_dict = memory.to_dict() if memory else {}

                user_name = mem_dict.get("user_name") or (profile.get("name") if profile else None)
                budget_range = mem_dict.get("budget_range", {})
                areas = mem_dict.get("preferred_areas", [])
                purpose = mem_dict.get("investment_vs_living")
                objections = mem_dict.get("objections_raised", [])
                liked = mem_dict.get("liked_properties", [])
                family = mem_dict.get("family_members_mentioned", [])
                payment = mem_dict.get("preferred_payment", {})
                competitors = mem_dict.get("competitors_mentioned", [])
                commitment = mem_dict.get("commitment_level", 0)

                has_data = any([user_name, budget_range.get("min") or budget_range.get("max"),
                               areas, purpose, objections, liked, family])

                if has_data:
                    dossier_parts.append("\n═══════════════════════════════════════")
                    dossier_parts.append("🕵️ USER INTELLIGENCE DOSSIER")
                    dossier_parts.append("═══════════════════════════════════════")
                    if user_name:
                        dossier_parts.append(f"👤 Name: {user_name}")
                    if budget_range.get("min") or budget_range.get("max"):
                        bmin = budget_range.get("min", 0) / 1_000_000
                        bmax = budget_range.get("max", 0) / 1_000_000
                        if bmin > 0 and bmax > 0:
                            dossier_parts.append(f"💰 Budget: {bmin:.1f}M - {bmax:.1f}M EGP")
                        elif bmax > 0:
                            dossier_parts.append(f"💰 Budget: Up to {bmax:.1f}M EGP")
                    if areas:
                        dossier_parts.append(f"📍 Preferred Areas: {', '.join(areas)}")
                    if purpose:
                        dossier_parts.append(f"🏠 Purpose: {purpose}")
                    if family:
                        dossier_parts.append(f"👨‍👩‍👧 Family: {', '.join(family)}")
                    if liked:
                        dossier_parts.append(f"❤️ Liked: {', '.join(liked)}")
                    if objections:
                        dossier_parts.append(f"⚠️ Objections raised: {', '.join(objections)}")
                    if competitors:
                        dossier_parts.append(f"🔄 Compared to: {', '.join(competitors)}")
                    if payment:
                        dp = payment.get("down_pct", "?")
                        yrs = payment.get("years", "?")
                        dossier_parts.append(f"💳 Payment pref: {dp}% down, {yrs}yr")
                    if commitment > 0:
                        dossier_parts.append(f"📊 Commitment: {commitment}/100")
                    dossier_parts.append("═══════════════════════════════════════")
                    dossier_parts.append("RULES: Address by name. Never re-ask known info.")
                    dossier_parts.append("Never suggest what contradicts their objections.")
                    dossier_parts.append("═══════════════════════════════════════")
                    context_parts.append("\n".join(dossier_parts))
            except Exception as e:
                logger.debug(f"User Dossier injection skipped: {e}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # V3: CHAIN-OF-THOUGHT REASONING INJECTION
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if reasoning_chain and reasoning_chain.steps:
                cot_prompt = reasoning_engine.generate_reasoning_prompt(reasoning_chain, language)
                if cot_prompt:
                    context_parts.append(cot_prompt)

            # V3: Psychology Chain-of-Thought injection
            if hasattr(psychology, 'thought_chain') and psychology.thought_chain:
                psy_cot = "\n[PSYCHOLOGY_CHAIN_OF_THOUGHT]"
                for i, t in enumerate(psychology.thought_chain, 1):
                    psy_cot += f"\nStep {i}: {t.observation} → {t.action}"
                if hasattr(psychology, 'buyer_persona') and psychology.buyer_persona.value != "unknown":
                    psy_cot += f"\nBUYER PERSONA: {psychology.buyer_persona.value}"
                if hasattr(psychology, 'decision_stage'):
                    psy_cot += f"\nDECISION STAGE: {psychology.decision_stage.value}"
                context_parts.append(psy_cot)

            # Build system prompt
            system_prompt = get_wolf_system_prompt() + "\n\n" + "\n".join(context_parts)
            
            # Price validation override
            if properties:
                prices = [p.get('price', 0) for p in properties]
                min_price = min(prices)
                max_price = max(prices)
                system_prompt += f"""

[PRICE_VALIDATION]
Actual price range in results: {min_price:,} - {max_price:,} EGP
DO NOT mention any prices outside this range.
"""
            
            # Language enforcement
            if language == "ar":
                system_prompt += "\n\nIMPORTANT: Reply in Egyptian Arabic (عامية مصرية محترفة)."
            
            # Convert history
            messages = []
            for msg in history[-30:]:
                if isinstance(msg, dict):
                    messages.append(msg)
            messages.append({"role": "user", "content": query})
            
            # For discovery phase, prefill the greeting to ensure correct format
            prefill = ""
            if is_discovery and intent and intent.filters.get('location'):
                location = intent.filters.get('location', '')
                segment_data = market_intelligence.get_market_segment(location)
                ar_name = segment_data.get('name_ar', location) if segment_data else location
                prefill = f"اهلا بيك في اصول!\n\nمتوسط أسعار الشقق في {ar_name}"
                messages.append({"role": "assistant", "content": prefill})
            
            # Call Claude — with Prompt Caching + Extended Thinking
            claude_model = config.CLAUDE_MODEL
            
            # ── Early return: streaming mode gets context only ──
            if _return_context:
                return {
                    "system_prompt": system_prompt,
                    "messages": messages,
                    "prefill": prefill,
                }
            
            # ── Prompt Caching (saves ~90% on repeated system prompt tokens) ──
            if config.ENABLE_PROMPT_CACHING:
                system_payload = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                system_payload = system_prompt
            
            # ── Extended Thinking (Claude's deep reasoning mode) ──
            # max_tokens MUST be > thinking.budget_tokens per Anthropic API
            thinking_budget = config.CLAUDE_THINKING_BUDGET
            max_tok = config.CLAUDE_MAX_TOKENS
            # Auto-adjust: if max_tokens is too low for the thinking budget,
            # shrink the budget instead of disabling thinking entirely.
            if config.CLAUDE_EXTENDED_THINKING:
                if max_tok <= thinking_budget:
                    thinking_budget = max(1024, max_tok - 1024)
                    logger.info(f"🧠 Auto-adjusted thinking budget to {thinking_budget} (max_tokens={max_tok})")
                response = await self._call_claude_with_retry(
                    model=claude_model,
                    max_tokens=max_tok,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": thinking_budget,
                    },
                    system=system_payload,
                    messages=messages,
                )
            else:
                response = await self._call_claude_with_retry(
                    model=claude_model,
                    max_tokens=min(4096, max_tok),
                    temperature=0.7,
                    system=system_payload,
                    messages=messages,
                )
            
            # ── Track Claude cost (prompt caching breakdown) ──
            try:
                from app.services.cost_monitor import cost_monitor
                usage = response.usage
                cost_monitor.log_claude_usage(
                    model=claude_model,
                    input_tokens=getattr(usage, 'input_tokens', 0),
                    output_tokens=getattr(usage, 'output_tokens', 0),
                    cache_creation_tokens=getattr(usage, 'cache_creation_input_tokens', 0),
                    cache_read_tokens=getattr(usage, 'cache_read_input_tokens', 0),
                    context="wolf_narrative",
                )
            except Exception as cost_err:
                logger.debug(f"Cost tracking error (non-fatal): {cost_err}")
            
            self.stats["claude_calls"] += 1
            
            # ── Extract text from response (skip thinking blocks) ──
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text
            
            # Combine prefill with response
            full_response = prefill + response_text if prefill else response_text
            return full_response
            
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}", exc_info=True)
            return "عذراً، حصل مشكلة فنية. جرب تاني يا افندم. (Sorry, technical issue. Try again.)"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError)),
        reraise=True,
    )
    async def _call_claude_with_retry(self, **kwargs):
        """Call Claude API with exponential backoff retry (only transient errors)."""
        return await self.anthropic.messages.create(**kwargs)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # REAL STREAMING (SSE) — replaces the fake word-drip
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    async def stream_wolf_narrative(
        self,
        system_prompt: str,
        messages: List[Dict],
        prefill: str = "",
    ) -> AsyncIterator[str]:
        """
        Stream the Wolf's Claude response token-by-token via SSE.
        
        Yields text chunks as they arrive from the Anthropic streaming API.
        Skips thinking blocks — only emits visible text.
        """
        claude_model = config.CLAUDE_MODEL
        
        # Prompt caching
        if config.ENABLE_PROMPT_CACHING:
            system_payload = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        else:
            system_payload = system_prompt
        
        # Yield prefill first
        if prefill:
            yield prefill
        
        try:
            stream_kwargs = dict(
                model=claude_model,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                system=system_payload,
                messages=messages,
            )
            
            # max_tokens MUST be > thinking.budget_tokens per Anthropic API
            # Auto-adjust budget if max_tokens is too low
            if config.CLAUDE_EXTENDED_THINKING:
                stream_budget = config.CLAUDE_THINKING_BUDGET
                if config.CLAUDE_MAX_TOKENS <= stream_budget:
                    stream_budget = max(1024, config.CLAUDE_MAX_TOKENS - 1024)
                stream_kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": stream_budget,
                }
            else:
                stream_kwargs["temperature"] = 0.7
            
            async with self.anthropic.messages.stream(**stream_kwargs) as stream:
                async for event in stream:
                    # Only yield visible text deltas (skip thinking)
                    if hasattr(event, 'type'):
                        if event.type == 'content_block_delta':
                            delta = getattr(event, 'delta', None)
                            if delta and getattr(delta, 'type', '') == 'text_delta':
                                yield delta.text
                
                # Track cost after stream completes
                try:
                    final_message = await stream.get_final_message()
                    from app.services.cost_monitor import cost_monitor
                    usage = final_message.usage
                    cost_monitor.log_claude_usage(
                        model=claude_model,
                        input_tokens=getattr(usage, 'input_tokens', 0),
                        output_tokens=getattr(usage, 'output_tokens', 0),
                        cache_creation_tokens=getattr(usage, 'cache_creation_input_tokens', 0),
                        cache_read_tokens=getattr(usage, 'cache_read_input_tokens', 0),
                        context="wolf_narrative_stream",
                    )
                except Exception:
                    pass
                
                self.stats["claude_calls"] += 1
                
        except Exception as e:
            logger.error(f"Streaming narrative failed: {e}", exc_info=True)
            yield "عذراً، حصل مشكلة فنية. جرب تاني. (Sorry, technical issue.)"
    
    def _format_property_context(self, properties: List[Dict]) -> str:
        """Format properties for Claude context."""
        if not properties:
            return "[NO_PROPERTIES_FOUND]"
        
        lines = ["[PROPERTIES_DATA]"]
        lines.append(f"Found {len(properties)} matching properties:\n")
        
        for i, prop in enumerate(properties[:5], 1):
            price = prop.get('price', 0)
            price_formatted = f"{price/1_000_000:.1f}M" if price >= 1_000_000 else f"{price:,}"
            
            lines.append(f"""
Property {i}: {prop.get('title', 'N/A')}
- Location: {prop.get('location', 'N/A')}
- Price: {price_formatted} EGP
- Size: {prop.get('size_sqm', 'N/A')} sqm
- Bedrooms: {prop.get('bedrooms', 'N/A')}
- Developer: {prop.get('developer', 'N/A')}
- Osool Score: {prop.get('osool_score', 'N/A')}/100
- Verdict: {prop.get('verdict', 'N/A')}
""")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict:
        """Get brain statistics."""
        return {
            **self.stats,
            "router_stats": wolf_router.get_stats(),
            "perception_stats": perception_layer.get_stats(),
        }


# Singleton instance
wolf_brain = WolfBrain()

# Backward compatibility alias
hybrid_brain = wolf_brain

__all__ = ["WolfBrain", "wolf_brain", "hybrid_brain"]
