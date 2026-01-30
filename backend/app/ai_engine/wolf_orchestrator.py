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
from typing import Dict, List, Any, Optional
from datetime import datetime
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

# Internal modules
from .wolf_router import wolf_router, RouteType, RouteDecision
from .perception_layer import perception_layer, Intent
from .psychology_layer import (
    analyze_psychology, 
    determine_strategy,
    get_psychology_context_for_prompt,
    PsychologyProfile,
    PsychologicalState
)
from .analytical_engine import analytical_engine, market_intelligence, OsoolScore, AREA_BENCHMARKS, MARKET_SEGMENTS
from .analytical_actions import generate_analytical_ui_actions
from .amr_master_prompt import get_wolf_system_prompt, AMR_SYSTEM_PROMPT
from .conversation_memory import ConversationMemory

# Database
from app.database import AsyncSessionLocal
from app.services.vector_search import search_properties as db_search_properties

logger = logging.getLogger(__name__)


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
        
        logger.info("🐺 Wolf Brain initialized")
    
    async def process_turn(
        self,
        query: str,
        history: List[Dict],
        profile: Optional[Dict] = None,
        language: str = "auto",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        The Main Thinking Loop - Wolf Brain V5.
        
        Args:
            query: User's natural language query
            history: Conversation history
            profile: User profile dict (optional)
            language: Preferred language ('ar', 'en', 'auto')
            session_id: Session identifier for memory
            
        Returns:
            Dict with response, ui_actions, properties, psychology, etc.
        """
        start_time = datetime.now()
        self.stats["turns_processed"] += 1
        
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 1: ROUTE (Quick classification)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            route = await wolf_router.route(query, history)
            logger.info(f"📍 Route: {route.route_type.value} (hybrid={route.use_hybrid_brain})")
            
            # For simple greetings/general queries, use fast GPT response
            if not route.use_hybrid_brain:
                return await self._handle_general_query(query, history, language)
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 2: PERCEPTION (Extract intent & filters)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            intent = await perception_layer.analyze(query, history)
            logger.info(f"🎯 Intent: {intent.action}, Filters: {intent.filters}")
            self.stats["gpt_calls"] += 1
            
            # Auto-detect language if needed
            if language == "auto":
                language = intent.language
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 3: DISCOVERY CHECK (Are we ready to show properties?)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            is_discovery_complete = self._is_discovery_complete(intent.filters, history)
            logger.info(f"📋 Discovery complete: {is_discovery_complete}")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4: PSYCHOLOGY (Detect emotional state)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            psychology = analyze_psychology(query, history, intent.to_dict())
            logger.info(f"🧠 Psychology: {psychology.primary_state.value}")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 5: FEASIBILITY SCREEN (The Gatekeeper)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            feasibility = None
            if is_discovery_complete and intent.filters.get('budget_max'):
                location = intent.filters.get('location', 'new cairo')
                property_type = intent.filters.get('property_type', 'apartment')
                budget = intent.filters.get('budget_max', 10_000_000)
                
                feasibility = market_intelligence.screen_feasibility(
                    location=location,
                    property_type=property_type,
                    budget=budget
                )
                
                if not feasibility.is_feasible:
                    logger.info(f"🛑 Feasibility FAILED: {property_type} in {location} needs {budget + feasibility.budget_gap}")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 6: HUNT (Search database for properties)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            properties = []
            if is_discovery_complete and intent.action in ["search", "comparison", "valuation", "investment"]:
                properties = await self._search_database(intent.filters)
                self.stats["searches"] += 1
                logger.info(f"🏠 Found {len(properties)} properties")
            elif not is_discovery_complete:
                logger.info("⏸️ Skipping property search - discovery not complete")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 7: ANALYZE (Score with Osool Score + Wolf Benchmarking)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            scored_properties = analytical_engine.score_properties(properties)
            
            # Add ROI analysis AND wolf benchmarking to each property
            for prop in scored_properties:
                # ROI Analysis
                roi = analytical_engine.calculate_true_roi(prop)
                prop["roi_analysis"] = roi.to_dict()
                
                # Wolf Benchmarking (Value Anchor)
                benchmark = market_intelligence.benchmark_property(prop)
                prop["wolf_analysis"] = benchmark.wolf_analysis
                prop["wolf_benchmark"] = benchmark.to_dict()
            
            top_verdict = scored_properties[0].get("verdict", "FAIR") if scored_properties else "FAIR"
            top_wolf_analysis = scored_properties[0].get("wolf_analysis", "FAIR_VALUE") if scored_properties else "FAIR_VALUE"
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 8: UI ACTIONS (Determine visualizations - skip cards if discovery incomplete)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ui_actions = self._determine_ui_actions(
                psychology, 
                scored_properties if is_discovery_complete else [],  # No cards during discovery
                intent,
                query
            )
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 9: STRATEGY (Psychology-aware pitch selection)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            strategy = determine_strategy(
                psychology,
                has_properties=len(scored_properties) > 0 and is_discovery_complete,
                top_property_verdict=top_verdict
            )
            logger.info(f"🎭 Strategy: {strategy['strategy']}")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 10: SPEAK (Claude narrative generation)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            response_text = await self._generate_wolf_narrative(
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
                feasibility=feasibility
            )
            self.stats["claude_calls"] += 1
            
            # Calculate processing time
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response_text,
                "properties": scored_properties[:5] if is_discovery_complete else [],  # Only show after discovery
                "ui_actions": ui_actions,
                "psychology": psychology.to_dict(),
                "strategy": strategy,
                "intent": intent.to_dict(),
                "route": route.to_dict(),
                "processing_time_ms": int(elapsed * 1000),
                "model_used": "wolf_brain_v5",
                "discovery_complete": is_discovery_complete,
                "feasibility": feasibility.to_dict() if feasibility else None,
                "top_wolf_analysis": top_wolf_analysis,
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
    
    async def _handle_general_query(
        self,
        query: str,
        history: List[Dict],
        language: str
    ) -> Dict[str, Any]:
        """Handle simple queries with fast GPT-4o response."""
        try:
            system_prompt = """You are AMR (عمرو), an Egyptian real estate AI consultant for Osool.
            
For greetings and simple questions, be warm and professional.
Introduce yourself as AMR and offer to help with real estate.

Respond in Egyptian Arabic (عامية مصرية) if the user writes in Arabic,
otherwise respond bilingually (Arabic then English).

Keep responses SHORT and friendly. Max 2-3 sentences."""

            messages = history[-5:] if history else []
            messages.append({"role": "user", "content": query})
            
            response = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            self.stats["gpt_calls"] += 1
            
            return {
                "response": response.choices[0].message.content,
                "properties": [],
                "ui_actions": [],
                "psychology": {"primary_state": "neutral"},
                "route": {"route_type": "general", "use_hybrid_brain": False},
                "model_used": "gpt-4o"
            }
            
        except Exception as e:
            logger.error(f"General query handling failed: {e}")
            return {
                "response": "أهلاً بيك! أنا عمرو، مستشارك العقاري. إزاي أقدر أساعدك؟ (Hello! I'm AMR, your real estate consultant. How can I help?)",
                "properties": [],
                "ui_actions": [],
                "psychology": {"primary_state": "neutral"},
            }
    
    async def _search_database(self, filters: Dict) -> List[Dict]:
        """
        Search database for properties matching filters.
        """
        try:
            async with AsyncSessionLocal() as db:
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
                
                query_text = " ".join(query_parts) if query_parts else "property"
                
                # Vector search
                results = await db_search_properties(
                    db=db,
                    query_text=query_text,
                    limit=50,
                    similarity_threshold=0.50,
                    price_min=filters.get('budget_min'),
                    price_max=filters.get('budget_max')
                )
                
                # Apply additional filters
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
                
        except Exception as e:
            logger.error(f"Database search failed: {e}", exc_info=True)
            return []
    
    def _is_discovery_complete(self, filters: Dict, history: List[Dict]) -> bool:
        """
        Check if discovery phase is complete.
        
        Discovery is complete when we have at least:
        1. Budget information (budget_min or budget_max), OR
        2. Purpose/intent is clear from history
        
        This ensures we don't show properties until we understand what the user wants.
        """
        # Check if we have budget info
        has_budget = bool(filters.get('budget_max') or filters.get('budget_min'))
        
        # Check history length - if we've had a few exchanges, can proceed
        has_context = len(history) >= 4  # At least 2 back-and-forth
        
        # Check if purpose was mentioned in current filters or history
        purpose_keywords = [
            "سكن", "استثمار", "invest", "live", "rental", "rent", "ايجار",
            "تجاري", "commercial", "سياحي", "vacation", "تمليك", "buy"
        ]
        
        has_purpose = False
        
        # Check in recent history
        for msg in history[-6:]:
            content = msg.get('content', '').lower() if isinstance(msg, dict) else ''
            if any(kw in content for kw in purpose_keywords):
                has_purpose = True
                break
        
        # Discovery is complete if:
        # 1. We have budget info, OR
        # 2. We have both context history AND purpose mentioned
        # 3. User has provided location + budget combo
        has_location = bool(filters.get('location'))
        
        # Complete if: (budget) OR (context + purpose) OR (location + budget) OR (location + purpose)
        if has_budget:
            logger.debug("Discovery complete: Has budget info")
            return True
        
        if has_context and has_purpose:
            logger.debug("Discovery complete: Has context + purpose")
            return True
        
        if has_location and has_purpose:
            logger.debug("Discovery complete: Has location + purpose")
            return True
        
        logger.debug(f"Discovery incomplete: budget={has_budget}, context={has_context}, purpose={has_purpose}, location={has_location}")
        return False
    
    def _determine_ui_actions(
        self,
        psychology: PsychologyProfile,
        properties: List[Dict],
        intent: Intent,
        query: str
    ) -> List[Dict]:
        """
        Determine which UI visualizations to trigger.
        """
        ui_actions = []
        query_lower = query.lower()
        
        # Check for investment/inflation triggers
        investment_keywords = ["استثمار", "عائد", "roi", "بنك", "شهادة", "تضخم", "inflation", "invest"]
        if any(kw in query_lower for kw in investment_keywords) or \
           psychology.primary_state == PsychologicalState.GREED_DRIVEN:
            
            # Add inflation comparison chart
            investment_amount = 5_000_000  # Default 5M
            if properties:
                investment_amount = properties[0].get('price', 5_000_000)
            
            inflation_data = analytical_engine.calculate_inflation_hedge(investment_amount, years=5)
            
            ui_actions.append({
                "type": "certificates_vs_property",
                "priority": "high",
                "title": "الحقيقة: العقار vs شهادات البنك",
                "title_en": "Truth: Property vs Bank CDs",
                "data": inflation_data
            })
        
        # Check for bank comparison triggers
        bank_keywords = ["bank", "بنك", "فايدة", "27%", "شهادات", "certificates"]
        if any(kw in query_lower for kw in bank_keywords):
            investment_amount = 5_000_000
            if properties:
                investment_amount = properties[0].get('price', 5_000_000)
            
            bank_data = analytical_engine.calculate_bank_vs_property(investment_amount, years=5)
            ui_actions.append({
                "type": "bank_vs_property",
                "priority": "high",
                "title": "شهادات البنك vs العقار (الحقيقة)",
                "title_en": "Bank CDs vs Property (The Truth)",
                "data": bank_data
            })
        
        # Property cards for search results
        if properties and intent.action == "search":
            ui_actions.append({
                "type": "property_cards",
                "priority": "medium",
                "properties": properties[:5]
            })
        
        # Bargain alert if found
        if properties:
            bargains = analytical_engine.detect_bargains(properties, threshold_percent=10)
            if bargains:
                ui_actions.append({
                    "type": "la2ta_alert",
                    "priority": "high",
                    "title": "🔥 لقطة",
                    "title_en": "🔥 Bargain Found",
                    "property": bargains[0],
                    "discount": bargains[0].get("la2ta_score", 0)
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
        feasibility: Optional[Any] = None
    ) -> str:
        """
        Generate the final narrative using Claude 3.5 Sonnet.
        
        This is where the Wolf speaks - combining data, psychology,
        and strategy into a persuasive response.
        """
        try:
            # Build context for Claude
            context_parts = []
            
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
            
            # Feasibility context (Reality Check - if request is not feasible)
            if feasibility and not feasibility.is_feasible:
                context_parts.append(f"""
[REALITY_CHECK - CRITICAL]
The user's request is NOT FEASIBLE given market realities!

{feasibility.message_ar}

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
            
            # Psychology context
            context_parts.append(get_psychology_context_for_prompt(psychology))
            
            # Strategy context
            context_parts.append(f"""
[STRATEGY: {strategy['strategy'].upper()}]
Angle: {strategy['angle']}
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
            
            # Build system prompt
            system_prompt = AMR_SYSTEM_PROMPT + "\n\n" + "\n".join(context_parts)
            
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
            for msg in history[-10:]:
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
            
            # Call Claude
            claude_model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
            
            response = await self.anthropic.messages.create(
                model=claude_model,
                max_tokens=1200,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )
            
            # Combine prefill with response
            full_response = prefill + response.content[0].text if prefill else response.content[0].text
            return full_response
            
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}", exc_info=True)
            return "عذراً، حصل مشكلة فنية. جرب تاني يا افندم. (Sorry, technical issue. Try again.)"
    
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
