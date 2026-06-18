"""
Osool Hybrid Intelligence Engine (Production)
---------------------------------------------
Combines statistical model inference (via dedicated MLOps endpoint)
with GPT-4o for market reasoning and legal context.

─────────────────────────────────────────────────────────────────────────────
DUAL-VALUATION ARCHITECTURE — read before changing pricing logic
─────────────────────────────────────────────────────────────────────────────
There are TWO valuation paths in this repository, intentionally kept separate:

  1. THIS FILE (Osool-Platform, Python, OpenAI GPT-4o + XGBoost MLOps)
     Used by: authenticated user dashboard (/api/ai/valuation, /api/ai/compare-price).
     Data source: MLOps XGBoost endpoint + DB-backed Area/Developer tables
     (via app.services.market_data_repository).
     Strength: real ML predictions, confidence bands, admin-editable inputs.

  2. Osool-orchestrator/apps/api/src/agents/brain/plugins/valuation.plugin.ts
     (TypeScript, Anthropic Claude)
     Used by: the marketing/SEO chat agent on the public site.
     Data source: hardcoded constants in @osool/shared.
     Strength: low-latency, no DB dependency, good for top-of-funnel chat.

The two MUST NOT be merged without a migration plan — they have different
SLAs, billing, and authentication models. If outputs need to agree, prefer
having the orchestrator call this Platform endpoint as the source of truth,
rather than duplicating inference in TypeScript.
─────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

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
        # Egyptian real estate location encodings for the XGBoost model.
        # Covers the major investment corridors. Unknown locations handled explicitly.
        self.location_map = {
            "New Cairo": 0, "Mostakbal City": 1, "Sheikh Zayed": 2,
            "6th of October": 3, "New Capital": 4, "Maadi": 5,
            "Nasr City": 6, "Heliopolis": 7,
            # Extended coverage — add new entries as model is retrained
            "El Shorouk": 8, "Obour": 9, "Badr City": 10,
            "North Coast": 11, "Ain Sokhna": 12,
        }
        # Simple in-memory cache for valuation results
        self._cache: Dict[str, Dict] = {}

    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate a cache key from input data."""
        return f"{data.get('location')}-{data.get('size')}-{data.get('finishing')}-{data.get('floor')}-{data.get('is_compound')}"

    def _get_xgboost_prediction(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Calls the dedicated MLOps inference endpoint for a statistical valuation.

        Returns:
            Predicted price (float) if the call succeeds and location is known,
            or None if the service is unavailable or the location is not in the
            training distribution (prevents silently using wrong encodings).
        """
        location = data.get("location", "")
        if location not in self.location_map:
            # Do NOT fall back to encoding 0 — that would silently predict prices
            # for "New Cairo" when the user asked about an unknown location.
            logger.warning(f"[MLOps] Location '{location}' not in model training set — skipping XGBoost prediction")
            return None

        try:
            input_data = {
                "instances": [{
                    "location_encoded": self.location_map[location],
                    "size_sqm": data["size"],
                    "finishing": data["finishing"],
                    "floor": data["floor"],
                    "is_compound": data["is_compound"]
                }]
            }

            response = requests.post(MLOPS_INFERENCE_URL, json=input_data, timeout=5)
            response.raise_for_status()

            predictions = response.json().get("predictions", [])
            if predictions and predictions[0] > 0:
                return round(float(predictions[0]), 0)

            logger.warning("[MLOps] Empty or zero prediction returned")
            return None

        except requests.exceptions.Timeout:
            logger.warning(f"[MLOps] Inference timeout for {location} — proceeding without XGBoost")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"[MLOps] Inference failed for {location}: {e} — proceeding without XGBoost")
            return None

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
        
        # Step 1: Get the hard number from the MLOps service (returns None if unavailable/unknown location)
        predicted_price: Optional[float] = self._get_xgboost_prediction(input_data)

        if predicted_price is not None:
            price_context = f"Our statistical model has valued this property at **{predicted_price:,.0f} EGP**."
        else:
            price_context = "We need to estimate a fair price for this property based on market comparables."
        
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
            "predicted_price": {int(predicted_price) if predicted_price is not None else "int (your estimate based on comparables)"},
            "price_per_sqm": int,
            "market_status": "Hot" or "Stable" or "Cool",
            "reasoning_bullets": ["reason 1", "reason 2", "reason 3"],
            "investment_advice": "string with short advice"
        }}
        """

        try:
            from app.services.circuit_breaker import openai_breaker
            from app.services.cost_monitor import cost_monitor

            # Phase 4: Wrap OpenAI call with circuit breaker
            def _gpt_valuation():
                response = self.openai_client.chat.completions.create(
                    model=GPT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3
                )

                # Phase 4: Track cost
                usage = response.usage
                cost_monitor.log_usage(
                    model="gpt-4o",
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    context="valuation"
                )

                return json.loads(response.choices[0].message.content)

            result = openai_breaker.call(_gpt_valuation)

            # XGBoost is the authoritative price source when available.
            # If not available (service down or unknown location), GPT estimate is used.
            if predicted_price is not None:
                result["predicted_price"] = int(predicted_price)
                result["source"] = "XGBoost (MLOps) + GPT-4o Hybrid"
                result["confidence"] = "HIGH"
                # XGBoost training error band ±10% — surfaced for the UI
                result["price_range"] = {
                    "low": int(predicted_price * 0.90),
                    "high": int(predicted_price * 1.10),
                }
            else:
                result["source"] = "GPT-4o Market Estimation (MLOps Unavailable or Unknown Location)"
                result["confidence"] = "LOW"
                # Wider band when only the LLM estimated — ±20%
                gpt_price = int(result.get("predicted_price") or 0)
                if gpt_price > 0:
                    result["price_range"] = {
                        "low": int(gpt_price * 0.80),
                        "high": int(gpt_price * 1.20),
                    }

            # Cache the result
            self._cache[cache_key] = result

            return result

        except Exception as e:
            fallback_price = int(predicted_price) if predicted_price is not None else None
            return {
                "predicted_price": fallback_price,
                "market_status": "Unknown",
                "reasoning_bullets": [
                    "AI reasoning unavailable; price is statistically calculated." if fallback_price
                    else "Unable to calculate price — both MLOps and AI unavailable."
                ],
                "source": "XGBoost Only" if fallback_price else "Error",
                "confidence": "MEDIUM" if fallback_price else "NONE",
                "price_range": (
                    {"low": int(fallback_price * 0.90), "high": int(fallback_price * 1.10)}
                    if fallback_price else None
                ),
                "error": str(e)
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

        if "error" in valuation or not valuation.get("predicted_price"):
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


    async def get_valuation_async(self, location: str, size: int, finishing: int,
                                   floor: int = 3, is_compound: int = 1) -> Dict[str, Any]:
        """Async wrapper for get_valuation — runs in a thread to avoid blocking the event loop."""
        return await asyncio.to_thread(self.get_valuation, location, size, finishing, floor, is_compound)

    async def compare_asking_price_async(self, asking_price: int, location: str,
                                         size: int, finishing: int) -> Dict[str, Any]:
        """Async wrapper for compare_asking_price — runs in a thread."""
        return await asyncio.to_thread(self.compare_asking_price, asking_price, location, size, finishing)


# Singleton instance for production use
hybrid_brain_prod = OsoolHybridBrainProd()
