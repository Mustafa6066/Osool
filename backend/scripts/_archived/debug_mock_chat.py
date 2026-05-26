
import sys
import os
import asyncio
from unittest.mock import MagicMock

# Mock dependencies before import
sys.modules["redis"] = MagicMock()
sys.modules["openai"] = MagicMock()
sys.modules["anthropic"] = MagicMock()
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.agents"] = MagicMock()
sys.modules["langchain_openai"] = MagicMock()
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()
sys.modules["langchain_core.prompts"] = MagicMock()
sys.modules["langchain_core.tools"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_community.vectorstores"] = MagicMock()
sys.modules["supabase"] = MagicMock()

# Mock specific attributes
sys.modules["langchain_openai"].ChatOpenAI = MagicMock()
sys.modules["langchain_openai"].OpenAIEmbeddings = MagicMock()
sys.modules["langchain_core.prompts"].ChatPromptTemplate = MagicMock()
sys.modules["langchain_core.messages"].SystemMessage = MagicMock()
sys.modules["langchain_core.messages"].HumanMessage = MagicMock()
sys.modules["langchain_core.messages"].AIMessage = MagicMock()

# Add app directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_chat_logic():
    print("----------- MOCK TEST START -----------")
    try:
        from app.ai_engine.claude_sales_agent import claude_sales_agent
        print("✅ Imported claude_sales_agent")

        print("Testing chat execution...")
        # Mock dependencies inside the instance
        claude_sales_agent.analytics = MagicMock()
        
        # We expect this to fail or succeed, but we want to catch the specific error
        response = await claude_sales_agent.chat("Hello test", "session_123")
        print(f"✅ Response: {response}")

    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_logic())
