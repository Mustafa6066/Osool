"""
Smart Follow-Up Suggestion Engine
-----------------------------------
Generates 3 contextual follow-up suggestions after every AI response
based on conversation phase, user psychology, and tools used.

Flow: conversation_phase + psychology + last_action → 3 clickable suggestions
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# PHASE-BASED SUGGESTION TEMPLATES
# ═══════════════════════════════════════════════════════════════

SUGGESTIONS_AR = {
    "qualification": [
        "عايز أعرف الأسعار في التجمع الخامس",
        "أنا بدور على شقة للسكن العائلي",
        "ميزانيتي حوالي 5 مليون جنيه",
        "عايز أستثمر مش أسكن",
        "إيه أفضل منطقة حالياً للاستثمار؟",
        "هل العاصمة الإدارية فرصة حقيقية؟",
    ],
    "exploration": [
        "قارن بين {property} ومشاريع تانية في نفس المنطقة",
        "ورّيني تاريخ المطور {developer}",
        "احسبلي الـ ROI على 5 سنين",
        "إيه بدائل تانية في نفس الميزانية؟",
        "تحليل سعر المتر في {location}",
        "هل فيه وحدات أرخص بنفس المواصفات؟",
    ],
    "comparison": [
        "مقارنة جنب جنب بين الاختيارات",
        "ورّيني خطة السداد والأقساط",
        "راجعلي العقد قانونياً (قانون 114)",
        "أنهي أفضل كاستثمار على المدى البعيد؟",
        "حلل الوحدة دي ضد التضخم",
        "إيه المخاطر اللي لازم أعرفها؟",
    ],
    "decision": [
        "احجزلي معاينة للوحدة دي",
        "ابدأ حجز الوحدة",
        "عايز مراجعة قانونية كاملة",
        "قارن خطط السداد النهائية",
        "إيه الخطوات اللي بعد كده؟",
    ],
}

SUGGESTIONS_EN = {
    "qualification": [
        "What are prices like in New Cairo?",
        "I'm looking for a family home",
        "My budget is around 5M EGP",
        "I want to invest, not live",
        "What's the best area for investment right now?",
        "Is New Capital a real opportunity?",
    ],
    "exploration": [
        "Compare {property} with similar projects",
        "Show me {developer}'s track record",
        "Calculate ROI over 5 years",
        "What alternatives exist in my budget?",
        "Analyze price per sqm in {location}",
        "Are there cheaper units with similar specs?",
    ],
    "comparison": [
        "Side-by-side comparison of my options",
        "Show me the payment plan breakdown",
        "Legal audit this contract (Law 114)",
        "Which is better as a long-term investment?",
        "Analyze this unit against inflation",
        "What risks should I know about?",
    ],
    "decision": [
        "Schedule a viewing for this property",
        "Start the reservation process",
        "I need a full legal review",
        "Compare final payment plans",
        "What are the next steps?",
    ],
}


def _detect_conversation_phase(
    lead_score: int,
    history_length: int,
    tools_used: List[str],
) -> str:
    """Determine conversation phase from lead score and interaction depth."""
    if lead_score >= 80 or "reserve" in " ".join(tools_used).lower():
        return "decision"
    if lead_score >= 55 or any(t in tools_used for t in ["comparison_matrix", "payment_timeline", "law_114_guardian"]):
        return "comparison"
    if lead_score >= 30 or history_length > 6 or any(t in tools_used for t in ["search_properties", "roi_calculator", "area_analysis"]):
        return "exploration"
    return "qualification"


def _fill_template(template: str, context: Dict) -> str:
    """Replace {property}, {developer}, {location} placeholders."""
    result = template
    result = result.replace("{property}", context.get("property", ""))
    result = result.replace("{developer}", context.get("developer", ""))
    result = result.replace("{location}", context.get("location", ""))
    return result


def generate_suggestions(
    language: str = "ar",
    lead_score: int = 0,
    history_length: int = 0,
    tools_used: Optional[List[str]] = None,
    last_property: Optional[Dict] = None,
    last_action: Optional[str] = None,
) -> List[str]:
    """
    Generate 3 contextual follow-up suggestions.

    Args:
        language: "ar" or "en"
        lead_score: Current lead score (0-100)
        history_length: Number of messages in conversation
        tools_used: List of tool/visualization types triggered
        last_property: Last property discussed (for template filling)
        last_action: Last action type (e.g., "search", "compare", "audit")

    Returns:
        List of 3 suggestion strings
    """
    tools_used = tools_used or []

    phase = _detect_conversation_phase(lead_score, history_length, tools_used)

    pool = SUGGESTIONS_AR if language == "ar" else SUGGESTIONS_EN

    candidates = list(pool.get(phase, pool["qualification"]))

    # Build template context from last property
    context = {
        "property": "",
        "developer": "",
        "location": "",
    }
    if last_property:
        context["property"] = last_property.get("title", last_property.get("compound", ""))
        context["developer"] = last_property.get("developer", "")
        context["location"] = last_property.get("location", "")

    # Fill templates & filter out ones with empty placeholders
    filled = []
    for template in candidates:
        suggestion = _fill_template(template, context)
        # Skip suggestions with unfilled placeholders
        if "{" not in suggestion and suggestion.strip():
            filled.append(suggestion)

    # Deduplicate and pick 3
    seen = set()
    unique = []
    for s in filled:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique[:3]


def generate_suggestions_from_turn(
    language: str,
    lead_score: int,
    history: List[Dict],
    ui_actions: List[Dict],
    properties: List[Dict],
) -> List[str]:
    """
    High-level wrapper called from wolf_orchestrator after each turn.
    Extracts context from the turn result and generates suggestions.
    """
    tools_used = [a.get("type", "") for a in ui_actions] if ui_actions else []
    last_property = properties[0] if properties else None
    last_action = tools_used[-1] if tools_used else None

    return generate_suggestions(
        language=language,
        lead_score=lead_score,
        history_length=len(history),
        tools_used=tools_used,
        last_property=last_property,
        last_action=last_action,
    )
