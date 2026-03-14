"""
Smart Follow-Up Suggestion Engine
-----------------------------------
Generates 3 contextual follow-up suggestions after every AI response
based on conversation phase, user psychology, tools used, and AI response content.

Flow: conversation_phase + psychology + last_action + response_hash → 3 unique clickable suggestions
"""

import hashlib
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# PHASE-BASED SUGGESTION TEMPLATES  (expanded for variety)
# ═══════════════════════════════════════════════════════════════

SUGGESTIONS_AR = {
    "qualification": [
        "عايز أعرف الأسعار في التجمع الخامس",
        "أنا بدور على شقة للسكن العائلي",
        "ميزانيتي حوالي 5 مليون جنيه",
        "عايز أستثمر مش أسكن",
        "إيه أفضل منطقة حالياً للاستثمار؟",
        "هل العاصمة الإدارية فرصة حقيقية؟",
        "إيه الفرق بين التجمع وأكتوبر؟",
        "عايز مشروع بمقدم أقل من 10%",
        "إيه المناطق اللي فيها أعلى عائد؟",
        "بدور على فيلا في الساحل",
        "هل الوقت ده مناسب للشراء؟",
        "إيه المطورين الموثوقين؟",
        "عايز أفهم حركة السوق",
        "هل فيه فرق بين السكن والاستثمار في المناطق دي؟",
    ],
    "exploration": [
        "قارن بين {property} ومشاريع تانية في نفس المنطقة",
        "ورّيني تاريخ المطور {developer}",
        "احسبلي الـ ROI على 5 سنين",
        "إيه بدائل تانية في نفس الميزانية؟",
        "تحليل سعر المتر في {location}",
        "هل فيه وحدات أرخص بنفس المواصفات؟",
        "ورّيني مشاريع {developer} التانية",
        "إيه نسبة الإشغال في {location}؟",
        "هل {location} مناسبة للعائلات؟",
        "إيه المدارس والخدمات القريبة؟",
        "احسبلي التضخم مقابل سعر الوحدة",
        "ممكن أشوف وحدات بتسليم أقرب؟",
    ],
    "comparison": [
        "مقارنة جنب جنب بين الاختيارات",
        "ورّيني خطة السداد والأقساط",
        "راجعلي العقد قانونياً (قانون 114)",
        "أنهي أفضل كاستثمار على المدى البعيد؟",
        "حلل الوحدة دي ضد التضخم",
        "إيه المخاطر اللي لازم أعرفها؟",
        "قارنلي خطط السداد المختلفة",
        "إيه أحسن وقت للتفاوض على السعر؟",
        "عايز أعرف حالة التسليم الفعلية",
        "هل الأسعار دي قابلة للتفاوض؟",
    ],
    "decision": [
        "احجزلي معاينة للوحدة دي",
        "ابدأ حجز الوحدة",
        "عايز مراجعة قانونية كاملة",
        "قارن خطط السداد النهائية",
        "إيه الخطوات اللي بعد كده؟",
        "إيه الأوراق المطلوبة للحجز؟",
        "عايز أتأكد من الوضع القانوني",
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
        "Compare New Cairo vs October for me",
        "Show me projects with less than 10% down",
        "Which areas have the highest ROI?",
        "Looking for a villa on the North Coast",
        "Is now a good time to buy?",
        "Which developers are most reliable?",
        "Give me a market overview",
        "What's the difference between residential and investment areas?",
    ],
    "exploration": [
        "Compare {property} with similar projects",
        "Show me {developer}'s track record",
        "Calculate ROI over 5 years",
        "What alternatives exist in my budget?",
        "Analyze price per sqm in {location}",
        "Are there cheaper units with similar specs?",
        "Show me other {developer} projects",
        "What's the occupancy rate in {location}?",
        "Is {location} good for families?",
        "What schools and services are nearby?",
        "Inflation vs this unit's price growth?",
        "Show me units with earlier delivery",
    ],
    "comparison": [
        "Side-by-side comparison of my options",
        "Show me the payment plan breakdown",
        "Legal audit this contract (Law 114)",
        "Which is better as a long-term investment?",
        "Analyze this unit against inflation",
        "What risks should I know about?",
        "Compare different payment plans",
        "When's the best time to negotiate?",
        "What's the actual delivery status?",
        "Are these prices negotiable?",
    ],
    "decision": [
        "Schedule a viewing for this property",
        "Start the reservation process",
        "I need a full legal review",
        "Compare final payment plans",
        "What are the next steps?",
        "What documents do I need to reserve?",
        "Verify the legal status first",
    ],
}

