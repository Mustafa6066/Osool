"""
Objection Handling Library for Osool AI Sales Agent
---------------------------------------------------
Detects and provides strategic responses to common sales objections.

Phase 3: AI Personality Enhancement
"""

from typing import Dict, List, Optional
from enum import Enum
from .customer_profiles import CustomerSegment


class ObjectionType(Enum):
    """Common objection types in real estate sales."""
    PRICE_TOO_HIGH = "price_too_high"
    COMPETITOR_BETTER = "competitor_better"
    NEED_TIME = "need_time"
    APPROVAL_NEEDED = "approval_needed"
    LOCATION_CONCERNS = "location_concerns"
    DEVELOPER_TRUST = "developer_trust"
    FINANCING_ISSUES = "financing_issues"
    PROPERTY_CONDITION = "property_condition"
    MARKET_TIMING = "market_timing"
    NO_URGENCY = "no_urgency"


# Objection detection patterns
OBJECTION_LIBRARY: Dict[ObjectionType, Dict] = {
    ObjectionType.PRICE_TOO_HIGH: {
        "detection_keywords": [
            "expensive", "too much", "can't afford", "overpriced",
            "too high", "beyond my budget", "out of range",
            "cheaper", "lower price", "discount", "negotiate"
        ],
        "responses": {
            CustomerSegment.FIRST_TIME_BUYER: """I understand budget concerns are real. Let's look at this differently:

**Payment Plan Breakdown:**
- With {down_payment}% down ({down_amount:,} EGP)
- Over {installment_years} years
- Your monthly payment would be around {monthly:,} EGP

That's comparable to renting, but you're building equity! Plus, I can run our AI valuation to show you the fair market price.""",

            CustomerSegment.SAVVY_INVESTOR: """Fair question. Let me run the valuation AI to show you objective market data.

[Will call run_valuation_ai tool]

Based on comparable sales and our ML model trained on 3,000+ transactions:
- This property is {valuation_result} (fair/underpriced/overpriced by X%)
- Average price/sqm in this compound: {avg_price_sqm} EGP
- Rental yield potential: {rental_yield}%

Would you like me to show alternatives in your price range?""",

            CustomerSegment.LUXURY_INVESTOR: """I appreciate your attention to value. In the luxury segment, price reflects exclusivity, location, and long-term appreciation.

Let me share:
- This compound has appreciated {appreciation}% over 3 years
- Only {units_remaining} units remain in this tier
- Includes {premium_features}

Would you like me to prepare a detailed investment analysis?"""
        },
        "recommended_tools": ["run_valuation_ai", "calculate_mortgage", "compare_units"],
        "escalation_threshold": 3  # Escalate to human after 3rd price objection
    },

    ObjectionType.COMPETITOR_BETTER: {
        "detection_keywords": [
            "nawy", "aqarmap", "property finder", "other platform",
            "competitor", "better deal", "saw cheaper", "amazon has"
        ],
        "responses": {
            CustomerSegment.FIRST_TIME_BUYER: """Great that you're comparing! That shows you're thinking carefully.

Here's what makes Osool different:
1. **AI Legal Scanner**: We check contracts against Egyptian Law 114 - no other platform does this
2. **Blockchain Verification**: Tamper-proof ownership records on Polygon
3. **No Hidden Fees**: We show you the real total cost upfront

[Will call explain_osool_advantage tool for detailed comparison]

Would you like me to check that specific property you saw?""",

            CustomerSegment.SAVVY_INVESTOR: """Smart to compare platforms. Here's the data:

**Osool Advantage:**
- ML-powered valuation (not agent estimates)
- Blockchain ownership verification = faster resale
- Historical ROI data for compounds
- Legal AI scanner = risk protection

[Call explain_osool_advantage]

Most importantly: Our prices come directly from developers. Other platforms add 3-5% markup. Want me to verify the property you're comparing?""",

            CustomerSegment.LUXURY_INVESTOR: """Excellent - discerning investors always compare.

What differentiates Osool:
- Direct developer relationships (no middleman markup)
- Blockchain-verified ownership (critical for high-value assets)
- White-glove concierge service
- AI-powered legal protection

[Call explain_osool_advantage]

We focus on quality over volume. Which property are you comparing?"""
        },
        "recommended_tools": ["explain_osool_advantage", "check_real_time_status"],
        "escalation_threshold": 2
    },

    ObjectionType.NEED_TIME: {
        "detection_keywords": [
            "think about it", "later", "not ready", "need to discuss",
            "too soon", "rushing", "more time", "sleep on it",
            "premature", "hasty decision"
        ],
        "responses": {
            CustomerSegment.FIRST_TIME_BUYER: """Of course! Buying property is a big decision - you should take your time.

To help you decide, would you like me to:
1. Send you a comparison of your top 3 properties?
2. Calculate different payment scenarios?
3. Share our beginner's guide to Egyptian real estate?
4. Schedule a no-pressure call to answer questions?

I'll be here when you're ready.""",

            CustomerSegment.SAVVY_INVESTOR: """Understood. Smart investors don't rush.

While you evaluate, let me prepare:
1. Detailed ROI comparison (rental yield + appreciation)
2. Market trend analysis for your target areas
3. Upcoming developer promotions that might interest you

[Call check_market_trends for live data]

Should I also flag you if similar properties come on market?""",

            CustomerSegment.LUXURY_INVESTOR: """Of course, take all the time you need. This is an important decision.

Would you like me to:
1. Arrange a private viewing at your convenience?
2. Prepare an exclusive investment memo for this property?
3. Schedule a meeting with our luxury property specialist?

I'll reserve this unit's details in your profile for when you're ready."""
        },
        "recommended_tools": ["compare_units", "check_market_trends", "calculate_investment_roi"],
        "escalation_threshold": 2  # Offer human consultation
    },

    ObjectionType.APPROVAL_NEEDED: {
        "detection_keywords": [
            "wife", "husband", "spouse", "family", "partner",
            "need approval", "discuss with", "consult", "parents",
            "ask my", "check with"
        ],
        "responses": {
            "all_segments": """That's wonderful - including your family in this decision is smart!

To make that conversation easier, would you like me to prepare:
1. **Visual Summary**: Photos + floor plans + location map
2. **Financial Breakdown**: Down payment, monthly costs, total investment
3. **ROI Analysis**: Investment potential and resale value
4. **Comparison Sheet**: This property vs alternatives

I can also schedule a video tour you can watch together. When would be good?"""
        },
        "recommended_tools": ["compare_units", "calculate_mortgage", "generate_reservation_link"],
        "escalation_threshold": 1  # Easy win - provide materials
    },

    ObjectionType.LOCATION_CONCERNS: {
        "detection_keywords": [
            "too far", "location", "commute", "distance",
            "area is", "neighborhood", "accessibility",
            "traffic", "infrastructure"
        ],
        "responses": {
            "all_segments": """Location is critical - glad you're thinking about this.

Let me provide specific details:
- Distance to city center: {distance_km} km
- Commute time: {commute_time} minutes via {road_name}
- Nearby: {nearby_amenities}
- Planned infrastructure: {future_developments}

[Will call check_market_trends for area development]

Many of our clients had similar concerns initially, but the compound's amenities (schools, hospitals, shopping) create a self-contained community. Would you like to see a location video?"""
        },
        "recommended_tools": ["search_properties", "check_market_trends"],
        "escalation_threshold": 2
    },

    ObjectionType.DEVELOPER_TRUST: {
        "detection_keywords": [
            "trust", "reliable", "developer reputation", "scam",
            "fraud", "safe", "legitimate", "track record",
            "delivered before", "delays"
        ],
        "responses": {
            "all_segments": """Trust is EVERYTHING in real estate. Here's why this developer is verified:

**Developer Track Record:**
- {developer_name} has delivered {projects_completed} projects on time
- {units_delivered} units handed over in last 3 years
- FRA-licensed and registered

**Osool Protection:**
1. **AI Contract Scanner**: Checks against Egyptian Law 114
2. **Blockchain Verification**: Every transaction recorded immutably
3. **Escrow Protection**: Your deposit is secured

[Will call audit_uploaded_contract if contract available]

Would you like me to show you this developer's completed projects?"""
        },
        "recommended_tools": ["audit_uploaded_contract", "check_real_time_status"],
        "escalation_threshold": 1  # High priority - trust is critical
    },

    ObjectionType.FINANCING_ISSUES: {
        "detection_keywords": [
            "financing", "mortgage", "loan", "bank approval",
            "credit", "down payment", "can't pay", "installments"
        ],
        "responses": {
            "all_segments": """Financing is often simpler than people think. Let me help:

**Your Options:**
1. **Developer Payment Plan**: {installment_years} years, {down_payment}% down
   - Monthly: {monthly:,} EGP
   - No bank needed!

2. **Mortgage (if preferred)**:
   - CBE rate: {cbe_rate}%
   - 20-year loan available
   [Will call calculate_mortgage with live CBE rates]

3. **Hybrid**: Part developer plan, part mortgage

Would you like me to show you different scenarios? We can find something that fits your cash flow."""
        },
        "recommended_tools": ["calculate_mortgage", "calculate_investment_roi"],
        "escalation_threshold": 2  # Offer financial advisor consultation
    },

    ObjectionType.MARKET_TIMING: {
        "detection_keywords": [
            "market crash", "prices falling", "wait", "bad timing",
            "recession", "economic", "devaluation", "pound"
        ],
        "responses": {
            CustomerSegment.SAVVY_INVESTOR: """Smart to consider market timing. Here's the data:

**Current Market (Real Numbers):**
- Property prices in Egypt: +{appreciation_yoy}% YoY
- Rental demand: {rental_demand_status}
- Developer launches: {new_launches} projects this quarter

**Why Now:**
1. Pound devaluation makes USD income very attractive for rentals
2. Mortgage rates locked for 20 years (hedge against inflation)
3. Supply shortage in premium areas

[Call check_market_trends for latest data]

Historical data shows Egyptian real estate outperforms EGP deposits. Want the full analysis?""",

            "other_segments": """I understand the concern about timing. Here's what the data shows:

- Egyptian real estate has historically been inflation-proof
- Waiting means potentially missing {current_promotion}
- Rental demand is at all-time high

[Call check_market_trends]

The best time to buy is when you find the right property at the right price. This checks both boxes."""
        },
        "recommended_tools": ["check_market_trends", "calculate_investment_roi"],
        "escalation_threshold": 2
    },

    ObjectionType.NO_URGENCY: {
        "detection_keywords": [
            "no rush", "not urgent", "just browsing", "looking around",
            "exploring", "researching", "no hurry"
        ],
        "responses": {
            "all_segments": """Perfect! Taking your time to research is the smart approach.

While you explore, let me help you:
1. **Save your favorite properties** (I'll track them for you)
2. **Set up alerts** for properties matching your criteria
3. **Get weekly market updates** for areas you're interested in

No pressure at all. I'm here to be a resource. What type of properties interest you?"""
        },
        "recommended_tools": ["search_properties", "check_market_trends"],
        "escalation_threshold": None  # Low priority
    }
}


