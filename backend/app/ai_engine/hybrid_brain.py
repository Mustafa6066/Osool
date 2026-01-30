"""
Osool Hybrid Intelligence Engine - V4 "Wolf Brain"
---------------------------------------------------
The "Brain" of the Wolf - Now with Psychology Layer & UI Triggers.

Architecture:
1. PERCEPTION (GPT-4o): Extract intent & filters from natural language
2. PSYCHOLOGY (Pattern Matching): Detect emotional state (FOMO, Risk-Averse, Greed)
3. PIVOT CHECK: Detect impossible requests and redirect
4. HUNT (Database): Search for real properties
5. ANALYZE (XGBoost): Score deals, find "La2ta" (the catch)
6. STRATEGY (Psychology-Aware): Determine pitch angle based on emotional state
7. SPEAK (Claude): Generate narrative using ONLY verified data
8. UI_TRIGGERS: Determine which visualizations to render in frontend
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from enum import Enum
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.ai_engine.amr_master_prompt import AMR_SYSTEM_PROMPT
from app.ai_engine.xgboost_predictor import xgboost_predictor
from app.ai_engine.psychology_layer import (
    analyze_psychology,
    get_psychology_context_for_prompt,
    PsychologyProfile,
    PsychologicalState
)
from app.ai_engine.proactive_alerts import proactive_alert_engine
from app.ai_engine.conversation_memory import ConversationMemory
from app.ai_engine.analytical_actions import generate_analytical_ui_actions
from app.services.vector_search import search_properties as db_search_properties
from app.services.market_statistics import get_market_statistics, format_statistics_for_ai
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class UIActionType(Enum):
    """Types of UI visualizations that can be triggered."""
    # Core Visualizations
    INFLATION_KILLER = "inflation_killer"
    INVESTMENT_SCORECARD = "investment_scorecard"
    COMPARISON_MATRIX = "comparison_matrix"
    PAYMENT_TIMELINE = "payment_timeline"
    MARKET_TREND_CHART = "market_trend_chart"
    LA2TA_ALERT = "la2ta_alert"
    LAW_114_GUARDIAN = "law_114_guardian"
    REALITY_CHECK = "reality_check"
    
    # V6: Advanced Analytics for Buyers & Investors
    AREA_ANALYSIS = "area_analysis"              # Price/sqm, trends, demand by area
    DEVELOPER_ANALYSIS = "developer_analysis"    # Developer reputation, delivery history, price ranges
    PROPERTY_TYPE_ANALYSIS = "property_type_analysis"  # Apartment vs Villa vs Townhouse comparison
    PAYMENT_PLAN_ANALYSIS = "payment_plan_analysis"    # Best payment plans, down payments, installment comparison
    RESALE_VS_DEVELOPER = "resale_vs_developer"  # Primary vs Secondary market comparison
    ROI_CALCULATOR = "roi_calculator"            # Rental yield, capital appreciation, break-even
    PRICE_HEATMAP = "price_heatmap"              # Price per sqm heatmap by area
    DELIVERY_TIMELINE = "delivery_timeline"      # Projects by delivery date


# Impossible request patterns for agentic pivots
IMPOSSIBLE_COMBINATIONS = [
    {
        "description": "Luxury area + Very low budget for villa",
        "conditions": {
            "locations": ["Sheikh Zayed", "New Cairo", "New Capital", "زايد", "التجمع", "العاصمة"],
            "budget_max": 2_000_000,
            "property_types": ["villa", "فيلا", "penthouse", "بنتهاوس", "توين هاوس", "twin house"]
        },
        "reality_message_ar": "يا افندم، صراحة فيلا في المنطقة دي تحت 2 مليون مش موجودة في السوق دلوقتي. بس خليني أقولك البدائل الذكية...",
        "reality_message_en": "Sir, a villa in this area under 2M doesn't exist in today's market. But let me show you smart alternatives...",
        "alternatives": [
            {"label_ar": "نفس الميزانية في أكتوبر", "label_en": "Same budget in 6th October", "action": "search_october"},
            {"label_ar": "شقة بجاردن في نفس المنطقة", "label_en": "Garden apartment in same area", "action": "search_garden_apt"},
            {"label_ar": "زيادة الميزانية لـ 3.5 مليون", "label_en": "Increase budget to 3.5M", "action": "increase_budget"}
        ]
    },
    {
        "description": "Ultra-luxury expectations with modest budget",
        "conditions": {
            "locations": ["Beverly Hills", "بيفرلي هيلز", "Lake View", "ليك فيو", "Hyde Park", "هايد بارك"],
            "budget_max": 3_000_000
        },
        "reality_message_ar": "الكمباوندات دي من أغلى الكمباوندات في مصر يا افندم. الميزانية دي محتاج أشوفلك فيها بدائل تانية...",
        "reality_message_en": "These are among Egypt's most premium compounds. With this budget, let me find you better alternatives...",
        "alternatives": [
            {"label_ar": "كمباوندات قريبة بأسعار أقل", "label_en": "Similar nearby compounds at lower prices", "action": "search_nearby"},
            {"label_ar": "وحدات إعادة بيع", "label_en": "Resale units (better prices)", "action": "search_resale"}
        ]
    }
]


class OsoolHybridBrain:
    """
    The Reasoning Loop Orchestrator.
    Forces: Hunt (Data) → Analyze (Math) → Speak (Charisma)
    """
    
    def __init__(self):
        """Initialize all AI components."""
        self.openai_async = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_async = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Feature flag for rollback safety
        self.enabled = os.getenv("ENABLE_REASONING_LOOP", "true").lower() == "true"

        # Session-scoped conversation memories
        self._session_memories: Dict[str, ConversationMemory] = {}

    def get_memory(self, session_id: str) -> ConversationMemory:
        """Get or create conversation memory for a session."""
        if session_id not in self._session_memories:
            self._session_memories[session_id] = ConversationMemory()
        return self._session_memories[session_id]
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English."""
        import re
        if not text:
            return "en"
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        arabic_chars = len(arabic_pattern.findall(text))
        total_chars = len(text.replace(" ", ""))
        if total_chars == 0:
            return "en"
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"

    async def _deep_analysis(
        self,
        properties: List[Dict],
        query: str,
        psychology: PsychologyProfile,
        market_stats: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        DEEP ANALYSIS STAGE (GPT-4o)
        Generates structured analytical insights from search results.
        NOW TRIGGERS FOR ANY SEARCH to ensure analytical-first responses.
        """
        # V8: ALWAYS generate analysis for any property search
        if len(properties) < 1:
            return None

        try:
            # Calculate market metrics
            prices = [p.get('price', 0) for p in properties if p.get('price')]
            prices_per_sqm = [p.get('price', 0) / max(p.get('size_sqm', 1), 1) for p in properties if p.get('size_sqm')]
            avg_price_sqm = sum(prices_per_sqm) / len(prices_per_sqm) if prices_per_sqm else 0
            locations = list(set([p.get('location', '') for p in properties if p.get('location')]))

            props_summary = json.dumps(
                [{
                    'title': p.get('title', ''),
                    'location': p.get('location', ''),
                    'price': p.get('price', 0),
                    'size_sqm': p.get('size_sqm', 0),
                    'bedrooms': p.get('bedrooms', 0),
                    'developer': p.get('developer', ''),
                    'wolf_score': p.get('wolf_score', 0),
                    'roi': self._calculate_roi_projection(p),
                    'price_per_sqm': round(p.get('price', 0) / max(p.get('size_sqm', 1), 1)),
                    'discount_vs_market': f"{round((1 - (p.get('price', 0) / max(p.get('size_sqm', 1), 1)) / avg_price_sqm) * 100, 1)}%" if avg_price_sqm > 0 else "N/A"
                } for p in properties[:5]],
                ensure_ascii=False
            )

            psych_state = psychology.primary_state.value if psychology else 'NEUTRAL'

            prompt = f"""You are an expert Egyptian real estate market analyst providing STRATEGIC insights.
Your role is to analyze the market situation and explain WHY certain properties are good investments,
NOT just list what they cost.

PROPERTIES DATA:
{props_summary}

MARKET METRICS (calculated):
- Average price/sqm in results: {avg_price_sqm:,.0f} EGP
- Price range: {min(prices):,} - {max(prices):,} EGP
- Locations: {', '.join(locations)}

USER CONTEXT:
- Query: {query}
- Psychology: {psych_state}
- Market Reality: Egypt 2024-2025, 33%+ inflation, EGP devaluation, real estate = inflation hedge

OUTPUT REQUIREMENTS:
Produce ONLY valid JSON (no markdown, no code fences). Response MUST be in the SAME LANGUAGE as the user query.

{{
  "market_intelligence": {{
    "area_status": "growth/stable/emerging - 1 sentence about this area's current market status",
    "price_trend": "rising/stable/opportunity - current price movement with % if known",
    "demand_level": "high/medium/low with brief explanation",
    "investment_timing": "good_time/wait/urgent - is now a good time to buy here?"
  }},
  "key_insight": "THE most important finding - one powerful sentence that adds VALUE",
  "value_analysis": {{
    "best_value_property": "property title with best price/sqm ratio and WHY",
    "growth_potential_property": "property title with best appreciation potential and WHY",
    "safest_choice": "property title from best developer and WHY"
  }},
  "strategic_recommendation": {{
    "action": "buy_now/secure_unit/wait/compare_more",
    "reasoning": "2 sentences explaining the strategic logic",
    "specific_target": "which exact property and why"
  }},
  "risks": ["specific risk 1", "specific risk 2"],
  "opportunities": ["specific opportunity that most agents would miss"],
  "confidence_score": 0.0-1.0,
  "analytical_summary": "3-4 sentences of STRATEGIC analysis that explains market dynamics, value propositions, and investment logic. This should sound like advice from a market expert, NOT a property listing."
}}"""

            response = await self.openai_async.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"🔬 Deep Analysis: {result.get('key_insight', 'N/A')}")
            return result

        except Exception as e:
            logger.warning(f"Deep analysis failed (non-fatal): {e}")
            return None

    async def process_turn(
        self,
        query: str,
        history: List[Dict],
        profile: Optional[Dict] = None,
        language: str = "auto"
    ) -> Dict[str, Any]:
        """
        The Main Thinking Loop - V4 with Psychology & UI Actions.

        Args:
            query: User's natural language query
            history: Conversation history as list of dicts with 'role' and 'content'
            profile: User profile dict (optional)
            language: Preferred language ('ar', 'en', 'auto')

        Returns:
            Dict with 'response', 'properties', 'ui_actions', 'psychology'
        """
        try:
            logger.info(f"🧠 Wolf Brain V4: Processing query: {query[:100]}...")

            # 0. SETUP: Detect Language (if auto)
            if language == "auto":
                language = self._detect_language(query)
            logger.info(f"🌐 Language set to: {language}")

            # 1. PERCEPTION: Analyze Intent & Extract Filters (GPT-4o)
            intent = await self._analyze_intent(query, history)
            logger.info(f"📊 Intent extracted: {intent}")

            # 2. PSYCHOLOGY: Detect emotional state
            psychology = analyze_psychology(query, history, intent)
            logger.info(f"🧠 Psychology: {psychology.primary_state.value}, Urgency: {psychology.urgency_level.value}")

            # 3. PIVOT CHECK: Detect impossible requests
            reality_check = self._detect_impossible_request(intent, query)
            if reality_check:
                logger.info(f"🚨 REALITY_CHECK_PIVOT: {reality_check['detected']}")
                # Return pivot response with alternatives
                return {
                    "response": reality_check['message_ar'],
                    "properties": [],
                    "ui_actions": [{
                        "type": UIActionType.REALITY_CHECK.value,
                        "priority": 10,
                        "data": reality_check
                    }],
                    "psychology": psychology.to_dict(),
                    "agentic_action": "REALITY_CHECK_PIVOT"
                }

            # 4. HUNT: Data Retrieval (PostgreSQL + Vector Search)
            market_data = []
            if intent.get('action') == 'search':
                market_data = await self._search_database(intent.get('filters', {}))
                logger.info(f"🔍 Found {len(market_data)} properties")

            # 5. ANALYZE: Deal Scoring (XGBoost)
            scored_data = self._apply_wolf_analytics(market_data, intent)
            logger.info(f"📈 Scored and ranked {len(scored_data)} properties")

            # 6. STRATEGY: Determine Pitch Angle (Psychology-Aware)
            strategy = self._determine_strategy(profile, scored_data, intent, psychology)
            logger.info(f"🎯 Strategy: {strategy}")

            # 6.5 DEEP ANALYSIS (GPT-4o): Structured analytical insights
            deep_analysis = await self._deep_analysis(
                scored_data, query, psychology
            )
            if deep_analysis:
                logger.info(f"🔬 Deep Analysis complete: {deep_analysis.get('key_insight', 'N/A')[:80]}")

            # 7. SPEAK: Generate Response (Claude 3.5 Sonnet)
            # Now with deep analysis context for analytical-first responses
            response = await self._generate_wolf_narrative(
                query,
                scored_data,
                history,
                strategy,
                psychology,
                language=language,
                profile=profile,
                deep_analysis=deep_analysis
            )

            # 8. UI_TRIGGERS: Determine which visualizations to show
            ui_actions = self._determine_ui_actions(psychology, scored_data, intent, query)

            # 8.5 ANALYTICAL ACTIONS: Add deep-analysis-driven UI actions
            if deep_analysis:
                analytical_ui = generate_analytical_ui_actions(
                    deep_analysis, psychology, scored_data
                )
                # Merge: analytical actions take precedence for matching types
                existing_types = {a['type'] for a in ui_actions}
                for action in analytical_ui:
                    if action['type'] not in existing_types:
                        ui_actions.append(action)
                # Re-sort and limit
                ui_actions = sorted(ui_actions, key=lambda x: x.get('priority', 0), reverse=True)[:5]

            logger.info(f"🎨 UI Actions: {[a['type'] for a in ui_actions]}")

            # 9. PROACTIVE_ALERTS: Scan for opportunities (V2)
            proactive_alerts = proactive_alert_engine.scan_for_opportunities(
                user_preferences=intent.get('filters', {}),
                market_data=scored_data,
                psychology=psychology,
                intent=intent
            )
            logger.info(f"🚨 Proactive Alerts: {len(proactive_alerts)} alerts generated")

            # ═══════════════════════════════════════════════════════════════
            # PROTOCOL: IMPRESS FIRST (Suppression Logic)
            # If first message and no specific project requested, suppress property cards
            # This forces the AI to "Flex" with insights/charts instead of selling immediately
            # ═══════════════════════════════════════════════════════════════
            suppress_cards = False
            if len(history) == 0 and not intent.get('filters', {}).get('keywords'):
                suppress_cards = True
                logger.info("🚫 Suppressing property cards for Impress First Protocol (First Turn + No Keyword)")

            logger.info(f"✅ Wolf Brain V6 complete")
            return {
                "response": response,
                "properties": scored_data if not suppress_cards else [],
                "ui_actions": ui_actions,
                "proactive_alerts": proactive_alerts,
                "deep_analysis": deep_analysis,
                "psychology": psychology.to_dict(),
                "agentic_action": None
            }

        except Exception as e:
            logger.error(f"❌ Wolf Brain failed: {e}", exc_info=True)
            raise  # Let caller handle fallback

    def _detect_impossible_request(self, intent: Dict, query: str) -> Optional[Dict]:
        """
        Detect if user is asking for something that doesn't exist in the market.
        Triggers REALITY_CHECK_PIVOT agentic action.

        Returns:
            Reality check data if impossible request detected, None otherwise
        """
        query_lower = query.lower()
        filters = intent.get('filters', {})

        for combo in IMPOSSIBLE_COMBINATIONS:
            conditions = combo['conditions']

            # Check location match
            location_match = any(
                loc.lower() in query_lower or loc.lower() in filters.get('location', '').lower()
                for loc in conditions.get('locations', [])
            )

            # Check budget violation
            budget_violation = False
            if 'budget_max' in conditions and 'budget_max' in filters:
                budget_violation = filters['budget_max'] <= conditions['budget_max']

            # Check property type match
            type_match = any(
                ptype in query_lower
                for ptype in conditions.get('property_types', [])
            )

            # Trigger if location + (budget violation OR property type mismatch)
            if location_match and (budget_violation and type_match if 'property_types' in conditions else budget_violation):
                return {
                    "type": "reality_check",
                    "detected": combo['description'],
                    "message_ar": combo['reality_message_ar'],
                    "message_en": combo['reality_message_en'],
                    "alternatives": combo.get('alternatives', []),
                    "pivot_action": "REALITY_CHECK_PIVOT"
                }

        return None

    def _determine_ui_actions(
        self,
        psychology: PsychologyProfile,
        properties: List[Dict],
        intent: Dict,
        query: str
    ) -> List[Dict]:
        """
        Determine which UI visualizations to trigger based on context.
        V5 AGGRESSIVE: ALWAYS show analytics whenever there's data!
        
        Philosophy: Charts and visualizations DRAMATICALLY increase conversion.
        Show them proactively, not just when explicitly requested.

        Returns:
            List of ui_action dicts ready for frontend consumption
        """
        ui_actions = []
        query_lower = query.lower()

        # ═══════════════════════════════════════════════════════════════
        # RULE 0: ALWAYS show Investment Scorecard when we have properties
        # This is the MOST valuable visualization - shows Wolf Score breakdown
        # ═══════════════════════════════════════════════════════════════
        if properties and len(properties) >= 1:
            top_property = properties[0]
            ui_actions.append({
                "type": UIActionType.INVESTMENT_SCORECARD.value,
                "priority": 10,  # Highest priority - always show
                "data": {
                    "property": top_property,
                    "analysis": {
                        "match_score": top_property.get('wolf_score', 75),
                        "score_breakdown": top_property.get('score_breakdown', {
                            "value": 70,
                            "growth": 75,
                            "developer": 80
                        }),
                        "roi_projection": self._calculate_roi_projection(top_property),
                        "risk_level": "Low" if top_property.get('wolf_score', 0) >= 85 else "Medium" if top_property.get('wolf_score', 0) >= 70 else "Higher",
                        "market_trend": self._get_location_trend(top_property.get('location', '')),
                        "price_verdict": top_property.get('valuation_verdict', 'Fair'),
                        "price_per_sqm": top_property.get('price', 0) / max(top_property.get('size_sqm', 1), 1),
                        "area_avg_price_per_sqm": self._get_area_avg_price(top_property.get('location', ''))
                    }
                },
                "trigger_reason": "ALWAYS_SHOW: Investment scorecard for property analysis",
                "chart_reference": "شوف التحليل ده - الـ Wolf Score بيوضحلك كل حاجة"
            })

        # ═══════════════════════════════════════════════════════════════
        # RULE 1: Multiple properties -> ALWAYS show Comparison Matrix
        # ═══════════════════════════════════════════════════════════════
        if len(properties) > 1:
            ui_actions.append({
                "type": UIActionType.COMPARISON_MATRIX.value,
                "priority": 9,
                "data": {
                    "properties": properties[:4],
                    "best_value_id": self._find_best_value(properties),
                    "recommended_id": properties[0].get('id') if properties else None,
                    "comparison_metrics": ["price", "size_sqm", "price_per_sqm", "wolf_score", "location"]
                },
                "trigger_reason": "ALWAYS_SHOW: Multiple properties need comparison",
                "chart_reference": "المقارنة دي هتساعدك تاخد قرار صح"
            })

        # ═══════════════════════════════════════════════════════════════
        # RULE 2: ALWAYS show Inflation Killer for ANY property discussion
        # Real estate vs inflation is ALWAYS relevant in Egypt
        # ═══════════════════════════════════════════════════════════════
        if properties:
            avg_price = sum(p.get('price', 0) for p in properties) / len(properties)
            inflation_data = xgboost_predictor.calculate_inflation_hedge_score({
                'price': avg_price
            })
            ui_actions.append({
                "type": UIActionType.INFLATION_KILLER.value,
                "priority": 8,
                "data": {
                    "initial_investment": int(avg_price),
                    "years": 5,
                    "projections": inflation_data.get('projections', []),
                    "summary_cards": inflation_data.get('summary_cards', []),
                    "final_values": inflation_data.get('final_values', {}),
                    "percentage_changes": inflation_data.get('percentage_changes', {}),
                    "advantages": inflation_data.get('advantages', {}),
                    "verdict": inflation_data.get('verdict', {}),
                    "hedge_score": inflation_data.get('hedge_score', 0),
                    "egypt_inflation_rate": 33.7,  # Current Egypt inflation rate
                    "property_appreciation": 15.5  # Average property appreciation
                },
                "trigger_reason": "ALWAYS_SHOW: Investment protection visualization",
                "chart_reference": "بص على الرسم البياني - العقار بيحميك من التضخم إزاي"
            })

        # ═══════════════════════════════════════════════════════════════
        # RULE 3: ALWAYS show Payment Timeline when properties have installments
        # ═══════════════════════════════════════════════════════════════
        if properties:
            prop_with_installment = next(
                (p for p in properties if p.get('installment_years') or p.get('monthly_installment')),
                properties[0]  # Default to first property
            )
            ui_actions.append({
                "type": UIActionType.PAYMENT_TIMELINE.value,
                "priority": 7,
                "data": {
                    "property": prop_with_installment,
                    "payment": {
                        "total_price": prop_with_installment.get('price', 0),
                        "down_payment_percent": prop_with_installment.get('down_payment', 10),
                        "down_payment_amount": prop_with_installment.get('price', 0) * (prop_with_installment.get('down_payment', 10) / 100),
                        "installment_years": prop_with_installment.get('installment_years', 7),
                        "monthly_installment": prop_with_installment.get('monthly_installment', 0) or self._calculate_monthly(prop_with_installment),
                        "delivery_date": prop_with_installment.get('delivery_date', '2027')
                    }
                },
                "trigger_reason": "ALWAYS_SHOW: Payment plan visualization",
                "chart_reference": "خطة الدفع واضحة هنا - شوف الأقساط الشهرية"
            })

        # ═══════════════════════════════════════════════════════════════
        # RULE 4: Market Trend Chart - Show for location-specific searches
        # ═══════════════════════════════════════════════════════════════
        if properties:
            location = properties[0].get('location', '')
            if location:
                ui_actions.append({
                    "type": UIActionType.MARKET_TREND_CHART.value,
                    "priority": 6,
                    "data": {
                        "location": location,
                        "trend_data": self._generate_market_trend_data(location),
                        "price_growth_ytd": self._get_price_growth(location),
                        "demand_index": self._get_demand_index(location),
                        "supply_level": self._get_supply_level(location)
                    },
                    "trigger_reason": "ALWAYS_SHOW: Market trend for location",
                    "chart_reference": f"السوق في {location} ماشي إزاي - شوف الاتجاهات"
                })

        # ═══════════════════════════════════════════════════════════════
        # RULE 5: La2ta Alert - FOMO or ANY bargain property
        # ═══════════════════════════════════════════════════════════════
        bargains = [p for p in properties if p.get('valuation_verdict') == 'BARGAIN']
        if bargains or psychology.primary_state == PsychologicalState.FOMO:
            la2ta_bargains = xgboost_predictor.detect_la2ta(bargains if bargains else properties, threshold_percent=5.0)
            if la2ta_bargains:
                ui_actions.append({
                    "type": UIActionType.LA2TA_ALERT.value,
                    "priority": 11,  # Highest when bargains exist
                    "data": {
                        "properties": la2ta_bargains[:3],
                        "best_discount": la2ta_bargains[0].get('la2ta_score', 0),
                        "total_savings": sum(b.get('savings', 0) for b in la2ta_bargains[:3]),
                        "urgency_level": "high" if psychology.primary_state == PsychologicalState.FOMO else "medium",
                        "message_ar": f"🐺 لقيتلك {len(la2ta_bargains)} لقطة! ده تحت السوق",
                        "message_en": f"Found {len(la2ta_bargains)} bargain(s)! Below market price"
                    },
                    "trigger_reason": "BARGAIN properties detected",
                    "chart_reference": "شايف اللقطة دي؟ تحت السوق بـ {}%!".format(
                        la2ta_bargains[0].get('la2ta_score', 10)
                    )
                })

        # ═══════════════════════════════════════════════════════════════
        # RULE 6: Law 114 Guardian - Risk-averse OR legal keywords
        # ═══════════════════════════════════════════════════════════════
        legal_keywords = ['عقد', 'contract', 'قانون', 'legal', 'ضمان', 'guarantee', 'أمان', 'safe', 'مخاطر', 'risk']
        if (psychology.primary_state == PsychologicalState.RISK_AVERSE or
            any(kw in query_lower for kw in legal_keywords)):
            ui_actions.append({
                "type": UIActionType.LAW_114_GUARDIAN.value,
                "priority": 5,
                "data": {
                    "status": "ready",
                    "capabilities": [
                        "كشف البنود المخفية (Red Flag Detection)",
                        "التحقق من بنود العقد الناقصة",
                        "مراجعة شروط المطور",
                        "التوافق مع قانون 114"
                    ],
                    "cta": {
                        "text_ar": "ارفع العقد وأنا أفحصه",
                        "text_en": "Upload contract for AI scan"
                    }
                },
                "trigger_reason": "Legal safety visualization",
                "chart_reference": "عايز تطمن على العقد؟ ارفعه وأنا أفحصه"
            })

        # ═══════════════════════════════════════════════════════════════
        # V6: ADVANCED ANALYTICS - Context-Aware Triggers
        # ═══════════════════════════════════════════════════════════════

        # RULE 7: Area Analysis - When user asks about specific area or compares areas
        area_keywords = ['منطقة', 'area', 'location', 'مكان', 'فين', 'where', 'أحسن منطقة', 'best area', 
                        'التجمع', 'زايد', 'أكتوبر', 'العاصمة', 'الساحل', 'مدينتي']
        if any(kw in query_lower for kw in area_keywords) and properties:
            locations = list(set(p.get('location', '') for p in properties if p.get('location')))
            ui_actions.append({
                "type": UIActionType.AREA_ANALYSIS.value,
                "priority": 8,
                "data": {
                    "areas": [self._generate_area_analysis(loc) for loc in locations[:5]],
                    "comparison": {
                        "cheapest_area": min(locations, key=lambda l: self._get_area_avg_price(l)) if locations else None,
                        "highest_growth": self._get_highest_growth_area(locations),
                        "best_for_families": self._get_best_family_area(locations),
                        "best_for_investment": self._get_best_investment_area(locations)
                    },
                    "price_heatmap": self._generate_price_heatmap(locations)
                },
                "trigger_reason": "Area analysis requested",
                "chart_reference": "شوف تحليل المناطق - فين أحسن سعر وأعلى نمو"
            })

        # RULE 8: Developer Analysis - When user asks about developers or specific developer
        developer_keywords = ['مطور', 'developer', 'شركة', 'company', 'إعمار', 'سوديك', 'بالم هيلز', 
                             'ماونتن فيو', 'طلعت', 'أورا', 'مين بنى', 'who built', 'سمعة', 'reputation']
        if any(kw in query_lower for kw in developer_keywords) and properties:
            developers = list(set(p.get('developer', '') for p in properties if p.get('developer')))
            ui_actions.append({
                "type": UIActionType.DEVELOPER_ANALYSIS.value,
                "priority": 7,
                "data": {
                    "developers": [self._generate_developer_analysis(dev) for dev in developers[:5]],
                    "ranking": {
                        "by_reputation": self._rank_developers_by_reputation(developers),
                        "by_price_value": self._rank_developers_by_value(developers),
                        "by_delivery_record": self._rank_developers_by_delivery(developers)
                    },
                    "tier_explanation": {
                        "tier1": "المطورين الكبار - أعلى سمعة وأغلى سعر",
                        "tier2": "مطورين ممتازين - سعر معقول وجودة عالية",
                        "tier3": "مطورين صاعدين - أسعار تنافسية"
                    }
                },
                "trigger_reason": "Developer analysis requested",
                "chart_reference": "مقارنة المطورين - مين أحسن من حيث السمعة والسعر"
            })

        # RULE 9: Property Type Analysis - When user compares types
        type_keywords = ['شقة', 'apartment', 'فيلا', 'villa', 'تاون', 'townhouse', 'دوبلكس', 'duplex',
                        'ستوديو', 'studio', 'بنتهاوس', 'penthouse', 'نوع', 'type', 'أيه الفرق', 'difference']
        if any(kw in query_lower for kw in type_keywords) and properties:
            types = list(set(p.get('type', '') for p in properties if p.get('type')))
            ui_actions.append({
                "type": UIActionType.PROPERTY_TYPE_ANALYSIS.value,
                "priority": 6,
                "data": {
                    "types": [self._generate_type_analysis(t, properties) for t in types],
                    "recommendation": {
                        "for_singles": "Studio / 1BR Apartment",
                        "for_couples": "2BR Apartment",
                        "for_families": "3BR+ Apartment / Townhouse",
                        "for_luxury": "Villa / Penthouse",
                        "for_investment": "2BR Apartment (highest rental demand)"
                    },
                    "price_comparison": self._compare_types_by_price(properties)
                },
                "trigger_reason": "Property type comparison",
                "chart_reference": "مقارنة أنواع العقارات - شقة ولا فيلا ولا تاون هاوس"
            })

        # RULE 10: Payment Plan Analysis - When user asks about payments/installments
        payment_keywords = ['قسط', 'تقسيط', 'installment', 'دفع', 'payment', 'مقدم', 'down payment',
                          'سنوات', 'years', 'شهري', 'monthly', 'أقل مقدم', 'أطول فترة', 'خطة']
        if any(kw in query_lower for kw in payment_keywords) and properties:
            ui_actions.append({
                "type": UIActionType.PAYMENT_PLAN_ANALYSIS.value,
                "priority": 9,
                "data": {
                    "plans": [self._extract_payment_plan(p) for p in properties],
                    "best_plans": {
                        "lowest_down_payment": self._find_lowest_down_payment(properties),
                        "longest_installment": self._find_longest_installment(properties),
                        "lowest_monthly": self._find_lowest_monthly(properties)
                    },
                    "comparison_table": self._generate_payment_comparison(properties),
                    "tips": [
                        "المقدم الأقل = سيولة أكتر في إيدك",
                        "الفترة الأطول = قسط شهري أقل",
                        "بعض المطورين بيدوا خصم للكاش"
                    ]
                },
                "trigger_reason": "Payment plan analysis requested",
                "chart_reference": "مقارنة خطط الدفع - شوف أقل مقدم وأطول فترة سداد"
            })

        # RULE 11: Resale vs Developer Analysis - When user compares primary/secondary
        resale_keywords = ['ريسيل', 'resale', 'إعادة بيع', 'مستعمل', 'جديد', 'new', 'من المطور', 
                         'from developer', 'سوق ثانوي', 'secondary', 'primary']
        if any(kw in query_lower for kw in resale_keywords) and properties:
            resale_props = [p for p in properties if p.get('sale_type', '').lower() in ['resale', 'ريسيل']]
            developer_props = [p for p in properties if p.get('sale_type', '').lower() not in ['resale', 'ريسيل']]
            ui_actions.append({
                "type": UIActionType.RESALE_VS_DEVELOPER.value,
                "priority": 8,
                "data": {
                    "resale": {
                        "count": len(resale_props),
                        "avg_price": sum(p.get('price', 0) for p in resale_props) / max(len(resale_props), 1),
                        "avg_price_per_sqm": self._avg_price_per_sqm(resale_props),
                        "pros": ["سعر أقل", "جاهز للتسليم", "تشطيب كامل عادةً"],
                        "cons": ["مفيش خطة سداد طويلة", "قد يحتاج صيانة"]
                    },
                    "developer": {
                        "count": len(developer_props),
                        "avg_price": sum(p.get('price', 0) for p in developer_props) / max(len(developer_props), 1),
                        "avg_price_per_sqm": self._avg_price_per_sqm(developer_props),
                        "pros": ["تقسيط طويل", "وحدة جديدة", "ضمان المطور"],
                        "cons": ["سعر أعلى", "انتظار التسليم"]
                    },
                    "recommendation": self._recommend_resale_or_developer(query_lower, psychology),
                    "price_difference_percent": self._calc_resale_discount(resale_props, developer_props)
                },
                "trigger_reason": "Resale vs Developer comparison",
                "chart_reference": "ريسيل ولا من المطور؟ شوف المقارنة الكاملة"
            })

        # RULE 12: ROI Calculator - For investors asking about returns
        roi_keywords = ['استثمار', 'investment', 'عائد', 'return', 'roi', 'إيجار', 'rent', 'rental',
                       'ربح', 'profit', 'yield', 'كام هيجيب', 'how much return', 'passive income']
        if (any(kw in query_lower for kw in roi_keywords) or 
            psychology.primary_state == PsychologicalState.GREED_DRIVEN) and properties:
            ui_actions.append({
                "type": UIActionType.ROI_CALCULATOR.value,
                "priority": 10,
                "data": {
                    "properties": [self._calculate_full_roi(p) for p in properties[:3]],
                    "market_benchmarks": {
                        "avg_rental_yield_egypt": 5.5,
                        "avg_capital_appreciation": 15.0,
                        "bank_deposit_rate": 22.0,
                        "inflation_rate": 33.7
                    },
                    "comparison": {
                        "vs_bank": self._compare_to_bank_deposit(properties[0]) if properties else None,
                        "vs_gold": self._compare_to_gold(properties[0]) if properties else None,
                        "vs_stocks": self._compare_to_stocks(properties[0]) if properties else None
                    },
                    "best_investment": max(properties, key=lambda p: self._calculate_roi_projection(p)) if properties else None
                },
                "trigger_reason": "ROI calculation requested",
                "chart_reference": "حسبتلك العائد المتوقع - شوف الأرقام"
            })

        # Sort by priority (highest first) and return
        # LIMIT to top 5 visualizations for comprehensive analysis
        sorted_actions = sorted(ui_actions, key=lambda x: x['priority'], reverse=True)
        return sorted_actions[:5]

    def _calculate_roi_projection(self, property: Dict) -> float:
        """Calculate estimated ROI based on location and property type."""
        location = property.get('location', '')
        base_roi = 5.5
        
        # Location multipliers
        if 'New Capital' in location or 'العاصمة' in location:
            base_roi += 3.0
        elif 'New Cairo' in location or 'التجمع' in location:
            base_roi += 1.5
        elif 'Sheikh Zayed' in location or 'زايد' in location:
            base_roi += 1.0
        elif 'North Coast' in location or 'الساحل' in location:
            base_roi += 2.0
            
        return round(base_roi, 1)

    def _get_location_trend(self, location: str) -> str:
        """Get market trend for location."""
        bullish_areas = ['New Capital', 'العاصمة', 'Mostakbal', 'المستقبل', 'New Cairo', 'North Coast']
        stable_areas = ['Sheikh Zayed', 'زايد', '6th October', 'أكتوبر']
        
        if any(area in location for area in bullish_areas):
            return "Bullish 📈"
        elif any(area in location for area in stable_areas):
            return "Stable ⚖️"
        return "Growing 📊"

    def _get_area_avg_price(self, location: str) -> int:
        """Get average price per sqm for location."""
        area_prices = {
            'New Cairo': 65000,
            'التجمع': 65000,
            'Sheikh Zayed': 70000,
            'زايد': 70000,
            'New Capital': 55000,
            'العاصمة': 55000,
            '6th October': 45000,
            'أكتوبر': 45000,
            'Madinaty': 60000,
            'مدينتي': 60000,
            'North Coast': 80000,
            'الساحل': 80000
        }
        for area, price in area_prices.items():
            if area in location:
                return price
        return 50000  # Default

    def _calculate_monthly(self, property: Dict) -> int:
        """Calculate monthly installment if not provided."""
        price = property.get('price', 0)
        down_payment = property.get('down_payment', 10) / 100
        years = property.get('installment_years', 7)
        
        remaining = price * (1 - down_payment)
        months = years * 12
        return int(remaining / months) if months > 0 else 0

    def _generate_market_trend_data(self, location: str) -> List[Dict]:
        """Generate market trend data for visualization."""
        import random
        
        # Base price index for different locations
        base_indices = {
            'New Cairo': 145, 'التجمع': 145,
            'Sheikh Zayed': 150, 'زايد': 150,
            'New Capital': 130, 'العاصمة': 130,
            '6th October': 125, 'أكتوبر': 125,
            'North Coast': 160, 'الساحل': 160
        }
        
        base = 100
        for area, idx in base_indices.items():
            if area in location:
                base = idx
                break
        
        # Generate 12 months of data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        current_year = 2025
        trend_data = []
        
        value = base - 20  # Start 20 points lower
        for i, month in enumerate(months):
            growth = random.uniform(0.5, 2.5)  # Monthly growth
            value += growth
            trend_data.append({
                "month": f"{month} {current_year}",
                "price_index": round(value, 1),
                "volume": random.randint(50, 150)
            })
        
        return trend_data

    def _get_price_growth(self, location: str) -> float:
        """Get YTD price growth for location."""
        growth_rates = {
            'New Capital': 25.5, 'العاصمة': 25.5,
            'North Coast': 22.0, 'الساحل': 22.0,
            'New Cairo': 18.5, 'التجمع': 18.5,
            'Sheikh Zayed': 15.0, 'زايد': 15.0,
            '6th October': 12.0, 'أكتوبر': 12.0
        }
        for area, rate in growth_rates.items():
            if area in location:
                return rate
        return 14.0  # Default

    def _get_demand_index(self, location: str) -> str:
        """Get demand level for location."""
        high_demand = ['New Capital', 'North Coast', 'New Cairo', 'العاصمة', 'الساحل', 'التجمع']
        if any(area in location for area in high_demand):
            return "High 🔥"
        return "Medium 📊"

    def _get_supply_level(self, location: str) -> str:
        """Get supply level for location."""
        limited_supply = ['North Coast', 'الساحل', 'Madinaty', 'مدينتي']
        if any(area in location for area in limited_supply):
            return "Limited ⚡"
        return "Moderate 📦"

    # ═══════════════════════════════════════════════════════════════
    # V6: ADVANCED ANALYTICS HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _generate_area_analysis(self, location: str) -> Dict:
        """Generate comprehensive analysis for a specific area."""
        return {
            "name": location,
            "avg_price_per_sqm": self._get_area_avg_price(location),
            "price_growth_ytd": self._get_price_growth(location),
            "demand_level": self._get_demand_index(location),
            "supply_level": self._get_supply_level(location),
            "market_trend": self._get_location_trend(location),
            "best_for": self._get_area_best_for(location),
            "top_developers": self._get_area_top_developers(location),
            "pros": self._get_area_pros(location),
            "cons": self._get_area_cons(location)
        }

    def _get_area_best_for(self, location: str) -> List[str]:
        """Get what the area is best suited for."""
        area_specialties = {
            'New Cairo': ['عائلات', 'استثمار طويل المدى', 'راحة وخصوصية'],
            'التجمع': ['عائلات', 'استثمار طويل المدى', 'راحة وخصوصية'],
            'Sheikh Zayed': ['عائلات كبيرة', 'فيلات فاخرة', 'مدارس دولية'],
            'زايد': ['عائلات كبيرة', 'فيلات فاخرة', 'مدارس دولية'],
            'New Capital': ['استثمار', 'موظفين حكومة', 'نمو سريع'],
            'العاصمة': ['استثمار', 'موظفين حكومة', 'نمو سريع'],
            '6th October': ['ميزانية محدودة', 'شباب', 'قرب الجيزة'],
            'أكتوبر': ['ميزانية محدودة', 'شباب', 'قرب الجيزة'],
            'North Coast': ['صيفي', 'استثمار موسمي', 'إيجار سياحي'],
            'الساحل': ['صيفي', 'استثمار موسمي', 'إيجار سياحي'],
            'Madinaty': ['عائلات', 'كمباوند متكامل', 'أمان']
        }
        for area, specs in area_specialties.items():
            if area in location:
                return specs
        return ['سكن عام', 'استثمار']

    def _get_area_top_developers(self, location: str) -> List[str]:
        """Get top developers in the area."""
        area_developers = {
            'New Cairo': ['TMG', 'Hyde Park', 'SODIC', 'Palm Hills'],
            'Sheikh Zayed': ['Palm Hills', 'SODIC', 'Ora', 'Emaar'],
            'New Capital': ['City Edge', 'Tatweer Misr', 'Misr Italia'],
            '6th October': ['Palm Hills', 'Mountain View', 'Better Home'],
            'North Coast': ['Emaar', 'SODIC', 'Ora', 'Mountain View']
        }
        for area, devs in area_developers.items():
            if area in location:
                return devs
        return ['Various Developers']

    def _get_area_pros(self, location: str) -> List[str]:
        """Get pros of the area."""
        area_pros = {
            'New Cairo': ['بنية تحتية ممتازة', 'كمباوندات راقية', 'قرب من المطار'],
            'Sheikh Zayed': ['هدوء', 'مساحات خضراء', 'مدارس دولية'],
            'New Capital': ['مشاريع جديدة', 'أسعار تنافسية', 'نمو مستقبلي'],
            '6th October': ['أسعار معقولة', 'قرب من الجيزة', 'خيارات متنوعة'],
            'North Coast': ['إطلالة بحر', 'عائد إيجار موسمي', 'ترفيه']
        }
        for area, pros in area_pros.items():
            if area in location:
                return pros
        return ['موقع جيد', 'خدمات متاحة']

    def _get_area_cons(self, location: str) -> List[str]:
        """Get cons of the area."""
        area_cons = {
            'New Cairo': ['زحمة الطريق الدائري', 'أسعار مرتفعة'],
            'Sheikh Zayed': ['بعد عن وسط البلد', 'أسعار مرتفعة'],
            'New Capital': ['مسافة من القاهرة', 'خدمات لسه بتتطور'],
            '6th October': ['زحمة المحور', 'بعض المناطق مزدحمة'],
            'North Coast': ['موسمي فقط', 'بعيد عن القاهرة']
        }
        for area, cons in area_cons.items():
            if area in location:
                return cons
        return ['مسافة من المركز']

    def _get_highest_growth_area(self, locations: List[str]) -> Optional[str]:
        """Find area with highest price growth."""
        if not locations:
            return None
        return max(locations, key=lambda l: self._get_price_growth(l))

    def _get_best_family_area(self, locations: List[str]) -> Optional[str]:
        """Find best area for families."""
        family_areas = ['New Cairo', 'التجمع', 'Sheikh Zayed', 'زايد', 'Madinaty', 'مدينتي']
        for loc in locations:
            if any(area in loc for area in family_areas):
                return loc
        return locations[0] if locations else None

    def _get_best_investment_area(self, locations: List[str]) -> Optional[str]:
        """Find best area for investment."""
        investment_areas = ['New Capital', 'العاصمة', 'North Coast', 'الساحل', 'Mostakbal']
        for loc in locations:
            if any(area in loc for area in investment_areas):
                return loc
        return self._get_highest_growth_area(locations)

    def _generate_price_heatmap(self, locations: List[str]) -> List[Dict]:
        """Generate price heatmap data for areas."""
        return [
            {
                "location": loc,
                "avg_price_per_sqm": self._get_area_avg_price(loc),
                "intensity": min(100, int(self._get_area_avg_price(loc) / 1000))  # Normalize to 0-100
            }
            for loc in locations
        ]

    def _generate_developer_analysis(self, developer: str) -> Dict:
        """Generate comprehensive analysis for a developer."""
        return {
            "name": developer,
            "tier": self._get_developer_tier(developer),
            "reputation_score": self._get_developer_reputation(developer),
            "avg_price_premium": self._get_developer_price_premium(developer),
            "delivery_rating": self._get_developer_delivery_rating(developer),
            "popular_projects": self._get_developer_projects(developer),
            "strengths": self._get_developer_strengths(developer)
        }

    def _get_developer_tier(self, developer: str) -> str:
        """Get developer tier (1, 2, or 3)."""
        dev_lower = developer.lower()
        tier1 = ['tmg', 'talaat', 'emaar', 'sodic', 'mountain view', 'palm hills', 'ora', 'city edge']
        tier2 = ['hyde park', 'tatweer', 'misr italia', 'better home', 'gates', 'marakez']
        
        if any(d in dev_lower for d in tier1):
            return "Tier 1 ⭐⭐⭐"
        elif any(d in dev_lower for d in tier2):
            return "Tier 2 ⭐⭐"
        return "Tier 3 ⭐"

    def _get_developer_reputation(self, developer: str) -> int:
        """Get developer reputation score (0-100)."""
        dev_lower = developer.lower()
        reputations = {
            'tmg': 95, 'talaat': 95, 'emaar': 98, 'sodic': 92,
            'mountain view': 90, 'palm hills': 93, 'ora': 88,
            'hyde park': 85, 'tatweer': 82, 'city edge': 85
        }
        for dev, score in reputations.items():
            if dev in dev_lower:
                return score
        return 70  # Default

    def _get_developer_price_premium(self, developer: str) -> str:
        """Get developer price premium vs market average."""
        tier = self._get_developer_tier(developer)
        if "Tier 1" in tier:
            return "+15-25% فوق متوسط السوق"
        elif "Tier 2" in tier:
            return "+5-15% فوق متوسط السوق"
        return "سعر السوق"

    def _get_developer_delivery_rating(self, developer: str) -> str:
        """Get developer delivery track record."""
        dev_lower = developer.lower()
        excellent = ['tmg', 'emaar', 'sodic', 'palm hills']
        good = ['mountain view', 'hyde park', 'ora']
        
        if any(d in dev_lower for d in excellent):
            return "ممتاز - التسليم في الموعد ✅"
        elif any(d in dev_lower for d in good):
            return "جيد - تأخير بسيط أحياناً 🟡"
        return "متوسط - راجع سابقة الأعمال"

    def _get_developer_projects(self, developer: str) -> List[str]:
        """Get popular projects by developer."""
        projects = {
            'tmg': ['Madinaty', 'Rehab City', 'Celia'],
            'emaar': ['Uptown Cairo', 'Mivida', 'Cairo Gate'],
            'sodic': ['Allegria', 'Villette', 'East Town'],
            'palm hills': ['Palm Hills October', 'Palm Hills Katameya', 'Badya'],
            'mountain view': ['iCity', 'Mountain View October', 'Lagoon Beach'],
            'ora': ['ZED', 'Silversands'],
            'hyde park': ['Hyde Park New Cairo', 'Tawny Hyde Park']
        }
        dev_lower = developer.lower()
        for dev, projs in projects.items():
            if dev in dev_lower:
                return projs
        return []

    def _get_developer_strengths(self, developer: str) -> List[str]:
        """Get developer key strengths."""
        dev_lower = developer.lower()
        if any(d in dev_lower for d in ['tmg', 'talaat']):
            return ['خبرة 50+ سنة', 'مجتمعات متكاملة', 'تسليم موثوق']
        elif 'emaar' in dev_lower:
            return ['علامة عالمية', 'جودة بناء عالية', 'تصميم فاخر']
        elif 'sodic' in dev_lower:
            return ['ابتكار في التصميم', 'مواقع مميزة', 'مجتمعات راقية']
        return ['مطور موثوق']

    def _rank_developers_by_reputation(self, developers: List[str]) -> List[str]:
        """Rank developers by reputation."""
        return sorted(developers, key=lambda d: self._get_developer_reputation(d), reverse=True)

    def _rank_developers_by_value(self, developers: List[str]) -> List[str]:
        """Rank developers by price value."""
        return sorted(developers, key=lambda d: self._get_developer_reputation(d))  # Lower tier = better value

    def _rank_developers_by_delivery(self, developers: List[str]) -> List[str]:
        """Rank developers by delivery record."""
        return self._rank_developers_by_reputation(developers)  # Same as reputation for now

    def _generate_type_analysis(self, property_type: str, properties: List[Dict]) -> Dict:
        """Generate analysis for a property type."""
        type_props = [p for p in properties if p.get('type', '').lower() == property_type.lower()]
        return {
            "type": property_type,
            "count": len(type_props),
            "avg_price": sum(p.get('price', 0) for p in type_props) / max(len(type_props), 1),
            "avg_size": sum(p.get('size_sqm', 0) for p in type_props) / max(len(type_props), 1),
            "avg_price_per_sqm": self._avg_price_per_sqm(type_props),
            "best_for": self._get_type_best_for(property_type),
            "typical_sizes": self._get_typical_sizes(property_type)
        }

    def _get_type_best_for(self, property_type: str) -> str:
        """Get who the property type is best for."""
        type_mapping = {
            'apartment': 'شباب، أزواج، عائلات صغيرة',
            'villa': 'عائلات كبيرة، باحثين عن الخصوصية',
            'townhouse': 'عائلات متوسطة، باحثين عن حديقة خاصة',
            'twinhouse': 'عائلات، يريدون فيلا بسعر أقل',
            'penthouse': 'باحثين عن الفخامة والإطلالة',
            'duplex': 'عائلات تحتاج مساحة، استقلالية الأدوار',
            'studio': 'أفراد، استثمار للإيجار'
        }
        return type_mapping.get(property_type.lower(), 'متنوع')

    def _get_typical_sizes(self, property_type: str) -> str:
        """Get typical sizes for property type."""
        sizes = {
            'apartment': '80-200 متر',
            'villa': '300-600 متر',
            'townhouse': '200-350 متر',
            'twinhouse': '250-400 متر',
            'penthouse': '200-400 متر',
            'duplex': '180-300 متر',
            'studio': '40-70 متر'
        }
        return sizes.get(property_type.lower(), '100-200 متر')

    def _compare_types_by_price(self, properties: List[Dict]) -> List[Dict]:
        """Compare property types by price."""
        types = {}
        for p in properties:
            ptype = p.get('type', 'Unknown')
            if ptype not in types:
                types[ptype] = []
            types[ptype].append(p)
        
        return [
            {
                "type": t,
                "avg_price": sum(p.get('price', 0) for p in props) / len(props),
                "avg_price_per_sqm": self._avg_price_per_sqm(props),
                "count": len(props)
            }
            for t, props in types.items()
        ]

    def _extract_payment_plan(self, property: Dict) -> Dict:
        """Extract payment plan details from property."""
        price = property.get('price', 0)
        down_payment_pct = property.get('down_payment', 10)
        years = property.get('installment_years', 7)
        
        return {
            "property_id": property.get('id'),
            "property_title": property.get('title', ''),
            "total_price": price,
            "down_payment_percent": down_payment_pct,
            "down_payment_amount": price * (down_payment_pct / 100),
            "installment_years": years,
            "monthly_installment": self._calculate_monthly(property),
            "delivery_date": property.get('delivery_date', 'TBD')
        }

    def _find_lowest_down_payment(self, properties: List[Dict]) -> Optional[Dict]:
        """Find property with lowest down payment."""
        if not properties:
            return None
        best = min(properties, key=lambda p: p.get('down_payment', 100))
        return self._extract_payment_plan(best)

    def _find_longest_installment(self, properties: List[Dict]) -> Optional[Dict]:
        """Find property with longest installment period."""
        if not properties:
            return None
        best = max(properties, key=lambda p: p.get('installment_years', 0))
        return self._extract_payment_plan(best)

    def _find_lowest_monthly(self, properties: List[Dict]) -> Optional[Dict]:
        """Find property with lowest monthly installment."""
        if not properties:
            return None
        best = min(properties, key=lambda p: self._calculate_monthly(p))
        return self._extract_payment_plan(best)

    def _generate_payment_comparison(self, properties: List[Dict]) -> List[Dict]:
        """Generate payment plan comparison table."""
        return [self._extract_payment_plan(p) for p in properties[:5]]

    def _avg_price_per_sqm(self, properties: List[Dict]) -> float:
        """Calculate average price per sqm for a list of properties."""
        if not properties:
            return 0
        total_price = sum(p.get('price', 0) for p in properties)
        total_sqm = sum(p.get('size_sqm', 1) for p in properties)
        return round(total_price / max(total_sqm, 1), 0)

    def _recommend_resale_or_developer(self, query: str, psychology: PsychologyProfile) -> Dict:
        """Recommend resale vs developer based on context."""
        if psychology.primary_state == PsychologicalState.RISK_AVERSE:
            return {
                "recommendation": "developer",
                "reason_ar": "من المطور أضمن - ضمان وخطة سداد طويلة",
                "reason_en": "Developer is safer - warranty and long payment plan"
            }
        elif 'جاهز' in query or 'ready' in query.lower() or 'فوري' in query:
            return {
                "recommendation": "resale",
                "reason_ar": "الريسيل جاهز للتسليم الفوري",
                "reason_en": "Resale is ready for immediate delivery"
            }
        elif 'أقل سعر' in query or 'cheap' in query.lower() or 'أرخص' in query:
            return {
                "recommendation": "resale",
                "reason_ar": "الريسيل عادةً أرخص 10-20%",
                "reason_en": "Resale is usually 10-20% cheaper"
            }
        return {
            "recommendation": "depends",
            "reason_ar": "يعتمد على أولوياتك - السعر ولا خطة السداد",
            "reason_en": "Depends on your priorities - price vs payment plan"
        }

    def _calc_resale_discount(self, resale_props: List[Dict], developer_props: List[Dict]) -> float:
        """Calculate average discount of resale vs developer."""
        if not resale_props or not developer_props:
            return 0
        resale_avg = self._avg_price_per_sqm(resale_props)
        dev_avg = self._avg_price_per_sqm(developer_props)
        if dev_avg == 0:
            return 0
        return round(((dev_avg - resale_avg) / dev_avg) * 100, 1)

    def _calculate_full_roi(self, property: Dict) -> Dict:
        """Calculate comprehensive ROI for a property."""
        price = property.get('price', 0)
        location = property.get('location', '')
        
        # Estimated rental yield by location
        rental_yields = {
            'New Cairo': 5.5, 'Sheikh Zayed': 5.0, 'New Capital': 4.5,
            '6th October': 6.0, 'North Coast': 8.0, 'Madinaty': 5.5
        }
        rental_yield = 5.0
        for area, yield_rate in rental_yields.items():
            if area in location:
                rental_yield = yield_rate
                break
        
        annual_rent = price * (rental_yield / 100)
        appreciation = self._get_price_growth(location)
        
        return {
            "property_id": property.get('id'),
            "property_title": property.get('title', ''),
            "price": price,
            "location": location,
            "rental_yield_percent": rental_yield,
            "estimated_annual_rent": annual_rent,
            "estimated_monthly_rent": annual_rent / 12,
            "capital_appreciation_percent": appreciation,
            "total_annual_return": rental_yield + appreciation,
            "break_even_years": round(100 / (rental_yield + appreciation), 1) if (rental_yield + appreciation) > 0 else 99,
            "5_year_projection": {
                "rental_income": annual_rent * 5,
                "capital_gain": price * (appreciation / 100) * 5,
                "total_return": annual_rent * 5 + price * (appreciation / 100) * 5
            }
        }

    def _compare_to_bank_deposit(self, property: Dict) -> Dict:
        """Compare property investment to bank deposit."""
        price = property.get('price', 0)
        bank_rate = 22.0  # Current Egyptian bank deposit rate
        property_return = self._calculate_roi_projection(property) + self._get_price_growth(property.get('location', ''))
        
        return {
            "investment_amount": price,
            "bank_annual_return": price * (bank_rate / 100),
            "property_annual_return": price * (property_return / 100),
            "bank_5_year": price * (1 + bank_rate/100) ** 5,
            "property_5_year": price * (1 + property_return/100) ** 5,
            "winner": "property" if property_return > bank_rate else "bank",
            "difference_percent": abs(property_return - bank_rate)
        }

    def _compare_to_gold(self, property: Dict) -> Dict:
        """Compare property investment to gold."""
        price = property.get('price', 0)
        gold_return = 15.0  # Average gold appreciation in Egypt
        property_return = self._calculate_roi_projection(property) + self._get_price_growth(property.get('location', ''))
        
        return {
            "investment_amount": price,
            "gold_annual_return": gold_return,
            "property_annual_return": property_return,
            "winner": "property" if property_return > gold_return else "gold",
            "property_advantage": "إيجار شهري + زيادة قيمة" if property_return > gold_return else None
        }

    def _compare_to_stocks(self, property: Dict) -> Dict:
        """Compare property investment to Egyptian stocks."""
        price = property.get('price', 0)
        stock_return = 12.0  # Average EGX return (volatile)
        property_return = self._calculate_roi_projection(property) + self._get_price_growth(property.get('location', ''))
        
        return {
            "investment_amount": price,
            "stocks_annual_return": stock_return,
            "property_annual_return": property_return,
            "stocks_risk": "مرتفع جداً 📉📈",
            "property_risk": "منخفض نسبياً 📊",
            "winner": "property" if property_return > stock_return else "stocks"
        }

    def _find_best_value(self, properties: List[Dict]) -> Optional[int]:
        """Find property with best price per sqm."""
        if not properties:
            return None

        best = None
        best_ratio = float('inf')

        for prop in properties:
            price = prop.get('price', 0)
            size = prop.get('size_sqm', 1)
            if price > 0 and size > 0:
                ratio = price / size
                if ratio < best_ratio:
                    best_ratio = ratio
                    best = prop.get('id')

        return best

    async def _analyze_intent(self, query: str, history: List) -> Dict:
        """
        STEP 1: PERCEPTION (GPT-4o)
        Extract structured filters from natural language.
        """
        try:
            # Build a simple prompt for intent extraction
            system_msg = """You are an intent extraction system for Egyptian real estate.
Extract search filters from user queries and return JSON.

Output format:
{
  "action": "search" | "valuation" | "question",
  "filters": {
"location": string (e.g., "New Cairo", "Sheikh Zayed"),
"budget_min": int (in EGP, minimum budget),
"budget_max": int (in EGP, maximum budget),
"bedrooms": int,
"property_type": string,
"keywords": string (e.g., specific project name like "Solaris", "Hyde Park")
  }
}

IMPORTANT BUDGET RULES:
- Watch for ranges like "من 4 مليون لـ 15 مليون" (from 4M to 15M)
- "تحت X" means budget_max = X
- "فوق X" or "اكتر من X" means budget_min = X
- When a range is given, set BOTH budget_min AND budget_max
- 1 million = 1,000,000 EGP

Examples:
- "عايز شقة في التجمع تحت 2 مليون" → {"action": "search", "filters": {"location": "New Cairo", "budget_max": 2000000}}
- "Apartment from 4 million to 15 million" → {"action": "search", "filters": {"budget_min": 4000000, "budget_max": 15000000}}
- "من 4 لـ 15 مليون" → {"action": "search", "filters": {"budget_min": 4000000, "budget_max": 15000000}}
- "Apartment in Zayed, 3 bedrooms" → {"action": "search", "filters": {"location": "Sheikh Zayed", "bedrooms": 3}}
- "What do you have in El Patio?" → {"action": "search", "filters": {"keywords": "El Patio"}}
"""
            
            completion = await self.openai_async.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            intent = json.loads(completion.choices[0].message.content)
            
            # Ensure filters exist
            if 'filters' not in intent:
                intent['filters'] = {}
                
            return intent
            
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            # Fallback: assume it's a search
            return {"action": "search", "filters": {}}

    async def _search_database(self, filters: Dict) -> List[Dict]:
        """
        STEP 2: HUNT (Database Query)
        Query actual PostgreSQL database for properties.
        """
        try:
            async with AsyncSessionLocal() as db:
                # Build query text from filters
                query_parts = []
                if 'location' in filters:
                    query_parts.append(filters['location'])
                if 'bedrooms' in filters:
                    query_parts.append(f"{filters['bedrooms']} bedrooms")
                if 'property_type' in filters:
                    query_parts.append(filters['property_type'])
                if 'keywords' in filters:
                    query_parts.append(filters['keywords'])
                # Add budget hint for semantic search
                if 'budget_max' in filters and filters['budget_max']:
                    budget_mil = filters['budget_max'] / 1000000
                    query_parts.append(f"under {budget_mil} million")
                    
                query_text = " ".join(query_parts) if query_parts else "property"
                
                # Call the vector search service with price filtering built-in
                results = await db_search_properties(
                    db=db,
                    query_text=query_text,
                    limit=50,  # Higher limit for variety
                    similarity_threshold=0.50,  # Lower threshold for better recall
                    price_min=filters.get('budget_min'),  # Direct SQL filtering
                    price_max=filters.get('budget_max')   # Direct SQL filtering
                )
                
                # Double-check budget filter (in case search didn't apply it)
                if 'budget_max' in filters and filters['budget_max']:
                    results = [r for r in results if r.get('price', 0) <= filters['budget_max']]
                
                if 'budget_min' in filters and filters['budget_min']:
                    results = [r for r in results if r.get('price', 0) >= filters['budget_min']]
                
                # Filter by bedrooms if specified
                if 'bedrooms' in filters and filters['bedrooms']:
                    results = [r for r in results if r.get('bedrooms', 0) >= filters['bedrooms']]
                
                # Filter by property_type if specified (critical for apartment vs office/villa)
                if 'property_type' in filters and filters['property_type']:
                    requested_type = filters['property_type'].lower()
                    # Map common variations to standard types
                    type_mappings = {
                        'apartment': ['apartment', 'شقة', 'شقه', 'flat'],
                        'villa': ['villa', 'فيلا', 'فيللا'],
                        'townhouse': ['townhouse', 'تاون هاوس', 'تاونهاوس'],
                        'twinhouse': ['twinhouse', 'twin house', 'توين هاوس', 'توينهاوس'],
                        'penthouse': ['penthouse', 'بنتهاوس', 'بنت هاوس'],
                        'duplex': ['duplex', 'دوبلكس'],
                        'studio': ['studio', 'ستوديو'],
                        'office': ['office', 'مكتب', 'اوفيس']
                    }
                    
                    # Find matching type group
                    allowed_types = [requested_type]
                    for standard_type, variations in type_mappings.items():
                        if requested_type in variations or requested_type == standard_type:
                            allowed_types = variations + [standard_type]
                            break
                    
                    # Filter results
                    results = [
                        r for r in results 
                        if r.get('type', '').lower() in allowed_types
                    ]
                    logger.info(f"🏠 Property type filter: '{requested_type}' → {len(results)} results")
                
                return results[:5]  # Top 5 results
                
        except Exception as e:
            logger.error(f"Database search failed: {e}", exc_info=True)
            return []

    def _apply_wolf_analytics(self, properties: List[Dict], intent: Dict) -> List[Dict]:
        """
        STEP 3: ANALYZE (XGBoost Scoring)
        Find the "La2ta" (The Catch) - best deals.
        """
        if not properties:
            return []
            
        try:
            for prop in properties:
                # 1. VALUE SCORE (Price/sqm vs Market Average)
                price = prop.get('price', 0)
                size = prop.get('size_sqm', 1) or 1
                price_per_sqm = price / size
                
                # Market averages (approximate for now, will use real stats later)
                market_avg = 50000 
                if 'New Cairo' in prop.get('location', ''): market_avg = 65000
                elif 'Sheikh Zayed' in prop.get('location', ''): market_avg = 70000
                elif 'Capital' in prop.get('location', ''): market_avg = 60000
                
                # Lower price/sqm = Higher Value Score
                value_ratio = market_avg / (price_per_sqm or 1)
                value_score = min(100, max(0, int(value_ratio * 70)))
                
                # 2. GROWTH SCORE (Location Potential)
                growth_score = 70
                loc = prop.get('location', '')
                if 'New Capital' in loc or 'Mostakbal' in loc: growth_score = 90
                elif 'North Coast' in loc: growth_score = 85
                elif 'New Cairo' in loc: growth_score = 80
                
                # 3. DEVELOPER SCORE (Reputation)
                dev_score = 60
                developer = prop.get('developer', '').lower()
                tier1 = ['tmg', 'talaat', 'emaar', 'sodic', 'mountain view', 'palm hills', 'ora', 'city edge']
                tier2 = ['hydepark', 'tatweer', 'misr italia', 'better home', 'gates']
                
                if any(d in developer for d in tier1): dev_score = 95
                elif any(d in developer for d in tier2): dev_score = 80
                
                # FINAL WOLF SCORE WEIGHTING
                # Investment: 40% Value, 40% Growth, 20% Developer
                # Default: 35% Value, 35% Developer, 30% Growth
                final_score = int((value_score * 0.35) + (dev_score * 0.35) + (growth_score * 0.30))
                
                prop['wolf_score'] = final_score
                prop['score_breakdown'] = {
                    "value": value_score,
                    "growth": growth_score,
                    "developer": dev_score
                }
                
                prop['valuation_verdict'] = "BARGAIN" if value_score > 85 else "FAIR" if value_score > 60 else "PREMIUM"
                
            # Sort by Wolf Score (best deals first)
            return sorted(properties, key=lambda x: x.get('wolf_score', 0), reverse=True)[:5]
            
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return properties[:3]  # Return top 3 without scoring

    def _determine_strategy(
        self,
        profile: Optional[Dict],
        data: List[Dict],
        intent: Dict,
        psychology: Optional[PsychologyProfile] = None
    ) -> str:
        """
        STEP 6: STRATEGY (Psychology-Aware)
        Decide pitch angle based on emotional state and data.
        """
        # If no data, always pivot to discovery
        if not data:
            return "PIVOT_TO_DISCOVERY"

        # Use psychology if available
        if psychology:
            state = psychology.primary_state

            # Map psychological states to strategies
            if state == PsychologicalState.FOMO:
                # Check for bargains to exploit FOMO
                has_bargain = any(p.get('valuation_verdict') == 'BARGAIN' for p in data)
                return "AGGRESSIVE_BARGAIN_PITCH" if has_bargain else "SCARCITY_PITCH"

            elif state == PsychologicalState.GREED_DRIVEN:
                return "ROI_FOCUSED_PITCH"

            elif state == PsychologicalState.RISK_AVERSE:
                return "TRUST_BUILDING_PITCH"

            elif state == PsychologicalState.ANALYSIS_PARALYSIS:
                return "SIMPLIFY_AND_RECOMMEND"

            elif state == PsychologicalState.IMPULSE_BUYER:
                return "FAST_CLOSE_PITCH"

            elif state == PsychologicalState.TRUST_DEFICIT:
                return "PROOF_AND_AUTHORITY_PITCH"

        # Fallback to original logic
        is_investor = False
        if profile:
            is_investor = profile.get('investor_mode', False)

        has_bargain = any(p.get('valuation_verdict') == 'BARGAIN' for p in data)

        if has_bargain:
            return "AGGRESSIVE_BARGAIN_PITCH"
        elif is_investor:
            return "ROI_FOCUSED_PITCH"
        else:
            return "FAMILY_SAFETY_PITCH"

    async def _generate_wolf_narrative(
        self,
        query: str,
        data: List[Dict],
        history: List[Dict],
        strategy: str,
        psychology: Optional[PsychologyProfile] = None,
        language: str = "auto",
        profile: Optional[Dict] = None,
        deep_analysis: Optional[Dict] = None
    ) -> str:
        """
        STEP 7: SPEAK (Claude 3.5 Sonnet)
        Generate the Wolf's response using ONLY verified data.
        Now with psychology-aware context injection and language control.
        """
        try:
            # Extract user's first name for personalization
            user_first_name = None
            if profile and profile.get('full_name'):
                user_first_name = profile['full_name'].split()[0]

            # Prepare database context
            if not data and strategy == "PIVOT_TO_DISCOVERY":
                context_str = """
[DATABASE_CONTEXT]: EMPTY - No properties found matching criteria.

INSTRUCTION: Since no properties were found, you MUST ask clarifying questions:
- "ميزانيتك في حدود كام يا افندم؟" (What's your budget range, sir?)
- "بتدور في أي منطقة؟" (Which area are you looking in?)
- "سكن ولا استثمار؟" (Living or investment?)

DO NOT invent any properties. Be charming and helpful while gathering info.
"""
            elif not data:
                # Handle follow-up questions when no current property search was done
                # Fetch market stats for general insights but DON'T invent specific prices
                market_stats = await get_market_statistics()
                market_stats_context = format_statistics_for_ai(market_stats, None)
                
                context_str = f"""
═══════════════════════════════════════════════════════════════════════════════
          FOLLOW-UP RESPONSE MODE (No Property Search This Turn)
═══════════════════════════════════════════════════════════════════════════════

{market_stats_context}

[CURRENT CONTEXT]: User is asking a follow-up question. No property search was triggered this turn.

🚫 CRITICAL: PRICE HALLUCINATION PREVENTION 🚫
- You do NOT have specific properties in context right now
- If you mention prices, ONLY use the MARKET STATISTICS above
- NEVER say "prices from 0 to 0" or similar placeholder values
- If referring to a property shown earlier, say "العقار اللي عرضته" (the property I showed)
- Do NOT invent specific price ranges like "من X مليون لحد Y مليون" unless they match the market stats above

For Wolf Score questions, explain the methodology without inventing numbers:
- "الـ Wolf Score بيقيس 3 حاجات: القيمة مقابل السعر، فرص النمو، وقوة المطور"
- "كل ما السكور أعلى، كل ما الفرصة أحسن"
- Refer to "العقار اللي عرضته قبل كده" (the property I showed before) instead of inventing details

STRATEGY: {strategy}
"""
            else:
                # Fetch pre-computed market statistics for accurate data
                market_stats = await get_market_statistics()
                
                # Determine location from search for location-specific stats
                search_location = None
                if data and len(data) > 0:
                    search_location = data[0].get('location')
                
                # Format market stats for AI
                market_stats_context = format_statistics_for_ai(market_stats, search_location)
                
                # Format properties for Claude with EXPLICIT names - RAG ENFORCEMENT
                props_formatted = json.dumps(data, indent=2, ensure_ascii=False)
                property_list = chr(10).join([f"  {i+1}. \"{p.get('title', 'Unknown')}\" - {p.get('compound', '')} - {p.get('location', 'Unknown')} - {p.get('price', 0):,} EGP" for i, p in enumerate(data)])
                
                context_str = f"""
═══════════════════════════════════════════════════════════════════════════════
                          RAG SYSTEM - STRICT DATA GROUNDING
═══════════════════════════════════════════════════════════════════════════════

{market_stats_context}

═══════════════════════════════════════════════════════════════════════════════

[RETRIEVED PROPERTIES]: {len(data)} properties found in database

{property_list}

[FULL PROPERTY DATA]:
{props_formatted}

═══════════════════════════════════════════════════════════════════════════════
                         ABSOLUTE RULES - ZERO TOLERANCE
═══════════════════════════════════════════════════════════════════════════════

🚨 RAG ENFORCEMENT - YOU ARE A RETRIEVAL-AUGMENTED GENERATION SYSTEM 🚨

1. YOU CAN ONLY DISCUSS THE {len(data)} PROPERTIES LISTED ABOVE.
2. NEVER mention ANY property, compound, or developer NOT in the list above.
3. FORBIDDEN NAMES (unless they appear in the list above):
   - Palm Hills, Hyde Park, Regent's Park, Madinaty, Mountain View, Emaar
   - Sodic, Hassan Allam, Talaat Moustafa, MNHD, Arkan, Mivida
   - Any compound/developer name NOT explicitly in the retrieved data
   
4. If user asks about a compound NOT in your list, respond:
   "للأسف مش لاقي بيانات عن [compound name] دلوقتي في قاعدة البيانات. 
   بس عندي خيارات حلوة زي [mention 1-2 from your list]. تحب أقولك عنهم؟"

5. PRESENT PROPERTIES IN ORDER OF WOLF SCORE (best deals first):
   - Property 1 (wolf_score: {data[0].get('wolf_score', 85)}/100) = "اللقطة" (The Catch)
   - Use EXACT prices and sizes from the data above
   - Never round or estimate - use the exact numbers

6. EVERY property name you mention MUST be copy-pasted from the list above.

7. 🚫 PRICE HALLUCINATION PREVENTION:
   - NEVER invent price ranges that don't match the actual properties
   - The ACTUAL lowest price in results: {min([p.get('price', 0) for p in data]):,} EGP
   - The ACTUAL highest price in results: {max([p.get('price', 0) for p in data]):,} EGP
   - If you say "prices range from X to Y", X and Y MUST match the actual min/max above
   - DO NOT make up market statistics or averages not in the data

8. When presenting properties, simply list those you have - don't create fictional price comparisons.

9. WOLF SCORE EXPLANATION:
   If user asks "Why these properties?" or "How do you rank them?", explain the Wolf Score:
   - "أنا برتبهم حسب الـ Wolf Score اللي بيقيس 3 حاجات:"
   - "القيمة مقابل السعر (Value): سعر المتر مقارنة بمتوسط المنطقة"
   - "فرص النمو (High Growth): مستقبل المنطقة والعائد المتوقع"
   - "قوة المطور (Developer): سمعة الشركة وسابقة أعمالها"
   - You MUST mention the ACTUAL Wolf Score of the top property (e.g., "أول شقة دي واخدة [score]/100 عشان...")
   - Do NOT say "88/100" unless that is the REAL score.

STRATEGY: {strategy}
"""

            # Add psychology context if available
            psychology_context = ""
            if psychology:
                psychology_context = get_psychology_context_for_prompt(psychology)

                # Add visual integration hint if UI actions will be triggered
                if psychology.primary_state in [PsychologicalState.GREED_DRIVEN, PsychologicalState.FOMO]:
                    psychology_context += """
[VISUAL_INTEGRATION]
A chart or visualization is being shown to the user. Reference it in your response:
- "بص على الشاشة دلوقتي..." (Look at the screen now...)
- "الرسم البياني ده بيوضح..." (This chart shows...)
- "زي ما واضح في الأرقام..." (As shown in the numbers...)
"""

            # Add deep analysis context (GPT-4o analytical insights)
            deep_analysis_context = ""
            if deep_analysis:
                market_intel = deep_analysis.get('market_intelligence', {})
                value_analysis = deep_analysis.get('value_analysis', {})
                strategic_rec = deep_analysis.get('strategic_recommendation', {})

                deep_analysis_context = f"""

═══════════════════════════════════════════════════════════════════════════════
          🧠 MARKET INTELLIGENCE (from GPT-4o Analytical Engine)
═══════════════════════════════════════════════════════════════════════════════

📊 MARKET STATUS:
- Area Status: {market_intel.get('area_status', 'N/A')}
- Price Trend: {market_intel.get('price_trend', 'N/A')}
- Demand Level: {market_intel.get('demand_level', 'N/A')}
- Investment Timing: {market_intel.get('investment_timing', 'N/A')}

💡 KEY INSIGHT (START YOUR RESPONSE WITH THIS):
{deep_analysis.get('key_insight', 'N/A')}

📈 VALUE ANALYSIS:
- Best Value: {value_analysis.get('best_value_property', 'N/A')}
- Best Growth: {value_analysis.get('growth_potential_property', 'N/A')}
- Safest Choice: {value_analysis.get('safest_choice', 'N/A')}

🎯 STRATEGIC RECOMMENDATION:
- Action: {strategic_rec.get('action', 'evaluate')}
- Reasoning: {strategic_rec.get('reasoning', 'N/A')}
- Target Property: {strategic_rec.get('specific_target', 'N/A')}

⚠️ Risks: {json.dumps(deep_analysis.get('risks', []), ensure_ascii=False)}
✨ Opportunities: {json.dumps(deep_analysis.get('opportunities', []), ensure_ascii=False)}

📝 ANALYTICAL SUMMARY (USE THIS AS YOUR FOUNDATION):
{deep_analysis.get('analytical_summary', 'N/A')}

═══════════════════════════════════════════════════════════════════════════════
          🚨 MANDATORY: MARKET INTELLIGENCE FIRST RESPONSE 🚨
═══════════════════════════════════════════════════════════════════════════════

YOUR RESPONSE MUST FOLLOW THIS EXACT STRUCTURE:

**FIRST 40% - MARKET ANALYSIS (MANDATORY):**
1. Start with the KEY INSIGHT above - this is your hook
2. Explain the MARKET STATUS (area growth, price trends, demand)
3. Share the STRATEGIC insight (why now? what opportunity?)

**THEN 30% - PROPERTIES WITH CONTEXT:**
4. Present properties BECAUSE OF the analysis, not instead of it
5. Reference WHY each property fits the market situation
6. Use Wolf Score with explanation

**THEN 20% - HONEST ASSESSMENT:**
7. Mention ONE risk from the analysis
8. Counter with ONE opportunity

**FINALLY 10% - STRATEGIC CLOSE:**
9. End with a specific question that moves toward action

❌ FORBIDDEN: Starting with "عندي شقة..." or "لقيتلك..." without market context first
✅ REQUIRED: Starting with market insight like "التجمع دلوقتي في مرحلة نمو قوية..."
"""

            # Add user personalization context
            personalization_context = ""
            if user_first_name:
                personalization_context = f"""
[USER_PERSONALIZATION]
The user's name is "{user_first_name}". Address them by name occasionally to build rapport:
- "تمام يا {user_first_name}..." 
- "{user_first_name}, خليني أقولك حاجة..."
- "بص يا {user_first_name}..."
Do NOT overuse the name - use it 1-2 times per response maximum.
"""

            # Build Claude prompt with psychology + deep analysis
            system_prompt = AMR_SYSTEM_PROMPT + f"\n\n{context_str}" + psychology_context + deep_analysis_context + personalization_context
            
            # Add CRITICAL override at the end (Claude pays more attention to end of prompt)
            prices_in_results = [p.get('price', 0) for p in data] if data else [0]
            min_price = min(prices_in_results)
            max_price = max(prices_in_results)
            
            system_prompt += f"""

═══════════════════════════════════════════════════════════════════════════════
🚨🚨🚨 FINAL CRITICAL OVERRIDE - READ THIS CAREFULLY 🚨🚨🚨
═══════════════════════════════════════════════════════════════════════════════

VERSION: v2.5-anti-hallucination

THE PROPERTIES I GAVE YOU HAVE THESE ACTUAL PRICES:
- LOWEST PRICE IN RESULTS: {min_price:,} EGP
- HIGHEST PRICE IN RESULTS: {max_price:,} EGP

🚫 YOU MUST NOT SAY:
- "الأسعار من 4 مليون لـ 15 مليون" (if that's not the actual min/max above)
- Any price range that doesn't match the ACTUAL min/max above
- Developer names like "إعمار", "سوديك", "ماونتن فيو" unless they are in the properties I gave you

✅ YOU MUST SAY (example):
- "الأسعار بتبدأ من {min_price/1000000:.1f} مليون لحد {max_price/1000000:.1f} مليون جنيه"

IF I ONLY GAVE YOU ONE PROPERTY, just discuss THAT property. Don't make up price ranges.
"""

            # Language Enforcement
            if language == "ar":
                system_prompt += "\n\nCRITICAL INSTRUCTION: You MUST reply in Egyptian Arabic (لغة عامية مصرية محترفة style)."
            elif language == "en":
                system_prompt += "\n\nCRITICAL INSTRUCTION: You MUST reply in English."

            # Convert history to Claude format
            messages = []
            for msg in history[-10:]:  # Last 10 messages for context
                if isinstance(msg, dict):
                    messages.append(msg)
                elif hasattr(msg, 'content'):
                    role = "user" if msg.__class__.__name__ == "HumanMessage" else "assistant"
                    messages.append({"role": role, "content": msg.content})

            # Add current query
            messages.append({"role": "user", "content": query})

            # Call Claude (use Haiku for speed/cost or Sonnet if env configured)
            claude_model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

            response = await self.anthropic_async.messages.create(
                model=claude_model,
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Narrative generation failed: {e}", exc_info=True)
            return "عذراً، حصل مشكلة فنية. جرب تاني يا افندم. (Sorry, technical issue. Try again, sir.)"


# Singleton instance
hybrid_brain = OsoolHybridBrain()

# Export
__all__ = ["hybrid_brain", "OsoolHybridBrain"]
