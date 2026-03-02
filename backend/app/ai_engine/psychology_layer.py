"""
Psychology Layer V3 - "The Wolf's Eye" (Chain-of-Thought Edition)
================================================================
Advanced emotional intelligence for real estate AI.

V1: Basic keyword-based state detection
V2: Dominant trait, emotional momentum, sarcasm detection, objection classification
V3 (THIS VERSION):
  - DecisionStage: Tracks where user is in the buying funnel
  - BuyerPersona: Composite personality (Investor, End-User, Speculator, First-Timer)
  - Emotional Decay: Older signals weighted less than recent ones
  - Cognitive Bias Detection: Anchoring, loss aversion, confirmation bias
  - Multi-turn Pattern Analysis: Psychology drift across conversation
  - Chain-of-Thought: Reasoning trace for every psychology decision
"""

import logging
import re
import math
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

    # V3 Egyptian Psychology Deep States
    BUYERS_REMORSE = "buyers_remorse"            # Post-decision regret / second-guessing after showing interest
    LIFE_EVENT_URGENCY = "life_event_urgency"    # Marriage, baby, job relocation — time-bound need
    EXPATRIATE_ANXIETY = "expatriate_anxiety"    # Diaspora buyer — remote trust issues, currency advantage
    SOCIAL_PRESSURE = "social_pressure"          # Peers/family bought; "everyone is buying" influence
    INHERITANCE_CONFUSION = "inheritance_confusion"  # Inherited money/property, doesn't know what to do
    DOWNGRADE_SHAME = "downgrade_shame"          # Budgetary reality forces smaller unit — ego protection needed

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# V3: DECISION STAGE — Where is the user in the buying funnel?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DecisionStage(Enum):
    """Tracks where user is in the real estate buying journey."""
    AWARENESS = "awareness"           # Just learning about market / areas
    RESEARCH = "research"             # Actively comparing areas, prices, developers
    CONSIDERATION = "consideration"   # Narrowed to 2-3 options, evaluating deeply
    DECISION = "decision"             # Ready to choose, needs final push
    ACTION = "action"                 # Wants to book/reserve/sign NOW


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# V3: BUYER PERSONA — Composite personality archetype
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class BuyerPersona(Enum):
    """Composite persona derived from combined signals."""
    INVESTOR = "investor"             # ROI-driven, comparing yields, financial literacy
    END_USER = "end_user"             # Buying to live in, family/lifestyle focused
    SPECULATOR = "speculator"         # Short-term flip, timing the market
    FIRST_TIMER = "first_timer"       # Never bought before, needs education
    UPGRADER = "upgrader"             # Has property, wants to upgrade
    PORTFOLIO_BUILDER = "portfolio"   # Already owns, adding to portfolio
    IMMEDIATE_MOVER = "immediate_mover"  # Needs to move NOW — resale/delivered priority
    UNKNOWN = "unknown"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# V3: COGNITIVE BIAS — Detected thinking patterns
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CognitiveBias(Enum):
    """Detected cognitive biases that influence decision-making."""
    ANCHORING = "anchoring"                   # Fixated on a reference price
    LOSS_AVERSION = "loss_aversion"           # More afraid of losing than eager to gain
    CONFIRMATION_BIAS = "confirmation_bias"   # Only wants info that supports existing view
    RECENCY_BIAS = "recency_bias"             # Over-weighting recent news/events
    HERD_MENTALITY = "herd_mentality"         # "Everyone is buying" influence
    STATUS_QUO_BIAS = "status_quo_bias"       # Prefers current situation over change
    NONE = "none"


