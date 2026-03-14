"""
Intent Extractor — Dual-Engine AI Module
------------------------------------------
Uses Claude 3.5 Sonnet to extract purchase intent, budget signals,
area preferences, and timeline from chat messages.

Called by: intent_endpoints.py → POST /api/intent/extract
"""

import os
import json
import logging
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

INTENT_SYSTEM_PROMPT = """You are an intent extraction engine for Osool, an Egyptian real estate AI platform.
Analyze the user's message and extract structured data.

Return a JSON object with EXACTLY these fields:
{
  "intent_type": one of ["SEARCH", "COMPARE", "PURCHASE", "VALUATION", "GENERAL", "COMPLAINT"],
  "confidence": float 0.0-1.0,
  "extracted": {
    "budget_min": int or null (in EGP),
    "budget_max": int or null (in EGP),
    "areas": list of area slugs or [] (e.g. ["sheikh-zayed", "new-capital-r7"]),
    "property_types": list or [] (e.g. ["apartment", "villa", "chalet", "duplex"]),
    "bedrooms": int or null,
    "timeline": string or null (e.g. "3 months", "next year", "immediately"),
    "developers": list or [] (e.g. ["emaar-misr", "sodic"]),
    "keywords": list of extracted keywords
  }
}

Area slug mapping for Egyptian market:
- Sheikh Zayed / الشيخ زايد → "sheikh-zayed"
- 6th October / أكتوبر → "6th-october"
- New Capital / العاصمة الإدارية → "new-capital-r5", "new-capital-r7", or "new-capital-r8"
- New Alamein / العلمين → "new-alamein"
- Ras El Hikma / رأس الحكمة → "ras-el-hikma"
- Ain Sokhna / العين السخنة → "ain-sokhna"
- Mostakbal City / المستقبل → "mostakbal-city"
- Madinaty / مدينتي → "madinaty"
- El Shorouk / الشروق → "el-shorouk"
- North Coast / الساحل → "north-coast"

Convert Arabic numbers: ٣ مليون = 3,000,000 EGP.
"مليون" = 1,000,000. Budget of "5-8 million" → budget_min: 5000000, budget_max: 8000000.

ONLY return the JSON object, nothing else."""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
async def extract_intent(message: str) -> dict:
    """
    Extract purchase intent from a chat message using Claude.

    Returns:
        dict with keys: intent_type, confidence, extracted
    """
    try:
        response = await _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=INTENT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": message}],
        )
        raw = response.content[0].text.strip()

        # Parse JSON from response (handle markdown code blocks)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        result = json.loads(raw)

        # Validate required fields
        valid_intents = {"SEARCH", "COMPARE", "PURCHASE", "VALUATION", "GENERAL", "COMPLAINT"}
        if result.get("intent_type") not in valid_intents:
            result["intent_type"] = "GENERAL"
        
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
        
        if "extracted" not in result:
            result["extracted"] = {}

        return result

    except json.JSONDecodeError:
        logger.warning("Intent extraction returned non-JSON: %s", raw[:200])
        return {
            "intent_type": "GENERAL",
            "confidence": 0.3,
            "extracted": {},
        }
    except Exception as e:
        logger.error("Intent extraction failed: %s", e)
        return {
            "intent_type": "GENERAL",
            "confidence": 0.0,
            "extracted": {},
        }