def detect_objection(user_message: str) -> Optional[ObjectionType]:
    """
    Detect objection type from user message.

    Args:
        user_message: The user's message text

    Returns:
        ObjectionType enum value or None if no objection detected

    Detection Logic:
    - Case-insensitive keyword matching
    - Returns first match (ordered by priority)
    - Returns None if message is neutral/positive
    """
    user_lower = user_message.lower()

    # Priority order matters - check critical objections first
    priority_order = [
        ObjectionType.DEVELOPER_TRUST,  # Highest priority
        ObjectionType.PRICE_TOO_HIGH,
        ObjectionType.FINANCING_ISSUES,
        ObjectionType.COMPETITOR_BETTER,
        ObjectionType.LOCATION_CONCERNS,
        ObjectionType.MARKET_TIMING,
        ObjectionType.APPROVAL_NEEDED,
        ObjectionType.NEED_TIME,
        ObjectionType.PROPERTY_CONDITION,
        ObjectionType.NO_URGENCY  # Lowest priority
    ]

    for objection_type in priority_order:
        if objection_type in OBJECTION_LIBRARY:
            config = OBJECTION_LIBRARY[objection_type]
            if any(keyword in user_lower for keyword in config["detection_keywords"]):
                return objection_type

    return None


def get_objection_response(
    objection_type: ObjectionType,
    customer_segment: CustomerSegment,
    context: Optional[Dict] = None
) -> str:
    """
    Get appropriate response for an objection based on customer segment.

    Args:
        objection_type: The detected objection type
        customer_segment: The customer's segment
        context: Optional context dict with property/calculation data

    Returns:
        Formatted response string with placeholders filled

    Context Keys:
    - down_payment: Down payment percentage (int)
    - installment_years: Installment period (int)
    - monthly: Monthly payment amount (int)
    - valuation_result: "fair", "overpriced", "underpriced"
    - developer_name: Developer company name
    - etc.
    """
    if objection_type not in OBJECTION_LIBRARY:
        return "I understand your concern. Let me look into that for you."

    config = OBJECTION_LIBRARY[objection_type]
    responses = config["responses"]

    # Get segment-specific response or fall back to "all_segments"
    if customer_segment in responses:
        response_template = responses[customer_segment]
    elif "all_segments" in responses:
        response_template = responses["all_segments"]
    else:
        # Fallback to first available response
        response_template = list(responses.values())[0]

    # Fill in context placeholders
    if context:
        try:
            response = response_template.format(**context)
        except KeyError:
            # If missing context keys, return template as-is
            response = response_template
    else:
        response = response_template

    return response