@dataclass
class PsychologyThought:
    """V3: Single reasoning step in the psychology chain-of-thought."""
    observation: str     # What was observed in the user's message
    interpretation: str  # What it means psychologically
    action: str          # What the AI should do about it
    confidence: float = 0.0  # 0-1

    def to_dict(self) -> Dict:
        return {
            "observation": self.observation,
            "interpretation": self.interpretation,
            "action": self.action,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class PsychologyProfile:
    """
    V3: Advanced psychological profile with chain-of-thought reasoning.

    Upgrades from V2:
    - decision_stage: Where user is in the buying funnel
    - buyer_persona: Composite personality archetype
    - cognitive_biases: Detected thinking patterns (list)
    - thought_chain: Explicit reasoning trace for every decision
    - emotional_intensity: 0-1 how strong the emotional signal is
    - state_history: Track psychology shifts across conversation
    """
    primary_state: PsychologicalState
    secondary_state: Optional[PsychologicalState] = None
    urgency_level: UrgencyLevel = UrgencyLevel.EXPLORING
    confidence_score: float = 0.5  # 0-1
    detected_triggers: List[str] = field(default_factory=list)
    recommended_tactics: List[str] = field(default_factory=list)

    # V2 fields (preserved)
    dominant_trait: Optional[PsychologicalState] = None
    emotional_momentum: str = "static"
    specific_objection: ObjectionType = ObjectionType.NONE

    # V3 Chain-of-Thought fields
    decision_stage: DecisionStage = DecisionStage.AWARENESS
    buyer_persona: BuyerPersona = BuyerPersona.UNKNOWN
    cognitive_biases: List[CognitiveBias] = field(default_factory=list)
    thought_chain: List[PsychologyThought] = field(default_factory=list)
    emotional_intensity: float = 0.5  # 0-1: how strong the emotional signal
    state_history: List[str] = field(default_factory=list)  # Last N states for drift detection

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
            "specific_objection": self.specific_objection.value,
            # V3 fields
            "decision_stage": self.decision_stage.value,
            "buyer_persona": self.buyer_persona.value,
            "cognitive_biases": [b.value for b in self.cognitive_biases],
            "thought_chain": [t.to_dict() for t in self.thought_chain],
            "emotional_intensity": round(self.emotional_intensity, 2),
            "state_history": self.state_history,
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
            "عائد", "ربح", "استثمار", "أستثمر", "استثمر", "بستثمر", "هستثمر", "نستثمر",
            "إيجار", "هيزيد", "هيجيب كام",
            "ROI", "دخل", "مكسب", "فلوس", "تضخم", "دهب", "دولار",
            "أحسن استثمار", "هيطلع كام", "مش للسكن", "مش هسكن"
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
    },

    # ═══════════════════════════════════════════════════════════════════════
    # V3 EGYPTIAN PSYCHOLOGY DEEP STATES
    # ═══════════════════════════════════════════════════════════════════════

    # === BUYERS REMORSE: Post-Decision Regret / Second-Guessing ===
    PsychologicalState.BUYERS_REMORSE: {
        "keywords_ar": [
            "غلطت", "ندمان", "كان لازم", "بتفكر تاني", "مش متأكد دلوقتي",
            "كنت اخدت", "ياريت", "لو كنت", "عملت صح", "أرجع فيها",
            "قلبي مش مرتاح", "إحساس وحش", "مكنتش المفروض"
        ],
        "keywords_en": [
            "regret", "mistake", "should have", "second thoughts", "not sure anymore",
            "wrong decision", "wish I", "if only", "go back", "change my mind",
            "buyer's remorse", "having doubts", "reconsider"
        ],
        "signals": [
            "revisiting_previous_decision",
            "expressing_post_decision_doubt",
            "asking_to_cancel_or_change"
        ],
        "recommended_tactics": ["reaffirm_data", "show_appreciation_since_decision", "meta_trust"],
        "weight": 1.2
    },

    # === LIFE EVENT URGENCY: Marriage, Baby, Job Relocation ===
    PsychologicalState.LIFE_EVENT_URGENCY: {
        "keywords_ar": [
            "جواز", "الجواز", "عروسة", "خطوبة", "فرح", "بنتقل", "نقل شغل",
            "بيبي", "مولود", "حامل", "الأولاد كبروا", "المدرسة", "السفر",
            "رجعت مصر", "بارجع", "لازم أسكن", "الشهر الجاي", "قبل الجواز",
            "بعد الفرح", "عايز أجهز", "لازم ألحق"
        ],
        "keywords_en": [
            "getting married", "marriage", "wedding", "engaged", "fiancée",
            "baby", "pregnant", "newborn", "kids growing", "school",
            "relocating", "moving back", "new job", "transfer",
            "need to settle", "before wedding", "after wedding", "prepare"
        ],
        "signals": [
            "mentioning_life_deadline",
            "time_pressure_from_event",
            "emotional_milestone_language"
        ],
        "recommended_tactics": ["timeline_anchor", "life_milestone_framing", "ready_to_move_priority"],
        "weight": 1.5  # Very high — real urgency, not manufactured
    },

    # === EXPATRIATE ANXIETY: Diaspora Buyer / Remote Trust Issues ===
    PsychologicalState.EXPATRIATE_ANXIETY: {
        "keywords_ar": [
            "أنا بره", "في الخليج", "في السعودية", "في الإمارات", "مغترب",
            "عايز أشتري من بره", "مش في مصر", "هيبقى صعب أزور",
            "توكيل", "حد ينوب عني", "أستثمر من بره", "فلوسي بره",
            "بالدولار", "بالريال", "بالدرهم", "تحويل"
        ],
        "keywords_en": [
            "abroad", "overseas", "gulf", "saudi", "uae", "dubai", "expat",
            "buy from abroad", "not in egypt", "can't visit easily",
            "power of attorney", "proxy", "invest remotely", "savings abroad",
            "in dollars", "currency", "transfer", "diaspora"
        ],
        "signals": [
            "mentioning_location_abroad",
            "remote_purchase_concerns",
            "currency_advantage_exploration",
            "trust_from_distance"
        ],
        "recommended_tactics": ["remote_buying_guide", "legal_proxy_help", "usd_pricing_option", "video_viewing_offer"],
        "weight": 1.3
    },

    # === SOCIAL PRESSURE: Peers Bought / Family Pressure / Herd ===
    PsychologicalState.SOCIAL_PRESSURE: {
        "keywords_ar": [
            "صاحبي اشترى", "كل الناس", "زي ما الناس", "أبويا بيقول",
            "مراتي عايزة", "جوزي بيقول", "الجيران", "قرايبي",
            "كلهم اشتروا", "فاضل أنا", "الكل عمال يشتري",
            "ضغط", "بيلحوا عليا", "أهلي", "العيلة"
        ],
        "keywords_en": [
            "friend bought", "everyone is", "like others", "father says",
            "wife wants", "husband says", "neighbors", "relatives",
            "all bought", "left behind", "everyone buying",
            "pressure", "pushing me", "family", "parents"
        ],
        "signals": [
            "mentioning_peer_purchases",
            "family_influence_language",
            "herd_behavior_indicators",
            "external_pressure_cues"
        ],
        "recommended_tactics": ["validate_social_proof", "independent_decision_framing", "community_sell"],
        "weight": 1.1
    },

    # === INHERITANCE CONFUSION: Inherited Money/Property, Needs Guidance ===
    PsychologicalState.INHERITANCE_CONFUSION: {
        "keywords_ar": [
            "ورث", "ميراث", "أبويا سابلي", "ورثت", "فلوس ميراث",
            "أرض ورثتها", "شقة ورثتها", "مش عارف أعمل إيه",
            "أبيع وأشتري", "أستبدل", "عندي أرض", "عندي شقة قديمة",
            "أحسن استخدام", "فلوس حصلتلي"
        ],
        "keywords_en": [
            "inherited", "inheritance", "father left me", "got money",
            "inherited land", "inherited apartment", "don't know what to do",
            "sell and buy", "exchange", "have land", "old apartment",
            "best use", "windfall", "received money"
        ],
        "signals": [
            "mentioning_inheritance",
            "confusion_about_asset_allocation",
            "asking_about_trade_up",
            "windfall_management"
        ],
        "recommended_tactics": ["trade_up_calculator", "asset_reallocation_advisor", "wealth_preservation"],
        "weight": 1.2
    },

    # === DOWNGRADE SHAME: Budget Forces Smaller Unit — Ego Protection ===
    PsychologicalState.DOWNGRADE_SHAME: {
        "keywords_ar": [
            "مش بالميزانية", "مش قادر", "أصغر", "أقل", "مش هينفع",
            "كنت عايز فيلا", "الميزانية مش كفاية", "نزلت توقعاتي",
            "مش اللي كنت متخيله", "إزاي أقنع", "عيب", "حرام",
            "الناس هتقول إيه", "مستوى أقل"
        ],
        "keywords_en": [
            "can't afford", "smaller", "less", "won't work",
            "wanted villa", "budget not enough", "lowered expectations",
            "not what I imagined", "how to justify", "embarrassing",
            "what will people say", "downgrade", "step down"
        ],
        "signals": [
            "expressing_budget_disappointment",
            "ego_protection_language",
            "social_status_concerns",
            "downgrade_resistance"
        ],
        "recommended_tactics": ["reframe_as_smart_move", "investment_angle_for_smaller", "upgrade_path_vision"],
        "weight": 1.3  # Sensitive — ego is involved
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
            model="claude-3-5-haiku-20241022",
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# V3: DECISION STAGE DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DECISION_STAGE_SIGNALS = {
    DecisionStage.AWARENESS: {
        "keywords": ["إيه الأحسن", "what's the best", "فين أروح", "where should i", "أعرف إيه", "tell me about",
                      "إيه الفرق", "ما هي", "what is", "مش فاهم", "explain"],
        "turn_range": (0, 3),
    },
    DecisionStage.RESEARCH: {
        "keywords": ["بقارن", "comparing", "الفرق بين", "difference between", "أسعار", "prices",
                      "أحسن منطقة", "best area", "المطورين", "developers", "متوسط", "average"],
        "turn_range": (2, 8),
    },
    DecisionStage.CONSIDERATION: {
        "keywords": ["بين دول", "between these", "أختار", "choose", "مميزات", "features",
                      "عيوب", "downsides", "المقارنة", "comparison", "أقرب حاجة", "closest"],
        "turn_range": (4, 15),
    },
    DecisionStage.DECISION: {
        "keywords": ["قررت", "decided", "هختار", "i'll pick", "الأفضل", "the best one",
                      "أحسن خيار", "best option", "إيه رأيك", "what do you think", "نصيحتك"],
        "turn_range": (5, 20),
    },
    DecisionStage.ACTION: {
        "keywords": ["عايز أحجز", "want to book", "نمضي", "sign", "أدفع", "pay",
                      "خطوة جاية", "next step", "reserve", "احجزلي", "book for me"],
        "turn_range": (3, 50),
    },
}

