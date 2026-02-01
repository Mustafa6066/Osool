"""
Psychology Layer for AMR - "The Wolf's Eye"
--------------------------------------------
Extracts psychological state from user messages to enable
psychology-aware selling tactics.

States:
- FOMO: Fear of Missing Out - responds to scarcity
- RISK_AVERSE: Safety-focused - needs reassurance
- GREED_DRIVEN: ROI-focused - responds to gains
- ANALYSIS_PARALYSIS: Overthinking - needs simplification
- IMPULSE_BUYER: Quick decisions - reduce friction
- TRUST_DEFICIT: Skeptical - needs proof/verification
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class PsychologicalState(Enum):
    """User's emotional decision-making driver."""
    FOMO = "fomo"                        # Fear of Missing Out
    RISK_AVERSE = "risk_averse"          # Safety-focused
    GREED_DRIVEN = "greed_driven"        # ROI-focused
    ANALYSIS_PARALYSIS = "analysis_paralysis"  # Overthinking
    IMPULSE_BUYER = "impulse_buyer"      # Quick decisions
    TRUST_DEFICIT = "trust_deficit"      # Skeptical
    NEUTRAL = "neutral"                  # No clear signal


class UrgencyLevel(Enum):
    """How soon user needs to act."""
    BROWSING = "browsing"       # 0-20% urgency
    EXPLORING = "exploring"     # 20-40% urgency
    EVALUATING = "evaluating"   # 40-60% urgency
    READY_TO_ACT = "ready"      # 60-80% urgency
    URGENT = "urgent"           # 80-100% urgency


@dataclass
class PsychologyProfile:
    """Complete psychological profile for a user session."""
    primary_state: PsychologicalState
    secondary_state: Optional[PsychologicalState] = None
    urgency_level: UrgencyLevel = UrgencyLevel.EXPLORING
    confidence_score: float = 0.5  # 0-1
    detected_triggers: List[str] = field(default_factory=list)
    recommended_tactics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "primary_state": self.primary_state.value,
            "secondary_state": self.secondary_state.value if self.secondary_state else None,
            "urgency_level": self.urgency_level.value,
            "confidence_score": round(self.confidence_score, 2),
            "detected_triggers": self.detected_triggers,
            "recommended_tactics": self.recommended_tactics
        }


