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
from app.services.vector_search import search_properties as db_search_properties
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class UIActionType(Enum):
    """Types of UI visualizations that can be triggered."""
    INFLATION_KILLER = "inflation_killer"
    INVESTMENT_SCORECARD = "investment_scorecard"
    COMPARISON_MATRIX = "comparison_matrix"
    PAYMENT_TIMELINE = "payment_timeline"
    MARKET_TREND_CHART = "market_trend_chart"
    LA2TA_ALERT = "la2ta_alert"
    LAW_114_GUARDIAN = "law_114_guardian"
    REALITY_CHECK = "reality_check"


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

            # 7. SPEAK: Generate Response (Claude 3.5 Sonnet)
            response = await self._generate_wolf_narrative(
                query,
                scored_data,
                history,
                strategy,
                psychology,
                language=language,
                profile=profile
            )

            # 8. UI_TRIGGERS: Determine which visualizations to show
            ui_actions = self._determine_ui_actions(psychology, scored_data, intent, query)
            logger.info(f"🎨 UI Actions: {[a['type'] for a in ui_actions]}")

            # 9. PROACTIVE_ALERTS: Scan for opportunities (V2)
            proactive_alerts = proactive_alert_engine.scan_for_opportunities(
                user_preferences=intent.get('filters', {}),
                market_data=scored_data,
                psychology=psychology,
                intent=intent
            )
            logger.info(f"🚨 Proactive Alerts: {len(proactive_alerts)} alerts generated")

            logger.info(f"✅ Wolf Brain V5 complete")
            return {
                "response": response,
                "properties": scored_data,
                "ui_actions": ui_actions,
                "proactive_alerts": proactive_alerts,
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
        V2: Now includes full visualization data and chart references.

        Returns:
            List of ui_action dicts ready for frontend consumption
        """
        ui_actions = []
        query_lower = query.lower()

        # Rule 1: FOMO user + bargain property -> show La2ta Alert
        if psychology.primary_state == PsychologicalState.FOMO:
            bargains = [p for p in properties if p.get('valuation_verdict') == 'BARGAIN']
            if bargains:
                # Use detect_la2ta for enhanced bargain data
                la2ta_bargains = xgboost_predictor.detect_la2ta(bargains, threshold_percent=5.0)
                if la2ta_bargains:
                    ui_actions.append({
                        "type": UIActionType.LA2TA_ALERT.value,
                        "priority": 10,
                        "data": {
                            "properties": la2ta_bargains[:3],
                            "best_discount": la2ta_bargains[0].get('la2ta_score', 0),
                            "total_savings": sum(b.get('savings', 0) for b in la2ta_bargains[:3]),
                            "message_ar": f"🐺 لقيتلك {len(la2ta_bargains)} لقطة! ده تحت السوق",
                            "message_en": f"Found {len(la2ta_bargains)} bargain(s)! Below market price"
                        },
                        "trigger_reason": "FOMO psychology + BARGAIN properties",
                        "chart_reference": "شايف اللقطة دي؟ تحت السوق بـ {}%!".format(
                            la2ta_bargains[0].get('la2ta_score', 10)
                        )
                    })

        # Rule 2: Greed-driven user OR investment keywords -> show Inflation Killer with FULL data
        investment_keywords = ['استثمار', 'عائد', 'roi', 'investment', 'profit', 'ربح', 'تضخم', 'inflation']
        if (psychology.primary_state == PsychologicalState.GREED_DRIVEN or
            any(kw in query_lower for kw in investment_keywords)):
            if properties:
                # Generate full inflation hedge data
                inflation_data = xgboost_predictor.calculate_inflation_hedge_score({
                    'price': properties[0].get('price', 5_000_000)
                })
                ui_actions.append({
                    "type": UIActionType.INFLATION_KILLER.value,
                    "priority": 9,
                    "data": {
                        "initial_investment": properties[0].get('price', 5_000_000),
                        "years": 5,
                        "projections": inflation_data.get('projections', []),
                        "summary_cards": inflation_data.get('summary_cards', []),
                        "final_values": inflation_data.get('final_values', {}),
                        "percentage_changes": inflation_data.get('percentage_changes', {}),
                        "advantages": inflation_data.get('advantages', {}),
                        "verdict": inflation_data.get('verdict', {}),
                        "hedge_score": inflation_data.get('hedge_score', 0)
                    },
                    "trigger_reason": "GREED_DRIVEN psychology or investment keywords",
                    "chart_reference": "بص على الشاشة دلوقتي يا افندم، الخط الأخضر ده العقار..."
                })

        # Rule 3: Risk-averse user OR contract/legal keywords -> show Law 114 Guardian
        legal_keywords = ['عقد', 'contract', 'قانون', 'legal', 'ضمان', 'guarantee', 'أمان', 'safe']
        if (psychology.primary_state == PsychologicalState.RISK_AVERSE or
            any(kw in query_lower for kw in legal_keywords)):
            ui_actions.append({
                "type": UIActionType.LAW_114_GUARDIAN.value,
                "priority": 8,
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
                }
            })

        # Rule 4: Multiple properties -> show Comparison Matrix
        if len(properties) > 1:
            ui_actions.append({
                "type": UIActionType.COMPARISON_MATRIX.value,
                "priority": 7,
                "data": {
                    "properties": properties[:4],
                    "best_value_id": self._find_best_value(properties),
                    "recommended_id": properties[0].get('id') if properties else None
                }
            })

        # Rule 5: Payment/installment keywords -> show Payment Timeline
        payment_keywords = ['قسط', 'تقسيط', 'installment', 'payment', 'دفع', 'monthly', 'شهري']
        if any(kw in query_lower for kw in payment_keywords) and properties:
            ui_actions.append({
                "type": UIActionType.PAYMENT_TIMELINE.value,
                "priority": 6,
                "data": {
                    "property": properties[0],
                    "payment": {
                        "down_payment_percent": properties[0].get('down_payment', 10),
                        "installment_years": properties[0].get('installment_years', 7),
                        "price": properties[0].get('price', 0)
                    }
                }
            })

        # Rule 6: Single high-scoring property -> show Investment Scorecard
        if properties and len(properties) == 1 and properties[0].get('wolf_score', 0) >= 70:
            ui_actions.append({
                "type": UIActionType.INVESTMENT_SCORECARD.value,
                "priority": 5,
                "data": {
                    "property": properties[0],
                    "analysis": {
                        "match_score": properties[0].get('wolf_score', 75),
                        "roi_projection": 6.5,
                        "risk_level": "Medium" if properties[0].get('wolf_score', 0) < 85 else "Low",
                        "market_trend": "Bullish",
                        "price_verdict": properties[0].get('price_vs_market', 'Fair price')
                    }
                }
            })

        # Sort by priority (highest first) and return
        return sorted(ui_actions, key=lambda x: x['priority'], reverse=True)

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
    "budget_max": int (in EGP),
    "bedrooms": int,
    "property_type": string,
    "keywords": string (e.g., specific project name like "Solaris", "Hyde Park")
  }
}

Examples:
- "عايز شقة في التجمع تحت 2 مليون" → {"action": "search", "filters": {"location": "New Cairo", "budget_max": 2000000}}
- "Apartment in Zayed, 3 bedrooms" → {"action": "search", "filters": {"location": "Sheikh Zayed", "bedrooms": 3}}
- "What do you have in Solaris?" → {"action": "search", "filters": {"keywords": "Solaris"}}
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
                    
                query_text = " ".join(query_parts) if query_parts else "property"
                
                # Call the vector search service
                # Note: vector_search.search_properties signature is (db, query_text, limit, threshold)
                results = await db_search_properties(
                    db=db,
                    query_text=query_text,
                    limit=10,
                    similarity_threshold=0.65  # Slightly lower for better recall
                )
                
                # Filter by budget if specified
                if 'budget_max' in filters and filters['budget_max']:
                    results = [r for r in results if r.get('price', 0) <= filters['budget_max']]
                
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
                # Predict deal probability
                deal_features = {
                    "price": prop.get('price', 0),
                    "location": prop.get('location', ''),
                    "size_sqm": prop.get('size_sqm', 0)
                }
                
                deal_score = xgboost_predictor.predict_deal_probability(deal_features)
                
                # Compare to market price
                valuation = xgboost_predictor.compare_price_to_market(
                    asking_price=prop.get('price', 0),
                    property_features=deal_features
                )
                
                # Add Wolf intelligence to each property
                prop['wolf_score'] = int(deal_score * 100)  # Convert to 0-100
                prop['valuation_verdict'] = valuation.get('verdict', 'FAIR')
                prop['price_vs_market'] = valuation.get('comparison', 'Fair price')
                
            # Sort by Wolf Score (best deals first)
            return sorted(properties, key=lambda x: x.get('wolf_score', 0), reverse=True)[:3]
            
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
        profile: Optional[Dict] = None
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
            else:
                # Format properties for Claude with EXPLICIT names - RAG ENFORCEMENT
                props_formatted = json.dumps(data, indent=2, ensure_ascii=False)
                property_list = chr(10).join([f"  {i+1}. \"{p.get('title', 'Unknown')}\" - {p.get('compound', '')} - {p.get('location', 'Unknown')} - {p.get('price', 0):,} EGP" for i, p in enumerate(data)])
                
                context_str = f"""
═══════════════════════════════════════════════════════════════════════════════
                          RAG SYSTEM - STRICT DATA GROUNDING
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

            # Build Claude prompt with psychology
            system_prompt = AMR_SYSTEM_PROMPT + f"\n\n{context_str}" + psychology_context + personalization_context

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