# V3: BUYER PERSONA SIGNALS
PERSONA_SIGNALS = {
    BuyerPersona.INVESTOR: {
        "keywords_ar": [
            "عائد", "roi", "إيجار", "استثمار", "أستثمر", "استثمر", "بستثمر", "هستثمر", "نستثمر",
            "محفظة", "ربح", "كام في السنة", "yield", "مش للسكن", "مش هسكن"
        ],
        "keywords_en": ["return", "roi", "rental", "investment", "invest", "portfolio", "profit", "yield", "capital gain", "not to live"],
    },
    BuyerPersona.END_USER: {
        "keywords_ar": ["سكن", "عايلة", "أولاد", "مدارس", "أمان", "هسكن", "بيت", "قريب من"],
        "keywords_en": ["live", "family", "kids", "schools", "safety", "home", "near to", "neighborhood"],
    },
    BuyerPersona.SPECULATOR: {
        "keywords_ar": ["أبيع", "فليب", "سريع", "قبل التسليم", "أكسب", "ريسيل", "إعادة بيع"],
        "keywords_en": ["flip", "resell", "before delivery", "quick profit", "sell before", "short term"],
    },
    BuyerPersona.FIRST_TIMER: {
        "keywords_ar": ["أول مرة", "مش فاهم", "إزاي الموضوع", "أبدأ منين", "معرفش", "جديد"],
        "keywords_en": ["first time", "don't understand", "how does it work", "new to", "never bought", "beginner"],
    },
    BuyerPersona.UPGRADER: {
        "keywords_ar": ["أكبر", "أحسن من", "بدل", "upgrade", "نقل", "مكاني ضيق"],
        "keywords_en": ["bigger", "better than", "upgrade", "move from", "current apartment", "outgrown"],
    },
    BuyerPersona.PORTFOLIO_BUILDER: {
        "keywords_ar": ["عندي شقة", "شقتي", "تاني وحدة", "إضافة", "ضيف على"],
        "keywords_en": ["already own", "second unit", "add to", "my apartment", "another property"],
    },
    BuyerPersona.IMMEDIATE_MOVER: {
        "keywords_ar": [
            "استلام فوري", "تسليم فوري", "جاهز للسكن", "جاهزة", "مسلمة",
            "محتاج أنقل", "محتاج أنقل دلوقتي", "ريسيل", "resale", "مسلم",
            "بدون انتظار", "نقلة فورية", "فوراً", "الشهر ده", "مستعجل",
            "ناوي ناو", "nawy now", "متسلمة", "delivered"
        ],
        "keywords_en": [
            "move now", "ready to move", "delivered", "instant delivery", "immediate",
            "resale", "no waiting", "move in", "this month", "ASAP", "urgent move",
            "nawy now", "ready apartment", "furnished", "already built"
        ],
    },
}