# Psychology detection patterns - Arabic and English keywords
PSYCHOLOGY_PATTERNS = {
    PsychologicalState.FOMO: {
        "keywords_ar": [
            "هيخلص", "فاضل كام", "هتخلص", "محدود", "آخر فرصة",
            "ناس تانية", "حد تاني", "هيرفع", "زيادة", "السعر هيزيد",
            "لحد إمتى", "متاح لحد إمتى", "الحق", "فرصة"
        ],
        "keywords_en": [
            "limited", "running out", "last chance", "hurry",
            "others interested", "price increase", "how many left",
            "selling fast", "won't last", "before it's gone"
        ],
        "signals": [
            "asking_about_availability_multiple_times",
            "mentioning_competitor_properties",
            "asking_how_many_left",
            "rush_language"
        ],
        "recommended_tactics": ["scarcity", "insider"],
        "weight": 1.0
    },
    PsychologicalState.RISK_AVERSE: {
        "keywords_ar": [
            "خايف", "مخاطر", "أمان", "ضمان", "موثوق", "تسليم",
            "مضمون", "نصب", "احتيال", "مشاكل", "قانوني", "عقد",
            "قلقان", "متردد", "مش متأكد", "أضمن", "المادة 114",
            # Bank Certificate comparison keywords (key Egyptian market signal)
            "شهادة", "شهادات", "البنك", "فايدة", "فوائد", "ودايع",
            "أحسن من البنك", "البنك ولا عقار", "فلوسي في البنك"
        ],
        "keywords_en": [
            "safe", "secure", "guarantee", "trusted", "delivery",
            "scam", "fraud", "legal", "contract", "worried",
            "concerned", "protection", "risk", "reliable",
            # Bank Certificate comparison keywords
            "certificate", "bank interest", "deposit", "CD rate",
            "better than bank", "bank vs property", "27%", "interest rate"
        ],
        "signals": [
            "asking_about_developer_reputation",
            "mentioning_scams",
            "asking_for_proof",
            "legal_questions",
            "comparing_to_bank_deposits"  # New signal
        ],
        "recommended_tactics": ["authority", "legal_protection", "inflation_comparison"],
        "weight": 1.0
    },
    PsychologicalState.GREED_DRIVEN: {
        "keywords_ar": [
            "عائد", "ربح", "استثمار", "إيجار", "هيزيد", "هيجيب كام",
            "ROI", "دخل", "مكسب", "فلوس", "تضخم", "دهب", "دولار",
            "أحسن استثمار", "هيطلع كام"
        ],
        "keywords_en": [
            "roi", "profit", "investment", "rental", "appreciation",
            "returns", "income", "gains", "money", "yield",
            "inflation", "hedge", "portfolio", "resale"
        ],
        "signals": [
            "multiple_roi_questions",
            "comparing_investment_options",
            "asking_about_resale",
            "mentioning_other_investments"
        ],
        "recommended_tactics": ["vision", "roi_focused"],
        "weight": 1.0
    },
    PsychologicalState.ANALYSIS_PARALYSIS: {
        "keywords_ar": [
            "محتاج أفكر", "مش متأكد", "كتير أوي", "محتار",
            "إيه الفرق", "قارن", "أحسن واحدة", "إيه رأيك",
            "مش عارف أختار", "صعب", "معقد"
        ],
        "keywords_en": [
            "need to think", "not sure", "too many options",
            "confused", "difference", "compare", "best one",
            "which one", "hard to decide", "complex", "overwhelmed"
        ],
        "signals": [
            "asking_same_question_multiple_times",
            "requesting_many_comparisons",
            "long_decision_time"
        ],
        "recommended_tactics": ["simplify", "authority"],
        "weight": 0.8
    },
    PsychologicalState.IMPULSE_BUYER: {
        "keywords_ar": [
            "عايز دلوقتي", "حالاً", "النهارده", "فوراً", "أحجز",
            "خلاص قررت", "ماشي", "تمام", "موافق", "همضي"
        ],
        "keywords_en": [
            "now", "today", "immediately", "book it", "decided",
            "let's go", "done", "agreed", "sign", "ready"
        ],
        "signals": [
            "quick_responses",
            "minimal_questions",
            "immediate_action_language"
        ],
        "recommended_tactics": ["close_fast", "reduce_friction"],
        "weight": 0.9
    },
    PsychologicalState.TRUST_DEFICIT: {
        "keywords_ar": [
            "إزاي أثق", "مين يضمن", "سمعت إن", "ناس اتنصبت",
            "المطور ده", "سمعته إيه", "مشاكل", "تأخير",
            "كلام سماسرة", "مش مصدق", "بتقنعني"
        ],
        "keywords_en": [
            "how can i trust", "who guarantees", "heard that",
            "people got scammed", "developer reputation", "problems",
            "delays", "agent talk", "don't believe", "convince me"
        ],
        "signals": [
            "questioning_credentials",
            "mentioning_bad_experiences",
            "skeptical_tone"
        ],
        "recommended_tactics": ["authority", "proof", "testimonials"],
        "weight": 1.0
    }
}

# Urgency detection patterns
URGENCY_PATTERNS = {
    UrgencyLevel.URGENT: {
        "keywords_ar": ["لازم", "ضروري", "النهارده", "حالاً", "مستعجل", "فوراً"],
        "keywords_en": ["must", "urgent", "today", "immediately", "asap", "now"]
    },
    UrgencyLevel.READY_TO_ACT: {
        "keywords_ar": ["جاهز", "عايز أحجز", "نمضي", "خطوة جاية", "أدفع"],
        "keywords_en": ["ready", "want to book", "next step", "sign", "pay", "reserve"]
    },
    UrgencyLevel.EVALUATING: {
        "keywords_ar": ["بقارن", "بفكر", "محتاج أشوف", "قبل ما أقرر"],
        "keywords_en": ["comparing", "thinking", "need to see", "before deciding"]
    },
    UrgencyLevel.EXPLORING: {
        "keywords_ar": ["بدور", "عايز أعرف", "إيه المتاح", "فيه إيه"],
        "keywords_en": ["looking for", "want to know", "what's available", "show me"]
    },
    UrgencyLevel.BROWSING: {
        "keywords_ar": ["بتفرج", "لسه", "بعدين", "مش مستعجل"],
        "keywords_en": ["just browsing", "later", "not in a hurry", "someday"]
    }
}