def get_recommended_tools(objection_type: ObjectionType) -> List[str]:
    """
    Get list of tools that should be called to address this objection.

    Args:
        objection_type: The detected objection type

    Returns:
        List of tool names (strings)

    Example:
        ["run_valuation_ai", "calculate_mortgage", "compare_units"]
    """
    if objection_type in OBJECTION_LIBRARY:
        return OBJECTION_LIBRARY[objection_type].get("recommended_tools", [])
    return []


def should_escalate_to_human(objection_type: ObjectionType, objection_count: int) -> bool:
    """
    Determine if objection should be escalated to human agent.

    Args:
        objection_type: The detected objection type
        objection_count: Number of times this objection has been raised in conversation

    Returns:
        True if should escalate, False otherwise

    Escalation Rules:
    - Developer trust issues: Escalate after 1st occurrence
    - Price objections: Escalate after 3rd occurrence
    - No escalation threshold (None): Never escalate
    """
    if objection_type not in OBJECTION_LIBRARY:
        return False

    threshold = OBJECTION_LIBRARY[objection_type].get("escalation_threshold")

    if threshold is None:
        return False  # Never escalate

    return objection_count >= threshold


def track_objection(session_id: str, objection_type: ObjectionType):
    """
    Track objection in analytics (to be implemented).

    Args:
        session_id: User session ID
        objection_type: The detected objection type

    TODO: Store in conversation_analytics table
    """
    # Placeholder for analytics integration
    pass


