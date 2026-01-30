"""
Wolf Checklist - Internal Validation Before Every Response
-----------------------------------------------------------
The AI must pass all 4 checks before responding:
1. Did I SCREEN? (budget/intent known)
2. Did I BENCHMARK? (price vs market comparison)
3. Did I DEFEND? (refused discount if asked)
4. Did I CLOSE? (specific Call to Action)

This module ensures the Wolf persona is consistently maintained.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


# ==============================================================================
# CHECKLIST RESULT
# ==============================================================================

@dataclass
class WolfChecklistResult:
    """Result of the Wolf Checklist validation."""
    screened: bool = False
    benchmarked: bool = False
    defended: bool = True  # Default True if no discount was asked
    closed: bool = False
    
    # Details for debugging
    screening_reason: str = ""
    benchmark_reason: str = ""
    defense_reason: str = ""
    close_reason: str = ""
    
    @property
    def passed(self) -> bool:
        """Overall pass requires screening and closing at minimum."""
        return self.screened and self.closed
    
    @property
    def score(self) -> int:
        """Score out of 4."""
        return sum([self.screened, self.benchmarked, self.defended, self.closed])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/JSON."""
        return {
            "screened": self.screened,
            "benchmarked": self.benchmarked,
            "defended": self.defended,
            "closed": self.closed,
            "passed": self.passed,
            "score": f"{self.score}/4",
            "details": {
                "screening": self.screening_reason,
                "benchmark": self.benchmark_reason,
                "defense": self.defense_reason,
                "close": self.close_reason
            }
        }


# ==============================================================================
# DETECTION PATTERNS
# ==============================================================================

# Screening keywords (we know intent/budget)
SCREENING_INTENT_KEYWORDS = [
    # English
    "rental", "rent", "investment", "resale", "capital appreciation",
    "live", "living", "family", "personal use",
    # Arabic
    "إيجار", "استثمار", "سكن", "عايز أسكن", "للسكن", "للاستثمار"
]

SCREENING_BUDGET_KEYWORDS = [
    # English
    "budget", "afford", "million", "payment plan", "down payment",
    # Arabic
    "ميزانية", "مليون", "دفعة", "قسط", "مقدم"
]

SCREENING_QUESTIONS = [
    # English
    "are you buying for", "what is your budget", "rental income or capital",
    "purpose", "goal",
    # Arabic
    "للإيجار ولا", "هدفك", "ميزانيتك"
]

# Benchmark keywords (price compared to market)
BENCHMARK_KEYWORDS = [
    # English
    "market average", "per sqm", "per meter", "compared to",
    "benchmark", "area average", "below market", "above market",
    "saving", "equity", "undervalued", "premium",
    # Arabic
    "متوسط السوق", "للمتر", "مقارنة", "تحت السوق", "فوق السوق",
    "توفير", "سعر المتر"
]

# Defense keywords (price defended, no discount)
DISCOUNT_REFUSAL_KEYWORDS = [
    # English
    "replacement cost", "can't lower", "payment plan instead",
    "not negotiable", "price is fixed", "developer price",
    # Arabic
    "تكلفة الإنشاء", "مش هينفع أقل", "خطة السداد"
]

# CTA keywords (call to action)
CTA_KEYWORDS = [
    # English
    "book", "reserve", "schedule", "visit", "viewing",
    "contact", "call", "let's", "secure", "lock in",
    "send me", "share", "upload", "next step",
    # Arabic
    "احجز", "زور", "معاينة", "اتصل", "ابعت", "كلمني",
    "الخطوة الجاية", "خلينا"
]


# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

def _check_screened(response: str, context: Dict, history: List[Dict]) -> tuple[bool, str]:
    """
    Check if screening happened (budget/intent known or being asked).
    
    Returns:
        (passed, reason)
    """
    response_lower = response.lower()
    
    # Check if context already has screening info
    if context.get("budget_known") or context.get("intent_known"):
        return True, "Context already has budget/intent"
    
    # Check if response contains screening question
    for question in SCREENING_QUESTIONS:
        if question in response_lower:
            return True, f"Asked screening question: '{question}'"
    
    # Check if user already provided intent in history
    for msg in history:
        if msg.get("role") == "user":
            content = msg.get("content", "").lower()
            for keyword in SCREENING_INTENT_KEYWORDS:
                if keyword in content:
                    return True, f"User previously mentioned intent: '{keyword}'"
            for keyword in SCREENING_BUDGET_KEYWORDS:
                if keyword in content:
                    return True, f"User previously mentioned budget: '{keyword}'"
    
    return False, "No screening question asked and no prior budget/intent"


