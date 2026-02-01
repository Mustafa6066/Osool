import sys
import os
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_superhuman_capabilities():
    print("\n🚀 STARTING SUPERHUMAN VERIFICATION 🚀\n")
    
    try:
        from app.ai_engine.hybrid_brain import OsoolHybridBrain
        from app.ai_engine.psychology_layer import analyze_psychology, PsychologicalState
        from app.ai_engine.amr_master_prompt import get_master_system_prompt
        
        brain = OsoolHybridBrain()
        
        # --- TEST 1: VELVET ROPE (Screening) ---
        print("🔹 Test 1: Velvet Rope (Screening Gate)")
        # Case A: Vague Request -> Should Intercept
        intent_vague = {"action": "search", "filters": {}, "raw_query": "how much is a villa?"}
        history = []
        result = brain._apply_screening_gate(intent_vague, history, "en")
        
        if result and "Before I quote" in result:
             print("✅ PASS: Vague request intercepted.")
        else:
             print(f"❌ FAIL: Vague request allowed. Result: {result}")
             
        # Case B: Qualified Request -> Should Pass
        intent_qual = {"action": "search", "filters": {"budget_max": 5000000}, "raw_query": "villa under 5M"}
        result_qual = brain._apply_screening_gate(intent_qual, history, "en")
        if result_qual is None:
             print("✅ PASS: Qualified request allowed.")
        else:
             print(f"❌ FAIL: Qualified request intercepted. Result: {result_qual}")

        # --- TEST 2: SARCASM DETECTION ---
        print("\n🔹 Test 2: Sarcasm Detection")
        # Case: "Great price" for expensive item
        query_sarcastic = "Yeah, 50 million is a great price"
        match_history = [{"role": "assistant", "content": "The villa is 50,000,000 EGP."}]
        # Mock intent
        intent_sarcastic = {"action": "search", "filters": {}}
        
        psych = analyze_psychology(query_sarcastic, match_history, intent_sarcastic)
        # Note: Depending on implementation, it might trigger TRUST_DEFICIT or SARCASM specific state
        # The code I added sets is_sarcastic=True but maps to TRUST_DEFICIT or specific handling
        
        # Checking logic in psychology_layer:
        # if is_sarcastic -> returns PsychologicalState.TRUST_DEFICIT
        if psych.primary_state == PsychologicalState.TRUST_DEFICIT:
             print(f"✅ PASS: Sarcasm detected as {psych.primary_state.name}")
        else:
             print(f"❌ FAIL: Sarcasm missed. Got {psych.primary_state.name}")

        # --- TEST 3: A/B TESTING HOOKS ---
        print("\n🔹 Test 3: A/B Testing Hooks")
        # Test Variant A
        prompt_a = get_master_system_prompt(closing_hook_variant="assumptive")
        if "Assumptive Close" in prompt_a:
             print("✅ PASS: Assumptive Hook injected")
        else:
             print("❌ FAIL: Assumptive Hook missing")

        # Test Variant B
        prompt_b = get_master_system_prompt(closing_hook_variant="fear_of_loss")
        if "Fear Of Loss" in prompt_b:
             print("✅ PASS: Fear of Loss Hook injected")
        else:
             print("❌ FAIL: Fear of Loss Hook missing")
             
        # --- TEST 4: IMPOSSIBLE REQUEST PIVOT ---
        print("\n🔹 Test 4: Impossible Request Pivot")
        # Luxury area + Low budget
        impossible_intent = {
            "action": "search", 
            "filters": {"location": "Sheikh Zayed", "budget_max": 1000000}
        }
        pivot = brain._detect_impossible_request(impossible_intent, "villa in zayed under 1 million")
        
        if pivot and pivot["type"] == "reality_check":
             print("✅ PASS: Impossible request detected")
        else:
             print(f"❌ FAIL: Impossible request missed. Result: {pivot}")

    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_superhuman_capabilities())
