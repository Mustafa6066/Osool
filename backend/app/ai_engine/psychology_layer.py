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
    TRUST_DEFICIT = "trust_deficit"      # Skeptical - needs proof/verification
    SKEPTICISM = "skepticism"            # Questions market data validity
    FAMILY_SECURITY = "family_security"  # Family home buyer - safety over ROI
    MACRO_SKEPTIC = "macro_skeptic"      # Questions market fundamentals (inflation, currency)
    LEGAL_ANXIETY = "legal_anxiety"      # Fear of contracts/registration status
    LIQUIDITY_SHIFT = "liquidity_shift"  # Moving money from Bank -> Real Estate

    # Egyptian Market-Specific States (2025-2026)
    INSTALLMENT_ANXIETY = "installment_anxiety"  # Fear of long-term payment commitments
    DELIVERY_FEAR = "delivery_fear"              # Fear of delayed delivery (post-2023 market trauma)
    CURRENCY_HEDGER = "currency_hedger"          # Actively moving USD/EGP to real estate as store of value
    INFLATION_REFUGEE = "inflation_refugee"      # Escaping currency devaluation to real assets

    NEUTRAL = "neutral"                  # No clear signal


class ObjectionType(Enum):
    """V2: Granular objection classification for specific responses."""
    FINANCIAL = "financial"       # "Can I afford the installments?"
    TRUST = "trust"               # "Will the developer deliver?"
    MARKET = "market"             # "Will the bubble burst?"
    TIMING = "timing"             # "Is now a good time?"
    LOCATION = "location"         # "Is this area good?"
    LEGAL = "legal"               # "Are the papers clean?"
    NONE = "none"                 # No specific objection


class UrgencyLevel(Enum):
    """How soon user needs to act."""
    BROWSING = "browsing"       # 0-20% urgency
    EXPLORING = "exploring"     # 20-40% urgency
    EVALUATING = "evaluating"   # 40-60% urgency
    READY_TO_ACT = "ready"      # 60-80% urgency
    URGENT = "urgent"           # 80-100% urgency


