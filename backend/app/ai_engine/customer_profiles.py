"""
Customer Segmentation System for Osool AI Sales Agent
------------------------------------------------------
Classifies customers into segments and provides persona-specific strategies.

Segments:
- Luxury Investor: High-net-worth individuals (>10M EGP budget)
- First-Time Buyer: New to real estate (<3M EGP budget)
- Savvy Investor: Experienced investors focused on ROI

Phase 3: AI Personality Enhancement
Phase 4: ELEPHANT MEMORY - Long-term user fact tracking
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import re
import json



class CustomerSegment(Enum):
    """Customer classification based on behavior and budget."""
    LUXURY_INVESTOR = "luxury"
    FIRST_TIME_BUYER = "first_time"
    SAVVY_INVESTOR = "savvy"
    UNKNOWN = "unknown"  # Default until classified


def classify_customer(
    budget: Optional[int],
    conversation_history: List[Dict],
    user_profile: Optional[Dict] = None
) -> CustomerSegment:
    """
    Classify customer based on multiple signals.

    Args:
        budget: User's stated budget in EGP (None if not mentioned yet)
        conversation_history: List of message dicts with 'role' and 'content'
        user_profile: Optional dict with user info (properties_owned, etc.)

    Returns:
        CustomerSegment enum value

    Classification Logic:
    1. Budget Threshold (Primary Signal):
       - >10M EGP = Luxury Investor
       - <3M EGP = First-Time Buyer
       - 3-10M EGP = Default to Savvy Investor

    2. Keyword Analysis (Secondary Signal):
       - "first property", "never bought" → First-Time Buyer
       - "portfolio", "rental yield", "ROI" → Savvy Investor
       - "exclusive", "premium", "bespoke" → Luxury Investor

    3. User Profile (Tertiary Signal):
       - properties_owned = 0 → First-Time Buyer
       - properties_owned >= 3 → Savvy Investor
    """

    # Combine all messages into searchable text
    # Defensive: ensure each message is a dict before calling .get()
    full_conversation = " ".join([
        msg.get("content", "") for msg in conversation_history
        if isinstance(msg, dict) and msg.get("role") == "user"
    ]).lower()

    # === PRIMARY SIGNAL: Budget Threshold ===
    if budget is not None:
        if budget > 10_000_000:
            return CustomerSegment.LUXURY_INVESTOR
        elif budget < 3_000_000:
            # Check if they're actually first-time or just budget-conscious
            if any(keyword in full_conversation for keyword in [
                "first property", "first time", "never bought", "new to real estate"
            ]):
                return CustomerSegment.FIRST_TIME_BUYER
            # Budget-conscious savvy investor
            return CustomerSegment.SAVVY_INVESTOR
        else:
            # 3-10M range: Check secondary signals
            pass  # Continue to secondary signals

    # === SECONDARY SIGNAL: Keyword Analysis ===
    first_time_keywords = [
        "first property", "first time", "never bought",
        "new to real estate", "how does buying work",
        "what documents do i need", "scared", "nervous",
        "don't understand", "explain to me"
    ]

    savvy_keywords = [
        "portfolio", "rental yield", "roi", "cap rate",
        "appreciation", "resale value", "market trends",
        "investment", "cash flow", "multiple properties",
        "property manager"
    ]

    luxury_keywords = [
        "exclusive", "premium", "bespoke", "luxury",
        "high-end", "elite", "vip", "concierge",
        "penthouses", "golf course", "marina",
        "new capital", "north coast"
    ]

    first_time_score = sum(1 for kw in first_time_keywords if kw in full_conversation)
    savvy_score = sum(1 for kw in savvy_keywords if kw in full_conversation)
    luxury_score = sum(1 for kw in luxury_keywords if kw in full_conversation)

    # If clear winner
    if first_time_score >= 2:
        return CustomerSegment.FIRST_TIME_BUYER
    if savvy_score >= 3:
        return CustomerSegment.SAVVY_INVESTOR
    if luxury_score >= 2:
        return CustomerSegment.LUXURY_INVESTOR

    # === TERTIARY SIGNAL: User Profile ===
    if user_profile:
        properties_owned = user_profile.get("properties_owned", 0)
        if properties_owned == 0:
            return CustomerSegment.FIRST_TIME_BUYER
        elif properties_owned >= 3:
            return CustomerSegment.SAVVY_INVESTOR

    # === DEFAULT: Unknown (needs more discovery) ===
    return CustomerSegment.UNKNOWN


# Persona configurations for each segment
SEGMENT_PERSONAS: Dict[CustomerSegment, Dict] = {
    CustomerSegment.LUXURY_INVESTOR: {
        "tone": "Ultra-professional, concierge-style, sophisticated",
        "language_style": "Formal, polished, use 'Ya Fandim' respectfully",
        "focus": [
            "Exclusivity and prestige",
            "Capital appreciation potential",
            "Premium compounds (New Capital, North Coast, Palm Hills)",
            "Privacy and security features",
            "Concierge services and amenities"
        ],
        "greeting": "Welcome. I'm Amr, your dedicated real estate consultant at Osool. I specialize in Egypt's most exclusive properties.",
        "value_proposition": "Access to off-market luxury units + blockchain-verified ownership + white-glove service",
        "urgency_style": "Subtle scarcity (limited units in tier-1 compounds)",
        "objection_handling": "Acknowledge concerns, emphasize value over price",
        "typical_questions": [
            "Show me penthouses in New Capital",
            "What's the best compound for privacy?",
            "I want something exclusive"
        ]
    },

    CustomerSegment.FIRST_TIME_BUYER: {
        "tone": "Educational, supportive, patient, reassuring",
        "language_style": "Simple, clear, avoid jargon, explain everything",
        "focus": [
            "Step-by-step guidance through buying process",
            "Payment plans and affordability",
            "Legal safety and FRA compliance",
            "Delivery guarantees and developer reputation",
            "Community facilities (schools, hospitals)"
        ],
        "greeting": "Welcome to Osool! I'm Amr, and I'm here to guide you through your first property purchase. No question is too small.",
        "value_proposition": "Legal protection + payment plan calculator + AI contract scanner + hand-holding support",
        "urgency_style": "Price increase warnings, developer promotions ending soon",
        "objection_handling": "Address fears first, build confidence, offer educational resources",
        "typical_questions": [
            "How does buying property work?",
            "What's the down payment?",
            "Is this safe?",
            "What if I can't afford it?"
        ]
    },

    CustomerSegment.SAVVY_INVESTOR: {
        "tone": "Data-driven, efficient, professional, ROI-focused",
        "language_style": "Direct, technical terms OK, numbers and metrics",
        "focus": [
            "Rental yields and cash flow",
            "Capital appreciation rates",
            "Market trends and forecasts",
            "Resale potential and liquidity",
            "Tax implications and ownership structure"
        ],
        "greeting": "Looking for your next investment? I'm Amr. Let's run the numbers.",
        "value_proposition": "ML-powered valuation + market trend analysis + blockchain transparency + ROI calculator",
        "urgency_style": "Market data (prices increasing X% YoY), comparative ROI, time-sensitive deals",
        "objection_handling": "Show data, run valuations, compare alternatives",
        "typical_questions": [
            "What's the rental yield?",
            "How's the resale market?",
            "Show me ROI comparison",
            "What are the hidden costs?"
        ]
    },

    CustomerSegment.UNKNOWN: {
        "tone": "Friendly, exploratory, consultative",
        "language_style": "Balanced, adaptable",
        "focus": [
            "Discovery questions to classify",
            "Understanding needs and goals",
            "Building rapport"
        ],
        "greeting": "Welcome to Osool! I'm Amr, your AI real estate consultant. What brings you here today?",
        "value_proposition": "AI-powered property search + legal protection + blockchain verification",
        "urgency_style": "Neutral, focus on value",
        "objection_handling": "Listen and adapt",
        "typical_questions": [
            "Tell me about your property goals",
            "What's your budget range?",
            "Are you buying for yourself or investment?"
        ]
    }
}


def get_persona_config(segment: CustomerSegment) -> Dict:
    """
    Get persona configuration for a customer segment.

    Args:
        segment: CustomerSegment enum value

    Returns:
        Dict with persona configuration (tone, focus, greeting, etc.)
    """
    return SEGMENT_PERSONAS.get(segment, SEGMENT_PERSONAS[CustomerSegment.UNKNOWN])


def get_discovery_questions(segment: CustomerSegment) -> List[str]:
    """
    Get appropriate discovery questions based on segment.

    Args:
        segment: CustomerSegment enum value

    Returns:
        List of questions to ask for segmentation/qualification
    """
    questions_by_segment = {
        CustomerSegment.LUXURY_INVESTOR: [
            "Are you looking for a primary residence or investment?",
            "Which areas interest you? (New Capital, North Coast, etc.)",
            "What amenities are most important to you?"
        ],
        CustomerSegment.FIRST_TIME_BUYER: [
            "Is this your first property purchase?",
            "What's your budget range?",
            "Are you buying for yourself or your family?",
            "Would you like me to explain the buying process?"
        ],
        CustomerSegment.SAVVY_INVESTOR: [
            "How many properties do you currently own?",
            "What's your target rental yield?",
            "Are you focused on capital appreciation or cash flow?",
            "What locations are you comparing?"
        ],
        CustomerSegment.UNKNOWN: [
            "What brings you to Osool today?",
            "Are you looking to buy a home or invest in real estate?",
            "What's your approximate budget range?",
            "Have you purchased property in Egypt before?"
        ]
    }

    return questions_by_segment.get(segment, questions_by_segment[CustomerSegment.UNKNOWN])


def extract_budget_from_conversation(conversation_history: List[Dict]) -> Optional[int]:
    """
    Extract budget from conversation using regex patterns.

    Args:
        conversation_history: List of message dicts

    Returns:
        Budget in EGP (integer) or None if not mentioned

    Patterns detected:
    - "5 million" → 5,000,000
    - "3M" → 3,000,000
    - "2.5M EGP" → 2,500,000
    - "budget is 4 million" → 4,000,000
    """
    # Defensive: ensure each message is a dict before calling .get()
    full_text = " ".join([
        msg.get("content", "") for msg in conversation_history
        if isinstance(msg, dict) and msg.get("role") == "user"
    ])

    # Pattern: "X million" or "XM"
    patterns = [
        r"(\d+\.?\d*)\s*million",
        r"(\d+\.?\d*)\s*m\b",
        r"budget.*?(\d+\.?\d*)\s*million",
        r"around\s*(\d+\.?\d*)\s*million",
        r"approximately\s*(\d+\.?\d*)\s*million"
    ]

    for pattern in patterns:
        match = re.search(pattern, full_text.lower())
        if match:
            amount = float(match.group(1))
            return int(amount * 1_000_000)  # Convert to EGP

    return None


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: Luxury Investor
    conv1 = [
        {"role": "user", "content": "I'm looking for exclusive penthouses in New Capital"},
        {"role": "assistant", "content": "Great! What's your budget?"},
        {"role": "user", "content": "Around 15 million EGP"}
    ]
    segment1 = classify_customer(15_000_000, conv1)
    print(f"Test 1 - Luxury Investor: {segment1}")
    print(f"Persona: {get_persona_config(segment1)['greeting']}\n")

    # Test case 2: First-Time Buyer
    conv2 = [
        {"role": "user", "content": "This is my first property. I'm nervous about the process"},
        {"role": "assistant", "content": "No worries, I'll guide you through everything"},
        {"role": "user", "content": "My budget is 2.5 million"}
    ]
    segment2 = classify_customer(2_500_000, conv2)
    print(f"Test 2 - First-Time Buyer: {segment2}")
    print(f"Persona: {get_persona_config(segment2)['greeting']}\n")

    # Test case 3: Savvy Investor
    conv3 = [
        {"role": "user", "content": "What's the rental yield in New Cairo?"},
        {"role": "assistant", "content": "Typically 6-8% annually"},
        {"role": "user", "content": "I have 3 properties already, looking for better ROI"}
    ]
    profile3 = {"properties_owned": 3}
    segment3 = classify_customer(None, conv3, profile3)
    print(f"Test 3 - Savvy Investor: {segment3}")
    print(f"Persona: {get_persona_config(segment3)['greeting']}\n")

    # Test budget extraction
    budget = extract_budget_from_conversation(conv1)
    print(f"Extracted budget: {budget:,} EGP")


def mock_crm_lookup(phone_number: str) -> Optional[Dict]:
    """
    Simulate a CRM lookup to find existing customers.
    In production, this would call Hubspot/Salesforce API.
    """
    mock_db = {
        "+201000000001": {"name": "Ahmed", "last_seen": "2 days ago", "interest": "New Cairo Villas", "status": "bouncing"},
        "+201222222222": {"name": "Sarah", "last_seen": "1 week ago", "interest": "Zayed Apartments", "status": "warm"},
        "+201111111111": {"name": "Dr. Mohamed", "last_seen": "3 months ago", "interest": "Investment", "status": "churned"},
    }
    return mock_db.get(phone_number)


def get_personalized_welcome(phone_number: Optional[str]) -> str:
    """
    Generate a hyper-personalized welcome message if user is known.
    """
    if not phone_number:
        return ""
        
    crm_data = mock_crm_lookup(phone_number)
    if not crm_data:
        return ""
        
    name = crm_data.get("name")
    last_interest = crm_data.get("interest")
    
    # "Welcome Back" pattern
    return f"Welcome back, {name}! 👋 I was just looking at some new {last_interest} that match what we discussed last time. Ready to see them?"


# ==============================================================================
# ELEPHANT MEMORY - Long-Term User Fact Tracker (Phase 4)
# ==============================================================================

class UserProfile(BaseModel):
    """
    The Long-Term Memory of the User (The Elephant).
    Stores persistent facts extracted from conversations.
    """
    name: Optional[str] = None
    risk_appetite: str = "Unknown"  # Conservative, Aggressive, Balanced
    hard_constraints: List[str] = Field(default_factory=list)  # "Max budget 5M", "Must be Zayed"
    soft_preferences: List[str] = Field(default_factory=list)  # "Hates ground floor", "Likes modern"
    wolf_status: str = "Cold Lead"   # Cold Lead, Warm Prospect, Hot Deal, Client
    key_facts: List[str] = Field(default_factory=list)  # "Buying for daughter", "Works at Vodafone"
    budget_extracted: Optional[int] = None  # Budget in EGP if explicitly mentioned
    purpose: Optional[str] = None  # "investment" or "living"
    preferred_locations: List[str] = Field(default_factory=list)
    deal_breakers: List[str] = Field(default_factory=list)  # Things user absolutely won't accept


async def extract_user_facts(
    current_profile: Dict[str, Any], 
    recent_history: List[Dict[str, str]], 
    openai_client
) -> Dict[str, Any]:
    """
    Uses GPT-4o to extract persistent facts from the conversation.
    This runs silently in the background to update the user's dossier.
    
    Args:
        current_profile: Existing user profile dict (may be empty)
        recent_history: Recent conversation messages (last 3-5 turns)
        openai_client: AsyncOpenAI client instance
        
    Returns:
        Updated user profile dict with newly extracted facts merged in
    """
    if not recent_history:
        return current_profile
    
    # Convert last 5 turns to text
    chat_text = "\n".join([
        f"{m.get('role', 'user')}: {m.get('content', '')}" 
        for m in recent_history[-5:]
    ])
    
    system_prompt = """You are a CRM Data Extraction Specialist for an Egyptian real estate consultancy.
