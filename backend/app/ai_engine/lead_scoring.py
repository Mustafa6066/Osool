"""
Lead Scoring and Temperature Classification for Osool AI Sales Agent
--------------------------------------------------------------------
Scores leads based on conversation signals and behavior to prioritize follow-up.

Temperature Levels:
- HOT: Ready to buy (asking about reservation, showing strong intent)
- WARM: Engaged and qualified (comparing options, asking details)
- COLD: Early stage (browsing, vague questions, no budget mentioned)

Phase 3: AI Personality Enhancement
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class LeadTemperature(Enum):
    """Lead classification by buying readiness."""
    HOT = "hot"      # Ready to transact (score >= 50)
    WARM = "warm"    # Engaged and qualified (score 25-49)
    COLD = "cold"    # Early discovery (score < 25)


class BehaviorSignal(Enum):
    """Trackable user behavior signals."""
    BUDGET_MENTIONED = "budget_mentioned"                   # +20 points
    PURCHASE_INTENT = "purchase_intent"                     # +30 points
    ACTIVE_COMPARISON = "active_comparison"                 # +20 points
    USED_VALUATION_TOOL = "used_valuation_tool"            # +15 points
    VIEWED_MULTIPLE_PROPERTIES = "viewed_multiple"          # +15 points
    SPECIFIC_LOCATION_PREFERENCE = "location_preference"    # +15 points
    ASKED_ABOUT_FINANCING = "asked_financing"              # +10 points
    TIMELINE_MENTIONED = "timeline_mentioned"               # +10 points
    ENGAGED_DEEPLY = "engaged_deeply"                       # +10 points (session > 10 min)
    OBJECTION_RAISED_BUT_ENGAGED = "objection_engaged"     # -5 points
    REPEATEDLY_POSTPONING = "postponing"                    # -10 points
    PRICE_SHOPPING = "price_shopping"                       # -5 points (comparing only on price)


# Signal detection patterns
SIGNAL_PATTERNS: Dict[BehaviorSignal, Dict] = {
    BehaviorSignal.BUDGET_MENTIONED: {
        "keywords": ["budget", "afford", "pay", "spend", "million", "EGP", "price range"],
        "points": 20,
        "description": "User stated their budget range"
    },
    BehaviorSignal.PURCHASE_INTENT: {
        "keywords": [
            "reserve", "buy", "purchase", "payment", "deposit",
            "down payment", "when can i move in", "contract",
            "how do i proceed", "next steps"
        ],
        "points": 30,
        "description": "Strong buying signals detected"
    },
    BehaviorSignal.SPECIFIC_LOCATION_PREFERENCE: {
        "keywords": [
            "new cairo", "new capital", "6th october", "north coast",
            "sheikh zayed", "palm hills", "madinaty", "compound name"
        ],
        "points": 15,
        "description": "Has specific location in mind"
    },
    BehaviorSignal.ASKED_ABOUT_FINANCING: {
        "keywords": ["mortgage", "loan", "bank", "financing", "installment", "monthly payment"],
        "points": 10,
        "description": "Interested in payment options"
    },
    BehaviorSignal.TIMELINE_MENTIONED: {
        "keywords": [
            "this month", "next month", "within", "by", "before",
            "urgent", "asap", "soon", "3 months", "6 months"
        ],
        "points": 10,
        "description": "Has defined purchase timeline"
    },
    BehaviorSignal.OBJECTION_RAISED_BUT_ENGAGED: {
        "keywords": ["but", "however", "concern", "worried", "issue"],
        "points": -5,
        "description": "Has concerns but still engaged"
    },
    BehaviorSignal.REPEATEDLY_POSTPONING: {
        "keywords": ["later", "maybe", "not sure", "thinking", "need time"],
        "points": -10,
        "description": "Showing hesitation or delay signals",
        "threshold_count": 2  # Only apply if repeated 2+ times
    }
}


def score_lead(
    conversation_history: List[Dict],
    session_metadata: Dict,
    user_profile: Optional[Dict] = None
) -> Dict:
    """
    Score lead based on conversation signals and behavior.

    Args:
        conversation_history: List of message dicts with 'role' and 'content'
        session_metadata: Dict with session data (properties_viewed, tools_used, etc.)
        user_profile: Optional user profile data

    Returns:
        Dict with:
        - score: int (0-100+)
        - temperature: str ("hot", "warm", "cold")
        - signals: List[str] (detected signals)
        - confidence: float (0.0-1.0)
        - recommended_action: str (next best action)
        - priority_level: int (1-5, where 5 is highest)

    Scoring Factors:
    - Budget mentioned: +20
    - Purchase intent keywords: +30
    - Specific location preference: +15
    - Asked about financing: +10
    - Timeline mentioned: +10
    - Viewed 3+ properties: +20
    - Used valuation/ROI tools: +15
    - Session duration > 10 min: +10
    - Objection raised but engaged: -5
    - Repeatedly postponing: -10
    """
    score = 0
    signals: List[str] = []
    detected_behaviors: List[BehaviorSignal] = []

    # Combine user messages into searchable text
    # Defensive: ensure each message is a dict before calling .get()
    user_messages = [
        msg.get("content", "") for msg in conversation_history
        if isinstance(msg, dict) and msg.get("role") == "user"
    ]
    full_text = " ".join(user_messages).lower()

    # HUMAN HANDOFF: Complex Query Detection
    # If user asks about offshore, corporate structures, or complex financing
    complex_triggers = ["offshore", "corporate ownership", "legal structure", "international transfer", "complex financing", "multi-partner", "syndicate"]
    if any(trigger in full_text for trigger in complex_triggers):
        return {
            "score": 0,
            "temperature": LeadTemperature.COLD.value,
            "signals": ["complex_query_detected"],
            "confidence": 1.0,
            "recommended_action": "ESCALATE_IMMEDIATELY",
            "priority_level": 5,
            "reason": "Complex legal/financing structure requested",
            "detected_behaviors": [],
            "session_summary": {}
        }
    
    # NEW: Detect "The Loop Trap" (Human Handoff Protocol)
    # Check if user asked the same question twice in last 3 turns
    last_3_user_msgs = [msg.get('content', '') for msg in conversation_history[-6:] if msg.get('role') == 'user']
    if len(last_3_user_msgs) >= 2 and len(set(last_3_user_msgs)) < len(last_3_user_msgs): # Duplicate detected
        return {
            "score": 0,
            "temperature": LeadTemperature.COLD.value,
            "signals": ["loop_detected"],
            "confidence": 0.0,
            "recommended_action": "ESCALATE_IMMEDIATELY",
            "priority_level": 5,
            "reason": "Loop detected - User repeating questions",
            "detected_behaviors": [],
            "session_summary": {}
        }

    # === SIGNAL DETECTION FROM CONVERSATION ===
    for signal, config in SIGNAL_PATTERNS.items():
        keywords = config["keywords"]
        points = config["points"]

        # Count keyword occurrences
        keyword_matches = sum(1 for kw in keywords if kw in full_text)

        # Check threshold if applicable
        threshold = config.get("threshold_count", 1)

        if keyword_matches >= threshold:
            score += points
            signals.append(signal.value)
            detected_behaviors.append(signal)

    # === BEHAVIORAL METRICS FROM SESSION ===

    # 1. Properties Viewed
    properties_viewed = session_metadata.get("properties_viewed", 0)
    if properties_viewed >= 3:
        score += 20
        signals.append(BehaviorSignal.VIEWED_MULTIPLE_PROPERTIES.value)

    # 2. Tools Used (especially valuation/ROI tools)
    tools_used = session_metadata.get("tools_used", [])
    high_intent_tools = [
        "run_valuation_ai", "calculate_mortgage", "calculate_investment_roi",
        "generate_reservation_link", "check_real_time_status"
    ]
    if any(tool in tools_used for tool in high_intent_tools):
        score += 15
        signals.append(BehaviorSignal.USED_VALUATION_TOOL.value)

    # 3. Session Duration (engagement indicator)
    session_start = session_metadata.get("session_start_time")
    if session_start:
        duration_minutes = (datetime.now() - session_start).total_seconds() / 60
        if duration_minutes > 10:
            score += 10
            signals.append(BehaviorSignal.ENGAGED_DEEPLY.value)

    # 4. Message Count (interaction depth)
    message_count = len(conversation_history)
    if message_count >= 10:
        score += 5  # Bonus for sustained conversation

    # 5. User Profile Signals (if available)
    # Defensive: ensure user_profile is a dict before using .get()
    if user_profile and isinstance(user_profile, dict):
        # Existing property owners are often warmer leads
        if user_profile.get("properties_owned", 0) > 0:
            score += 10

        # Phone verified = more serious
        if user_profile.get("phone_verified", False):
            score += 5

        # Completed KYC = very serious
        if user_profile.get("kyc_status") == "approved":
            score += 15

    # === TEMPERATURE CLASSIFICATION ===
    if score >= 50:
        temperature = LeadTemperature.HOT
        priority_level = 5
    elif score >= 25:
        temperature = LeadTemperature.WARM
        priority_level = 3
    else:
        temperature = LeadTemperature.COLD
        priority_level = 1

    # === CONFIDENCE CALCULATION ===
    # Higher confidence with more signals and longer engagement
    confidence_factors = [
        len(signals) / 10,  # More signals = higher confidence
        min(message_count / 20, 1.0),  # More messages = higher confidence
        min(properties_viewed / 5, 1.0)  # More views = higher confidence
    ]
    confidence = min(sum(confidence_factors) / len(confidence_factors), 1.0)

    # === RECOMMENDED ACTION ===
    recommended_action = _get_recommended_action(temperature, detected_behaviors, session_metadata)

    return {
        "score": score,
        "temperature": temperature.value,
        "signals": signals,
        "confidence": round(confidence, 2),
        "recommended_action": recommended_action,
        "priority_level": priority_level,
        "detected_behaviors": [b.value for b in detected_behaviors],
        "session_summary": {
            "properties_viewed": properties_viewed,
            "tools_used": tools_used,
            "message_count": message_count,
            "duration_minutes": session_metadata.get("duration_minutes", 0)
        }
    }


def _get_recommended_action(
    temperature: LeadTemperature,
    behaviors: List[BehaviorSignal],
    session_metadata: Dict
) -> str:
    """
    Determine next best action based on lead temperature and behavior.

    Args:
        temperature: Lead temperature level
        behaviors: List of detected behavior signals
        session_metadata: Session metadata dict

    Returns:
        Recommended action string
    """
    actions = {
        LeadTemperature.HOT: {
            "default": "Check property availability + Generate reservation link + Close with urgency",
            "no_property_viewed": "Ask for specific property interest + Show top matches",
            "financing_asked": "Calculate mortgage scenarios + Generate reservation with payment plan"
        },
        LeadTemperature.WARM: {
            "default": "Compare top 3 properties + Address objections + Schedule viewing",
            "multiple_properties_viewed": "Ask which property resonates most + Highlight unique value props",
            "objection_raised": "Address objection with data + Show alternative options"
        },
        LeadTemperature.COLD: {
            "default": "Ask discovery questions + Educate on process + Share success story",
            "no_budget_mentioned": "Gently ask about budget range",
            "browsing": "Offer to save favorites + Set up property alerts"
        }
    }

    # Get appropriate action set
    action_set = actions[temperature]

    # Check for specific conditions
    if BehaviorSignal.ASKED_ABOUT_FINANCING in behaviors:
        return action_set.get("financing_asked", action_set["default"])

    if session_metadata.get("properties_viewed", 0) == 0:
        return action_set.get("no_property_viewed", action_set["default"])

    if session_metadata.get("properties_viewed", 0) >= 3:
        return action_set.get("multiple_properties_viewed", action_set["default"])

    if BehaviorSignal.OBJECTION_RAISED_BUT_ENGAGED in behaviors:
        return action_set.get("objection_raised", action_set["default"])

    return action_set["default"]


def classify_by_intent(conversation_history: List[Dict]) -> str:
    """
    Classify user's primary intent.

    Args:
        conversation_history: List of message dicts

    Returns:
        Intent string: "residential", "investment", "resale", "unknown"
    """
    full_text = " ".join([
        msg.get("content", "") for msg in conversation_history
        if isinstance(msg, dict) and msg.get("role") == "user"
    ]).lower()

    # Intent patterns
    if any(kw in full_text for kw in ["rental", "invest", "roi", "yield", "rent out", "cash flow"]):
        return "investment"

    if any(kw in full_text for kw in ["live", "family", "move in", "home", "villa", "apartment"]):
        return "residential"

    if any(kw in full_text for kw in ["resale", "flip", "appreciation", "sell later"]):
        return "resale"

    return "unknown"


def get_follow_up_schedule(temperature: LeadTemperature, last_interaction: datetime) -> Dict:
    """
    Determine optimal follow-up timing based on lead temperature.

    Args:
        temperature: Lead temperature level
        last_interaction: Datetime of last conversation

    Returns:
        Dict with follow_up_hours and follow_up_method
    """
    follow_up_schedule = {
        LeadTemperature.HOT: {
            "hours": 4,  # Follow up within 4 hours
            "method": "WhatsApp + Phone call",
            "urgency": "high",
            "message": "Check availability + Offer immediate reservation"
        },
        LeadTemperature.WARM: {
            "hours": 24,  # Follow up next day
            "method": "WhatsApp message",
            "urgency": "medium",
            "message": "Share property comparison + Ask if they have questions"
        },
        LeadTemperature.COLD: {
            "hours": 72,  # Follow up in 3 days
            "method": "Email newsletter",
            "urgency": "low",
            "message": "Send market insights + New property alerts"
        }
    }

    schedule = follow_up_schedule[temperature]

    # Calculate next follow-up time
    from datetime import timedelta
    next_follow_up = last_interaction + timedelta(hours=schedule["hours"])

    return {
        "next_follow_up_time": next_follow_up,
        "follow_up_method": schedule["method"],
        "urgency": schedule["urgency"],
        "suggested_message": schedule["message"],
        "hours_until_follow_up": schedule["hours"]
    }


# Example usage and testing
if __name__ == "__main__":
    from datetime import datetime, timedelta

    # Test Case 1: HOT Lead
    hot_conversation = [
        {"role": "user", "content": "I want to buy an apartment in New Cairo, budget is 5 million"},
        {"role": "assistant", "content": "Great! Let me show you some options"},
        {"role": "user", "content": "I like unit 42. How do I reserve it? What's the down payment?"},
        {"role": "assistant", "content": "Down payment is 10%. Let me calculate"},
        {"role": "user", "content": "I want to proceed. Can I reserve today?"}
    ]

    hot_session = {
        "properties_viewed": 5,
        "tools_used": ["search_properties", "calculate_mortgage", "generate_reservation_link"],
        "session_start_time": datetime.now() - timedelta(minutes=15),
        "duration_minutes": 15
    }

    hot_profile = {"phone_verified": True, "properties_owned": 0}

    result = score_lead(hot_conversation, hot_session, hot_profile)

    print("=== HOT LEAD TEST ===")
    print(f"Score: {result['score']}")
    print(f"Temperature: {result['temperature']}")
    print(f"Signals: {', '.join(result['signals'])}")
    print(f"Confidence: {result['confidence']}")
    print(f"Priority: {result['priority_level']}/5")
    print(f"Action: {result['recommended_action']}\n")

    # Test Case 2: WARM Lead
    warm_conversation = [
        {"role": "user", "content": "Show me apartments in New Cairo"},
        {"role": "assistant", "content": "Sure! What's your budget?"},
        {"role": "user", "content": "Around 4 million. I'm comparing different areas"},
        {"role": "assistant", "content": "Let me show you options"},
        {"role": "user", "content": "These look good. I need to discuss with my family"}
    ]

    warm_session = {
        "properties_viewed": 3,
        "tools_used": ["search_properties", "compare_units"],
        "session_start_time": datetime.now() - timedelta(minutes=8),
        "duration_minutes": 8
    }

    result2 = score_lead(warm_conversation, warm_session)

    print("=== WARM LEAD TEST ===")
    print(f"Score: {result2['score']}")
    print(f"Temperature: {result2['temperature']}")
    print(f"Signals: {', '.join(result2['signals'])}")
    print(f"Confidence: {result2['confidence']}")
    print(f"Action: {result2['recommended_action']}\n")

    # Test Case 3: COLD Lead
    cold_conversation = [
        {"role": "user", "content": "Just browsing"},
        {"role": "assistant", "content": "Welcome! What type of property interests you?"},
        {"role": "user", "content": "Not sure yet, just looking"}
    ]

    cold_session = {
        "properties_viewed": 1,
        "tools_used": [],
        "session_start_time": datetime.now() - timedelta(minutes=3),
        "duration_minutes": 3
    }

    result3 = score_lead(cold_conversation, cold_session)

    print("=== COLD LEAD TEST ===")
    print(f"Score: {result3['score']}")
    print(f"Temperature: {result3['temperature']}")
    print(f"Signals: {', '.join(result3['signals'])}")
    print(f"Confidence: {result3['confidence']}")
    print(f"Action: {result3['recommended_action']}\n")

    # Test Intent Classification
    print("=== INTENT CLASSIFICATION ===")
    print(f"HOT Lead Intent: {classify_by_intent(hot_conversation)}")
    print(f"Investment Intent: {classify_by_intent([{'role': 'user', 'content': 'Looking for rental yield properties'}])}")

    # Test Follow-up Scheduling
    print("\n=== FOLLOW-UP SCHEDULING ===")
    hot_follow_up = get_follow_up_schedule(LeadTemperature.HOT, datetime.now())
    print(f"HOT Lead: {hot_follow_up['follow_up_method']} in {hot_follow_up['hours_until_follow_up']} hours")

    warm_follow_up = get_follow_up_schedule(LeadTemperature.WARM, datetime.now())
    print(f"WARM Lead: {warm_follow_up['follow_up_method']} in {warm_follow_up['hours_until_follow_up']} hours")

    cold_follow_up = get_follow_up_schedule(LeadTemperature.COLD, datetime.now())
    print(f"COLD Lead: {cold_follow_up['follow_up_method']} in {cold_follow_up['hours_until_follow_up']} hours")
