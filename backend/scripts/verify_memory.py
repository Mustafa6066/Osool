"""
Standalone verification for ConversationMemory implementation.
Tests the memory extraction and context summary functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai_engine.conversation_memory import ConversationMemory


def test_memory_extraction():
    """Test that ConversationMemory correctly extracts facts from messages."""
    print("=" * 60)
    print("CONVERSATION MEMORY VERIFICATION")
    print("=" * 60)
    
    memory = ConversationMemory()
    
    # Simulate a conversation
    messages = [
        "مرحبا، اسمي أحمد",
        "I'm looking for a property in New Cairo",
        "My budget is around 5 million",
        "I want it for living with my family",
        "Show me some options",
        "What about properties in Sheikh Zayed?",
        "That one looks expensive, is there anything cheaper?",
        "I need to buy soon, maybe next month",
    ]
    
    print("\n📥 Processing messages...")
    for i, msg in enumerate(messages, 1):
        memory.extract_from_message(msg)
        print(f"  [{i}] {msg[:50]}...")
    
    print("\n" + "=" * 60)
    print("📊 EXTRACTED MEMORY CONTEXT:")
    print("=" * 60)
    context = memory.get_context_summary()
    print(context)
    
    # Verify extraction
    print("\n" + "=" * 60)
    print("✅ VERIFICATION RESULTS:")
    print("=" * 60)
    
    checks = {
        "Budget extracted": memory.budget_range is not None,
        "Areas extracted": len(memory.preferred_areas) > 0,
        "Purpose extracted": memory.investment_vs_living is not None,
        "Objections captured": len(memory.objections_raised) > 0,
        "Timeline extracted": memory.timeline is not None,
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check}")
        if not passed:
            all_passed = False
    
    # Print extracted values
    print("\n📋 Extracted Values:")
    print(f"  Budget: {memory.budget_range}")
    print(f"  Areas: {memory.preferred_areas}")
    print(f"  Purpose: {memory.investment_vs_living}")
    print(f"  Objections: {memory.objections_raised}")
    print(f"  Timeline: {memory.timeline}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL MEMORY TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED - Review ConversationMemory implementation")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = test_memory_extraction()
    sys.exit(0 if success else 1)