# ═══════════════════════════════════════════════════════════════
# RESPONSE-CONTENT KEYWORD TRIGGERS (override phase suggestions)
# ═══════════════════════════════════════════════════════════════
CONTENT_TRIGGERS_AR = [
    (["تضخم", "inflation", "فلوسك"], ["إزاي أحمي فلوسي؟", "حلل العائد الحقيقي بعد التضخم", "أنهي أحسن: عقار ولا شهادات بنك؟"]),
    (["مطور", "developer", "تسليم"], ["إيه سجل التسليم بتاعهم؟", "هل فيه مطور أضمن؟", "ورّيني التقييمات والشكاوي"]),
    (["ساحل", "سوخنة", "coast", "sokhna"], ["أنهي أحسن: ساحل ولا سوخنة؟", "هل العائد الإيجاري كويس؟", "إيه أحسن كمبوند هناك؟"]),
    (["ROI", "عائد", "ربح", "return"], ["قارن العائد مع البنك", "إيه أعلى عائد في الميزانية دي؟", "حلل العائد على 3 و5 و10 سنين"]),
    (["أقساط", "سداد", "installment", "payment"], ["إيه أطول خطة سداد؟", "هل فيه سداد بدون فوايد؟", "قارن خطط السداد المتاحة"]),
    (["قانون", "عقد", "law", "legal"], ["هل العقد محمي قانونياً؟", "ورّيني تحليل قانون 114", "إيه حقوقي لو المطور اتأخر؟"]),
]

CONTENT_TRIGGERS_EN = [
    (["inflation", "cash", "money"], ["How can I protect my money?", "Analyze real return after inflation", "Property vs bank CDs — which is better?"]),
    (["developer", "delivery", "track record"], ["What's their delivery track record?", "Is there a more reliable developer?", "Show me ratings and complaints"]),
    (["coast", "sokhna", "sahel", "north coast"], ["North Coast vs Sokhna — which is better?", "Is rental yield good there?", "Best compound in that area?"]),
    (["ROI", "return", "profit", "yield"], ["Compare return vs bank deposits", "Highest ROI in my budget?", "Analyze return over 3, 5, and 10 years"]),
    (["installment", "payment", "plan"], ["What's the longest payment plan?", "Any interest-free payment?", "Compare available payment plans"]),
    (["law", "legal", "contract"], ["Is this contract legally protected?", "Analyze Law 114 for me", "What are my rights if developer delays?"]),
]


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


def _content_trigger_suggestions(
    ai_response: str,
    user_message: str,
    language: str,
) -> List[str]:
    """Check AI response + user message for keyword triggers → return override suggestions."""
    combined = (ai_response + " " + user_message).lower()
    triggers = CONTENT_TRIGGERS_AR if language == "ar" else CONTENT_TRIGGERS_EN
    for keywords, suggestions in triggers:
        if any(kw in combined for kw in keywords):
            return suggestions
    return []


def _deterministic_rotate(candidates: List[str], seed: str, count: int = 3) -> List[str]:
    """Pick `count` items from candidates using a deterministic hash-rotation.
    Different seed → different selection, but same seed → same selection (stable)."""
    if len(candidates) <= count:
        return candidates
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    offset = h % len(candidates)
    rotated = candidates[offset:] + candidates[:offset]
    return rotated[:count]


def generate_suggestions(
    language: str = "ar",
    lead_score: int = 0,
    history_length: int = 0,
    tools_used: Optional[List[str]] = None,
    last_property: Optional[Dict] = None,
    last_action: Optional[str] = None,
    ai_response: str = "",
    user_message: str = "",
) -> List[str]:
    """
    Generate 3 contextual follow-up suggestions.
    Uses content triggers first, then phase-based pool with rotation.
    """
    tools_used = tools_used or []

    # 1) Check content triggers (highest priority — topic-specific)
    triggered = _content_trigger_suggestions(ai_response, user_message, language)
    if triggered:
        seed = ai_response[:200] + user_message[:100]
        return _deterministic_rotate(triggered, seed, 3)

    # 2) Phase-based pool
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
        if "{" not in suggestion and suggestion.strip():
            filled.append(suggestion)

    # 3) Deterministic rotation using AI response as seed → different response = different chips
    seed = ai_response[:200] + str(history_length) + user_message[:100]
    return _deterministic_rotate(filled, seed, 3)


def generate_suggestions_from_turn(
    language: str,
    lead_score: int,
    history: List[Dict],
    ui_actions: List[Dict],
    properties: List[Dict],
    ai_response: str = "",
    user_message: str = "",
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
        ai_response=ai_response,
        user_message=user_message,
    )
