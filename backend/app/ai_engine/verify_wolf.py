
import asyncio
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ai_engine.wolf_orchestrator import wolf_brain
from app.ai_engine.lead_scoring import score_lead

async def verify_wolf():
    print("🐺 STARTING WOLF VERIFICATION 🐺")
    print("=================================")

    # Test 1: Velvet Rope (Low Score Gating)
    print("\n[TEST 1] Velvet Rope Gating (Cold Lead)")
    cold_history = [] # Empty history = low score
    cold_query = "Find me a villa in Zayed" # Direct request without building value
    
    response = await wolf_brain.process_turn(cold_query, cold_history)
    print(f"Query: {cold_query}")
    print(f"Response: {response['response'][:100]}...")
    
    if "عشان أكون صريح معاك" in response['response'] or "To filter out" in response['response']:
        print("✅ PASS: Velvet Rope triggered (blocked low score).")
    elif response.get('model_used') == 'wolf_gatekeeper':
        print("✅ PASS: Wolf Gatekeeper model used.")
    else:
        print("❌ FAIL: Velvet Rope NOT triggered.")
        print(f"Got model: {response.get('model_used')}")

    # Test 2: The Loop (Human Handoff)
    print("\n[TEST 2] Loop Detection (Human Handoff)")
    loop_history = [
        {"role": "user", "content": "What is the ROI?"},
        {"role": "assistant", "content": "The ROI is 20%."},
        {"role": "user", "content": "What is the ROI?"}, # Duplicate
        {"role": "assistant", "content": "As I said, 20%."},
    ]
    loop_query = "What is the ROI?" # 3rd time
    
    # We test lead scoring directly first as orchestrator might clear history
    score = score_lead(loop_history + [{"role": "user", "content": loop_query}], {})
    if "loop_detected" in score['signals']:
        print("✅ PASS: Lead Scoring detected loop.")
    else:
        print("❌ FAIL: Lead Scoring missed loop.")

    # Simulating Orchestrator Loop
    response_loop = await wolf_brain.process_turn(loop_query, loop_history)
    if response_loop.get('handoff') or "#URGENT" in response_loop.get('response', ''):
        print("✅ PASS: Orchestrator triggered Handoff.")
    else:
        print("❌ FAIL: Orchestrator did not trigger Handoff.")

    # Test 3: Universal Response Protocol (Prompt Check)
    print("\n[TEST 3] Universal Response Protocol Context")
    # We can't easily check the prompt sent to Claude without mocking, 
    # but we can check if the system prompt loaded correctly.
    from app.ai_engine.amr_master_prompt import AMR_SYSTEM_PROMPT
    if "PROTOCOL 6" in AMR_SYSTEM_PROMPT:
         print("✅ PASS: Protocol 6 is in System Prompt.")
    else:
         print(f"❌ FAIL: Protocol 6 missing from System Prompt. Found: {AMR_SYSTEM_PROMPT[:100]}...")

    if "PART 1: THE FLEX" in AMR_SYSTEM_PROMPT:
         print("✅ PASS: Protocol Parts (Flex/Context/Audit) present.")
    else:
         print("❌ FAIL: Protocol Parts missing.")

if __name__ == "__main__":
    asyncio.run(verify_wolf())
