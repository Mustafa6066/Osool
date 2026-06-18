"""
Osool AI Intelligence Layer
---------------------------
OpenAI + Claude-powered AI services for:
1. Smart Property Valuation with Market Reasoning

Upgrades (v2):
- Async clients throughout
"""

import os
import json
import logging
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class OsoolAI:
    """
    AI services powered by GPT-4o + Claude for Egyptian Real Estate market.
    Now fully async.
    """

    def __init__(self):
        self.model = "gpt-4o"
        self.openai = _openai_client
        self.anthropic = _anthropic_client


    async def get_smart_valuation(self, location: str, size_sqm: int, finishing: str,
                            bedrooms: int = 3, property_type: str = "Apartment") -> dict:
        """
        AI-powered property valuation with market reasoning.
        Returns price range AND explanation of why.
        
        This builds trust because users see the reasoning, not just a number.
        """
        
        system_prompt = """
        You are a Senior Real Estate Consultant specializing in the Egyptian Market (Cairo, Giza, New Capital).
        You have access to current market data as of Q1 2026.
        
        Provide property valuations with detailed reasoning based on:
        - Location demand and infrastructure developments
        - Inflation and currency trends
        - Comparable sales in the area
        - Developer reputation (if applicable)
        
        Be specific about Cairo neighborhoods: New Cairo (التجمع), Sheikh Zayed, 6th October, 
        New Capital (العاصمة الإدارية), Mostakbal City, Maadi, Zamalek, etc.
        
        Return STRICT JSON format.
        """
        
        user_prompt = f"""
        Estimate the fair market value for this property:
        
        - Location: {location}
        - Property Type: {property_type}
        - Size: {size_sqm} sqm
        - Bedrooms: {bedrooms}
        - Finishing: {finishing}
        
        Provide:
        1. Price Range (Low - High) in EGP
        2. Price per sqm in EGP
        3. Detailed reasoning (mention infrastructure, demand, inflation)
        4. Investment recommendation
        
        Return JSON:
        {{
            "estimated_price_min": int,
            "estimated_price_max": int,
            "price_per_sqm_min": int,
            "price_per_sqm_max": int,
            "currency": "EGP",
            "reasoning": "string explaining the valuation",
            "market_trends": "string about current market direction",
            "investment_verdict": "Good Investment" OR "Fair Value" OR "Overpriced"
        }}
        """
        
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            return {"error": f"Valuation Failed: {str(e)}"}
    
    async def compare_price_to_market(self, asking_price: int, location: str, 
                                 size_sqm: int, finishing: str) -> dict:
        """
        Compare a seller's asking price against AI valuation.
        Returns whether the price is fair, high, or a bargain.
        """
        
        valuation = await self.get_smart_valuation(location, size_sqm, finishing)
        
        if "error" in valuation:
            return valuation
        
        min_price = valuation.get("estimated_price_min", 0)
        max_price = valuation.get("estimated_price_max", 0)
        mid_price = (min_price + max_price) / 2
        
        if asking_price < min_price * 0.9:
            verdict = "BARGAIN"
            message = "السعر أقل من السوق بنسبة كبيرة - تأكد من سبب الخصم"
            percentage_diff = ((min_price - asking_price) / min_price) * 100
        elif asking_price <= max_price * 1.05:
            verdict = "FAIR"
            message = "السعر ضمن النطاق المعقول للسوق"
            percentage_diff = ((asking_price - mid_price) / mid_price) * 100
        else:
            verdict = "OVERPRICED"
            message = "السعر أعلى من السوق - حاول التفاوض"
            percentage_diff = ((asking_price - max_price) / max_price) * 100
        
        return {
            "asking_price": asking_price,
            "fair_price_range": {
                "min": min_price,
                "max": max_price
            },
            "verdict": verdict,
            "message_arabic": message,
            "percentage_difference": round(percentage_diff, 1),
            "market_reasoning": valuation.get("reasoning", "")
        }


    async def chat_with_osool(self, user_message: str) -> dict:
        """
        Interactive chat with Osool AI Sales Agent.
        
        Persona:
        - Expert Egyptian Real Estate Consultant.
        - Always quotes Law No. 114 (Registration).
        - Warns against Urfi contracts.
        - Guides users toward verified reservations.
        """
        
        system_prompt = """
        You are Osool, an AI Real Estate Consultant in Egypt.
        
        Your Core Directives:
        1. **Identity**: You are a helpful, professional, and knowledgeable automated consultant for Osool.
        2. **Legal Safety**: You MUST always quote **Egyptian Law No. 114 of 1946** (The Real Estate Registration Law) when discussing ownership. Explain that unregistered contracts are not final.
        3. **Risk Warning**: If a user mentions "Urfi" (customary) contracts, DANGER ALERT them. Explain that Urfi contracts do not prove ownership against third parties.
        4. **Goal**: Your primary goal is to guide the user to **Reserve Property** on the Osool platform for safety.
        
        Tone: Professional, trusted, slightly formal but accessible.
        Language: Respond in the same language as the user (English or Arabic).
        """
        
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            return {"response": response.choices[0].message.content}
            
        except Exception as e:
            return {"error": f"Chat Failed: {str(e)}"}


# Singleton instance
osool_ai = OsoolAI()