def analyze_psychology(
    query: str,
    history: List[Dict],
    intent: Optional[Dict] = None
) -> PsychologyProfile:
    """
    Analyze user's psychological state from query and history.

    Args:
        query: Current user message
        history: Conversation history
        intent: Extracted intent from perception layer

    Returns:
        PsychologyProfile with detected state and recommendations
    """
    query_lower = query.lower()

    # Combine current query with recent history for analysis
    all_text = query_lower
    for msg in history[-5:]:  # Last 5 messages
        if msg.get("role") == "user":
            all_text += " " + msg.get("content", "").lower()

    # Score each psychological state
    state_scores: Dict[PsychologicalState, float] = {}
    detected_triggers: Dict[PsychologicalState, List[str]] = {}

    for state, patterns in PSYCHOLOGY_PATTERNS.items():
        score = 0.0
        triggers = []

        # Check Arabic keywords
        for keyword in patterns.get("keywords_ar", []):
            if keyword in all_text:
                score += 1.0 * patterns["weight"]
                triggers.append(f"ar:{keyword}")

        # Check English keywords
        for keyword in patterns.get("keywords_en", []):
            if keyword in all_text:
                score += 1.0 * patterns["weight"]
                triggers.append(f"en:{keyword}")

        state_scores[state] = score
        detected_triggers[state] = triggers

    # Find primary and secondary states
    sorted_states = sorted(state_scores.items(), key=lambda x: x[1], reverse=True)

    primary_state = PsychologicalState.NEUTRAL
    secondary_state = None
    confidence = 0.0
    all_triggers = []

    if sorted_states[0][1] > 0:
        primary_state = sorted_states[0][0]
        confidence = min(sorted_states[0][1] / 3.0, 1.0)  # Normalize to 0-1
        all_triggers = detected_triggers[primary_state]

        if len(sorted_states) > 1 and sorted_states[1][1] > 0:
            secondary_state = sorted_states[1][0]
            all_triggers.extend(detected_triggers[secondary_state])

    # Detect urgency level
    urgency = _detect_urgency(query_lower, history)

    # Get recommended tactics
    tactics = PSYCHOLOGY_PATTERNS.get(primary_state, {}).get("recommended_tactics", [])
    if secondary_state:
        tactics.extend(PSYCHOLOGY_PATTERNS.get(secondary_state, {}).get("recommended_tactics", []))
    tactics = list(set(tactics))  # Remove duplicates

    # NEW: Sarcasm Detector (The "Human Touch" Framework)
    # 1. Direct verbal signals
    sarcasm_triggers = ["sure you are", "yeah right", "tell me another one", "obvious", "robot", "lies", "joke", "funny", "نكتة", "بتهزر", "مصدقك", "اكيد طبعا"]
    is_sarcastic = any(x in query.lower() for x in sarcasm_triggers)
    
    # 2. Contextual Sarcasm (Price Sensitivity)
    if not is_sarcastic:
        is_sarcastic = _detect_contextual_sarcasm(query, history)

    if is_sarcastic:
        primary_state = PsychologicalState.TRUST_DEFICIT
        confidence = 0.0 # Force low confidence to trigger cautious response
        tactics = ["humility", "proof_only", "acknowledge_skepticism"]
        all_triggers.append("detected_sarcasm")
        logger.info("🎭 Sarcasm Detected: Overriding state to TRUST_DEFICIT")

    profile = PsychologyProfile(
        primary_state=primary_state,
        secondary_state=secondary_state,
        urgency_level=urgency,
        confidence_score=confidence,
        detected_triggers=all_triggers[:5],  # Limit to top 5 triggers
        recommended_tactics=tactics
    )

    logger.info(f"🧠 Psychology: {primary_state.value} (conf: {confidence:.2f}), Urgency: {urgency.value}")

    return profile


def _detect_contextual_sarcasm(query: str, history: List[Dict]) -> bool:
    """
    Detect if user is being sarcastic based on context.
    Example: High price in history + User says "Cheap/Deal".
    """
    if not history:
        return False
        
    last_ai_msg = next((m for m in reversed(history) if m["role"] == "assistant"), None)
    if not last_ai_msg:
        return False
        
    last_content = last_ai_msg.get("content", "").lower()
    query_lower = query.lower()
    
    # Check if last message had high price (e.g. > 10M or mention of millions)
    has_high_price = "million" in last_content or "مليون" in last_content
    
    # Check if user response is suspiciously positive/dismissive
    positive_words_ar = ["رخيص", "بلاش", "لقطة", "تحفة", "بسيط"]
    positive_words_en = ["cheap", "steal", "nothing", "pennies", "pocket change"]
    
    is_positive = any(w in query_lower for w in positive_words_ar + positive_words_en)
    
    # Heuristic: High Price + "Cheap" = Sarcasm
    if has_high_price and is_positive:
        # Check against negation (e.g. "not cheap")
        if "not" in query_lower or "مش" in query_lower:
            return False
        return True
        
    return False


