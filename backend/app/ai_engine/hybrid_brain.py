"""
Osool Hybrid Intelligence Engine
--------------------------------
The "Brain" of the Wolf.
Combines:
1. Retrieval (Vector Search with Dynamic Fallback)
2. Analysis (XGBoost Deal Probability)
3. Synthesis (Wolf Persona via GPT-4o)
"""

import json
import logging
from typing import List, Dict, Any
from app.ai_engine.amr_master_prompt import AMR_SYSTEM_PROMPT, WOLF_TACTICS
from app.services.vector_search import search_properties as db_search_properties
from app.ai_engine.xgboost_predictor import predict_deal_probability
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

class VectorSearchService:
    """Shim to adapt functional vector_search to class-based usage."""
    async def search_properties(self, query: str, limit: int = 5) -> List[Dict]:
        async with AsyncSessionLocal() as db:
            # We use the updated search_properties with dynamic fallback
            return await db_search_properties(db, query, limit=limit, similarity_threshold=0.7)

class HybridBrain:
    def __init__(self, llm_client=None):
        # Allow passing distinct client or default to None (handled in generate methods)
        self.llm = llm_client
        self.vector_search = VectorSearchService()
        
        # Initialize OpenAI client if not provided
        if not self.llm:
            from openai import OpenAI
            import os
            self.llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def think_and_act(self, user_query: str, history: List[Dict]) -> str:
        """
        The Core Logic Loop: Retrieve -> Analyze -> Synthesize.
        """
        # 1. RETRIEVE (The Ammo)
        # Dynamic threshold logic is handled inside search_properties
        properties = await self.vector_search.search_properties(user_query)
        
        # 2. ANALYZE (The Math - XGBoost)
        # We calculate a 'Deal Heat' score for the retrieved properties
        market_context = []
        for prop in properties:
            # Predict likelihood of this property selling (0.0 to 1.0)
            success_prob = await predict_deal_probability(prop) 
            prop['ai_deal_score'] = f"{success_prob * 100:.1f}%"
            market_context.append(prop)

        # 3. SYNTHESIZE (The Wolf Persona)
        # We don't just dump data. We frame it.
        if not market_context:
            # Handle the "Empty Handed" case with charisma, not stupidity
            return await self._generate_pivot_response(user_query, history)

        return await self._generate_wolf_response(user_query, market_context, history)

    async def _generate_wolf_response(self, query, context, history):
        # We feed the "Deal Score" into the prompt to give Amr confidence.
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        
        system_instruction = f"""
        {AMR_SYSTEM_PROMPT}
        
        [LIVE MARKET DATA - EYES ONLY]
        {context_str}
        
        [TACTICAL DIRECTIVE]
        1. Pick the property with the highest 'ai_deal_score'. This is your "Star".
        2. Use the 'Scarcity' tactic: "{WOLF_TACTICS['scarcity']}"
        3. Ignore the boring details. Sell the ROI (Return on Investment) and the Lifestyle.
        4. Speak ONLY in Egyptian Arabic (Masri). Be high energy.
        """

        response = self.llm.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_instruction},
                *history,
                {"role": "user", "content": query}
            ],
            temperature=0.7 # Higher temperature for charisma
        )
        return response.choices[0].message.content

    async def _generate_pivot_response(self, query, history):
        """When we have no data, we don't say 'I don't know'. We pivot."""
        return self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": AMR_SYSTEM_PROMPT + "\n\nCRITICAL: You found NO properties. Do not apologize. Instead, pivot to asking about their budget or preferred location to 'unlock' your private inventory."},
                *history,
                {"role": "user", "content": query}
            ]
        ).choices[0].message.content

# Singleton instance
hybrid_brain = HybridBrain()
