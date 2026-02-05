
import asyncio
import os
import json
import random
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock

# Set mock env vars
os.environ["OPENAI_API_KEY"] = "sk-mock-key"
os.environ["ANTHROPIC_API_KEY"] = "sk-mock-key"
os.environ["ENABLE_REASONING_LOOP"] = "true"

# Mock dependencies
sys_modules = {
    "app.ai_engine.psychology_layer": MagicMock(),
    "app.ai_engine.proactive_alerts": MagicMock(),
    "app.ai_engine.conversation_memory": MagicMock(),
    "app.ai_engine.analytical_actions": MagicMock(),
    "app.services.vector_search": MagicMock(),
    "app.services.market_statistics": MagicMock(),
    "app.database": MagicMock(),
    "app.ai_engine.xgboost_predictor": MagicMock(),
}

import sys
for name, mock in sys_modules.items():
    sys.modules[name] = mock

# Mock specific functions
sys.modules["app.ai_engine.psychology_layer"].analyze_psychology = MagicMock(return_value=MagicMock(primary_state=MagicMock(value="neutral"), urgency_level=MagicMock(value="medium")))
sys.modules["app.ai_engine.psychology_layer"].get_psychology_context_for_prompt = MagicMock(return_value="")
sys.modules["app.ai_engine.xgboost_predictor"].xgboost_predictor.detect_la2ta = MagicMock(return_value=[])
sys.modules["app.services.vector_search"].search_properties = AsyncMock(return_value=[{"id": 1, "title": "Test Villa", "price": 5000000, "location": "New Cairo"}])

# Import target modules
from app.ai_engine.customer_profiles import extract_user_facts, UserProfile, profile_to_context_string
from app.ai_engine.amr_master_prompt import get_master_system_prompt
# We need to monkeypatch hybrid_brain to use our mocks before importing
from app.ai_engine.hybrid_brain import OsoolHybridBrain

async def test_elephant_memory():
    print("\n🐘 TEST 1: Elephant Memory Extraction")
    
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "name": "Ahmed Test",
        "hard_constraints": ["Budget 5M"],
        "purpose": "investment"
    })))]
    mock_client.chat.completions.create.return_value = mock_response
    
    current_profile = {}
    history = [
        {"role": "user", "content": "I am Ahmed, looking for investment with 5M budget"}
    ]
    
    updated = await extract_user_facts(current_profile, history, mock_client)
    
    print(f"Input History: {history[0]['content']}")
    print(f"Updated Profile: {json.dumps(updated, indent=2, ensure_ascii=False)}")
    
    assert updated["name"] == "Ahmed Test"
    assert "Budget 5M" in updated["hard_constraints"]
    print("✅ Elephant Memory extraction successful")

async def test_context_injection():
    print("\n💉 TEST 2: Context Injection")
    
    profile_data = {
        "name": "Mona",
        "wolf_status": "Warm Prospect",
        "budget_extracted": 10000000,
        "purpose": "living",
        "preferred_locations": ["Zayed"],
        "hard_constraints": ["Must have garden"]
    }
    
    prompt = get_master_system_prompt(user_profile_data=profile_data)
    
    print("Checking prompt for injected data...")
    assert "Mona" in prompt
    assert "10.0 مليون جنيه" in prompt
    assert "Zayed" in prompt
    assert "Must have garden" in prompt
    
    print("✅ Context Injection successful - Dossier found in prompt")

async def test_chain_of_thought():
    print("\n💭 TEST 3: Chain of Thought Flow")
    
    brain = OsoolHybridBrain()
    
    # Mock internal methods to isolate CoT
    brain._analyze_intent = AsyncMock(return_value={"action": "search", "filters": {}})
    brain._apply_screening_gate = MagicMock(return_value=None)  # CRITICAL: Return None to pass gate
    brain._detect_impossible_request = MagicMock(return_value=None)
    brain._search_database = AsyncMock(return_value=[{"id": 1, "price": 5000000}])
    brain._apply_wolf_analytics = MagicMock(return_value=[{"id": 1, "price": 5000000, "wolf_score": 85}])
    brain._determine_strategy = MagicMock(return_value="consultant")
    brain._generate_wolf_narrative = AsyncMock(return_value="Response generated")
    brain._deep_analysis = AsyncMock(return_value=None)
    brain._determine_ui_actions = MagicMock(return_value=[])
    
    # Mock CoT generation
    brain.openai_async.chat.completions.create = AsyncMock()
    brain.openai_async.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="OBSERVATION: User wants villa\nSTRATEGY: Pivot to townhouse"))
    ]
    
    # Mock Elephant Memory
    # using side_effect to mock the imported function in hybrid_brain
    # NOTE: In a real run, we'd rely on the actual import, but here we can't easily mock module-level imports inside the function
    # So we'll trust the flow if _generate_reasoning_trace is called
    
    result = await brain.process_turn(
        query="I want a villa",
        history=[],
        profile={"name": "Test User"}
    )
    
    print(f"Reasoning Trace: {result['reasoning_trace']}")
    assert "OBSERVATION" in result['reasoning_trace']
    print("✅ Chain of Thought trace generated and returned")
    
    assert "updated_profile" in result
    print("✅ Updated profile passed through")

async def main():
    try:
        await test_elephant_memory()
        await test_context_injection()
        await test_chain_of_thought()
        print("\n✨ ALL TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
