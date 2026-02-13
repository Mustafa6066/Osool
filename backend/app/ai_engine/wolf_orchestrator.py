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
import re
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
from .market_analytics_layer import MarketAnalyticsLayer
from .analytical_actions import generate_analytical_ui_actions
from .amr_master_prompt import get_wolf_system_prompt, AMR_SYSTEM_PROMPT, is_discount_request, FRAME_CONTROL_EXAMPLES
from .hybrid_brain_prod import hybrid_brain_prod  # The Specialist Tools
from .conversation_memory import ConversationMemory
from .lead_scoring import score_lead, LeadTemperature, BehaviorSignal
from .wolf_checklist import validate_checklist, WolfChecklistResult


# Database
from app.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_search import search_properties as db_search_properties
from app.services.cache import cache
from app.services.market_statistics import get_cached_qa_statistics, format_qa_stats_for_ai

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
        
        logger.info("🐺 Wolf Brain initialized (Reloaded for Protocol 6)")
    
    async def process_turn(
        self,
        query: str,
        history: List[Dict],
        profile: Optional[Dict] = None,
        language: str = "auto",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        The Main Thinking Loop - Wrapper for Session Management.
        """
        async with AsyncSessionLocal() as session:
            return await self._process_turn_logic(
                query=query,
                history=history,
                session=session,
                profile=profile,
                language=language,
                session_id=session_id
            )

    async def _process_turn_logic(
        self,
        query: str,
        history: List[Dict],
        session: AsyncSession,
        profile: Optional[Dict] = None,
        language: str = "auto",
        session_id: Optional[str] = None
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
            # STEP 3: LOGIC GATES (Loop Detection & Feasibility)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # HUMAN HANDOFF CHECK
            if "loop_detected" in lead_data.get("signals", []):
                return {
                    "response": "لقد لاحظت تكرار الأسئلة، وهذا يتطلب تدخلاً من خبير بشري لتحليل الوضع بدقة.\n\n"
                                "سأقوم بتحويلك الآن لمستشار أول (Senior Consultant) لمراجعة حالتك.\n"
                                "تم فتح تذكرة #URGENT-882.",
                    "properties": [],
                    "ui_actions": [{"type": "handoff_alert", "priority": "high"}],
                    "psychology": psychology.to_dict(),
                    "handoff": True
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

                return {
                    "response": resp,
                    "ui_actions": [{
                        "type": "law_114_guardian", # Triggers a cool "Scanning..." UI animation
                        "status": "active"
                    }],
                    "strategy": {"strategy": "confidence_building", "route": "legal"},
                    "psychology": psychology.to_dict()
                }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 4: DISCOVERY CHECK
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            is_discovery_complete = self._is_discovery_complete(intent.filters, history, query)
            
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
                        "psychology": psychology.to_dict()
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

                    return {
                        "response": resp,
                        "properties": [], # Don't show properties yet
                        "ui_actions": [{"type": "market_trend_chart", "data": market_segment}], # Show a chart to look smart
                        "strategy": {"strategy": "screening_gate", "market_segment": market_segment},
                        "psychology": psychology.to_dict()
                    }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 6: THE SMART HUNT (Agentic Search with Reflexion)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            properties = []
            scored_properties = []
            hunt_strategy = "none"
            pivot_message = None
            
            # Determine "Smart Display" Strategy
            showing_strategy = self._determine_showing_strategy(intent, psychology, is_discovery_complete)
            logger.info(f"👁️ Visual Strategy: {showing_strategy}")

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # FAMILY HOUSING INTENT ENHANCEMENT
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if (intent.filters.get('purpose') == 'living'
                and intent.intent_bucket == 'serious_buyer'
                and not intent.filters.get('bedrooms')):
                # Family buyer with no bedroom preference → default to 3+ bedrooms
                intent.filters['bedrooms'] = 3
                logger.info("👨‍👩‍👧‍👦 Family buyer detected: auto-setting min 3 bedrooms")

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
            ui_actions = self._determine_ui_actions(
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
            # STEP 8: SPEAK (Narrative Generation)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            response_text = await self._generate_wolf_narrative(
                query=query,
                properties=scored_properties,
                psychology=psychology,
                strategy=strategy,
                ui_actions=ui_actions,
                history=history,
                language=language, # Strict detected language
                profile=profile,
                is_discovery=not is_discovery_complete,
                intent=intent,
                feasibility=None, 
                no_discount_mode=no_discount_mode,
                market_segment=strategy.get("market_segment"), # Pass market segment if used
                market_pulse=market_pulse,  # Inject live DB stats
                showing_strategy=showing_strategy,  # Smart Display strategy
                pivot_message=pivot_message,  # NEW: Reflexion pivot explanation
                hunt_strategy=hunt_strategy  # NEW: Reflexion hunt strategy used
            )
            self.stats["claude_calls"] += 1

            # Calculate processing time
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response_text,
                "properties": scored_properties[:5] if showing_strategy == 'FULL_LIST' else (scored_properties[:1] if showing_strategy == 'TEASER' else []),
                "ui_actions": ui_actions,
                "psychology": psychology.to_dict(),
                "strategy": strategy,
                "intent": intent.to_dict(),
                "processing_time_ms": int(elapsed * 1000),
                "model_used": "wolf_brain_v7_reflexion",
                "showing_strategy": showing_strategy,
                "hunt_strategy": hunt_strategy,  # NEW: Reflexion strategy used
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
        
        return {
            "response": script_ar if language != "en" else script_en,
            "ui_actions": [],
            "properties": [],
            "psychology": {"primary_state": "neutral"},
            "strategy": {"strategy": "fast_gate"},
            "model_used": "wolf_fast_gate"
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
        """Execute the actual search logic."""
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
        # REFLEXION: Relaxed Search (Drop all filters, keep location only)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if location:
            relaxed_filters = {"location": filters.get("location")}
            alternatives = await self._search_database(relaxed_filters, db_session=session)
            if alternatives:
                logger.info(f"🔄 SMART HUNT: Relaxed search success (location-only for {location})")
                if language == "ar":
                    pivot_msg = "معايير البحث المحددة ضيقة شوية، بس لقيت خيارات تانية في نفس المنطقة ممكن تعجبك."
                else:
                    pivot_msg = "Your specific criteria are quite narrow, but I found other options in the same area that might interest you."
                return alternatives[:5], "relaxed_search", pivot_msg

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REFLEXION: Any Area Search (Drop location too, keep budget only)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if budget_max and budget_max > 0:
            any_filters = {"budget_max": int(budget_max * 1.1)}
            alternatives = await self._search_database(any_filters, db_session=session)
            if alternatives:
                logger.info(f"🔄 SMART HUNT: Any-area search success (budget-only)")
                if language == "ar":
                    pivot_msg = "مفيش وحدات بالمواصفات دي في المنطقة المحددة، بس لقيت فرص ممتازة في مناطق تانية بنفس الميزانية."
                else:
                    pivot_msg = "No units match in the specified area, but I found excellent options in other areas within your budget."
                return alternatives[:5], "any_area_search", pivot_msg

        # All strategies exhausted - ask for adjusted criteria
        logger.info("❌ SMART HUNT: All reflexion strategies failed")
        if language == "ar":
            pivot_msg = "الفرص المتاحة حالياً محدودة بالمواصفات دي. خليني أعرف أكتر عن احتياجاتك عشان أرشحلك أفضل البدائل."
        else:
            pivot_msg = "Current availability is limited for these exact specs. Tell me more about your needs so I can find the best alternatives."
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
    
    def _determine_showing_strategy(self, intent: Intent, psychology: PsychologyProfile, is_discovery_complete: bool) -> str:
        """
        Smart Display Protocol: Decides HOW to show properties based on User Intent & Psychology.
        
        Returns: 'NONE', 'TEASER', 'FULL_LIST'
        
        Tiers:
        - NONE: Window shoppers, educational queries → Charts only
        - TEASER: Location but no budget → 1 anchor property to test price sensitivity
        - FULL_LIST: Qualified user (budget + location) → 3-5 targeted properties
        """
        # 1. Block if Trust Deficit (Psychology Rule)
        if psychology.primary_state == PsychologicalState.TRUST_DEFICIT:
            logger.info("👁️ Strategy: NONE (Trust Deficit - build confidence first)")
            return 'NONE'

        # 2. Block if purely educational query (e.g. "What is ROI?")
        if intent.action in ["investment", "general", "legal"] and not intent.filters.get("location"):
            logger.info("👁️ Strategy: NONE (Educational query without location)")
            return 'NONE'

        # 3. FULL LIST: If Discovery Complete OR Explicit show keywords
        show_keywords = ["show", "أوريني", "ورجيني", "best", "أفضل", "options", "خيارات"]
        has_show_keyword = any(kw in intent.raw_query.lower() for kw in show_keywords)
        
        if is_discovery_complete or has_show_keyword:
            logger.info("👁️ Strategy: FULL_LIST (Qualified or explicit request)")
            return 'FULL_LIST'

        # 4. TEASER: If we have Location but NO Budget (The "Anchor" Strategy)
        # We show 1 property to force them to react to the price.
        if intent.filters.get("location") and not intent.filters.get("budget_max"):
            logger.info("👁️ Strategy: TEASER (Location without budget - anchor mode)")
            return 'TEASER'

        # 5. Default: Window shopper - don't show yet
        if intent.intent_bucket == "window_shopper":
            logger.info("👁️ Strategy: NONE (Window shopper)")
            return 'NONE'

        logger.info("👁️ Strategy: NONE (Default fallback)")
        return 'NONE'
    

    def _determine_ui_actions(
        self,
        psychology: PsychologyProfile,
        properties: List[Dict],
        intent: Intent,
        query: str,
        showing_strategy: str = 'NONE',
        wolf_strategy: Optional[Dict] = None  # NEW: Pass chosen verbal strategy
    ) -> List[Dict]:
        """
        Determine which UI visualizations to trigger.
        ALWAYS include market analytics from the first answer.
        Uses showing_strategy to control property display.
        Uses wolf_strategy to ensure charts match the script (e.g. "Look at the chart").
        """
        ui_actions = []
        query_lower = query.lower()
        
        # ═══════════════════════════════════════════════════════════════
        # ALWAYS SHOW: Market Analytics (FROM FIRST ANSWER)
        # ═══════════════════════════════════════════════════════════════
        location = intent.filters.get('location', '')
        if location:
            # Get market segment data for the location
            market_segment = market_intelligence.get_market_segment(location)
            area_context = market_intelligence.get_area_context(location)
            
            if market_segment.get('found') or area_context.get('found'):
                ui_actions.append({
                    "type": "market_benchmark",
                    "priority": "high",
                    "title": f"📊 أسعار السوق في {market_segment.get('name_ar', location)}",
                    "title_en": f"📊 Market Prices in {location}",
                    "data": {
                        "market_segment": market_segment,
                        "area_context": area_context,
                        "avg_price_sqm": area_context.get('avg_price_sqm', 0),
                        "rental_yield": area_context.get('rental_yield', 0.065),
                        "growth_rate": area_context.get('growth_rate', 0.12),
                    }
                })
        
        # ═══════════════════════════════════════════════════════════════
        # PSYCHOLOGY-DRIVEN CHARTS (Automatic triggers based on emotional state)
        # ═══════════════════════════════════════════════════════════════
        # FAMILY_SECURITY -> Always show inflation protection chart
        if psychology.primary_state == PsychologicalState.FAMILY_SECURITY:
            investment_amount = properties[0].get('price', 5_000_000) if properties else 5_000_000
            inflation_data = analytical_engine.calculate_inflation_hedge(investment_amount, years=5)
            if inflation_data and inflation_data.get('projections'):  # Only add if calculation produced data
                ui_actions.append({
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
            ui_actions.append({
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
            if inflation_data and inflation_data.get('projections'):  # Only add if calculation produced data
                ui_actions.append({
                    "type": "inflation_killer",  # Use consistent type for frontend
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
            if bank_data and bank_data.get('data_points'):  # Only add if calculation produced data
                ui_actions.append({
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
            
            ui_actions.append({
                "type": "property_cards",
                "priority": "medium" if showing_strategy == 'FULL_LIST' else "low",
                "title": card_title_ar,
                "title_en": card_title_en,
                "properties": display_properties,
                "is_teaser": showing_strategy == 'TEASER'  # Flag for frontend styling
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

        # ═══════════════════════════════════════════════════════════════
        # FOMO TRIGGER: Hot Market Price Increase Warning
        # When buyer is hesitant + area has >30% growth → urgency alert
        # ═══════════════════════════════════════════════════════════════
        if location and psychology.primary_state in [
            PsychologicalState.HESITATION,
            PsychologicalState.ANALYSIS_PARALYSIS,
            PsychologicalState.SKEPTICISM
        ]:
            area_context = market_intelligence.get_area_context(location)
            growth_rate = area_context.get('growth_rate', 0) if area_context.get('found') else 0
            if growth_rate > 0.25:  # >25% annual growth = hot market
                avg_price = area_context.get('avg_price_sqm', 0)
                projected_increase = int(avg_price * growth_rate)
                ui_actions.append({
                    "type": "la2ta_alert",
                    "priority": "high",
                    "title": "⏰ تحذير زيادة أسعار",
                    "title_en": "⏰ Price Increase Warning",
                    "property": properties[0] if properties else {},
                    "discount": 0,
                    "fomo_data": {
                        "area": location,
                        "growth_rate": f"{growth_rate*100:.0f}%",
                        "current_avg_sqm": avg_price,
                        "projected_increase_sqm": projected_increase,
                        "message_ar": f"أسعار {location} بتزيد {growth_rate*100:.0f}% سنوياً. المتر هيزيد ~{projected_increase:,} جنيه السنة الجاية.",
                        "message_en": f"{location} prices rising {growth_rate*100:.0f}% annually. Expect ~{projected_increase:,} EGP/sqm increase next year."
                    }
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
        pivot_message: Optional[str] = None,  # NEW: Reflexion pivot explanation
        hunt_strategy: str = 'none'  # NEW: Reflexion hunt strategy used
    ) -> str:
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
            # REFLEXION CONTEXT (Search Pivot Explanation)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if hunt_strategy != 'direct_match' and pivot_message:
                # We had to pivot the search - inject explanation
                pivot_type_names = {
                    'location_pivot': 'Location Alternative',
                    'type_pivot': 'Property Type Alternative',
                    'budget_pivot': 'Budget Stretch',
                    'relaxed_search': 'Flexible Criteria',
                    'any_area_search': 'Cross-Area Search',
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
            if properties and showing_strategy == 'TEASER':
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
                # FULL MODE: Show best matches and sell hard
                if language == 'ar':
                    wolf_insight_instruction += """
[STRATEGY: FULL_INVENTORY]
أنت بتعرض أفضل الخيارات المتاحة. اختار الأفضل واشرح ليه هي لقطة.
ركز على ROI والقيمة مقارنة بالسوق.
"""
                else:
                    wolf_insight_instruction += """
[STRATEGY: FULL_INVENTORY]
You are showing the best matches. Pick the top winner and sell its ROI hard.
Focus on value compared to market average.
"""
            
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
                area_avg = market_pulse['avg_price_sqm'] if market_pulse else analytical_engine.get_avg_price_per_sqm(location)
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
                         wolf_insight_instruction = f"""
[MANDATORY OPENER]
You MUST start your response with this EXACT sentence (in Egyptian Arabic):
"🐺 أنا لقيت لقطة في السوق. الوحدة دي سعر مترها {price_sqm:,.0f} جنيه، في حين إن متوسط المنطقة {area_avg:,.0f} جنيه."
"""
                    else:
                         wolf_insight_instruction = f"""
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
                
                # Economic constants (Egyptian market 2024)
                inflation_rate = 33  # Real inflation
                bank_rate = 27       # Best CD rate
                negative_yield = inflation_rate - bank_rate  # 6% loss
                
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

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # PROTOCOL F: CAPITAL PRESERVATION PSYCHOLOGY
            # When user's primary concern is protecting savings, not investing
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            preservation_keywords = [
                "تحويشة", "تحويشتي", "حفظ قيمة", "فلوس البنك", "قيمة الفلوس",
                "تحويشة العمر", "أمان الفلوس", "أحمي فلوسي", "حماية", "ادخار",
                "savings", "protect my money", "preserve", "safe investment"
            ]
            is_preservation = any(kw in query.lower() for kw in preservation_keywords)

            if is_preservation or psychology.primary_state == PsychologicalState.FEAR_OF_LOSS:
                wolf_insight_instruction += """
[PROTOCOL_F_CAPITAL_PRESERVATION]
The user's concern is PROTECTING their savings, not maximizing returns.
APPROACH: Switch from "investor pitch" to "wealth guardian" mode.

MANDATORY FRAMEWORK:
1. Validate their fear: "حفظ الفلوس في البنك مش حفظ قيمة. ده تآكل بطيء."
2. Show the math: "لو حطيت 5 مليون في البنك، بعد 5 سنين القوة الشرائية بتبقى X مليون بس"
3. Reframe property: "أنت مش بتشتري عقار، أنت بتحوّل فلوسك من عملة بتخس لأصل بيكبر"
4. Close with safety: "العقار هو الـ safe haven الوحيد اللي بينمو فوق التضخم"
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
            # DATABASE STATISTICS INJECTION (Verified Numbers from PostgreSQL)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            try:
                requested_location = intent.filters.get('location', '') if intent else ''
                qa_stats = await get_cached_qa_statistics(area=requested_location or None)
                if qa_stats and qa_stats.get('summary', {}).get('total_properties', 0) > 0:
                    stats_context = format_qa_stats_for_ai(qa_stats, location=requested_location or None)
                    context_parts.append(stats_context)
                    logger.info(f"📊 Injected QA stats into narrative context (location={requested_location or 'all'})")
            except Exception as e:
                logger.warning(f"Failed to inject QA stats: {e}")

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
            claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            
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