@dataclass
class PsychologyProfile:
    """
    V2: Enhanced psychological profile with emotional trajectory.
    
    Upgrades:
    - dominant_trait: Session-wide personality (not just current message)
    - emotional_momentum: Tracks if user is warming up or cooling down
    - specific_objection: Granular objection type for targeted responses
    """
    primary_state: PsychologicalState
    secondary_state: Optional[PsychologicalState] = None
    urgency_level: UrgencyLevel = UrgencyLevel.EXPLORING
    confidence_score: float = 0.5  # 0-1
    detected_triggers: List[str] = field(default_factory=list)
    recommended_tactics: List[str] = field(default_factory=list)
    
    # V2 Superhuman Upgrades
    dominant_trait: Optional[PsychologicalState] = None  # Session personality
    emotional_momentum: str = "static"  # "warming_up", "cooling_down", "static"
    specific_objection: ObjectionType = ObjectionType.NONE  # Granular objection

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "primary_state": self.primary_state.value,
            "secondary_state": self.secondary_state.value if self.secondary_state else None,
            "urgency_level": self.urgency_level.value,
            "confidence_score": round(self.confidence_score, 2),
            "detected_triggers": self.detected_triggers,
            "recommended_tactics": self.recommended_tactics,
            # V2 fields
            "dominant_trait": self.dominant_trait.value if self.dominant_trait else None,
            "emotional_momentum": self.emotional_momentum,
            "specific_objection": self.specific_objection.value
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
    },
    # === FAMILY SECURITY: The "Life Decision Maker" Profile ===
    PsychologicalState.FAMILY_SECURITY: {
        "keywords_ar": [
            "سكن عائلي", "بيت العيلة", "بيت للعيلة", "منزل العائلة",
            "مدارس", "قريب من مدرسة", "المدارس", "أولاد", "اولادي", "الأطفال",
            "أمان", "أمن", "خصوصية", "جيران", "مجتمع", "كمباوند",
            "هادي", "هدوء", "مستقر", "استقرار", "سكن", "عيشة",
            "مجمع مغلق", "سيكيوريتي", "حراسة", "أمان للأولاد",
            "بنتي", "ابني", "زوجتي", "عروسة", "جواز", "الجواز"
        ],
        "keywords_en": [
            "family home", "family living", "kids", "children", "schools",
            "near school", "safety", "secure", "privacy", "neighbors",
            "community", "compound", "gated", "quiet", "peaceful",
            "settle down", "daughter", "son", "wife", "marriage", "wedding"
        ],
        "signals": [
            "asking_about_schools",
            "asking_about_community",
            "mentioning_children",
            "mentioning_family_needs",
            "life_decision_language"
        ],
        "recommended_tactics": ["authority", "legal_protection", "community_audit", "developer_reputation"],
        "weight": 1.2  # Slightly higher weight - life decisions are serious
    },
    # === MACRO SKEPTIC: The "Market Doubter" Profile ===
    PsychologicalState.MACRO_SKEPTIC: {
        "keywords_ar": [
            "الدولار", "التعويم", "فقاعة", "الأسعار غالية", "هينزل", "السوق هيقع",
            "مش وقته", "أستنى", "الاقتصاد", "التضخم", "البنك أحسن", "شهادات البنك",
            "الأسعار مجنونة", "ده نصب", "كله غالي", "فلوسي في البنك",
            "هتخس فلوسي", "خايف من بكرة", "تحويشة العمر"
        ],
        "keywords_en": [
            "dollar", "devaluation", "bubble", "too expensive", "prices will drop",
            "market crash", "not the right time", "wait", "economy", "inflation",
            "bank is safer", "bank certificates", "crazy prices", "losing money",
            "scared of tomorrow", "life savings"
        ],
        "signals": [
            "questioning_market_fundamentals",
            "comparing_to_bank_deposits",
            "expressing_macro_fear",
            "mentioning_currency_concerns",
            "life_savings_at_stake"
        ],
        "recommended_tactics": ["replacement_cost_logic", "inflation_hedge_math", "wealth_preservation"],
        "weight": 1.3  # High weight - macro fear needs immediate counter-argument
    },
    # === LEGAL ANXIETY: The "Urfi Contract" Fear ===
    PsychologicalState.LEGAL_ANXIETY: {
        "keywords_ar": [
            "عقد", "مسجل", "شهر عقاري", "تراخيص", "ورق", "محامي", "ملكية", 
            "عقد ابتدائي", "تسجيل", "مخالفات", "توكيل", "صحة توقيع"
        ],
        "keywords_en": [
            "contract", "registered", "registration", "license", "permits", 
            "lawyer", "ownership", "title", "legal", "preliminary contract"
        ],
        "signals": ["asking_for_legal_docs", "fear_of_scams", "mentioning_lawyer"],
        "recommended_tactics": ["law_114_guardian", "legal_audit", "transparency"],
        "weight": 1.4 # Critical trust blocker
    },
    # === LIQUIDITY SHIFT: The "Bank Exodous" Investor ===
    PsychologicalState.LIQUIDITY_SHIFT: {
        "keywords_ar": [
            "شهادات", "البنك", "فايدة", "وديعة", "فك الشهادة", "البنك المركزي",
            "سعر الفايدة", "عائد شهري", "تحويشة", "معاش", "فلوس البنك"
        ],
        "keywords_en": [
            "certificates", "bank", "interest rate", "deposit", "cd",
            "maturity", "central bank", "monthly income"
        ],
        "signals": ["comparing_real_estate_to_bank", "seeking_monthly_income"],
        "recommended_tactics": ["inflation_hedge_math", "ready_to_move_priority", "rental_yield_focus"],
        "weight": 1.3
    },

    # ═══════════════════════════════════════════════════════════════════════
    # EGYPTIAN MARKET-SPECIFIC STATES (2025-2026)
    # ═══════════════════════════════════════════════════════════════════════

    # === INSTALLMENT ANXIETY: Fear of Long-Term Payment Commitments ===
    PsychologicalState.INSTALLMENT_ANXIETY: {
        "keywords_ar": [
            "أقساط طويلة", "قسط شهري", "هأقدر أدفع", "مدة السداد", "فايدة",
            "تمويل", "قرض", "سنين كتير", "8 سنين", "10 سنين", "التزام",
            "الالتزام", "مش هقدر", "القسط كبير", "لو اتغيرت الظروف",
            "لو فقدت شغلي", "لو حصل حاجة", "ظروف صعبة"
        ],
        "keywords_en": [
            "installment", "monthly payment", "afford", "payment period", "interest",
            "financing", "loan", "many years", "commitment", "can't afford",
            "too much", "circumstances change", "lose job", "what if"
        ],
        "signals": [
            "asking_about_installment_details",
            "expressing_payment_concerns",
            "asking_about_flexible_plans",
            "long_term_commitment_fear"
        ],
        "recommended_tactics": ["payment_plan_analysis", "affordability_calculator", "compare_to_rent"],
        "weight": 1.2
    },

    # === DELIVERY FEAR: Post-2023 Market Trauma (Developer Trust Issues) ===
    PsychologicalState.DELIVERY_FEAR: {
        "keywords_ar": [
            "تسليم", "هيسلم امتى", "اتأخر", "تأخير", "مسلموش", "استلام",
            "معاد التسليم", "التزام المطور", "مشاريع متأخرة", "ناس مستلمتش",
            "سنين بتستنى", "المواعيد", "وعود", "وعدوني", "قالوا هيسلموا",
            "المشروع واقف", "تجميد", "إفلاس", "المطور وقع"
        ],
        "keywords_en": [
            "delivery", "when delivered", "delayed", "delay", "not delivered",
            "handover", "delivery date", "developer commitment", "delayed projects",
            "people waiting", "years waiting", "promises", "promised",
            "project stopped", "frozen", "bankruptcy", "developer failed"
        ],
        "signals": [
            "asking_about_delivery_timeline",
            "mentioning_delayed_projects",
            "asking_about_developer_track_record",
            "expressing_delivery_skepticism"
        ],
        "recommended_tactics": ["developer_track_record", "delivery_timeline_show", "escrow_protection", "law_114_guardian"],
        "weight": 1.4  # High weight - major Egyptian market trauma
    },

    # === CURRENCY HEDGER: Moving Money to Real Estate as Store of Value ===
    PsychologicalState.CURRENCY_HEDGER: {
        "keywords_ar": [
            "الدولار", "سعر الصرف", "الجنيه بينزل", "العملة", "تحويشة بالدولار",
            "فلوسي بره", "التحويل", "القيمة الشرائية", "الجنيه هيفضل",
            "أحافظ على فلوسي", "تخزين القيمة", "بدل ما تقل قيمتها"
        ],
        "keywords_en": [
            "dollar", "exchange rate", "currency devaluation", "currency",
            "savings abroad", "convert", "purchasing power", "pound will",
            "preserve money", "store of value", "before it loses value"
        ],
        "signals": [
            "mentioning_currency_concerns",
            "comparing_currencies",
            "asking_about_dollar_pricing",
            "wealth_preservation_intent"
        ],
        "recommended_tactics": ["wealth_preservation", "usd_pricing_option", "historical_appreciation"],
        "weight": 1.3
    },

    # === INFLATION REFUGEE: Escaping Currency Devaluation to Real Assets ===
    PsychologicalState.INFLATION_REFUGEE: {
        "keywords_ar": [
            "التضخم", "الأسعار بتزيد", "كل حاجة غليت", "فلوسي بتقل",
            "القوة الشرائية", "معدل التضخم", "13%", "20%", "30%",
            "الفلوس مش بتجيب حاجة", "قيمة الفلوس", "البنك مش كفاية",
            "الفايدة مش بتغطي", "التضخم أعلى من الفايدة"
        ],
        "keywords_en": [
            "inflation", "prices rising", "everything expensive", "money losing value",
            "purchasing power", "inflation rate", "money doesn't buy",
            "value of money", "bank not enough", "interest doesn't cover",
            "inflation higher than interest"
        ],
        "signals": [
            "mentioning_inflation_concerns",
            "comparing_inflation_to_returns",
            "expressing_value_erosion_fear",
            "seeking_inflation_hedge"
        ],
        "recommended_tactics": ["inflation_killer_chart", "real_returns_calculation", "asset_appreciation_history"],
        "weight": 1.3
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

# V2: OBJECTION PATTERNS for granular classification
OBJECTION_PATTERNS = {
    ObjectionType.FINANCIAL: {
        "keywords_ar": [
            "أقسط", "أقدر أدفع", "الأقساط", "مقدم", "كاش", "فلوس", "ميزانية",
            "غالي", "رخيص", "السعر عالي", "مش قادر", "الدفع", "التمويل"
        ],
        "keywords_en": [
            "afford", "installments", "down payment", "budget", "expensive",
            "financing", "payment plan", "cash", "price too high", "can't pay"
        ]
    },
    ObjectionType.TRUST: {
        "keywords_ar": [
            "المطور", "تسليم", "تأخير", "نصب", "سمعة", "موثوق",
            "ناس اتنصبت", "هيسلم", "ضمان التسليم"
        ],
        "keywords_en": [
            "developer", "delivery", "delay", "scam", "reputation", "reliable",
            "will they deliver", "track record", "guarantee delivery"
        ]
    },
    ObjectionType.MARKET: {
        "keywords_ar": [
            "الفقاعة", "هينزل", "السوق هيقع", "الأسعار هتنزل", "مستقر",
            "وقت مناسب", "التضخم", "الاقتصاد"
        ],
        "keywords_en": [
            "bubble", "crash", "prices will drop", "market stable", "good time",
            "inflation", "economy", "will prices fall"
        ]
    },
    ObjectionType.TIMING: {
        "keywords_ar": [
            "أستنى", "بعدين", "مش الوقت", "السنة الجاية", "لسه بدري",
            "مش مستعجل"
        ],
        "keywords_en": [
            "wait", "later", "not the right time", "next year", "too early",
            "not in a hurry"
        ]
    },
    ObjectionType.LOCATION: {
        "keywords_ar": [
            "المنطقة", "الجيران", "الخدمات", "قريب من", "بعيد عن",
            "الموقع ده", "فين بالظبط"
        ],
        "keywords_en": [
            "area", "neighborhood", "services", "close to", "far from",
            "location", "where exactly"
        ]
    },
    ObjectionType.LEGAL: {
        "keywords_ar": [
            "العقد", "الأوراق", "قانوني", "تسجيل", "ملكية", "114",
            "تسلسل الملكية", "رخصة"
        ],
        "keywords_en": [
            "contract", "papers", "legal", "registration", "ownership",
            "law 114", "chain of title", "permit"
        ]
    }
}


def _detect_objection_type(query: str, triggers: List[str]) -> ObjectionType:
    """
    V2: Detect specific objection type for granular response.
    This enables different responses for financial vs trust vs market concerns.
    """
    query_lower = query.lower()
    
    # Score each objection type
    scores = {}
    for objection_type, patterns in OBJECTION_PATTERNS.items():
        score = 0
        for keyword in patterns.get("keywords_ar", []):
            if keyword in query_lower:
                score += 1
        for keyword in patterns.get("keywords_en", []):
            if keyword in query_lower:
                score += 1
        scores[objection_type] = score
    
    # Find highest scoring objection
    best_objection = max(scores, key=scores.get)
    if scores[best_objection] > 0:
        return best_objection
    
    return ObjectionType.NONE


def _calculate_emotional_momentum(history: List[Dict]) -> str:
    """
    V2: Track if user is warming up or cooling down over conversation.
    
    Analyzes state progression across recent messages:
    - warming_up: Moving from skeptical -> engaged
    - cooling_down: Moving from engaged -> skeptical
    - static: No clear trajectory
    """
    if len(history) < 4:
        return "static"
    
    # Positive signals (warming up)
    positive_signals = [
        "عايز", "جاهز", "موافق", "حلو", "تمام", "كويس", "ممتاز",
        "interested", "ready", "sounds good", "okay", "let's", "show me more"
    ]
    
    # Negative signals (cooling down)
    negative_signals = [
        "مش متأكد", "بعدين", "محتاج أفكر", "غالي", "مش مقتنع",
        "not sure", "later", "need to think", "expensive", "not convinced"
    ]
    
    # Count signals in first half vs second half
    recent_history = history[-6:]
    first_half = recent_history[:3]
    second_half = recent_history[3:]
    
    def count_signals(msgs, signals):
        count = 0
        for msg in msgs:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                count += sum(1 for s in signals if s in content)
        return count
    
    first_positive = count_signals(first_half, positive_signals)
    first_negative = count_signals(first_half, negative_signals)
    second_positive = count_signals(second_half, positive_signals)
    second_negative = count_signals(second_half, negative_signals)
    
    # Determine trajectory
    if second_positive > first_positive and second_negative <= first_negative:
        return "warming_up"
    elif second_negative > first_negative and second_positive <= first_positive:
        return "cooling_down"
    
    return "static"


def _calculate_dominant_trait(history: List[Dict]) -> Optional[PsychologicalState]:
    """
    V2: Calculate user's dominant personality trait across entire session.
    
    This is different from primary_state (current message) - it tracks
    the overall pattern across all messages.
    """
    if len(history) < 3:
        return None
    
    # Count state occurrences across history
    state_counts = {state: 0 for state in PsychologicalState}
    
    for msg in history:
        if msg.get("role") == "user":
            content = msg.get("content", "").lower()
            
            # Simple keyword matching for each state
            for state, patterns in PSYCHOLOGY_PATTERNS.items():
                for keyword in patterns.get("keywords_ar", []) + patterns.get("keywords_en", []):
                    if keyword in content:
                        state_counts[state] += 1
    
    # Find most common state
    if max(state_counts.values()) > 0:
        dominant = max(state_counts, key=state_counts.get)
        if state_counts[dominant] >= 2:  # Minimum threshold
            return dominant
    
    return None


async def semantic_classify_emotion(query: str, history_context: str = "") -> Tuple[PsychologicalState, float]:
    """
    V2: Semantic fallback using LLM when keyword matching returns NEUTRAL/low confidence.
    
    This catches nuanced expressions like:
    - "I'm not sure if I want to commit my life savings to a hole in the ground"
    (Should be RISK_AVERSE, but no keywords match)
    
    Uses Claude Haiku for speed and cost efficiency.
    """
    try:
        from langchain_anthropic import ChatAnthropic
        
        classifier = ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0,
            max_tokens=100
        )
        
        classification_prompt = f"""Classify this Egyptian real estate buyer's emotional state.

User message: "{query}"
Recent context: {history_context[:500] if history_context else "None"}

Classify into ONE of these states:
- FOMO: Fear of missing out, wants to act fast
- RISK_AVERSE: Worried about safety, scams, delivery
- GREED_DRIVEN: Focused on ROI, profit, investment returns
- ANALYSIS_PARALYSIS: Overthinking, can't decide
- IMPULSE_BUYER: Ready to act immediately
- TRUST_DEFICIT: Skeptical of claims, needs proof
- SKEPTICISM: Questions market data validity
- FAMILY_SECURITY: Buying for family living, prioritizes safety/schools
- MACRO_SKEPTIC: Questions market fundamentals (inflation, currency, bubble fears)
- NEUTRAL: No clear emotional driver

Respond with ONLY:
{{"state": "STATE_NAME", "confidence": 0.X}}"""

        response = await classifier.ainvoke(classification_prompt)
        
        # Parse response
        import json
        result = json.loads(response.content)
        state_name = result.get("state", "NEUTRAL").upper()
        confidence = float(result.get("confidence", 0.5))
        
        # Map to enum
        state_map = {
            "FOMO": PsychologicalState.FOMO,
            "RISK_AVERSE": PsychologicalState.RISK_AVERSE,
            "GREED_DRIVEN": PsychologicalState.GREED_DRIVEN,
            "ANALYSIS_PARALYSIS": PsychologicalState.ANALYSIS_PARALYSIS,
            "IMPULSE_BUYER": PsychologicalState.IMPULSE_BUYER,
            "TRUST_DEFICIT": PsychologicalState.TRUST_DEFICIT,
            "SKEPTICISM": PsychologicalState.SKEPTICISM,
            "FAMILY_SECURITY": PsychologicalState.FAMILY_SECURITY,
            "MACRO_SKEPTIC": PsychologicalState.MACRO_SKEPTIC,
            "NEUTRAL": PsychologicalState.NEUTRAL
        }
        
        return state_map.get(state_name, PsychologicalState.NEUTRAL), confidence
        
    except Exception as e:
        logger.warning(f"Semantic classification failed: {e}")
        return PsychologicalState.NEUTRAL, 0.3


