"""
Osool Hybrid Intelligence Engine (Production)
---------------------------------------------
Combines statistical model inference (via dedicated MLOps endpoint)
with GPT-4o for market reasoning and legal context.
"""

import os
import json
import requests
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration for MLOps and AI services
MLOPS_INFERENCE_URL = os.getenv("MLOPS_INFERENCE_URL", "http://localhost:8080/v1/models/xgboost:predict")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4o"


class OsoolHybridBrainProd:
    """
    Production-grade hybrid AI engine combining:
    1. MLOps-served XGBoost for precise statistical valuation
    2. GPT-4o for market context and legal analysis
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.location_map = {
            "New Cairo": 0, "Mostakbal City": 1, "Sheikh Zayed": 2, 
            "6th of October": 3, "New Capital": 4, "Maadi": 5, 
            "Nasr City": 6, "Heliopolis": 7
        }
        # Simple in-memory cache for valuation results
        self._cache: Dict[str, Dict] = {}

    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate a cache key from input data."""
        return f"{data.get('location')}-{data.get('size')}-{data.get('finishing')}-{data.get('floor')}-{data.get('is_compound')}"

    def _get_xgboost_prediction(self, data: Dict[str, Any]) -> float:
        """
        Calls the dedicated MLOps inference endpoint for the hard number.
        Falls back to 0.0 if MLOps service is unavailable.
        """
        try:
            # Prepare data for the MLOps endpoint (e.g., a standardized JSON format)
            input_data = {
                "instances": [{
                    "location_encoded": self.location_map.get(data["location"], 0),
                    "size_sqm": data["size"],
                    "finishing": data["finishing"],
                    "floor": data["floor"],
                    "is_compound": data["is_compound"]
                }]
            }
            
            response = requests.post(MLOPS_INFERENCE_URL, json=input_data, timeout=5)
            response.raise_for_status()
            
            predictions = response.json().get("predictions", [])
            if predictions:
                return round(predictions[0], 0)
            
            return 0.0
            
        except requests.exceptions.RequestException as e:
            print(f"[!] MLOps Inference Failed: {e}")
            return 0.0

    def get_valuation(self, location: str, size: int, finishing: int, 
                      floor: int = 3, is_compound: int = 1) -> Dict[str, Any]:
        """
        Hybrid valuation combining MLOps XGBoost + GPT-4o.
        
        Returns:
            dict with predicted_price, price_per_sqm, market_status, reasoning_bullets
        """
        
        input_data = {
            "location": location, "size": size, "finishing": finishing, 
            "floor": floor, "is_compound": is_compound
        }
        
        # Check cache
        cache_key = self._get_cache_key(input_data)
        if cache_key in self._cache:
            print(f"[+] Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        # Step 1: Get the hard number from the MLOps service
        predicted_price = self._get_xgboost_prediction(input_data)
        
        price_context = f"Our statistical model has valued this property at **{predicted_price:,} EGP**." if predicted_price > 0 else "We need to estimate a fair price for this property."
        
        # Step 2: Use GPT-4o for market context and reasoning
        system_prompt = """
        You are a Senior Real Estate Consultant in Cairo specializing in the Egyptian Market (2026).
        Provide property valuations with detailed reasoning based on current market trends.
        Return STRICT JSON format.
        """
        
        user_prompt = f"""
        {price_context}
        
        Property Details:
        - Location: {location}
        - Size: {size} sqm
        - Finishing Level: {finishing} (0=Core&Shell, 1=Semi, 2=Finished, 3=Ultra Lux)
        - Floor: {floor}
        - Inside Compound: {"Yes" if is_compound else "No"}
        
        Task:
        1. Provide 3 bullet points on WHY this location ({location}) is trending right now (e.g., new monorail, inflation, new roads, government projects).
        2. Determine if the market is Hot, Stable, or Cool.
        
        Return JSON:
        {{
            "predicted_price": {predicted_price if predicted_price > 0 else "int (your estimate)"},
            "price_per_sqm": int,
            "market_status": "Hot" or "Stable" or "Cool",
            "reasoning_bullets": ["reason 1", "reason 2", "reason 3"],
            "investment_advice": "string with short advice"
        }}
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            result = json.loads(response.choices[0].message.content)
            
            # Ensure the XGBoost price is the final source of truth if available
            if predicted_price > 0:
                result["predicted_price"] = predicted_price
                result["source"] = "XGBoost (MLOps) + GPT-4o Hybrid"
            else:
                result["source"] = "GPT-4o Estimation (MLOps Offline)"
            
            # Cache the result
            self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return {
                "predicted_price": predicted_price,
                "market_status": "Unknown",
                "reasoning_bullets": ["AI reasoning unavailable, but price is statistically calculated." if predicted_price > 0 else "Unable to calculate price."],
                "source": "XGBoost Only" if predicted_price > 0 else "Error",
                "error": str(e)
            }

    def audit_contract(self, contract_text: str) -> Dict[str, Any]:
        """
        Scans specifically for Egyptian Real Estate Scams using Legal Context (GPT-4o).
        
        Returns:
            dict with risk_score, verdict, red_flags, missing_clauses, recommendations
        """
        system_prompt = """
        You are a Senior Egyptian Real Estate Lawyer. Your job is to PROTECT THE BUYER.
        Analyze the contract text based on Egyptian Civil Code No. 131 of 1948 and Law 114 of 1946.

        CRITICAL CHECKS (You MUST look for these):
        1. "Tawkil" (Power of Attorney / توكيل رسمي): Is a Tawkil Rasmy Aam or Khass explicitly mentioned?
        2. "Delivery Date & Penalty" (تاريخ التسليم وغرامة التأخير): Is there a specific penalty for late delivery?
        3. "Withdrawal/Cancellation" (حق الإلغاء): Can the SELLER cancel the contract arbitrarily?
        4. "Taslsol Malekeya" (تسلسل الملكية): Is the ownership chain documented?
        5. "Area Variance" (فرق المساحة): Does the contract allow +/- 10% area change without compensation?

        Return STRICT JSON:
        {
            "risk_score": int (0-100, where 100 is extreme danger),
            "verdict": "Safe to Sign" or "Proceed with Caution" or "DO NOT SIGN",
            "red_flags": ["Specific dangerous clause with explanation"],
            "missing_clauses": ["What should be there but is missing"],
            "recommendations": ["What the buyer should demand before signing"],
            "legal_summary_arabic": "ملخص قانوني بالعربية للمستخدم"
        }
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this contract:\n\n{contract_text[:15000]}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "error": f"Legal analysis failed: {str(e)}",
                "risk_score": -1,
                "verdict": "Analysis Failed"
            }

    def compare_asking_price(self, asking_price: int, location: str, 
                              size: int, finishing: int) -> Dict[str, Any]:
        """
        Compare a seller's asking price against AI valuation.
        
        Returns:
            dict with verdict (BARGAIN/FAIR/OVERPRICED), difference_percent, market_context
        """
        
        # Get fair value using hybrid method
        valuation = self.get_valuation(location, size, finishing)
        
        if "error" in valuation or valuation.get("predicted_price", 0) == 0:
            return {"error": "Could not calculate fair price"}
        
        fair_price = valuation["predicted_price"]
        
        # Calculate difference
        diff_percent = ((asking_price - fair_price) / fair_price) * 100
        
        if diff_percent < -15:
            verdict = "BARGAIN"
            message = "⚠️ السعر أقل من السوق بنسبة كبيرة - تأكد من سبب الخصم ووثائق الملكية"
        elif diff_percent <= 10:
            verdict = "FAIR"
            message = "✅ السعر مناسب ومتوافق مع السوق"
        else:
            verdict = "OVERPRICED"
            message = f"❌ السعر أعلى من السوق بنسبة {diff_percent:.0f}% - حاول التفاوض"
        
        return {
            "asking_price": asking_price,
            "fair_price": fair_price,
            "difference_percent": round(diff_percent, 1),
            "verdict": verdict,
            "message_arabic": message,
            "market_context": valuation.get("reasoning_bullets", [])
        }


# Singleton instance for production use
hybrid_brain_prod = OsoolHybridBrainProd()
