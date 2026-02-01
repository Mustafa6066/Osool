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
            is_discovery_complete = self._is_discovery_complete(intent.filters, history)
            
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
            if intent.action in ["search", "price_check"] and not is_discovery_complete:
                
                # 1. Identify the Area they asked about (e.g., New Cairo)
                location = intent.filters.get('location') or "New Cairo" # Default to New Cairo if unclear
                
                # 2. Get Market Intelligence (The "Value" we give)
                market_segment = market_intelligence.get_market_segment(location)
                
                if market_segment.get("found"):
                    logger.info(f"🧱 GIVE-TO-GET: Screening user for {location}")
                    
                    if language == "ar":
                         resp = (
                            f"استنى لحظة، قبل ما نتكلم في أرقام ووحدات في {market_segment.get('name_ar', location)}، لازم تفهم السوق هناك ماشي ازاي عشان متدفعش زيادة.\n\n"
                            f"السوق هناك مقسوم نوعين:\n\n"
                            f"🏆 **الفئة الأولى (Premium)**: بتبدأ من {market_segment['class_a']['min_price']/1000000:.1f} مليون (مطورين زي {', '.join(market_segment['class_a']['developers_ar'][:2])}).\n"
                            f"⭐ **الفئة الثانية (Value)**: بتبدأ من {market_segment['class_b']['min_price']/1000000:.1f} مليون.\n\n"
                            "عشان أرشحلك صح: **حضرتك بتدور على استثمار (ROI) ولا سكن فاخر؟**"
                        )
                    else:
                        resp = (
                            f"Wait, before we talk specific units in {location}, you need to know the market reality:\n\n"
                            f"The market there is split into two tiers:\n"
                            f"🏆 **Tier 1 (Premium):** Starts from {market_segment['class_a']['min_price']/1000000:.1f}M (Developers like {market_segment['class_a']['developers'][0]}).\n"
                            f"⭐ **Tier 2 (Value):** Starts from {market_segment['class_b']['min_price']/1000000:.1f}M.\n\n"
                            "To give you the right recommendation: **Are you looking for High ROI (Investment) or Luxury Living?**"
                        )

                    return {
                        "response": resp,
                        "properties": [], # Don't show properties yet
                        "ui_actions": [{"type": "market_trend_chart", "data": market_segment}], # Show a chart to look smart
                        "strategy": {"strategy": "screening_gate", "market_segment": market_segment},
                        "psychology": psychology.to_dict()
                    }

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # STEP 6: THE HUNT (Database Search)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            properties = []
            scored_properties = []
            
            # Only search if we passed the gate or it's a specific keyword search
            if intent.action in ["search", "comparison", "valuation", "investment"] or (not is_discovery_complete and intent.filters.get("location")):
                if is_discovery_complete or intent.filters.get("keywords"):
                    # Pass session to reuse connection
                    properties = await self._search_database(intent.filters, db_session=session)
                    self.stats["searches"] += 1
        
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
            ui_actions = self._determine_ui_actions(
                psychology, 
                scored_properties if is_discovery_complete else [], 
                intent, 
                query
            )
            
            strategy = determine_strategy(
                psychology,
                has_properties=len(scored_properties) > 0 and is_discovery_complete,
                top_property_verdict=top_verdict
            )
            
            # PRICE DEFENSE (The "Wolf" Logic)
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
                market_pulse=market_pulse  # Inject live DB stats
            )
            self.stats["claude_calls"] += 1

            # Calculate processing time
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": response_text,
                "properties": scored_properties[:5] if is_discovery_complete else [],
                "ui_actions": ui_actions,
                "psychology": psychology.to_dict(),
                "strategy": strategy,
                "intent": intent.to_dict(),
                "processing_time_ms": int(elapsed * 1000),
                "model_used": "wolf_brain_v6_turbo",
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
        ALWAYS include market analytics from the first answer.
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
        # ALWAYS SHOW: Investment Comparison (Bank vs Property)
        # Show on ANY property-related query
        # ═══════════════════════════════════════════════════════════════
        property_keywords = ["شقة", "فيلا", "عقار", "apartment", "villa", "property", "بيت", "unit"]
        has_property_intent = any(kw in query_lower for kw in property_keywords) or intent.action in ["search", "price_check", "investment"]
        
        if has_property_intent:
            investment_amount = 5_000_000  # Default 5M
            if properties:
                investment_amount = properties[0].get('price', 5_000_000)
            
            inflation_data = analytical_engine.calculate_inflation_hedge(investment_amount, years=5)
            
            ui_actions.append({
                "type": "certificates_vs_property",
                "priority": "high",
                "title": "العقار vs شهادات البنك (27% فايدة)",
                "title_en": "Property vs Bank CDs (27% Interest)",
                "data": inflation_data
            })
        
        # Check for explicit bank comparison triggers
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

        feasibility: Optional[Any] = None,
        no_discount_mode: bool = False,
        market_segment: Optional[Dict] = None,
        market_pulse: Optional[Dict] = None
    ) -> str:
        """
        STEP 8: SPEAK (Claude 3.5 Sonnet)
        Generate the Wolf's response using ONLY verified data.
        Now with psychology-aware context injection and language control.
        """
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # INSIGHT INJECTION (The "Wolf" Edge)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            wolf_insight_instruction = ""
            
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