# V3: COGNITIVE BIAS PATTERNS
BIAS_PATTERNS = {
    CognitiveBias.ANCHORING: {
        "signals_ar": ["كان بـ", "السعر القديم", "زمان كان", "كام كان", "السنة اللي فاتت"],
        "signals_en": ["used to be", "old price", "last year it was", "it was", "back when"],
    },
    CognitiveBias.LOSS_AVERSION: {
        "signals_ar": ["هخسر", "خسارة", "ضمان", "أفقد", "مخاطرة", "خايف أخسر"],
        "signals_en": ["lose", "loss", "guarantee", "risk", "afraid of losing", "what if it drops"],
    },
    CognitiveBias.CONFIRMATION_BIAS: {
        "signals_ar": ["أنا عارف", "بالظبط", "زي ما قلت", "ده اللي أنا فاكره", "ده يأكد"],
        "signals_en": ["i knew it", "exactly", "like i said", "confirms", "that proves", "see i told you"],
    },
    CognitiveBias.RECENCY_BIAS: {
        "signals_ar": ["امبارح", "النهاردة", "الأسبوع ده", "شفت في الأخبار", "حد قالي"],
        "signals_en": ["yesterday", "today", "this week", "saw in the news", "someone told me", "just heard"],
    },
    CognitiveBias.HERD_MENTALITY: {
        "signals_ar": ["الكل بيشتري", "صحابي", "الناس", "كلهم", "الموجة"],
        "signals_en": ["everyone is buying", "my friends", "people are", "the trend", "everybody"],
    },
    CognitiveBias.STATUS_QUO_BIAS: {
        "signals_ar": ["الفلوس في البنك", "كويس كده", "مرتاح", "مش محتاج أتحرك"],
        "signals_en": ["money in the bank", "fine as is", "comfortable", "don't need to move", "why change"],
    },
}


def _detect_decision_stage(query: str, history: List[Dict]) -> DecisionStage:
    """V3: Determine where user is in the buying funnel."""
    query_lower = query.lower()
    turn_count = len([m for m in history if m.get("role") == "user"])

    # Score each stage
    stage_scores: Dict[DecisionStage, float] = {}
    for stage, signals in DECISION_STAGE_SIGNALS.items():
        score = 0.0
        # Keyword matching
        for kw in signals["keywords"]:
            if kw in query_lower:
                score += 1.0
        # Turn range bonus (is the conversation length typical for this stage?)
        min_t, max_t = signals["turn_range"]
        if min_t <= turn_count <= max_t:
            score += 0.5
        stage_scores[stage] = score

    # Pick highest scoring stage
    best = max(stage_scores, key=stage_scores.get)
    if stage_scores[best] > 0:
        return best

    # Default based on conversation length
    if turn_count >= 8:
        return DecisionStage.CONSIDERATION
    elif turn_count >= 4:
        return DecisionStage.RESEARCH
    return DecisionStage.AWARENESS


def _detect_buyer_persona(query: str, history: List[Dict]) -> BuyerPersona:
    """V3/V4: Determine buyer persona from full conversation history.
    
    V4 FIX: Negation-aware — "مش أسكن" won't boost END_USER score.
    Also checks for explicit negation of a persona's keywords.
    """
    import re
    # Arabic negation — must be standalone words to avoid false matches inside وكمان, لأن, etc.
    _NEGATION_RE = re.compile(r'(?:^|\s)(?:مش|مو|ما|لا|بلاش|مني)\s')

    # Combine all user messages
    all_text = query.lower()
    for msg in history:
        if msg.get("role") == "user":
            all_text += " " + msg.get("content", "").lower()

    def _keyword_score(kw: str) -> float:
        """Return +1 if keyword present and NOT negated, -0.5 if negated."""
        idx = all_text.find(kw)
        if idx < 0:
            return 0.0
        # Check ~20 chars before the keyword for negation
        prefix = all_text[max(0, idx - 20):idx]
        if _NEGATION_RE.search(prefix):
            return -0.5  # Keyword is negated → penalty
        return 1.0

    # Score each persona
    scores: Dict[BuyerPersona, float] = {}
    for persona, signals in PERSONA_SIGNALS.items():
        score = 0.0
        for kw in signals.get("keywords_ar", []) + signals.get("keywords_en", []):
            score += _keyword_score(kw)
        scores[persona] = score

    best = max(scores, key=scores.get)
    if scores[best] >= 1.0:
        return best
    return BuyerPersona.UNKNOWN


def _detect_cognitive_biases(query: str, history: List[Dict]) -> List[CognitiveBias]:
    """V3: Detect cognitive biases active in the user's thinking."""
    query_lower = query.lower()
    # Also check last 3 user messages
    recent_text = query_lower
    user_msgs = [m for m in history if m.get("role") == "user"]
    for msg in user_msgs[-3:]:
        recent_text += " " + msg.get("content", "").lower()

    detected = []
    for bias, patterns in BIAS_PATTERNS.items():
        for signal in patterns.get("signals_ar", []) + patterns.get("signals_en", []):
            if signal in recent_text:
                detected.append(bias)
                break  # One match per bias is enough

    return detected if detected else [CognitiveBias.NONE]


