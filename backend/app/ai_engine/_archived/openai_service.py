"""
Osool AI Intelligence Layer
---------------------------
OpenAI + Claude-powered AI services for:
1. Legal Contract Analysis (Egyptian Real Estate Law) — text + vision
2. Smart Property Valuation with Market Reasoning
3. Vision Contract Analysis (photographed documents)

Upgrades (v2):
- Async clients throughout
- Vision support for photographed contracts (GPT-4o / Claude)
- Retry with tenacity
"""

import os
import json
import re
import base64
import logging
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class OsoolAI:
    """
    AI services powered by GPT-4o + Claude for Egyptian Real Estate market.
    Now fully async with vision support for photographed contracts.
    """
    
    def __init__(self):
        self.model = "gpt-4o"
        self.openai = _openai_client
        self.anthropic = _anthropic_client
    
    
    async def analyze_contract_with_egyptian_context(self, contract_text: str) -> dict:
        """
        The 'Killer Feature': Scans legal text for Egyptian Real Estate risks.
        Based on Civil Code No. 131 of 1948 and Law No. 114 of 1946.
        """
        
        # -----------------------------------------------------------
        # HARDCODED REGEX SAFETY CHECKS (The "Guardian")
        # -----------------------------------------------------------
        risk_score = 0
        red_flags = []
        is_safe = True
        
        # Check 1: Tawkil (Power of Attorney)
        # Must specifically mention "توكيل" (Tawkil)
        if not re.search(r'توكيل', contract_text, re.IGNORECASE):
            risk_score += 40
            red_flags.append("CRITICAL: No mention of 'Power of Attorney' (Tawkil/توكيل). You cannot sell the unit without this!")
            is_safe = False
            
        # Check 2: Share in Land (Hissa fel Ard)
        # Must mention "حصة في الأرض" or "hissa"
        if not re.search(r'حصة.*الأرض', contract_text, re.IGNORECASE) and not re.search(r'share.*land', contract_text, re.IGNORECASE):
            risk_score += 30
            red_flags.append("HIGH RISK: No 'Share in Land' (Hissa fel Ard/حصة في الأرض) specified. You might own the air, not the land!")
            is_safe = False

        # If strict checks failed, inject them into the prompt to force AI awareness
        regex_warnings = ""
        if not is_safe:
            regex_warnings = f"""
            WARNING - PRE-ANALYSIS FOUND MISSING TERMS:
            {json.dumps(red_flags, ensure_ascii=False)}
            
            YOU MUST MENTION THESE AS CRITICAL FLAWS IN YOUR ANALYSIS.
            SET RISK SCORE TO AT LEAST {risk_score}.
            """
        
        system_prompt = f"""
        You are a Senior Egyptian Real Estate Lawyer (Consultant).
        Your job is to protect the BUYER.
        
        {regex_warnings}
        
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
        {{
            "risk_score": INTEGER (0 to 100, where 100 is a scam),
            "contract_type": "Primary (Ibtida'i)" OR "Final (Neha'i)" OR "Accession (Ilhaq)",
            "red_flags": [
                "Detailed explanation of risk 1",
                "Detailed explanation of risk 2"
            ],
            "missing_essential_clauses": [
                "List of clauses that should be there but are missing"
            ],
            "ai_verdict": "Safe to Sign" OR "Proceed with Caution" OR "DO NOT SIGN",
            "legal_summary_arabic": "A short summary in Arabic for the user."
        }}
        """
        
        user_prompt = f"""
        Here is the contract text provided by the user. Analyze it now.
        
        --- BEGIN CONTRACT TEXT ---
        {contract_text[:15000]}
        --- END CONTRACT TEXT ---
        """
        
        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature = strict analysis
            )
            ai_result = json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Fallback if API fails
            print(f"AI Analysis Failed: {e}")
            ai_result = {
                "risk_score": 0,
                "ai_verdict": "Unknown (AI Offline)",
                "contract_type": "Unknown",
                "legal_summary_arabic": "تعذر تحليل العقد. يُرجى المحاولة مجدداً.",
                "red_flags": [],
                "missing_essential_clauses": []
            }

        # Merge hardcoded warnings if AI missed them (Safety Net)
        # This now runs EVEN IF api call failed (using the fallback dict)
        if not is_safe:
            # Ensure risk score is high enough
            if ai_result.get("risk_score", 0) < risk_score:
                ai_result["risk_score"] = risk_score
            
            # Append hardcoded red flags
            existing_flags = ai_result.get("red_flags", [])
            for flag in red_flags:
                if not any(flag[:20] in f for f in existing_flags):
                    existing_flags.insert(0, flag)
            ai_result["red_flags"] = existing_flags
            
            if ai_result["ai_verdict"] in ["Safe to Sign", "Unknown (AI Offline)"]:
                ai_result["ai_verdict"] = "DO NOT SIGN"
        
        return ai_result
    
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VISION: Analyze Photographed Contracts (GPT-4o / Claude Vision)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
    async def analyze_contract_from_image(
        self,
        image_data: str,
        image_media_type: str = "image/jpeg",
        use_claude: bool = True,
    ) -> dict:
        """
        Analyze a photographed real estate contract using vision AI.
        
        Accepts base64-encoded image data of a contract photo.
        Uses Claude Vision (preferred for Arabic OCR) or GPT-4o Vision.
        
        Args:
            image_data: Base64-encoded image data
            image_media_type: MIME type (image/jpeg, image/png, image/webp)
            use_claude: Use Claude Vision (better Arabic) or GPT-4o Vision
            
        Returns:
            Contract analysis dict with risk_score, red_flags, etc.
        """
        system_prompt = """You are a Senior Egyptian Real Estate Lawyer analyzing a photographed contract.

1. First, OCR the contract image — extract ALL Arabic and English text.
2. Then analyze based on Egyptian Civil Code and Law 114 of 1946.

CRITICAL CHECKS:
- "Tawkil" (Power of Attorney / توكيل): MISSING = HIGH RISK
- "Taslsol Malekeya" (Ownership Sequence)
- "Delivery Date" with penalty clause
- "Maintenance Deposit" (fixed or variable?)
- "Refund Policy" (reasonable or abusive?)
- "Share in Land" (حصة في الأرض): MISSING = HIGH RISK

Return JSON:
{
    "extracted_text": "The OCR'd text from the image",
    "risk_score": 0-100,
    "contract_type": "Primary/Final/Accession",
    "red_flags": ["..."],
    "missing_essential_clauses": ["..."],
    "ai_verdict": "Safe to Sign" | "Proceed with Caution" | "DO NOT SIGN",
    "legal_summary_arabic": "ملخص قانوني بالعربي",
    "legal_summary_english": "Legal summary in English"
}"""

        try:
            if use_claude:
                # Claude Vision — better Arabic OCR
                response = await self.anthropic.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": image_media_type,
                                        "data": image_data,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Analyze this contract photo. Extract ALL text and check for legal risks.",
                                },
                            ],
                        }
                    ],
                )
                result_text = response.content[0].text
            else:
                # GPT-4o Vision fallback
                response = await self.openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{image_media_type};base64,{image_data}",
                                        "detail": "high",
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Analyze this contract photo. Extract ALL text and check for legal risks.",
                                },
                            ],
                        },
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=4096,
                    temperature=0.1,
                )
                result_text = response.choices[0].message.content

            # Parse JSON from response
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result_text)
                if json_match:
                    return json.loads(json_match.group(1))
                return {
                    "risk_score": 50,
                    "ai_verdict": "Proceed with Caution",
                    "extracted_text": result_text,
                    "red_flags": ["Could not parse structured analysis — review extracted text manually"],
                    "missing_essential_clauses": [],
                }

        except Exception as e:
            logger.error(f"Vision contract analysis failed: {e}", exc_info=True)
            return {
                "risk_score": 0,
                "ai_verdict": "Unknown (Vision AI Offline)",
                "red_flags": [],
                "missing_essential_clauses": [],
                "error": str(e),
            }


# Singleton instance
osool_ai = OsoolAI()