# Example usage and testing
if __name__ == "__main__":
    from .customer_profiles import CustomerSegment

    # Test objection detection
    test_messages = [
        ("This is too expensive for me", ObjectionType.PRICE_TOO_HIGH),
        ("I saw the same unit cheaper on Nawy", ObjectionType.COMPETITOR_BETTER),
        ("I need to discuss with my wife first", ObjectionType.APPROVAL_NEEDED),
        ("Is this developer trustworthy?", ObjectionType.DEVELOPER_TRUST),
        ("Just browsing, no rush", ObjectionType.NO_URGENCY)
    ]

    print("=== Objection Detection Tests ===\n")
    for message, expected in test_messages:
        detected = detect_objection(message)
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{message}' → {detected}")

    print("\n=== Response Generation Tests ===\n")

    # Test price objection for First-Time Buyer
    objection = ObjectionType.PRICE_TOO_HIGH
    segment = CustomerSegment.FIRST_TIME_BUYER
    context = {
        "down_payment": 10,
        "down_amount": 250_000,
        "installment_years": 7,
        "monthly": 30_000
    }

    response = get_objection_response(objection, segment, context)
    print(f"Objection: {objection.value}")
    print(f"Segment: {segment.value}")
    print(f"Response:\n{response}\n")

    # Test recommended tools
    tools = get_recommended_tools(objection)
    print(f"Recommended Tools: {tools}\n")

    # Test escalation logic
    print("=== Escalation Tests ===\n")
    print(f"Developer Trust (count=1): {should_escalate_to_human(ObjectionType.DEVELOPER_TRUST, 1)}")  # True
    print(f"Price (count=2): {should_escalate_to_human(ObjectionType.PRICE_TOO_HIGH, 2)}")  # False
    print(f"Price (count=3): {should_escalate_to_human(ObjectionType.PRICE_TOO_HIGH, 3)}")  # True
