"""
Osool AI Intelligence Layer
---------------------------
OpenAI-powered AI services for:
1. Legal Contract Analysis (Egyptian Real Estate Law)
2. Smart Property Valuation with Market Reasoning

This is the "Killer Feature" that differentiates Osool from competitors.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class OsoolAI:
    """
    AI services powered by GPT-4o for Egyptian Real Estate market.
    """
    
    def __init__(self):
        # GPT-4o handles Arabic legal nuances better than 3.5
        self.model = "gpt-4o"
    
    def analyze_contract_with_egyptian_context(self, contract_text: str) -> dict:
        """
        The 'Killer Feature': Scans legal text for Egyptian Real Estate risks.
        Based on Civil Code No. 131 of 1948 and Law No. 114 of 1946.
        
        CRITICAL CHECKS:
        1. Tawkil (Power of Attorney) - Required for ownership transfer
        2. Taslsol Malekeya (Ownership Sequence) - History of previous owners
        3. Delivery Date with Penalties - Protection against delays
        4. Maintenance Deposit - Fixed vs. variable amounts
        5. Refund Policy - Reasonable vs. abusive cancellation terms
        
        Returns structured JSON with risk score and analysis.
        """
        
        system_prompt = """
        You are a Senior Egyptian Real Estate Lawyer (Consultant).
        Your job is to protect the BUYER.
        Analyze the provided Real Estate Contract (in Arabic or English) based on Egyptian Civil Code and Law 114 of 1946.

        Step 1: Extract the following key clauses.
        Step 2: Assign a "Danger Score" (0-100).
        Step 3: Return the result in STRICT JSON format.

        CRITICAL CHECKS (You must look for these):
        1. "Tawkil" (Power of Attorney): Does the seller specifically agree to issue a 'Tawkil Rasmy Aam' or 'Tawkil Khass' for the unit? (MISSING = HIGH RISK).
        2. "Taslsol Malekeya" (Ownership Sequence): Is the history of previous owners listed?
        3. "Delivery Date" (Tareekh El Estelam): Is there a specific penalty (e.g., EGP per day) for late delivery?
        4. "Maintenance Deposit" (Wadeea): Is the amount fixed, or can the developer increase it later?
        5. "Refund Policy" (Estirdad): If the buyer cancels, is the penalty reasonable (e.g., 5-10%) or abusive (e.g., 100% of paid amount)?

        JSON OUTPUT FORMAT:
        {
            "risk_score": INTEGER (0 to 100, where 100 is a scam),
            "contract_type": "Primary (Ibtida'i)" OR "Final (Neha'i)" OR "Accession (Ilhaq)",
            "red_flags": [
                "Detailed explanation of risk 1 (e.g., No penalty clause for late delivery)",
                "Detailed explanation of risk 2 (e.g., Seller refuses Tawkil)"
            ],
            "missing_essential_clauses": [
                "List of clauses that should be there but are missing"
            ],
            "ai_verdict": "Safe to Sign" OR "Proceed with Caution" OR "DO NOT SIGN",
            "legal_summary_arabic": "A short summary in Arabic for the user."
        }
        """
        
        user_prompt = f"""
        Here is the contract text provided by the user. Analyze it now.
        
        --- BEGIN CONTRACT TEXT ---
        {contract_text[:15000]}
        --- END CONTRACT TEXT ---
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature = strict analysis
            )
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            return {"error": f"AI Analysis Failed: {str(e)}"}
    
    def get_smart_valuation(self, location: str, size_sqm: int, finishing: str, 
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
            response = client.chat.completions.create(
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
    
    def compare_price_to_market(self, asking_price: int, location: str, 
                                 size_sqm: int, finishing: str) -> dict:
        """
        Compare a seller's asking price against AI valuation.
        Returns whether the price is fair, high, or a bargain.
        """
        
        valuation = self.get_smart_valuation(location, size_sqm, finishing)
        
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


    def chat_with_osool(self, user_message: str) -> dict:
        """
        Interactive chat with Osool AI Sales Agent.
        
        Persona:
        - Expert Egyptian Real Estate Consultant.
        - Always quotes Law No. 114 (Registration).
        - Warns against Urfi contracts.
        - Pushes for Blockchain Reservation.
        """
        
        system_prompt = """
        You are Osool, an AI Real Estate Consultant in Egypt.
        
        Your Core Directives:
        1. **Identity**: You are a helpful, professional, and knowledgeable automated consultant for Osool.
        2. **Legal Safety**: You MUST always quote **Egyptian Law No. 114 of 1946** (The Real Estate Registration Law) when discussing ownership. Explain that unregistered contracts are not final.
        3. **Risk Warning**: If a user mentions "Urfi" (customary) contracts, DANGER ALERT them. Explain that Urfi contracts do not prove ownership against third parties.
        4. **Goal**: Your primary goal is to guide the user to **Reserve Property via the Blockchain** on the Osool platform for safety.
        
        Tone: Professional, trusted, slightly formal but accessible.
        Language: Respond in the same language as the user (English or Arabic).
        """
        
        try:
            response = client.chat.completions.create(
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
