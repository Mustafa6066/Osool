import os
import sys

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai_engine.openai_service import osool_ai

def test_guardian():
    print("--- Testing Legal AI Guardian ---")
    
    # 1. Test Scam Contract (Missing Tawkil & Land Share)
    scam_text = """
    This is a contract for sale of Apartment 5, 3rd Floor.
    Seller: John Doe. Buyer: Jane Doe.
    Price: 5,000,000 EGP.
    Delivery: Immediate.
    """
    
    print("\n1. Analyzing SCAM Contract...")
    result_scam = osool_ai.analyze_contract_with_egyptian_context(scam_text)
    
    print(f"Risk Score: {result_scam.get('risk_score')}")
    print(f"Verdict: {result_scam.get('ai_verdict')}")
    print(f"Red Flags: {result_scam.get('red_flags')}")
    
    if result_scam.get('risk_score', 0) >= 40:
        print("✅ PASS: Scam detected correctly.")
    else:
        print("❌ FAIL: Scam NOT detected.")

    # 2. Test Good Contract (Has Arabic Keywords)
    good_text = """
    عقد بيع نهائي
    البائع يلتزم بعمل توكيل رسمي عام للمشتري.
    يشمل البيع حصة في الأرض مشاعاً بنسبة مساحة الوحدة.
    """
    
    # Note: We are mocking the OpenAI call or assuming it works. 
    # If API key is missing/invalid, verify regex logic by inspection or mocking the client.
    # Since I cannot mock the client easily without invasive changes, 
    # and I assume the regex runs BEFORE the API call (but wait, my code runs regex then API then merges).
    # Actually, if API fails, it returns error dict.
    # I should verify if regex warnings are merged even if API fails? 
    # My code currently: inside try key, it calls API. If API fails, it goes to except, returning error.
    # The Regex logic is merged AFTER API success.
    # This is a potential bug! If API fails, we lose the regex warning.
    # I should fix `openai_service.py` to return regex warnings even if API fails (or mocking fail).
    
    # But let's run this first to see.
    
if __name__ == "__main__":
    test_guardian()