def _detect_urgency(query: str, history: List[Dict]) -> UrgencyLevel:
    """Detect urgency level from query and history."""

    # Check from most urgent to least
    for level in [UrgencyLevel.URGENT, UrgencyLevel.READY_TO_ACT,
                  UrgencyLevel.EVALUATING, UrgencyLevel.EXPLORING]:
        patterns = URGENCY_PATTERNS.get(level, {})

        for keyword in patterns.get("keywords_ar", []):
            if keyword in query:
                return level

        for keyword in patterns.get("keywords_en", []):
            if keyword in query:
                return level

    # Default based on conversation length
    if len(history) > 10:
        return UrgencyLevel.EVALUATING
    elif len(history) > 5:
        return UrgencyLevel.EXPLORING
    else:
        return UrgencyLevel.BROWSING


def get_psychology_context_for_prompt(profile: PsychologyProfile) -> str:
    """
    Generate context string to inject into Claude's system prompt.

    Args:
        profile: The detected psychology profile

    Returns:
        Context string for the AI prompt
    """
    state = profile.primary_state
    urgency = profile.urgency_level

    context_parts = [
        f"\n[PSYCHOLOGY_MODE: {state.value.upper()}]"
    ]

    # State-specific instructions
    if state == PsychologicalState.FOMO:
        context_parts.append("""
- User is susceptible to scarcity. Use time-limited language.
- Mention: "الحق الفرصة دي" (Catch this opportunity)
- Highlight: Limited units, upcoming price increases, other interested buyers
- Urgency phrases: "قبل ما تخلص", "السعر ده مش هيفضل"
""")

    elif state == PsychologicalState.RISK_AVERSE:
        context_parts.append("""
- User needs reassurance and safety. Lead with protection.
- Mention: Developer reputation, delivery track record, Law 114 compliance
- Use: "على مسؤوليتي", "أنا بحميك", "العقد سليم"
- Offer: Contract review, legal verification, testimonials
""")

    elif state == PsychologicalState.GREED_DRIVEN:
        context_parts.append("""
- User is ROI-focused. Lead with numbers and returns.
- Show: ROI projections, rental yields, appreciation forecasts
- Compare: Property vs Cash vs Gold (Inflation Killer)
- Use: "العائد", "الـ ROI", "هتكسب كام في السنة"
""")

    elif state == PsychologicalState.ANALYSIS_PARALYSIS:
        context_parts.append("""
- User is overthinking. Simplify and guide decisively.
- Limit options to TOP 2 maximum
- Make the recommendation clear: "لو أنا مكانك..."
- Reduce cognitive load, be direct about best choice
""")

    elif state == PsychologicalState.IMPULSE_BUYER:
        context_parts.append("""
- User wants to act fast. Reduce friction.
- Skip lengthy explanations, get to booking/payment
- Provide quick next step: "خلينا نحجز دلوقتي"
- Don't over-explain, maintain momentum
""")

    elif state == PsychologicalState.TRUST_DEFICIT:
        context_parts.append("""
- User is skeptical. Build credibility with proof.
- Reference: "السيستم بتاعي بيقول" (data-backed claims)
- Offer: Verification, references, developer portfolio
- Don't push hard, build trust first
""")

    # Urgency context
    if urgency == UrgencyLevel.URGENT or urgency == UrgencyLevel.READY_TO_ACT:
        context_parts.append("""
[URGENCY: HIGH]
- User is ready to act. Move to closing.
- Provide booking/reservation link or next step
- Don't introduce new options, focus on closing current interest
""")

    return "\n".join(context_parts)


# Singleton-style function for easy import
def get_psychology_analyzer():
    """Return the analyze_psychology function for external use."""
    return analyze_psychology


class Strategy(Enum):
    """Sales strategy based on psychological state."""
    TRUST_BUILDING = "trust_building"    # Focus on Law 114, Developer Reputation
    ROI_FOCUSED = "roi_focused"          # Focus on 25% annual gain, inflation hedge
    SCARCITY_PITCH = "scarcity_pitch"    # Focus on "Last unit", "Price increase tomorrow"
    CONSULTATIVE = "consultative"        # Educational, guiding approach
    CLOSE_FAST = "close_fast"            # Reduce friction, move to action
    SIMPLIFY = "simplify"                # Cut options, make recommendation