def _check_benchmarked(response: str, context: Dict) -> tuple[bool, str]:
    """
    Check if price was compared to market benchmark.
    
    Returns:
        (passed, reason)
    """
    response_lower = response.lower()
    
    # Check if response contains benchmark comparison
    for keyword in BENCHMARK_KEYWORDS:
        if keyword in response_lower:
            return True, f"Contains benchmark: '{keyword}'"
    
    # Check if showing property without benchmark (only applies if price mentioned)
    price_patterns = [r"\d+,?\d*\s*(egp|جنيه|k)", r"\d+\s*million"]
    for pattern in price_patterns:
        if re.search(pattern, response_lower):
            # Price is mentioned but no benchmark
            return False, "Price mentioned without market comparison"
    
    # No price mentioned, benchmark not required
    return True, "No price mentioned, benchmark N/A"


def _check_defended(response: str, context: Dict) -> tuple[bool, str]:
    """
    Check if discount was refused (only if discount was requested).
    
    Returns:
        (passed, reason)
    """
    response_lower = response.lower()
    
    # Check if discount was requested
    if not context.get("discount_requested", False):
        return True, "No discount requested, defense N/A"
    
    # Check if response contains discount refusal
    for keyword in DISCOUNT_REFUSAL_KEYWORDS:
        if keyword in response_lower:
            return True, f"Discount refused with: '{keyword}'"
    
    # Check if discount was offered (FAIL)
    discount_offer_patterns = [
        r"i can offer.*discount",
        r"special price",
        r"manager approval",
        r"\d+%\s*off",
        r"خصم",
        r"عرض خاص"
    ]
    for pattern in discount_offer_patterns:
        if re.search(pattern, response_lower):
            return False, "Discount was offered (VIOLATION)"
    
    # Payment plan redirect is acceptable
    if "payment plan" in response_lower or "خطة السداد" in response_lower:
        return True, "Pivoted to payment plan improvement"
    
    return False, "Discount requested but not properly refused"


def _check_closed(response: str, context: Dict) -> tuple[bool, str]:
    """
    Check if response ends with a specific call to action.
    
    Returns:
        (passed, reason)
    """
    response_lower = response.lower()
    
    # Check if response contains CTA
    for keyword in CTA_KEYWORDS:
        if keyword in response_lower:
            return True, f"Contains CTA: '{keyword}'"
    
    # Check for question as CTA (acceptable)
    questions = ["?", "؟"]
    for q in questions:
        if q in response:
            return True, "Ends with question (engaging user)"
    
    return False, "No call to action found"


# ==============================================================================
# MAIN VALIDATION FUNCTION
# ==============================================================================

def validate_checklist(
    response: str,
    context: Dict,
    history: List[Dict]
) -> WolfChecklistResult:
    """
    Validate response against Wolf Checklist.
    
    Args:
        response: The AI's drafted response
        context: Current conversation context with keys:
            - budget_known: bool
            - intent_known: bool
            - discount_requested: bool
            - current_property: dict (optional)
        history: Conversation history (list of {role, content} dicts)
    
    Returns:
        WolfChecklistResult with pass/fail for each check
    """
    result = WolfChecklistResult()
    
    # 1. SCREENED
    result.screened, result.screening_reason = _check_screened(response, context, history)
    
    # 2. BENCHMARKED
    result.benchmarked, result.benchmark_reason = _check_benchmarked(response, context)
    
    # 3. DEFENDED
    result.defended, result.defense_reason = _check_defended(response, context)
    
    # 4. CLOSED
    result.closed, result.close_reason = _check_closed(response, context)
    
    # Log result
    logger.info(f"Wolf Checklist: {result.score}/4 - {result.to_dict()}")
    
    return result


def format_checklist_for_debug(result: WolfChecklistResult) -> str:
    """Format checklist result for debug logging."""
    checks = [
        f"[{'✅' if result.screened else '❌'}] SCREEN: {result.screening_reason}",
        f"[{'✅' if result.benchmarked else '❌'}] BENCHMARK: {result.benchmark_reason}",
        f"[{'✅' if result.defended else '❌'}] DEFEND: {result.defense_reason}",
        f"[{'✅' if result.closed else '❌'}] CLOSE: {result.close_reason}",
    ]
    return "\n".join(checks)


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "WolfChecklistResult",
    "validate_checklist",
    "format_checklist_for_debug"
]
