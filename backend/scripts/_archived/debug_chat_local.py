
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add app directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

async def test_chat_agent():
    print("----------- DIAGNOSTIC START -----------")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"PYTHONPATH: {sys.path}")
    
    print("\n[1] Checking Environment Variables...")
    required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DATABASE_URL"]
    for var in required_vars:
        val = os.getenv(var)
        print(f"  {var}: {'[OK] Present' if val else '[MISSING] PLEASE SET THIS'}")

    print("\n[2] Attempting Imports...")
    try:
        print("  Importing sales_agent (deps check)...")
        from app.ai_engine import sales_agent
        print("  [OK] sales_agent imported successfully")
    except Exception as e:
        print(f"  [FAIL] FAILED to import sales_agent: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        print("  Importing claude_sales_agent...")
        from app.ai_engine.claude_sales_agent import claude_sales_agent
        print("  [OK] claude_sales_agent imported successfully")
    except Exception as e:
        print(f"  [FAIL] FAILED to import claude_sales_agent: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n[3] Testing Chat Agent Initialization...")
    try:
        if not claude_sales_agent:
             print("  [FAIL] claude_sales_agent is None!")
        else:
             print("  [OK] claude_sales_agent initialized")
             print(f"  Model: {claude_sales_agent.model}")
    except Exception as e:
        print(f"  [FAIL] Error accessing agent: {e}")

    print("\n----------- DIAGNOSTIC END -----------")

if __name__ == "__main__":
    asyncio.run(test_chat_agent())