def calculate_card_readiness(
    psychology: PsychologyProfile,
    history: List[Dict],
    memory: Optional[Any] = None,
    lead_score: int = 0
) -> Dict[str, Any]:
    """
    Calculate a composite 'card readiness' score 0-100 that determines
    when the user is psychologically ready to see property cards.

    Factors:
    - Lead score contribution (0-30 points)
    - Engagement depth (0-20 points)
    - Emotional momentum (0-15 points)
    - Urgency level (0-15 points)
    - Objection resolution / state modifiers (0-20 points)
    """
    score = 0
    reasons = []

    # 1. Base from lead score (0-30 points)
    score += min(int(lead_score * 0.3), 30)

    # 2. Engagement depth (0-20 points)
    turn_count = len([m for m in history if m.get("role") == "user"])
    depth_points = min(turn_count * 4, 20)
    score += depth_points
    if turn_count >= 3:
        reasons.append("sustained_engagement")

    # 3. Emotional momentum (-10 to +15 points)
    if psychology.emotional_momentum == "warming_up":
        score += 15
        reasons.append("warming_up")
    elif psychology.emotional_momentum == "cooling_down":
        score -= 10
        reasons.append("cooling_down")

    # 4. Urgency (0-15 points)
    urgency_scores = {
        UrgencyLevel.URGENT: 15,
        UrgencyLevel.READY_TO_ACT: 12,
        UrgencyLevel.EVALUATING: 8,
        UrgencyLevel.EXPLORING: 4,
        UrgencyLevel.BROWSING: 0,
    }
    score += urgency_scores.get(psychology.urgency_level, 0)

    # 5. Objection resolution (0-20 points)
    if memory:
        objections = getattr(memory, 'objections_raised', [])
        if len(objections) > 0 and turn_count > len(objections) + 2:
            score += 20  # Objections were raised and conversation continued
            reasons.append("objections_resolved")
        elif len(objections) > 0:
            score -= 10  # Active unresolved objections
            reasons.append("unresolved_objections")

    # 6. State-specific modifiers
    state_modifiers = {
        PsychologicalState.IMPULSE_BUYER: 20,
        PsychologicalState.GREED_DRIVEN: 15,
        PsychologicalState.FOMO: 15,
        PsychologicalState.LIQUIDITY_SHIFT: 10,
        PsychologicalState.CURRENCY_HEDGER: 10,
        PsychologicalState.NEUTRAL: 10,
        PsychologicalState.FAMILY_SECURITY: 5,
        PsychologicalState.INFLATION_REFUGEE: 5,
        PsychologicalState.RISK_AVERSE: -10,
        PsychologicalState.ANALYSIS_PARALYSIS: -15,
        PsychologicalState.SKEPTICISM: -15,
        PsychologicalState.MACRO_SKEPTIC: -15,
        PsychologicalState.LEGAL_ANXIETY: -10,
        PsychologicalState.DELIVERY_FEAR: -10,
        PsychologicalState.INSTALLMENT_ANXIETY: -5,
        PsychologicalState.TRUST_DEFICIT: -30,
    }
    modifier = state_modifiers.get(psychology.primary_state, 0)
    score += modifier

    score = max(0, min(100, score))

    # Threshold mapping
    if score >= 70:
        recommendation = "FULL_LIST"
    elif score >= 45:
        recommendation = "TEASER"
    elif score >= 20:
        recommendation = "ANALYTICS_ONLY"
    else:
        recommendation = "NONE"

    return {
        "readiness_score": score,
        "recommendation": recommendation,
        "reasons": reasons,
        "state_modifier": modifier,
        "turn_count": turn_count,
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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # V2 SUPERHUMAN UPGRADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # 1. Calculate Dominant Trait (session-wide personality)
    dominant_trait = _calculate_dominant_trait(history)
    
    # 2. Calculate Emotional Momentum (warming up vs cooling down)
    emotional_momentum = _calculate_emotional_momentum(history)
    
    # 3. Detect Specific Objection Type (granular risk classification)
    specific_objection = _detect_objection_type(query, all_triggers)
    
    logger.info(f"🧠 V2 Psychology: dominant={dominant_trait}, momentum={emotional_momentum}, objection={specific_objection.value}")

    profile = PsychologyProfile(
        primary_state=primary_state,
        secondary_state=secondary_state,
        urgency_level=urgency,
        confidence_score=confidence,
        detected_triggers=all_triggers[:5],  # Limit to top 5 triggers
        recommended_tactics=tactics,
        # V2 fields
        dominant_trait=dominant_trait,
        emotional_momentum=emotional_momentum,
        specific_objection=specific_objection
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

    elif state == PsychologicalState.FAMILY_SECURITY:
        context_parts.append("""
[🏠 FAMILY SECURITY & WEALTH MODE - LIFE DECISION]
- User is buying for FAMILY. This can mean two things in Egypt:
  1. LIFESTYLE: Wants a safe compound (Sodic, Emaar). Prioritize security/amenities.
  2. LEGACY/INVESTMENT (Sakan A'eli): Wants a private building (B+G+3). Prioritize land value and building permits.
- If they ask for "سكن عائلي" outside a compound, DO NOT discard based on "Class A Developer" status.
- HIGHLIGHT: Land appreciation and "Wealth for the next generation" (بيت العيلة).
- QUALIFICATION SCRIPT:
  "'سكن عائلي' كلمة كبيرة. حضرتك بتدور على 'كمباوند' عشان الخصوصية والأمان؟ ولا 'عمارة سكن عائلي' كاستثمار وبيت للعيلة كلها؟"
- NEVER suggest new/untested developers for family buyers unless it's a "Building/Land" request.
""")

    elif state == PsychologicalState.MACRO_SKEPTIC:
        context_parts.append("""
[📉 MACRO SKEPTIC MODE - WEALTH PRESERVATION ARGUMENT]
- User fears MACRO RISKS: currency, inflation, bubble, economy.
- DO NOT sell features. Sell WEALTH PRESERVATION.
- USE "Replacement Cost" logic: "This unit costs 45k/sqm. To BUILD this same unit today costs 40k. You're buying at cost."
- USE "Inflation Killer" math: "Bank = 22%. Inflation = 13.6%. Real rates are positive but property beats it by 14.5% REAL growth."
- USE "Hedge Economy" frame: "Egyptian market became a hedge economy. Property is now a currency store."
- TRIGGER: Show Inflation vs Bank chart.
- FRAME: "سؤال ذكي. سيبك من كلام البيع. خليني أوريك الماث الحقيقي."
- VALIDATION SCRIPT:
  "حضرتك خايف من الاقتصاد؟ خليني أوريك ليه الدولار والتضخم هما السبب الحقيقي إن العقار هو الملاذ."
""")

    elif state == PsychologicalState.LEGAL_ANXIETY:
        context_parts.append("""
[⚖️ LEGAL ANXIETY MODE - THE GUARDIAN]
- User is afraid of "Urfi Contracts" and scams.
- IGNORE ROI/Price for now. Focus 100% on SAFETY.
- TRIGGER: "Law 114 Guardian" protocol.
- EXPLAIN: "Primary Contract" vs "Final Registration" (Shahra El Akari).
- OFFER: "I will not let you sign until I see the land license myself."
- SCRIPT:
  "حقك تقلق. السوق مليان عقود مضروبة. خليني أشغل 'Law 114 Guardian' على الورق قبل ما تدفع جنيه."
""")

    elif state == PsychologicalState.LIQUIDITY_SHIFT:
        context_parts.append("""
[💸 LIQUIDITY SHIFT MODE - BANK EXODUS]
- User is moving money from Bank CDs (27% expired) to Real Estate.
- COMPETITOR is NOT other developers. COMPETITOR is THE BANK (22%).
- EMPHASIZE: "Recall of Capital" + "Monthly Income".
- PRIORITIZE: Ready-to-move / Immediate Delivery units (to start rent immediately).
- SCRIPT:
  "الشهادات بتخسر قيمتها الشرائية. العقار بيزيد 30% سنوياً + 7% إيجار. دي المعادلة الوحيدة اللي بتحفظ فلوسك."
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
    # V2 Granular Strategies
    FINANCIAL_REASSURANCE = "financial_reassurance"  # Payment plan, affordability
    MARKET_ANCHORING = "market_anchoring"            # Inflation data, market proof
    LOCATION_EDUCATION = "location_education"        # Area value, development plans
    # V3 Family-Focused Strategy
    FAMILY_SAFETY_PITCH = "family_safety_pitch"      # Developer reputation, community, law 114
    # V4 Macro-Fear Counter Strategy
    REPLACEMENT_COST_PITCH = "replacement_cost_pitch"  # Construction cost logic, wealth preservation


def determine_strategy(
    psychology: PsychologyProfile,
    has_properties: bool = True,
    top_property_verdict: str = "FAIR"
) -> Dict[str, Any]:
    """
    V2: Enhanced strategy selector with granular objection handling.
    
    This is the core "Wolf" strategy selector that maps emotional
    state + specific objection to the optimal persuasion angle.
    
    Args:
        psychology: The detected psychology profile
        has_properties: Whether we have properties to show
        top_property_verdict: Best property verdict (BARGAIN/FAIR/PREMIUM)
    
    Returns:
        Strategy dict with angle and talking points
    """
    state = psychology.primary_state
    urgency = psychology.urgency_level
    objection = psychology.specific_objection  # V2: Granular objection
    momentum = psychology.emotional_momentum   # V2: Emotional trajectory
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # V2: GRANULAR OBJECTION HANDLING
    # Different responses for financial vs trust vs market concerns
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if state == PsychologicalState.RISK_AVERSE:
        # V2: Check SPECIFIC type of risk
        if objection == ObjectionType.FINANCIAL:
            strategy = Strategy.FINANCIAL_REASSURANCE
            angle = "affordability"
            talking_points = [
                "خليني أوريك خطة السداد بالتفصيل - ممكن تبدأ بمقدم 10% بس.",
                "الأقساط على 8 سنين، يعني الشهري أقل من إيجار شقة في نفس المنطقة.",
                "حاسبلك: القسط الشهري هيكون حوالي [X] جنيه. ده في حدود ميزانيتك؟",
                "فيه تمويل بنكي كمان لو محتاج - أنا بساعدك في الورق."
            ]
        elif objection == ObjectionType.LEGAL:
            strategy = Strategy.TRUST_BUILDING
            angle = "legal_protection"
            talking_points = [
                "سؤال ممتاز. ابعتلي كود الوحدة أو العقد، وأنا هشغل عليه فحص قانون 114.",
                "بتأكد من: تسلسل الملكية، رخصة البناء، وشروط التسليم.",
                "مش بنمضي حاجة غير لما الورق يطلع نضيف 100%.",
                "Law 114 Scanner بيكشف 47 نوع مشكلة قانونية - مجاناً ليك."
            ]
        elif objection == ObjectionType.TRUST:
            strategy = Strategy.TRUST_BUILDING
            angle = "developer_track_record"
            talking_points = [
                "المطور ده عنده track record: 95% تسليم في الوقت، 0 قضايا.",
                "أنا بحط سمعتي على المحك - مش هرشحلك حاجة مش مضمونة.",
                "تحب أوريك مشاريعهم اللي اتسلمت؟ عندي صور وتقييمات من سكان.",
                "ده من قايمة Class A developers - الكبار بس."
            ]
        else:
            # Default RISK_AVERSE handling
            strategy = Strategy.TRUST_BUILDING
            angle = "trust"
            talking_points = [
                "Don't sign anything yet. Send me the contract first; I'll run my Legal Scanner on it.",
                "I utilize a Law 114 Legal Scanner to detect contract loopholes.",
                "This developer has a 95% on-time delivery record. Zero legal violations.",
                "My protocol requires verification on Polygon before I recommend this.",
            ]
            
    elif objection == ObjectionType.MARKET:
        # V2: Market doubt objection (regardless of state)
        strategy = Strategy.MARKET_ANCHORING
        angle = "inflation_proof"
        talking_points = [
            "سؤال ذكي. خليني أوريك الأرقام الحقيقية.",
            "التضخم 13.6%، الشهادات 22%. يعني الكاش بيخسر قيمته، بس العقار لسه بيزيد.",
            "العقار في المنطقة دي زايد 30% السنة اللي فاتت - ده data مش رأي.",
            "تحب أوريك رسم الـ Inflation Killer؟ بيوضح الفرق بالأرقام."
        ]
        
    elif objection == ObjectionType.TIMING:
        # V2: Timing concern handling
        strategy = Strategy.SCARCITY_PITCH
        angle = "timing_urgency"
        talking_points = [
            "أفهم اللي بتقوله. بس الأرقام بتقول حاجة تانية.",
            "الأسعار زادت 20% في آخر 6 شهور. الاستنى = دفع أكتر.",
            "السيستم بتاعي بيقولي إن المطور هيرفع الأسعار الأسبوع الجاي.",
            "لو مش النهاردة، على الأقل حدد تاريخ نتكلم فيه تاني."
        ]
        
    elif objection == ObjectionType.LOCATION:
        # V2: Location concern handling
        strategy = Strategy.LOCATION_EDUCATION
        angle = "area_value"
        talking_points = [
            "خليني أفهمك المنطقة دي كويس:",
            "الخدمات: مدارس، مستشفيات، مولات - كله في 10 دقايق.",
            "خطة التطوير الجاية هتزود القيمة 15-20% خلال 3 سنين.",
            "الجيران هناك professionals و عائلات - community كويسة."
        ]
        
    elif state == PsychologicalState.GREED_DRIVEN:
        strategy = Strategy.ROI_FOCUSED
        angle = "profit"
        talking_points = [
            "This unit is an 'Inflation Killer'. It generates 2x the return of a bank deposit.",
            "Inflation is 13.6%. Bank CDs are 22%. Property beats both with 30% growth.",
            "Projected ROI is 37% (Growth + Rent). You beat Gold and the Bank.",
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
        
    elif state == PsychologicalState.SKEPTICISM:
        # V2: New SKEPTICISM state handling
        strategy = Strategy.MARKET_ANCHORING
        angle = "data_proof"
        talking_points = [
            "سؤال ممتاز. سيبك من كلام البيع وخلينا نتكلم بالأرقام.",
            "Live Market Pulse: التضخم 13.6%، البنك 22%. العقار بيعمل 30% نمو.",
            "العقار في المنطقة دي زايد [GROWTH_RATE]% - ده data مش رأي.",
            "تحب أوريك الرسم البياني؟"
        ]
        
    elif state == PsychologicalState.LEGAL_ANXIETY:
        # V3: Legal Anxiety - "Law 114 Guardian"
        strategy = Strategy.TRUST_BUILDING
        angle = "legal_guardian"
        talking_points = [
            "حقك تقلق، السوق فيه عقود كتير 'عرفي' مش بتحميك.",
            "أنا مش بس ببيعلك، أنا 'بفلتر' المخاطر ليك.",
            "أي وحدة بنرشحها لازم تكون عدت على Law 114 Check: رخصة، أرض، تسلسل ملكية.",
            "لو الورق مش سليم 100%، أنا اللي هقولك 'ماتشتريش'."
        ]

    elif state == PsychologicalState.LIQUIDITY_SHIFT:
        # V3: Bank Exodus - "Money Migration"
        strategy = Strategy.ROI_FOCUSED
        angle = "bank_comparison"
        talking_points = [
            "الشهادات كانت حل كويس زمان، بس دلوقتي الفايدة 22% والتضخم بياكلها.",
            "العقار هنا بيديك حاجتين: أصل سعره بيزيد 30% + إيجار 7% بيسدد أقساطك.",
            "دي مش بس 'شقة'، دي 'محفظة مالية' بتحميك من تآكل العملة.",
            "خلينا نركز على استلام فوري عشان نبدأ نأجر علطول ونشغل الفلوس."
        ]
        
    elif state == PsychologicalState.FAMILY_SECURITY:
        # V3: Family Home Buyer - LIFE DECISION MODE
        strategy = Strategy.FAMILY_SAFETY_PITCH
        angle = "family_safety"
        talking_points = [
            "'سكن عائلي' ده قرار حياة. قولي الأول: بتدور على أمان الكمباوند ولا استثمار في عمارة خاصة؟",
            "لو كمباوند، أنا بفلتر العروض على أساس 'الجيران' و'وسمعة المطور' قبل العائد.",
            "مشاريعنا كلها فيها سيكيوريتي 24 ساعة ومجتمعات مقفولة.",
            "المطور ده سلم 100% من مشاريعه - ده اللي يهمنا عشان العيلة.",
            "خليني أشغل Law 114 Guardian - نتأكد من الورق قبل أي خطوة."
        ]
        
    elif state == PsychologicalState.MACRO_SKEPTIC:
        # V4: Macro Fear Counter - WEALTH PRESERVATION MODE
        strategy = Strategy.REPLACEMENT_COST_PITCH
        angle = "wealth_preservation"
        talking_points = [
            "سؤال ذكي. سيبك من كلام البيع. خليني أوريك الماث الحقيقي.",
            "الوحدة دي سعرها 45 ألف/متر. عشان المطور يبنيها النهاردة تكلفته 40 ألف. يعني حضرتك بتشتري بتكلفة الإحلال.",
            "التضخم 30%. البنك 27%. يعني الكاش بيخسر 3% سنوياً. العقار زايد 14.5% REAL.",
            "السوق المصري بقى 'Hedge Economy' - العقار بقى مخزن قيمة، مش مجرد سكن.",
            "الدولار والتضخم هما السبب إن العقار هو الملاذ، مش العكس.",
            "تحب أوريك رسم الـ Inflation Killer يوضحلك بالأرقام؟"
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
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # V2: MOMENTUM-BASED ADJUSTMENTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if momentum == "cooling_down":
        # User is losing interest - need to re-engage
        talking_points.insert(0, "🔄 حاسس إنك محتاج معلومة معينة؟ قولي بالظبط اللي ناقصك.")
    elif momentum == "warming_up":
        # User is getting interested - push towards close
        talking_points.append("🎯 أنا شايف إنك مهتم - نعمل الخطوة الجاية؟")
    
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
        # V2 added fields
        "specific_objection": objection.value,
        "emotional_momentum": momentum,
    }


# Export
__all__ = [
    "PsychologicalState",
    "ObjectionType",  # V2: Granular objection classification
    "UrgencyLevel",
    "PsychologyProfile",
    "Strategy",
    "analyze_psychology",
    "semantic_classify_emotion",  # V2: LLM fallback classifier
    "determine_strategy",
    "get_psychology_context_for_prompt",
    "PSYCHOLOGY_PATTERNS",
    "OBJECTION_PATTERNS"  # V2: Objection patterns
]