def _calculate_emotional_intensity(state_scores: Dict, primary_score: float) -> float:
    """V3: How intense is the emotional signal? 0.0 = faint, 1.0 = overwhelming."""
    if primary_score <= 0:
        return 0.0
    # Intensity = how dominant the primary state is vs others
    all_scores = sorted(state_scores.values(), reverse=True)
    if len(all_scores) < 2 or all_scores[1] == 0:
        return min(primary_score / 2.0, 1.0)  # No competition = moderate intensity
    # Ratio of primary to second
    ratio = primary_score / max(all_scores[1], 0.1)
    return min(ratio / 3.0, 1.0)


def _build_thought_chain(
    query: str,
    primary_state: PsychologicalState,
    secondary_state: Optional[PsychologicalState],
    triggers: List[str],
    decision_stage: DecisionStage,
    persona: BuyerPersona,
    biases: List[CognitiveBias],
    momentum: str,
    confidence: float,
) -> List[PsychologyThought]:
    """V3: Build explicit chain-of-thought reasoning trace."""
    thoughts = []

    # Step 1: Emotional State Detection
    trigger_summary = ", ".join(triggers[:3]) if triggers else "no strong signals"
    thoughts.append(PsychologyThought(
        observation=f"User message contains signals: [{trigger_summary}]",
        interpretation=f"Primary emotional driver: {primary_state.value}"
                       + (f", with secondary {secondary_state.value}" if secondary_state else ""),
        action=f"Apply {primary_state.value} communication strategy",
        confidence=confidence,
    ))

    # Step 2: Decision Stage Assessment
    thoughts.append(PsychologyThought(
        observation=f"User is at {decision_stage.value} stage in buying journey",
        interpretation={
            DecisionStage.AWARENESS: "Still learning — needs education, not selling",
            DecisionStage.RESEARCH: "Actively comparing — provide data and comparisons",
            DecisionStage.CONSIDERATION: "Narrowing options — highlight differentiators",
            DecisionStage.DECISION: "About to choose — give clear recommendation",
            DecisionStage.ACTION: "Ready to act — minimize friction, provide next step",
        }.get(decision_stage, "Unknown stage"),
        action={
            DecisionStage.AWARENESS: "Lead with market education + area analysis",
            DecisionStage.RESEARCH: "Show comparison data + growth charts",
            DecisionStage.CONSIDERATION: "Focus on top 2-3 options with pros/cons",
            DecisionStage.DECISION: "Make a single clear recommendation",
            DecisionStage.ACTION: "Provide booking/payment info immediately",
        }.get(decision_stage, "Guide the conversation"),
        confidence=0.7,
    ))

    # Step 3: Persona Classification
    if persona != BuyerPersona.UNKNOWN:
        thoughts.append(PsychologyThought(
            observation=f"Buyer persona detected: {persona.value}",
            interpretation={
                BuyerPersona.INVESTOR: "ROI-focused — needs numbers, yields, growth projections",
                BuyerPersona.END_USER: "Family/lifestyle buyer — needs safety, schools, community",
                BuyerPersona.SPECULATOR: "Flip-minded — needs entry price, resale timing, demand data",
                BuyerPersona.FIRST_TIMER: "New buyer — needs education, reassurance, simple language",
                BuyerPersona.UPGRADER: "Upgrading — needs comparison to current situation",
                BuyerPersona.PORTFOLIO_BUILDER: "Portfolio play — needs diversification logic",
            }.get(persona, "Unknown persona"),
            action=f"Tailor language and data presentation for {persona.value}",
            confidence=0.65,
        ))

    # Step 4: Cognitive Bias Response
    real_biases = [b for b in biases if b != CognitiveBias.NONE]
    if real_biases:
        bias_names = ", ".join(b.value for b in real_biases)
        thoughts.append(PsychologyThought(
            observation=f"Cognitive biases detected: {bias_names}",
            interpretation={
                CognitiveBias.ANCHORING: "User is anchored to an old price — reframe with current market reality",
                CognitiveBias.LOSS_AVERSION: "Fear of loss dominates — show downside protection first",
                CognitiveBias.CONFIRMATION_BIAS: "User seeks validation — acknowledge their view, then expand",
                CognitiveBias.RECENCY_BIAS: "Over-weighting recent events — show 5-year trend perspective",
                CognitiveBias.HERD_MENTALITY: "Social proof matters — mention what other buyers are doing",
                CognitiveBias.STATUS_QUO_BIAS: "Resistance to change — show cost of inaction (inflation erosion)",
            }.get(real_biases[0], "Monitor and adapt"),
            action="Adjust messaging to address detected bias",
            confidence=0.6,
        ))

    # Step 5: Momentum-Based Adaptation
    if momentum != "static":
        thoughts.append(PsychologyThought(
            observation=f"Emotional momentum: {momentum}",
            interpretation="warming_up: User engagement increasing" if momentum == "warming_up"
                          else "cooling_down: User losing interest or becoming skeptical",
            action="Push toward close" if momentum == "warming_up"
                   else "Re-engage with new value proposition or data",
            confidence=0.55,
        ))

    return thoughts


