import asyncio
from app.ai_engine.claude_sales_agent import claude_sales_agent

async def test_chat():
    print("🤖 Simulating User Query: 'عايز شقه في التجمع' ...\n")
    
    user_query = "عايز شقه في التجمع"
    
    print("⏳ Calling chat_with_context...")
    try:
        result = await asyncio.wait_for(
            claude_sales_agent.chat_with_context(
                user_input=user_query,
                session_id="test_session_1",
                chat_history=[], # New conversation
                user=None,
                language="ar"
            ),
            timeout=60
        )
    except asyncio.TimeoutError:
        print("❌ Timeout reached!")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
        
    print("✅ Response Received!")
    
    print("--- AI Response ---")
    print(result.get("response"))
    print("\n--- UI Actions ---")
    print(result.get("ui_actions"))
    print("\n--- Properties ---")
    print(result.get("properties"))

if __name__ == "__main__":
    asyncio.run(test_chat())
