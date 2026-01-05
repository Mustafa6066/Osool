"""
Osool Hybrid Intelligence Engine
--------------------------------
Combines the statistical precision of XGBoost with GPT-4o's reasoning.

Architecture:
- XGBoost: Gives hard, accurate numbers based on data (math)
- GPT-4o: Explains WHY that number matters (context)

This is superior to using just one model alone.
"""

import os
import json
import joblib
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class OsoolHybridBrain:
    """
    Hybrid AI engine that combines:
    1. XGBoost for precise statistical valuation
    2. GPT-4o for market context and legal analysis
    """
    
    def __init__(self):
        self.xgboost_model_path = os.path.join(
            os.path.dirname(__file__), "osool_xgboost.pkl"
        )
        self.encoder_path = os.path.join(
            os.path.dirname(__file__), "location_encoder.pkl"
        )
        self.xgboost_model = None
        self.location_encoder = None
        self.gpt_model = "gpt-4o"
        
        # Location mapping for encoding
        self.location_map = {
            "New Cairo": 0,
            "Mostakbal City": 1,
            "Sheikh Zayed": 2,
            "6th of October": 3,
            "New Capital": 4,
            "Maadi": 5,
            "Nasr City": 6,
            "Heliopolis": 7
        }

    def _load_xgboost(self):
        """Lazy load the XGBoost model only when needed."""
        if not self.xgboost_model:
            if os.path.exists(self.xgboost_model_path):
                self.xgboost_model = joblib.load(self.xgboost_model_path)
                if os.path.exists(self.encoder_path):
                    self.location_encoder = joblib.load(self.encoder_path)
            else:
                # Model not trained yet - will use GPT-4o only
                print("⚠️ XGBoost model not found. Using GPT-4o only.")
                return False
        return True

    def _encode_location(self, location: str) -> int:
        """Encode location string to numeric value."""
        if self.location_encoder:
            try:
                return self.location_encoder.transform([location])[0]
            except ValueError:
                return self.location_map.get(location, 0)
        return self.location_map.get(location, 0)

    # ==========================================================
    # FEATURE 1: HYBRID VALUATION (Math + Reasoning)
    # ==========================================================
    def get_valuation(self, location: str, size: int, finishing: int, 
                      floor: int = 3, is_compound: int = 1) -> dict:
        """
        Hybrid valuation combining XGBoost + GPT-4o.
        
        Step 1: XGBoost calculates the exact EGP value.
        Step 2: GPT-4o explains the market trends for that location.
        
        Args:
            location: Area name (e.g., "New Cairo", "Sheikh Zayed")
            size: Property size in sqm
            finishing: 0=Core&Shell, 1=Semi, 2=Finished, 3=Ultra Lux
            floor: Floor number (affects price)
            is_compound: 1 if in a gated compound, 0 otherwise
        
        Returns:
            dict with predicted_price, market_status, and reasoning_bullets
        """
        
        predicted_price = None
        
        # --- PHASE A: The Math (XGBoost) ---
        if self._load_xgboost():
            try:
                # Prepare input for XGBoost
                input_data = pd.DataFrame([{
                    "location_encoded": self._encode_location(location),
                    "size_sqm": size,
                    "bedrooms": max(1, size // 60),
                    "finishing": finishing,
                    "floor": floor,
                    "is_compound": is_compound
                }])
                
                # Get the hard number
                predicted_price = int(self.xgboost_model.predict(input_data)[0])
            except Exception as e:
                print(f"XGBoost prediction failed: {e}")
                predicted_price = None
        
        # --- PHASE B: The Context (GPT-4o) ---
        # We feed the XGBoost number into GPT-4o to get the "Story"
        
        price_context = f"Our proprietary algorithm has valued this property at **{predicted_price:,} EGP**." if predicted_price else "We need to estimate a fair price for this property."
        
        prompt = f"""
        You are a Real Estate Consultant in Cairo specializing in the Egyptian market (2026).
        {price_context}
        
        Property Details:
        - Location: {location}
        - Size: {size} sqm
        - Bedrooms: {max(1, size // 60)}
        - Finishing Level: {finishing} (0=Core&Shell, 1=Semi, 2=Finished, 3=Ultra Lux)
        - Floor: {floor}
        - Inside Compound: {"Yes" if is_compound else "No"}
        
        Task:
        1. {"Validate if this price seems reasonable" if predicted_price else "Estimate a fair price range"} for 2026 market conditions.
        2. Provide 3 bullet points on WHY this location ({location}) is trending right now (e.g., new monorail, inflation, new roads, government projects).
        3. Determine if the market is Hot, Stable, or Cool.
        
        Return STRICT JSON:
        {{
            "predicted_price": {predicted_price if predicted_price else "int (your estimate)"},
            "price_per_sqm": int,
            "market_status": "Hot" or "Stable" or "Cool",
            "reasoning_bullets": ["reason 1", "reason 2", "reason 3"],
            "investment_advice": "string with short advice"
        }}
        """

        try:
            response = client.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            result = json.loads(response.choices[0].message.content)
            
            # Override with XGBoost price if available (more accurate)
            if predicted_price:
                result["predicted_price"] = predicted_price
                result["source"] = "XGBoost + GPT-4o Hybrid"
            else:
                result["source"] = "GPT-4o Estimation"
            
            return result
            
        except Exception as e:
            # If OpenAI fails, at least return the XGBoost number
            return {
                "predicted_price": predicted_price or 0,
                "market_status": "Unknown",
                "reasoning_bullets": ["AI reasoning unavailable, but price is statistically calculated." if predicted_price else "Unable to calculate price."],
                "source": "XGBoost Only" if predicted_price else "Error",
                "error": str(e)
            }

    # ==========================================================
    # FEATURE 2: LEGAL AUDIT (The Egyptian Lawyer)
    # ==========================================================
    def audit_contract(self, contract_text: str) -> dict:
        """
        Scans specifically for Egyptian Real Estate Scams using Legal Context.
        Based on Egyptian Civil Code No. 131 and Law 114 of 1946.
        
        CRITICAL CHECKS:
        1. "Tawkil" (Power of Attorney) - Required for ownership transfer
        2. "Delivery Penalty" - Protection against developer delays
        3. "Withdrawal Clause" - Can seller cancel arbitrarily?
        4. "Shahr El Aqari" - Registration requirements
        
        Returns:
            dict with risk_score, verdict, red_flags, and missing_clauses
        """
        
        system_prompt = """
        You are a Senior Egyptian Real Estate Lawyer. Your job is to PROTECT THE BUYER.
        Analyze the contract text based on Egyptian Civil Code No. 131 of 1948 and Law 114 of 1946.

        CRITICAL CHECKS (You MUST look for these):
        
        1. "Tawkil" (Power of Attorney / توكيل رسمي):
           - Is a Tawkil Rasmy Aam or Khass explicitly mentioned?
           - Does the seller agree to issue it at the Notary (Shahr El Aqari)?
           - MISSING = HIGH RISK (Cannot transfer ownership without it)
        
        2. "Delivery Date & Penalty" (تاريخ التسليم وغرامة التأخير):
           - Is there a SPECIFIC delivery date?
           - Is there a penalty clause (e.g., EGP per day/month) if developer is late?
           - MISSING = RISK (Developer can delay indefinitely)
        
        3. "Withdrawal/Cancellation" (حق الإلغاء):
           - Can the SELLER cancel the contract arbitrarily?
           - If buyer withdraws, is the penalty reasonable (5-10%) or abusive (100%)?
           - ABUSIVE = RED FLAG
        
        4. "Taslsol Malekeya" (تسلسل الملكية):
           - Is the ownership chain documented?
           - Who is the original owner? How did current seller acquire it?
           - MISSING = FRAUD RISK (Could be stolen property)
        
        5. "Area Variance" (فرق المساحة):
           - Does the contract allow +/- 10% area change without compensation?
           - This is a COMMON SCAM - developer gives smaller unit
        
        Return STRICT JSON:
        {
            "risk_score": int (0-100, where 100 is extreme danger),
            "contract_type": "Primary (Ibtida'i)" or "Final (Neha'i)" or "Unknown",
            "verdict": "Safe to Sign" or "Proceed with Caution" or "DO NOT SIGN",
            "red_flags": [
                "Specific dangerous clause with explanation"
            ],
            "missing_clauses": [
                "What should be there but is missing"
            ],
            "recommendations": [
                "What the buyer should demand before signing"
            ],
            "legal_summary_arabic": "ملخص قانوني بالعربية للمستخدم"
        }
        """

        try:
            response = client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this contract:\n\n{contract_text[:15000]}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Zero creativity, maximum strictness
            )
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "error": f"Legal analysis failed: {str(e)}",
                "risk_score": -1,
                "verdict": "Analysis Failed"
            }

    # ==========================================================
    # FEATURE 3: PRICE COMPARISON
    # ==========================================================
    def compare_asking_price(self, asking_price: int, location: str, 
                              size: int, finishing: int) -> dict:
        """
        Compare a seller's asking price against AI valuation.
        
        Returns:
            dict with verdict (BARGAIN/FAIR/OVERPRICED) and explanation
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


# Singleton instance
hybrid_brain = OsoolHybridBrain()