def _calculate_scores_with_decay(query: str, history: List[Dict]) -> Tuple[Dict, Dict]:
    """
    V3: Score each psychological state with EMOTIONAL DECAY.
    Recent messages contribute more than older ones.
    Decay formula: weight = 1.0 / (1 + distance * 0.3)
    """
    state_scores: Dict[PsychologicalState, float] = {}
    detected_triggers: Dict[PsychologicalState, List[str]] = {}

    # Build weighted text corpus: most recent = highest weight
    user_msgs = [query.lower()]
    for msg in reversed(history):
        if msg.get("role") == "user":
            user_msgs.append(msg.get("content", "").lower())

    for state, patterns in PSYCHOLOGY_PATTERNS.items():
        score = 0.0
        triggers = []
        weight = patterns.get("weight", 1.0)

        for distance, text in enumerate(user_msgs):
            decay = 1.0 / (1.0 + distance * 0.3)  # decay: 1.0, 0.77, 0.63, 0.53...

            for keyword in patterns.get("keywords_ar", []):
                if keyword in text:
                    score += decay * weight
                    if distance == 0:  # Only trigger from current msg
                        triggers.append(f"ar:{keyword}")

            for keyword in patterns.get("keywords_en", []):
                if keyword in text:
                    score += decay * weight
                    if distance == 0:
                        triggers.append(f"en:{keyword}")

            # Only look at last 6 messages
            if distance >= 6:
                break

        state_scores[state] = score
        detected_triggers[state] = triggers

    return state_scores, detected_triggers


def _extract_state_history(history: List[Dict]) -> List[str]:
    """V3: Extract previous psychology states from conversation metadata."""
    states = []
    for msg in history:
        if msg.get("role") == "assistant":
            meta = msg.get("metadata", {})
            ps = meta.get("psychology_state") or meta.get("primary_state")
            if ps:
                states.append(ps)
    return states[-10:]  # Last 10 states max


def analyze_psychology(
    query: str,
    history: List[Dict],
    intent: Optional[Dict] = None
) -> PsychologyProfile:
    """
    V3: Analyze user's psychological state with chain-of-thought reasoning.

    Upgrades from V2:
    - Emotional decay (recent messages weigh more)
    - Decision stage detection (buying funnel position)
    - Buyer persona classification
    - Cognitive bias detection
    - Explicit thought chain for every decision
    - Emotional intensity measurement
    """
    query_lower = query.lower()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 1: Score states with EMOTIONAL DECAY (V3 upgrade)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    state_scores, detected_triggers = _calculate_scores_with_decay(query, history)

    # Find primary and secondary states
    sorted_states = sorted(state_scores.items(), key=lambda x: x[1], reverse=True)

    primary_state = PsychologicalState.NEUTRAL
    secondary_state = None
    confidence = 0.0
    all_triggers = []

    if sorted_states[0][1] > 0:
        primary_state = sorted_states[0][0]
        confidence = min(sorted_states[0][1] / 3.0, 1.0)
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
    tactics = list(set(tactics))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 2: Sarcasm Detection (preserved from V2)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sarcasm_triggers = ["sure you are", "yeah right", "tell me another one", "obvious", "robot", "lies", "joke", "funny", "نكتة", "بتهزر", "مصدقك", "اكيد طبعا"]
    is_sarcastic = any(x in query_lower for x in sarcasm_triggers)
    if not is_sarcastic:
        is_sarcastic = _detect_contextual_sarcasm(query, history)

    if is_sarcastic:
        primary_state = PsychologicalState.TRUST_DEFICIT
        confidence = 0.0
        tactics = ["humility", "proof_only", "acknowledge_skepticism"]
        all_triggers.append("detected_sarcasm")
        logger.info("🎭 Sarcasm Detected: Overriding state to TRUST_DEFICIT")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 3: V2 Upgrades (preserved)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    dominant_trait = _calculate_dominant_trait(history)
    emotional_momentum = _calculate_emotional_momentum(history)
    specific_objection = _detect_objection_type(query, all_triggers)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STEP 4: V3 CHAIN-OF-THOUGHT UPGRADES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    decision_stage = _detect_decision_stage(query, history)
    buyer_persona = _detect_buyer_persona(query, history)
    cognitive_biases = _detect_cognitive_biases(query, history)
    emotional_intensity = _calculate_emotional_intensity(
        state_scores, sorted_states[0][1] if sorted_states else 0
    )
    state_history = _extract_state_history(history)

    # Build the chain-of-thought reasoning trace
    thought_chain = _build_thought_chain(
        query=query,
        primary_state=primary_state,
        secondary_state=secondary_state,
        triggers=all_triggers,
        decision_stage=decision_stage,
        persona=buyer_persona,
        biases=cognitive_biases,
        momentum=emotional_momentum,
        confidence=confidence,
    )

    logger.info(
        f"🧠 V3 Psychology: state={primary_state.value} (conf:{confidence:.2f}), "
        f"stage={decision_stage.value}, persona={persona_name(buyer_persona)}, "
        f"biases={[b.value for b in cognitive_biases]}, intensity={emotional_intensity:.2f}, "
        f"thoughts={len(thought_chain)}"
    )

    profile = PsychologyProfile(
        primary_state=primary_state,
        secondary_state=secondary_state,
        urgency_level=urgency,
        confidence_score=confidence,
        detected_triggers=all_triggers[:5],
        recommended_tactics=tactics,
        # V2 fields
        dominant_trait=dominant_trait,
        emotional_momentum=emotional_momentum,
        specific_objection=specific_objection,
        # V3 fields
        decision_stage=decision_stage,
        buyer_persona=buyer_persona,
        cognitive_biases=cognitive_biases,
        thought_chain=thought_chain,
        emotional_intensity=emotional_intensity,
        state_history=state_history,
    )

    return profile


