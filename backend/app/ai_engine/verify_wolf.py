"""
Verify Wolf - Hypered Brain Protocol Tests
-------------------------------------------
Comprehensive verification of all Hypered Brain protocols:
1. Velvet Rope (Cold Lead Gating)
2. Price Integrity (No Discount)
3. Confidence Protocol (Law 114 Offer)
4. Price Sandwich (Benchmarking)
5. Wolf Checklist (Quality Gate)
"""

import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ai_engine.wolf_orchestrator import wolf_brain
from app.ai_engine.lead_scoring import score_lead
from app.ai_engine.amr_master_prompt import (
    AMR_SYSTEM_PROMPT, 
    is_discount_request,
    FRAME_CONTROL_EXAMPLES,
    NEGOTIATION_KEYWORDS
)
from app.ai_engine.wolf_checklist import validate_checklist, WolfChecklistResult


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result with emoji."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   └─ {details}")


async def verify_hypered_brain():
    """Full verification of Hypered Brain protocols."""
    print("\n" + "="*60)
    print("🐺 HYPERED BRAIN VERIFICATION - V7")
    print("="*60 + "\n")
    
    all_passed = True
    
    # =========================================================================
    # TEST 1: Velvet Rope Protocol (Cold Lead Gating)
    # =========================================================================
    print("\n[TEST 1] Velvet Rope Protocol (Cold Lead Gating)")
    print("-" * 50)
    
    try:
        cold_query = "Find me a villa in Zayed"
        cold_history = []  # Empty history = cold lead
        
        response = await wolf_brain.process_turn(
            cold_query, 
            cold_history, 
            session_id="test_velvet_rope"
        )
        
        response_text = response.get('response', '').lower()
        model_used = response.get('model_used', '')
        
        # Check for screening behavior
        screening_keywords = ["rental", "capital", "resale", "investment", "استثمار", "إيجار"]
        has_screening = any(kw in response_text for kw in screening_keywords)
        is_gatekeeper = model_used in ['wolf_gatekeeper', 'wolf_educator']
        
        passed = has_screening or is_gatekeeper
        all_passed = all_passed and passed
        print_result(
            "Velvet Rope triggered",
            passed,
            f"Model: {model_used}, Screening keywords found: {has_screening}"
        )
    except Exception as e:
        print_result("Velvet Rope triggered", False, f"Error: {e}")
        all_passed = False
    
    # =========================================================================
    # TEST 2: Price Integrity Protocol (No Discount)
    # =========================================================================
    print("\n[TEST 2] Price Integrity Protocol (No Discount)")
    print("-" * 50)
    
    # Test the is_discount_request function
    discount_queries = [
        "Can I get a discount?",
        "What's the best price?",
        "كام أحسن سعر؟",
        "ممكن خصم؟",
        "negotiate the price"
    ]
    
    all_detected = True
    for query in discount_queries:
        detected = is_discount_request(query)
        all_detected = all_detected and detected
        print_result(f"Detected discount request: '{query[:30]}...'", detected)
    
    # Test non-discount queries don't trigger
    non_discount_queries = [
        "What's the price?",
        "How much is this villa?",
        "كام سعر الشقة؟"
    ]
    
    for query in non_discount_queries:
        detected = is_discount_request(query)
        passed = not detected  # Should NOT be detected
        all_detected = all_detected and passed
        print_result(f"Non-discount query NOT triggering: '{query[:30]}...'", passed)
    
    all_passed = all_passed and all_detected
    
    # =========================================================================
    # TEST 3: Confidence Protocol (Trust Deficit → Law 114 Offer)
    # =========================================================================
    print("\n[TEST 3] Confidence Protocol (Law 114 Offer)")
    print("-" * 50)
    
    try:
        skeptic_query = "I don't trust developers. They're all scammers."
        skeptic_history = []
        
        response = await wolf_brain.process_turn(
            skeptic_query,
            skeptic_history,
            session_id="test_confidence"
        )
        
        response_text = response.get('response', '').lower()
        strategy = response.get('strategy', {}).get('strategy', '')
        
        # Check for Law 114 offer
        trust_keywords = ["law 114", "contract", "scanner", "audit", "عقد"]
        has_trust_offer = any(kw in response_text for kw in trust_keywords)
        is_confidence_strategy = strategy == 'confidence_building'
        
        passed = has_trust_offer or is_confidence_strategy
        all_passed = all_passed and passed
        print_result(
            "Law 114 Scanner offered",
            passed,
            f"Strategy: {strategy}, Trust keywords found: {has_trust_offer}"
        )
    except Exception as e:
        print_result("Law 114 Scanner offered", False, f"Error: {e}")
        all_passed = False
    
    # =========================================================================
    # TEST 4: AMR System Prompt Contains All Protocols
    # =========================================================================
    print("\n[TEST 4] AMR System Prompt Verification")
    print("-" * 50)
    
    required_sections = [
        ("NO DISCOUNTS", "RULE 1: NO DISCOUNTS"),
        ("DATA FIRST", "RULE 2: DATA FIRST"),
        ("CONTROL THE FRAME", "RULE 3: CONTROL THE FRAME"),
        ("PRICE SANDWICH", "RULE 4: THE ANALYST'S RULE"),
        ("VELVET ROPE", "PROTOCOL 1: THE VELVET ROPE"),
        ("PRICE INTEGRITY", "PROTOCOL 2: PRICE INTEGRITY"),
        ("CONFIDENCE CHECK", "PROTOCOL 3: THE CONFIDENCE CHECK"),
        ("WOLF CHECKLIST", "PROTOCOL 4: THE WOLF CHECKLIST"),
        ("CONSULT, DON'T SELL", "THE GOLDEN RULE")
    ]
    
    for name, search_term in required_sections:
        found = search_term.lower() in AMR_SYSTEM_PROMPT.lower()
        all_passed = all_passed and found
        print_result(f"{name} in prompt", found)
    
    # =========================================================================
    # TEST 5: Wolf Checklist Validation
    # =========================================================================
    print("\n[TEST 5] Wolf Checklist Validation")
    print("-" * 50)
    
    # Test a good response
    good_response = (
        "Market average in New Cairo is 65,000 EGP/sqm. "
        "This unit is 58,000 EGP/sqm - you're saving 12% vs market. "
        "Book a viewing now to secure this price."
    )
    good_context = {"budget_known": True, "intent_known": True, "discount_requested": False}
    good_history = [{"role": "user", "content": "I want to invest in rental"}]
    
    result = validate_checklist(good_response, good_context, good_history)
    
    print_result("Good response passes checklist", result.passed)
    print(f"   └─ Screened: {result.screened}, Benchmarked: {result.benchmarked}, "
          f"Defended: {result.defended}, Closed: {result.closed}")
    all_passed = all_passed and result.passed
    
    # Test a bad response (no benchmark, no CTA)
    bad_response = "This is a nice villa in a beautiful location."
    bad_context = {"budget_known": False, "intent_known": False, "discount_requested": False}
    bad_history = []
    
    bad_result = validate_checklist(bad_response, bad_context, bad_history)
    
    # Bad response should fail
    passed = not bad_result.passed
    print_result("Bad response fails checklist", passed)
    print(f"   └─ Screened: {bad_result.screened}, Benchmarked: {bad_result.benchmarked}, "
          f"Defended: {bad_result.defended}, Closed: {bad_result.closed}")
    all_passed = all_passed and passed
    
    # =========================================================================
    # TEST 6: Frame Control Examples Exist
    # =========================================================================
    print("\n[TEST 6] Frame Control Examples")
    print("-" * 50)
    
    required_frames = ["cheap_villa", "discount_request", "unqualified_price_ask", "trust_deficit"]
    
    for frame in required_frames:
        exists = frame in FRAME_CONTROL_EXAMPLES
        all_passed = all_passed and exists
        
        if exists:
            has_ar = "response_ar" in FRAME_CONTROL_EXAMPLES[frame]
            print_result(f"Frame '{frame}' exists with Arabic", has_ar)
        else:
            print_result(f"Frame '{frame}' exists", False)
    
    # =========================================================================
    # TEST 7: Loop Detection (Human Handoff)
    # =========================================================================
    print("\n[TEST 7] Loop Detection (Human Handoff)")
    print("-" * 50)
    
    loop_history = [
        {"role": "user", "content": "What is the ROI?"},
        {"role": "assistant", "content": "The ROI is 20%."},
        {"role": "user", "content": "What is the ROI?"},
        {"role": "assistant", "content": "As I said, 20%."},
    ]
    loop_query = "What is the ROI?"  # 3rd time
    
    # Test lead scoring directly
    score = score_lead(
        loop_history + [{"role": "user", "content": loop_query}], 
        {"session_start_time": None}
    )
    
    loop_detected = "loop_detected" in score.get('signals', [])
    all_passed = all_passed and loop_detected
    print_result("Lead Scoring detected loop", loop_detected, f"Signals: {score.get('signals', [])}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Hypered Brain V7 is operational!")
    else:
        print("⚠️  SOME TESTS FAILED - Review the results above.")
    print("="*60 + "\n")
    
    return all_passed


async def quick_test():
    """Quick test of key components without full orchestrator."""
    print("\n🔬 Quick Component Tests")
    print("-" * 50)
    
    # Test is_discount_request
    assert is_discount_request("give me a discount") == True
    assert is_discount_request("what's the price") == False
    print("✅ is_discount_request() working")
    
    # Test Wolf Checklist
    result = validate_checklist(
        "Market average is 60k. This is 55k. Book now!", 
        {"budget_known": True}, 
        []
    )
    assert result.benchmarked == True
    assert result.closed == True
    print("✅ validate_checklist() working")
    
    print("\n✅ Quick tests passed!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    else:
        asyncio.run(verify_hypered_brain())