Analyze the conversation and extract/update the user's profile.

CURRENT PROFILE:
{current_profile}

EXTRACTION RULES:
1. HARD CONSTRAINTS (Non-negotiable): Budget limits, required locations, delivery dates, must-have features
2. SOFT PREFERENCES (Nice to have): Style preferences, amenities, view preferences
3. PERSONAL FACTS: Name, job, family situation, reason for buying
4. RISK PROFILE: Conservative (first-timer, safety-focused) vs Aggressive (investor, ROI-focused)
5. WOLF STATUS: 
   - "Cold Lead" = Just browsing, no commitment signals
   - "Warm Prospect" = Shared budget/location, showing interest
   - "Hot Deal" = Ready to buy, asking about contracts/next steps
   - "Client" = Has already purchased

IMPORTANT:
- Extract ONLY facts explicitly stated or strongly implied
- Do NOT guess or assume
- Preserve existing facts unless explicitly contradicted
- For Arabic names, keep them in Arabic script

Output ONLY valid JSON (no markdown, no explanation):
{{
    "name": "string or null",
    "risk_appetite": "Unknown|Conservative|Aggressive|Balanced",
    "hard_constraints": ["list of non-negotiable requirements"],
    "soft_preferences": ["list of preferences"],
    "wolf_status": "Cold Lead|Warm Prospect|Hot Deal|Client",
    "key_facts": ["personal facts for rapport"],
    "budget_extracted": number or null (in EGP),
    "purpose": "investment|living|null",
    "preferred_locations": ["list of locations"],
    "deal_breakers": ["things user won't accept"]
}}"""
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt.format(current_profile=json.dumps(current_profile, ensure_ascii=False))},
                {"role": "user", "content": f"Extract user facts from this conversation:\n\n{chat_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=500
        )
        
        extracted = json.loads(response.choices[0].message.content)
        
        # Merge with existing profile (new facts override old, but preserve non-null values)
        merged = {**current_profile}
        for key, value in extracted.items():
            if value is not None and value != "" and value != []:
                if isinstance(value, list) and key in merged and isinstance(merged[key], list):
                    # Merge lists, avoiding duplicates
                    existing = set(merged[key])
                    merged[key] = merged[key] + [v for v in value if v not in existing]
                else:
                    merged[key] = value
        
        return merged
        
    except Exception as e:
        print(f"⚠️ Elephant Memory extraction failed (non-fatal): {e}")
        return current_profile


def profile_to_context_string(profile: Dict[str, Any]) -> str:
    """
    Convert a user profile dict to a human-readable context string
    for injection into the AI prompt.
    """
    if not profile:
        return ""
    
    parts = []
    
    if profile.get('name'):
        parts.append(f"اسم العميل: {profile['name']}")
    
    if profile.get('wolf_status') and profile['wolf_status'] != 'Cold Lead':
        status_ar = {
            'Warm Prospect': 'مهتم',
            'Hot Deal': 'جاهز للشراء',
            'Client': 'عميل حالي'
        }.get(profile['wolf_status'], profile['wolf_status'])
        parts.append(f"الحالة: {status_ar}")
    
    if profile.get('budget_extracted'):
        budget_m = profile['budget_extracted'] / 1_000_000
        parts.append(f"الميزانية: {budget_m:.1f} مليون جنيه")
    
    if profile.get('purpose'):
        purpose_ar = "استثمار" if profile['purpose'] == 'investment' else "سكن"
        parts.append(f"الهدف: {purpose_ar}")
    
    if profile.get('preferred_locations'):
        parts.append(f"المناطق المفضلة: {', '.join(profile['preferred_locations'])}")
    
    if profile.get('hard_constraints'):
        parts.append(f"شروط أساسية: {', '.join(profile['hard_constraints'])}")
    
    if profile.get('soft_preferences'):
        parts.append(f"تفضيلات: {', '.join(profile['soft_preferences'])}")
    
    if profile.get('key_facts'):
        parts.append(f"معلومات شخصية: {', '.join(profile['key_facts'])}")
    
    if profile.get('deal_breakers'):
        parts.append(f"⛔ يرفض: {', '.join(profile['deal_breakers'])}")
    
    return "\n".join(parts) if parts else ""