def persona_name(p: BuyerPersona) -> str:
    """Short display name for logging."""
    return p.value if p else "unknown"


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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # V3: CHAIN-OF-THOUGHT REASONING INJECTION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if hasattr(profile, 'thought_chain') and profile.thought_chain:
        cot_lines = ["\n[PSYCHOLOGY_REASONING_CHAIN]"]
        for i, thought in enumerate(profile.thought_chain, 1):
            cot_lines.append(
                f"Step {i}: {thought.observation} → {thought.interpretation} → ACTION: {thought.action}"
            )
        context_parts.append("\n".join(cot_lines))

    # V3: Decision Stage Context
    if hasattr(profile, 'decision_stage'):
        stage = profile.decision_stage
        context_parts.append(f"\n[DECISION_STAGE: {stage.value.upper()}]")
        if stage == DecisionStage.AWARENESS:
            context_parts.append("- EDUCATE first. Show market overview + growth charts. Do NOT push properties yet.")
        elif stage == DecisionStage.RESEARCH:
            context_parts.append("- COMPARE and ANALYZE. Show data, charts, area comparisons. Growth chart is MANDATORY.")
        elif stage == DecisionStage.CONSIDERATION:
            context_parts.append("- NARROW DOWN. Focus on top 2-3 options. Show clear pros/cons.")
        elif stage == DecisionStage.DECISION:
            context_parts.append("- RECOMMEND ONE. Make a clear, confident recommendation. Show why it's the best.")
        elif stage == DecisionStage.ACTION:
            context_parts.append("- CLOSE NOW. Provide booking steps, payment info. Minimize new information.")

    # V3: Buyer Persona Context
    if hasattr(profile, 'buyer_persona') and profile.buyer_persona != BuyerPersona.UNKNOWN:
        context_parts.append(f"\n[BUYER_PERSONA: {profile.buyer_persona.value.upper()}]")

    # V3: Cognitive Bias Counter-Strategy
    if hasattr(profile, 'cognitive_biases'):
        real_biases = [b for b in profile.cognitive_biases if b != CognitiveBias.NONE]
        if real_biases:
            context_parts.append(f"\n[COGNITIVE_BIAS_DETECTED: {', '.join(b.value for b in real_biases)}]")
            for bias in real_biases:
                if bias == CognitiveBias.ANCHORING:
                    context_parts.append("- Counter anchoring: Show 5-year price chart to reframe reference point")
                elif bias == CognitiveBias.LOSS_AVERSION:
                    context_parts.append("- Counter loss aversion: Emphasize inflation erosion of cash — inaction IS the loss")
                elif bias == CognitiveBias.RECENCY_BIAS:
                    context_parts.append("- Counter recency bias: Show long-term 5-year growth trajectory, not just recent moves")
                elif bias == CognitiveBias.STATUS_QUO_BIAS:
                    context_parts.append("- Counter status quo: Calculate cost of waiting — each month delay = X EGP lost to inflation")

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

    # ═════════════════════════════════════════════════════════════════
    # V3: NEW EGYPTIAN PSYCHOLOGY DEEP STATES
    # ═════════════════════════════════════════════════════════════════

    elif state == PsychologicalState.BUYERS_REMORSE:
        strategy = Strategy.TRUST_BUILDING
        angle = "reaffirmation"
        talking_points = [
            "أنا فاهم الإحساس ده — بس خليني أوريك الأرقام من يوم ما قررت.",
            "الوحدة اللي اخترتها زادت [X]% من وقتها. القرار كان صح بالداتا.",
            "الشك بعد القرار طبيعي جداً — بس الندم الحقيقي هو إنك متشتريش في سوق صاعد.",
            "لو عايز reassurance، خليني أعملك Updated ROI Report يطمنك."
        ]

    elif state == PsychologicalState.LIFE_EVENT_URGENCY:
        strategy = Strategy.CLOSE_FAST
        angle = "life_milestone"
        talking_points = [
            "ألف مبروك! ده وقت مهم — وأنا هنا أخلي القرار سهل عليك.",
            "بما إن عندك timeline، خليني أركز على وحدات جاهزة أو قريبة التسليم.",
            "الوقت مهم — خليني أوريك أفضل 3 options تقدر تتحرك فيهم فوراً.",
            "خلينا نحجز دلوقتي ونأمّن السعر قبل ما يتغير."
        ]

    elif state == PsychologicalState.EXPATRIATE_ANXIETY:
        strategy = Strategy.TRUST_BUILDING
        angle = "remote_guidance"
        talking_points = [
            "أهلاً! أنا فاهم إنك بره — خليني أطمنك: عملنا ده مع مغتربين كتير.",
            "زيارة الوحدة ممكن تتعمل Virtual أو عن طريق وكيل موثوق.",
            "تقدر تعمل توكيل رسمي ونخلص كل حاجة وإنت مكانك.",
            "الحلو إن فلوسك بالدولار/الريال — قوتك الشرائية أكبر من اللي في مصر."
        ]

    elif state == PsychologicalState.SOCIAL_PRESSURE:
        strategy = Strategy.CONSULTATIVE
        angle = "independent_smart_decision"
        talking_points = [
            "إن الناس حواليك اشتروا ده مؤشر كويس — بس المهم تشتري اللي يناسبك أنت.",
            "خليني أعملك تحليل مستقل — ننسى اللي اشتراه حد تاني، ونركز على أهدافك أنت.",
            "الحقيقة إن اللي اشتروا في المنطقة دي حققوا [X]% عائد — وأنت تقدر أكتر.",
            "القرار الذكي مش إنك تعمل زي الناس — بل تعمل أحسن بالداتا."
        ]

    elif state == PsychologicalState.INHERITANCE_CONFUSION:
        strategy = Strategy.CONSULTATIVE
        angle = "asset_advisor"
        talking_points = [
            "الله يرحم — حضرتك عندك فرصة تحول الأصل ده لاستثمار يكبر.",
            "خليني أعملك Trade-Up Analysis: أبيع القديم وأشتري إيه بالمبلغ ده؟",
            "المبلغ ده لو فضل كاش هيخسر [X]% سنوياً. لو اتحول عقار هيكسب [Y]%.",
            "أنا هنا أرتبلك خطة — مش بس أبيعلك شقة."
        ]

    elif state == PsychologicalState.DOWNGRADE_SHAME:
        strategy = Strategy.CONSULTATIVE
        angle = "smart_investor_reframe"
        talking_points = [
            "الحدود عندك مش نهاية — ده بداية ذكية. أنجح المستثمرين بدأوا بشقة صغيرة.",
            "الوحدة الأصغر دي ممكن تأجرها وتجمع لـ upgrade خلال 3-5 سنين.",
            "في عالم العقارات: Smart Entry > Big Entry. المهم تدخل السوق.",
            "خليني أوريك خطة الـ Trade-Up: تبدأ هنا والطريق لحلمك واضح."
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


# ═══════════════════════════════════════════════════════════════════════
# V4: OBJECTION RESOLUTION TRACKER
# Tracks objections raised, resolution attempts, and outcomes
# ═══════════════════════════════════════════════════════════════════════

class ObjectionResolutionTracker:
    """
    Tracks every objection across the conversation lifecycle.
    
    For each objection type, records:
    - When it was raised (turn number)
    - Resolution attempts made
    - Whether it was resolved
    - Effective resolution tactic
    
    This enables AMR to:
    1. Never repeat a failed tactic
    2. Escalate unresolved objections
    3. Know when to pivot vs. push
    """

    def __init__(self):
        self._objections: Dict[str, Dict] = {}
        # Maps: objection_type -> {raised_turn, attempts, resolved, effective_tactic}

    def raise_objection(self, objection_type: str, turn: int, trigger_text: str = ""):
        """Register a new objection or re-raise an existing one."""
        if objection_type not in self._objections:
            self._objections[objection_type] = {
                "raised_turn": turn,
                "trigger_text": trigger_text[:100],
                "attempts": [],
                "resolved": False,
                "effective_tactic": None,
                "re_raised_count": 0,
            }
        else:
            # Re-raised: user brought it up again
            self._objections[objection_type]["re_raised_count"] += 1

    def record_resolution_attempt(self, objection_type: str, tactic: str, turn: int):
        """Record an attempt to resolve an objection."""
        if objection_type in self._objections:
            self._objections[objection_type]["attempts"].append({
                "tactic": tactic,
                "turn": turn,
            })

    def resolve_objection(self, objection_type: str, tactic: str = ""):
        """Mark an objection as resolved."""
        if objection_type in self._objections:
            self._objections[objection_type]["resolved"] = True
            self._objections[objection_type]["effective_tactic"] = tactic

    def get_unresolved(self) -> List[str]:
        """Get list of unresolved objection types."""
        return [k for k, v in self._objections.items() if not v["resolved"]]

    def get_failed_tactics(self, objection_type: str) -> List[str]:
        """Get tactics already tried (and failed) for an objection."""
        obj = self._objections.get(objection_type, {})
        if obj.get("resolved"):
            return []
        return [a["tactic"] for a in obj.get("attempts", [])]

    def should_escalate(self, objection_type: str) -> bool:
        """Check if an objection needs escalation (3+ failed attempts or re-raised 2+ times)."""
        obj = self._objections.get(objection_type)
        if not obj:
            return False
        return (len(obj.get("attempts", [])) >= 3 or obj.get("re_raised_count", 0) >= 2)

    def get_prompt_context(self, language: str = "ar") -> str:
        """Generate objection resolution context for Claude prompt injection."""
        if not self._objections:
            return ""

        lines = ["\n[OBJECTION_RESOLUTION_TRACKER]"]
        for obj_type, data in self._objections.items():
            status = "✅ RESOLVED" if data["resolved"] else "❌ UNRESOLVED"
            attempts_count = len(data.get("attempts", []))
            re_raised = data.get("re_raised_count", 0)

            lines.append(f"- {obj_type}: {status} ({attempts_count} attempts, re-raised {re_raised}x)")

            if not data["resolved"]:
                failed = self.get_failed_tactics(obj_type)
                if failed:
                    lines.append(f"  ⚠️ FAILED tactics: {', '.join(failed)} — DO NOT repeat these")
                if self.should_escalate(obj_type):
                    if language == "ar":
                        lines.append(f"  🔴 ESCALATE: هذا الاعتراض محتاج تدخل مباشر. اعترف بالقلق وقدم حل ملموس.")
                    else:
                        lines.append(f"  🔴 ESCALATE: This objection needs direct intervention. Acknowledge and offer concrete solution.")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return dict(self._objections)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ObjectionResolutionTracker':
        tracker = cls()
        if data:
            tracker._objections = data
        return tracker


# Export
__all__ = [
    "PsychologicalState",
    "ObjectionType",
    "UrgencyLevel",
    "PsychologyProfile",
    "Strategy",
    "analyze_psychology",
    "semantic_classify_emotion",
    "determine_strategy",
    "get_psychology_context_for_prompt",
    "PSYCHOLOGY_PATTERNS",
    "OBJECTION_PATTERNS",
    # V3 exports
    "DecisionStage",
    "BuyerPersona",
    "CognitiveBias",
    "PsychologyThought",
    # V4 exports
    "ObjectionResolutionTracker",
    "calculate_card_readiness",
]

