import asyncio
import os
import sys
from typing import Dict, List
import logging

# Add project root to path
sys.path.append("d:\\Osool\\backend")
os.environ["OPENAI_API_KEY"] = "sk-dummy-key" # Mock key for tests
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-dummy-key" # Mock key for tests

# Mock the database and external services to avoid async session issues in simple script
from unittest.mock import MagicMock, AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_simulation():
    print("🐺 STARTING WOLF BRAIN SIMULATION...")
    
    # Mocking dependencies
    with patch('app.ai_engine.wolf_orchestrator.AsyncSessionLocal') as mock_db, \
         patch('app.ai_engine.wolf_orchestrator.db_search_properties', new_callable=AsyncMock) as mock_search, \
         patch('app.ai_engine.wolf_orchestrator.AsyncAnthropic') as mock_anthropic, \
         patch('app.ai_engine.wolf_orchestrator.AsyncOpenAI') as mock_openai:
        
        # Setup mocks
        mock_search.return_value = [
            {"price": 5000000, "size_sqm": 100, "location": "New Cairo", "developer": "Sodic", "type": "Apartment"}
        ]
        
        # Mock Claude response
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="[MOCKED NARRATIVE]")]
        mock_anthropic_instance = mock_anthropic.return_value
        mock_anthropic_instance.messages.create = AsyncMock(return_value=mock_msg)

        # Mock OpenAI response (for perception/intent)
        mock_openai_instance = mock_openai.return_value
        # tailored for perception layer mocks if we were testing it deeply, but we can rely on real perception if env vars are set,
        # OR better, let's mock the perception layer directly to control the test inputs without burning tokens.
        
        from app.ai_engine.wolf_orchestrator import WolfBrain
        from app.ai_engine.perception_layer import Intent
        from app.ai_engine.psychology_layer import PsychologyProfile, PsychologicalState
        
        wolf = WolfBrain()
        
        # ==================================================================================
        # SCENARIO 1: THE CHEAP USER (Gatekeeper Test)
        # ==================================================================================
        print("\n🧪 SCENARIO 1: The Cheap User (Low Score + Asking Price)")
        
        # Mocking modules for specific behavior
        with patch('app.ai_engine.wolf_orchestrator.score_lead') as mock_score, \
             patch('app.ai_engine.wolf_orchestrator.perception_layer.analyze') as mock_intent:
            
            mock_score.return_value = {"score": 10, "temperature": "COLD"} # Low Score
            mock_intent.return_value = AsyncMock(action="price_check", filters={"location": "New Cairo"}, language="ar")
            mock_intent.return_value.to_dict.return_value = {} # simple mock
            mock_intent.return_value.action = "price_check"
            mock_intent.return_value.filters = {"location": "New Cairo"}

            # Act
            result = await wolf.process_turn(
                query="بكام الشقق في التجمع؟", 
                history=[], 
                profile={"first_name": "Ghost"}
            )
            
            # Assert
            if result.get("strategy", {}).get("strategy") == "benchmarking_gate":
                print("✅ PASS: Correctly triggered 'benchmarking_gate' for low score user.")
                print(f"   Response Preview: {result['response'][:100]}...")
            else:
                print(f"❌ FAIL: Expected 'benchmarking_gate', got {result.get('strategy')}")

        # ==================================================================================
        # SCENARIO 2: THE SKEPTIC (Trust Deficit Test)
        # ==================================================================================
        print("\n🧪 SCENARIO 2: The Skeptic (Trust Deficit)")
        
        with patch('app.ai_engine.wolf_orchestrator.score_lead') as mock_score, \
             patch('app.ai_engine.wolf_orchestrator.analyze_psychology') as mock_psych:
            
            mock_score.return_value = {"score": 50, "temperature": "WARM"}
            mock_psych.return_value = PsychologyProfile(primary_state=PsychologicalState.TRUST_DEFICIT)

            # Act
            result = await wolf.process_turn(
                query="أنا قلقان من العقود واللعب ده", 
                history=[], 
                profile={"first_name": "Skeptic"}
            )
            
            # Assert
            ui_actions = [a['type'] for a in result.get("ui_actions", [])]
            if "upload_contract_trigger" in ui_actions:
                print("✅ PASS: Correctly triggered 'upload_contract_trigger'.")
            else:
                print(f"❌ FAIL: Expected 'upload_contract_trigger', got {ui_actions}")

        # ==================================================================================
        # SCENARIO 3: THE NEGOTIATOR (Price Defense Test)
        # ==================================================================================
        print("\n🧪 SCENARIO 3: The Negotiator (No Discount Protocol)")
        
        with patch('app.ai_engine.wolf_orchestrator.score_lead') as mock_score, \
             patch('app.ai_engine.wolf_orchestrator.perception_layer.analyze') as mock_intent, \
             patch('app.ai_engine.wolf_orchestrator.WolfBrain._generate_wolf_narrative', new_callable=AsyncMock) as mock_generate, \
             patch('app.ai_engine.wolf_orchestrator.WolfBrain._is_discovery_complete', return_value=True):
            
            mock_score.return_value = {"score": 80, "temperature": "HOT"}
            mock_intent.return_value.action = "search"
            mock_intent.return_value.filters = {"location": "New Cairo"}
            
            # Act
            await wolf.process_turn(
                query="ممكن خصم شوية عشان نخلص؟", 
                history=[{"role":"assistant", "content":"..."}], 
                profile={"first_name": "Buyer"}
            )
            
            # Assert
            # Check if _generate_wolf_narrative was called with no_discount_mode=True
            call_args = mock_generate.call_args
            if call_args and call_args.kwargs.get('no_discount_mode') is True:
                print("✅ PASS: Correctly called generator with 'no_discount_mode=True'.")
            else:
                print(f"❌ FAIL: 'no_discount_mode' was not True in call args: {call_args.kwargs if call_args else 'No call'}")

if __name__ == "__main__":
    asyncio.run(run_simulation())
