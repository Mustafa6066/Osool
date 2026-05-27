#!/usr/bin/env python3
"""Quick test: verify the 5 production bugs are fixed."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test 1: _extract_purpose with negation
print("=" * 60)
print("TEST 1: _extract_purpose with Arabic negation")
print("=" * 60)

from app.ai_engine.conversation_memory import ConversationMemory

mem = ConversationMemory()
# "I want to invest, not to live"
test_msg = "عايز أستثمر مش أسكن"
mem._extract_purpose(test_msg.lower())
print(f'  Input: "{test_msg}"')
print(f'  Result: investment_vs_living = "{mem.investment_vs_living}"')
assert mem.investment_vs_living == 'investment', f"FAIL: Expected 'investment', got '{mem.investment_vs_living}'"
print("  ✅ PASS")

# Test 1b: Pure living intent still works
mem2 = ConversationMemory()
test_msg2 = "عايز أسكن في التجمع مع العيلة"
mem2._extract_purpose(test_msg2.lower())
print(f'\n  Input: "{test_msg2}"')
print(f'  Result: investment_vs_living = "{mem2.investment_vs_living}"')
assert mem2.investment_vs_living == 'living', f"FAIL: Expected 'living', got '{mem2.investment_vs_living}'"
print("  ✅ PASS")

# Test 1c: Both (no negation)
mem3 = ConversationMemory()
test_msg3 = "عايز أستثمر وكمان أسكن"
mem3._extract_purpose(test_msg3.lower())
print(f'\n  Input: "{test_msg3}"')
print(f'  Result: investment_vs_living = "{mem3.investment_vs_living}"')
assert mem3.investment_vs_living == 'both', f"FAIL: Expected 'both', got '{mem3.investment_vs_living}'"
print("  ✅ PASS")

# Test 2: GPT purpose override
print("\n" + "=" * 60)
print("TEST 2: GPT purpose field used from ai_analysis")
print("=" * 60)

mem4 = ConversationMemory()
mem4.extract_from_message("عايز أستثمر مش أسكن", ai_analysis={
    'filters': {'location': 'New Cairo', 'purpose': 'investment'}
})
print(f'  Result: investment_vs_living = "{mem4.investment_vs_living}"')
assert mem4.investment_vs_living == 'investment', f"FAIL: Expected 'investment', got '{mem4.investment_vs_living}'"
print("  ✅ PASS")

# Test 3: Memory merge allows correction
print("\n" + "=" * 60)
print("TEST 3: Memory merge allows purpose correction")
print("=" * 60)

mem_old = ConversationMemory()
mem_old.investment_vs_living = 'living'  # Wrong initial value
mem_new = ConversationMemory()
mem_new.investment_vs_living = 'investment'  # Corrected value
mem_old.merge(mem_new)
print(f'  Old had "living", new has "investment"')
print(f'  After merge: "{mem_old.investment_vs_living}"')
assert mem_old.investment_vs_living == 'investment', f"FAIL: Expected 'investment', got '{mem_old.investment_vs_living}'"
print("  ✅ PASS")

# Test 4: Buyer persona detection with negation
print("\n" + "=" * 60)
print("TEST 4: Buyer persona detection (negation-aware)")
print("=" * 60)

from app.ai_engine.psychology_layer import _detect_buyer_persona, BuyerPersona

persona = _detect_buyer_persona("عايز أستثمر مش أسكن", [])
print(f'  Input: "عايز أستثمر مش أسكن"')
print(f'  Result: persona = {persona.value}')
assert persona == BuyerPersona.INVESTOR, f"FAIL: Expected 'investor', got '{persona.value}'"
print("  ✅ PASS")

# Test 4b: Pure end_user still works
persona2 = _detect_buyer_persona("عايز أسكن مع العيلة والأولاد", [])
print(f'\n  Input: "عايز أسكن مع العيلة والأولاد"')
print(f'  Result: persona = {persona2.value}')
assert persona2 == BuyerPersona.END_USER, f"FAIL: Expected 'end_user', got '{persona2.value}'"
print("  ✅ PASS")

# Test 5: Lead scoring with Arabic keywords
print("\n" + "=" * 60)
print("TEST 5: Lead scoring works with Arabic text")
print("=" * 60)

from app.ai_engine.lead_scoring import score_lead

result = score_lead(
    conversation_history=[
        {"role": "user", "content": "عايز شقة في التجمع بميزانية 5 مليون"},
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "عايز أستثمر مش أسكن، محتاج أسمع عن الأقساط"},
    ],
    session_metadata={"properties_viewed": 0, "tools_used": []},
)
print(f'  Score: {result["score"]}')
print(f'  Temperature: {result["temperature"]}')
print(f'  Signals: {result["signals"]}')
assert result["score"] > 0, f"FAIL: Score should be > 0 but is {result['score']}"
print("  ✅ PASS (score > 0 for Arabic conversation)")

# Test 5b: Loop trap requires 3+ exact repeats, not 2
result2 = score_lead(
    conversation_history=[
        {"role": "user", "content": "عايز شقة"},
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "عايز شقة"},
        {"role": "assistant", "content": "..."},
    ],
    session_metadata={"properties_viewed": 0, "tools_used": []},
)
print(f'\n  Loop trap test (2 repeats): score={result2["score"]}, action={result2.get("recommended_action", "none")}')
assert result2.get("recommended_action") != "ESCALATE_IMMEDIATELY", "FAIL: 2 repeats should NOT trigger escalation"
print("  ✅ PASS (2 repeats don't trigger loop trap)")

print("\n" + "=" * 60)
print("✅ ALL 5 BUG FIXES VERIFIED SUCCESSFULLY")
print("=" * 60)