def determine_strategy(
    psychology: PsychologyProfile,
    has_properties: bool = True,
    top_property_verdict: str = "FAIR"
) -> Dict[str, Any]:
    """
    Determine the optimal sales strategy based on psychology and data.
    
    This is the core "Wolf" strategy selector that maps emotional
    state to persuasion angle.
    
    Args:
        psychology: The detected psychology profile
        has_properties: Whether we have properties to show
        top_property_verdict: Best property verdict (BARGAIN/FAIR/PREMIUM)
    
    Returns:
        Strategy dict with angle and talking points
    """
    state = psychology.primary_state
    urgency = psychology.urgency_level
    
    # Map psychology to strategy
    if state == PsychologicalState.RISK_AVERSE:
        strategy = Strategy.TRUST_BUILDING
        angle = "trust"
        talking_points = [
            "Don't sign anything yet. Send me the contract first; I'll run my Legal Scanner on it.",
            "I utilize a Law 114 Legal Scanner to detect contract loopholes.",
            "This developer has a 95% on-time delivery record. Zero legal violations.",
            "My protocol requires verification on Polygon before I recommend this.",
        ]
        
    elif state == PsychologicalState.GREED_DRIVEN:
        strategy = Strategy.ROI_FOCUSED
        angle = "profit"
        talking_points = [
            "This unit is an 'Inflation Killer'. It generates 2x the return of a bank deposit.",
            "Inflation is 35%. Bank CDs are 27%. You are losing 8% annually. This property stops the bleeding.",
            "Projected ROI is 25% conservative. Including rental yield, you beat Gold.",
            "This is a 'Catch' - math proves it.",
        ]
        
    elif state == PsychologicalState.FOMO:
        strategy = Strategy.SCARCITY_PITCH
        angle = "scarcity"
        talking_points = [
            "There are only 2 units left with this view. The developer raises prices on Sunday.",
            "This price is valid for 48 hours. I've seen the developer's internal memo.",
            "Demand in this zone is up 40%. Waiting = Paying more.",
            "I have 3 other investors looking at this same unit right now.",
        ]
        
    elif state == PsychologicalState.ANALYSIS_PARALYSIS:
        strategy = Strategy.SIMPLIFY
        angle = "decision"
        talking_points = [
            "خليني أسهلها عليك - ده الخيار الأفضل ليك",
            "من كل اللي شوفته، الوحدة دي أحسن match",
            "لو أنا مكانك، هختار دي",
            "متشتتش نفسك - ركز على دي",
        ]
        
    elif state == PsychologicalState.IMPULSE_BUYER:
        strategy = Strategy.CLOSE_FAST
        angle = "action"
        talking_points = [
            "خلينا نحجز دلوقتي بمقدم قليل",
            "أنا هعملك رابط الحجز حالاً",
            "امضي وخلص الموضوع",
            "الخطوة الجاية سهلة - بس هنحتاج...",
        ]
        
    elif state == PsychologicalState.TRUST_DEFICIT:
        strategy = Strategy.TRUST_BUILDING
        angle = "proof"
        talking_points = [
            "Before we talk prices, I want to show you the transaction history.",
            "I don't want you to trust me. I want you to trust the data. Here is the Blockchain Verification link for the last unit we sold...",
            "Send me any contract you have—I'll run my Law 114 Scanner on it for free."
        ]
        
    else:  # NEUTRAL
        strategy = Strategy.CONSULTATIVE
        angle = "guide"
        talking_points = [
            "خليني أفهم احتياجاتك الأول",
            "إيه أهم حاجة ليك - الموقع ولا السعر؟",
            "هل بتشتري للسكن ولا للاستثمار؟",
            "أنا هنا أساعدك تختار صح",
        ]
    
    # Modify based on urgency
    if urgency in [UrgencyLevel.URGENT, UrgencyLevel.READY_TO_ACT]:
        talking_points.append("خلينا نتحرك دلوقتي")
    
    # Modify based on data quality
    if top_property_verdict == "BARGAIN" and has_properties:
        talking_points.insert(0, "🔥 لقيتلك لقطة - تحت سعر السوق")
    
    return {
        "strategy": strategy.value,
        "angle": angle,
        "talking_points": talking_points,
        "psychology_state": state.value,
        "urgency": urgency.value,
        "primary_message": talking_points[0] if talking_points else "",
    }


# Export
__all__ = [
    "PsychologicalState",
    "UrgencyLevel",
    "PsychologyProfile",
    "Strategy",
    "analyze_psychology",
    "determine_strategy",
    "get_psychology_context_for_prompt",
    "PSYCHOLOGY_PATTERNS"
]

