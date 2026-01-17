"""
Osool Hybrid Intelligence Engine - V3 Reasoning Loop
----------------------------------------------------
The "Brain" of the Wolf - Now with Structured Thinking.

Architecture:
1. PERCEPTION (GPT-4o): Extract intent & filters from natural language
2. HUNT (Database): Search for real properties
3. ANALYZE (XGBoost): Score deals, find "La2ta" (the catch)
4. STRATEGY (Psychology): Determine pitch angle (investor vs family)
5. SPEAK (Claude): Generate narrative using ONLY verified data
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI, AsyncOpenAI
from anthropic import AsyncAnthropic

from app.ai_engine.amr_master_prompt import AMR_SYSTEM_PROMPT, WOLF_TACTICS
from app.ai_engine.xgboost_predictor import xgboost_predictor
from app.services.vector_search import search_properties as db_search_properties
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


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
        
    async def process_turn(
        self, 
        query: str, 
        history: List[Dict], 
        profile: Optional[Dict] = None
    ) -> str:
        """
        The Main Thinking Loop.
        
        Args:
            query: User's natural language query
            history: Conversation history as list of dicts with 'role' and 'content'
            profile: User profile dict (optional)
            
        Returns:
            AI response text
        """
        try:
            logger.info(f"🧠 Reasoning Loop: Processing query: {query[:100]}...")
            
            # 1. PERCEPTION: Analyze Intent & Extract Filters (GPT-4o)
            intent = await self._analyze_intent(query, history)
            logger.info(f"📊 Intent extracted: {intent}")
            
            # 2. HUNT: Data Retrieval (PostgreSQL + Vector Search)
            market_data = []
            if intent.get('action') == 'search':
                market_data = await self._search_database(intent.get('filters', {}))
                logger.info(f"🔍 Found {len(market_data)} properties")
            
            # 3. ANALYZE: Deal Scoring (XGBoost)
            scored_data = self._apply_wolf_analytics(market_data, intent)
            logger.info(f"📈 Scored and ranked {len(scored_data)} properties")
            
            # 4. STRATEGY: Determine Pitch Angle (Psychology)
            strategy = self._determine_strategy(profile, scored_data, intent)
            logger.info(f"🎯 Strategy: {strategy}")
            
            # 5. SPEAK: Generate Response (Claude 3.5 Sonnet)
            response = await self._generate_wolf_narrative(
                query, 
                scored_data, 
                history, 
                strategy
            )
            
            logger.info(f"✅ Reasoning loop complete")
            return response
            
        except Exception as e:
            logger.error(f"❌ Reasoning loop failed: {e}", exc_info=True)
            raise  # Let caller handle fallback

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
    "property_type": string
  }
}

Examples:
- "عايز شقة في التجمع تحت 2 مليون" → {"action": "search", "filters": {"location": "New Cairo", "budget_max": 2000000}}
- "Apartment in Zayed, 3 bedrooms" → {"action": "search", "filters": {"location": "Sheikh Zayed", "bedrooms": 3}}
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
        intent: Dict
    ) -> str:
        """
        STEP 4: STRATEGY (Psychology)
        Decide: Are we selling Fear (Scarcity) or Greed (ROI)?
        """
        # If no data, always pivot to discovery
        if not data:
            return "PIVOT_TO_DISCOVERY"
        
        # Check if user is investor-focused (based on profile or query)
        is_investor = False
        if profile:
            is_investor = profile.get('investor_mode', False)
        
        # Check if any property is a "BARGAIN"
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
        strategy: str
    ) -> str:
        """
        STEP 5: SPEAK (Claude 3.5 Sonnet)
        Generate the Wolf's response using ONLY verified data.
        """
        try:
            # Prepare database context
            if not data and strategy == "PIVOT_TO_DISCOVERY":
                context_str = """
[DATABASE_CONTEXT]: EMPTY - No properties found matching criteria.

INSTRUCTION: Since no properties were found, you MUST ask clarifying questions:
- "ميزانيتك في حدود كام يا باشا؟" (What's your budget range, boss?)
- "بتدور في أي منطقة؟" (Which area are you looking in?)
- "سكن ولا استثمار؟" (Living or investment?)

DO NOT invent any properties. Be charming and helpful while gathering info.
"""
            else:
                # Format properties for Claude
                props_formatted = json.dumps(data, indent=2, ensure_ascii=False)
                context_str = f"""
[DATABASE_CONTEXT]: {len(data)} VERIFIED PROPERTIES FROM DATABASE

{props_formatted}

INSTRUCTION:
- Present the TOP property (first in the list) as the "La2ta" (the catch)
- Mention its wolf_score: "الـ AI بتاعي قيمها بـ {data[0].get('wolf_score', 0)}/100"
- Highlight the valuation_verdict: "{data[0].get('valuation_verdict', 'FAIR')}"
- Use ONLY data from above. DO NOT invent compound names or prices.

STRATEGY: {strategy}
"""
            
            # Build Claude prompt
            system_prompt = AMR_SYSTEM_PROMPT + f"\n\n{context_str}"
            
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
            import os
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
            return "عذراً، حصل مشكلة فنية. جرب تاني يا باشا. (Sorry, technical issue. Try again, boss.)"


# Singleton instance
hybrid_brain = OsoolHybridBrain()

# Export
__all__ = ["hybrid_brain", "OsoolHybridBrain"]
