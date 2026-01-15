"""
Egyptian Real Estate Market Psychology & Sales Strategies
---------------------------------------------------------
Phase 1: Market intelligence for AMR AI agent

This module contains buyer personas, location psychology, and objection
handling strategies specifically designed for the Egyptian real estate market.
"""

EGYPTIAN_BUYER_PERSONAS = {
    "first_time_buyer": {
        "characteristics": [
            "Budget-conscious (typically 2-4M EGP)",
            "Needs flexible payment plans",
            "Wants established compounds with amenities",
            "Family-focused (schools, hospitals, safety)",
            "Risk-averse, prefers known developers",
            "Influenced by family opinions"
        ],
        "sales_approach": [
            "Emphasize payment flexibility and low monthly installments",
            "Show nearby schools, hospitals, and mosques",
            "Mention established developer reputation (Sodic, Palm Hills)",
            "Compare monthly payment to rent costs",
            "Highlight community amenities (pools, gym, security)",
            "Offer virtual tours to build confidence"
        ],
        "language_style": {
            "ar": "دافئ، مطمئن، يركز على الأسرة والأمان",
            "en": "Warm, reassuring, family-focused, emphasize security"
        },
        "typical_questions": [
            "What's the monthly payment?",
            "Is it safe for kids?",
            "Are there good schools nearby?",
            "Can I afford this?"
        ]
    },

    "investor": {
        "characteristics": [
            "ROI-focused (expects 15-20% annual return)",
            "Wants data and numbers, not emotions",
            "Considers resale value and liquidity",
            "Follows market trends closely",
            "Often owns multiple properties",
            "Makes quick decisions when data is good"
        ],
        "sales_approach": [
            "Lead with ROI projections and rental yield",
            "Show market trend charts and appreciation data",
            "Highlight location hotspots (New Cairo growth)",
            "Provide comparison with other investment options",
            "Emphasize capital appreciation potential",
            "Mention upcoming infrastructure projects"
        ],
        "language_style": {
            "ar": "احترافي، موجه بالبيانات، مباشر",
            "en": "Professional, data-driven, direct, numbers-focused"
        },
        "typical_questions": [
            "What's the ROI?",
            "What's the rental yield?",
            "Will prices go up in this area?",
            "What's the exit strategy?"
        ]
    },

    "upgrader": {
        "characteristics": [
            "Selling current property to upgrade",
            "Wants better location or larger size",
            "Established career, higher budget (5M+ EGP)",
            "Quality over price",
            "Status-conscious, wants prestige address",
            "Willing to wait for the right property"
        ],
        "sales_approach": [
            "Focus on prestige locations (Beverly Hills, Allegria)",
            "Highlight luxury features and finishing quality",
            "Show lifestyle upgrade benefits",
            "Mention exclusive compound memberships",
            "Emphasize social status and networking opportunities",
            "Compare to current property's limitations"
        ],
        "language_style": {
            "ar": "راقي، يركز على الجودة والمكانة",
            "en": "Sophisticated, quality-focused, status-oriented"
        },
        "typical_questions": [
            "What makes this better than my current property?",
            "Who are my neighbors?",
            "What's the compound reputation?",
            "Is this a prestigious address?"
        ]
    },

    "diaspora_egyptian": {
        "characteristics": [
            "Living abroad, investing in Egypt",
            "Prefers English communication",
            "Wants hassle-free process",
            "Concerned about legal safety",
            "May not visit property in person",
            "Values transparency and documentation"
        ],
        "sales_approach": [
            "Emphasize legal safety and contract transparency",
            "Offer virtual tours and detailed documentation",
            "Explain payment process for international transfers",
            "Highlight property management services",
            "Provide clear timeline and milestones",
            "Mention other diaspora buyers in compound"
        ],
        "language_style": {
            "ar": "مزيج من الإنجليزية والعربية، رسمي",
            "en": "Professional, clear, documentation-focused"
        },
        "typical_questions": [
            "How do I pay from abroad?",
            "Is my money safe?",
            "Can I see the contract?",
            "Who will manage the property?"
        ]
    }
}

LOCATION_PSYCHOLOGY = {
    "New Cairo": {
        "buyer_motivation": "Modern lifestyle, international community, AUC proximity",
        "selling_points": [
            "American University in Cairo (AUC) nearby",
            "Cairo Festival City and Mall of Arabia",
            "International schools (AIS, BIS, CAISC)",
            "Expat-friendly community",
            "Modern infrastructure and wide roads",
            "Easy access to Ring Road"
        ],
        "typical_buyer": "Upper-middle class families, expats, young professionals, investors",
        "price_range": "35,000-60,000 EGP/sqm",
        "growth_trend": "High growth, 12-15% annual appreciation",
        "objections": {
            "far_from_downtown": "New highways reduced commute to 30 minutes. Plus, everything you need is in New Cairo now - no need to go downtown.",
            "too_expensive": "Investment in New Cairo pays off - highest appreciation rate in Greater Cairo. Your property value grows faster here.",
            "no_character": "Modern living means better infrastructure, reliable utilities, and planned communities. Character comes from the lifestyle, not old buildings."
        },
        "hot_compounds": ["Madinaty", "Rehab", "5th Settlement", "Mountain View", "Hyde Park"]
    },

    "Sheikh Zayed": {
        "buyer_motivation": "Established area, green spaces, Beverly Hills prestige, proximity to Smart Village",
        "selling_points": [
            "Allegria and Beverly Hills (ultra-luxury)",
            "Smart Village for tech professionals",
            "Mall of Egypt and Arkan Plaza",
            "Green spaces and lower density",
            "Established infrastructure",
            "High-end dining and entertainment"
        ],
        "typical_buyer": "Wealthy families, business owners, tech professionals, investors",
        "price_range": "45,000-80,000 EGP/sqm (up to 150,000 in Beverly Hills)",
        "growth_trend": "Steady growth, 8-10% annual appreciation",
        "objections": {
            "too_expensive": "Best appreciation rates in Greater Cairo. Sheikh Zayed is where serious wealth protects itself from inflation.",
            "traffic_issues": "New ring road expansions have improved traffic significantly. Plus, most amenities are within the area.",
            "limited_supply": "That's exactly why it's valuable - scarcity drives demand. Properties here rarely come to market."
        },
        "hot_compounds": ["Beverly Hills", "Allegria", "West Town", "Palm Hills", "Sodic West"]
    },

    "6th October": {
        "buyer_motivation": "Affordable prices, industrial zone proximity, good payment plans",
        "selling_points": [
            "Most affordable prices in Greater Cairo",
            "Flexible payment plans (10+ years)",
            "Smart Village and industrial zones nearby",
            "Growing infrastructure",
            "Good for first-time buyers",
            "Strong rental demand from factory workers"
        ],
        "typical_buyer": "First-time buyers, middle class, factory workers, investors (rental yield)",
        "price_range": "15,000-30,000 EGP/sqm",
        "growth_trend": "Moderate growth, 6-8% annual appreciation",
        "objections": {
            "industrial_area": "New compounds are far from factories. Plus, proximity to jobs means strong rental demand.",
            "basic_amenities": "Rapidly developing - Mall of Arabia and new entertainment coming soon. Perfect opportunity to buy before prices rise.",
            "lower_status": "Smart investment is about ROI, not status. 6th October offers best rental yield in Greater Cairo (8-10%)."
        },
        "hot_compounds": ["Dreamland", "Beverly Hills", "Palm Hills October", "Hadayek October", "Zayed Dunes"]
    },

    "New Capital": {
        "buyer_motivation": "New city, government backing, high appreciation potential, future vision",
        "selling_points": [
            "Government administrative district",
            "Iconic Tower (tallest in Africa)",
            "Smart city infrastructure",
            "Massive government investment",
            "Future central business district",
            "Potential for 100%+ appreciation"
        ],
        "typical_buyer": "Investors, early adopters, government employees, speculators",
        "price_range": "25,000-50,000 EGP/sqm (varies widely)",
        "growth_trend": "Very high potential, 20-30% expected appreciation",
        "objections": {
            "still_under_construction": "That's exactly why prices are still reasonable. Buy now before completion and prices double.",
            "no_services_yet": "Government moving in 2024. Services follow government. This is a 5-10 year investment, not immediate living.",
            "too_risky": "Government backing means lowest risk for new development. Egypt's future capital is not a gamble."
        },
        "hot_compounds": ["Capital Gardens", "Entrada", "IL Bosco City", "Jefaira", "North Investors"]
    },

    "Mostakbal City": {
        "buyer_motivation": "New development, modern planning, good value, family-friendly",
        "selling_points": [
            "Planned community with modern infrastructure",
            "Good value compared to New Cairo",
            "Family-friendly compounds",
            "Easy payment plans",
            "Close to New Cairo amenities",
            "Growing rapidly"
        ],
        "typical_buyer": "Young families, first-time buyers, investors",
        "price_range": "25,000-40,000 EGP/sqm",
        "growth_trend": "High growth, 10-12% annual appreciation",
        "objections": {
            "too_new": "Newest doesn't mean riskiest - means modern planning and no legacy infrastructure problems.",
            "far_from_cairo": "That's the point - quiet family living with easy access to Cairo. Best of both worlds.",
            "unknown_area": "Backed by major developers (Golden Square). Unknown means undiscovered opportunity."
        },
        "hot_compounds": ["Solana", "Sarai", "Mountain View ICity", "Bloomfields", "Latin Quarter"]
    }
}

EGYPTIAN_SALES_OBJECTIONS = {
    "price_too_high": {
        "arabic_response": "فهمتك تماماً. خلينا نشوف خيارات الدفع. في خطط تقسيط تخليك تدفع {monthly} جنيه بس شهرياً على {years} سنة. أقل من إيجار شقة في نفس المنطقة!",
        "english_response": "I understand. Let's explore payment plans. You can pay just {monthly} EGP monthly over {years} years - less than renting in the same area!",
        "action": "show_payment_timeline",
        "reframing": "Compare monthly payment to rent cost, emphasize ownership benefits"
    },

    "need_to_think": {
        "arabic_response": "طبعاً! قرار مهم زي ده لازم تفكر فيه كويس. عايز أساعدك بإيه علشان تكون صورة أوضح؟ ممكن أعملك مقارنة مع عقارات تانية أو أحسب ROI؟",
        "english_response": "Absolutely! This is a major decision. How can I help you get clarity? I can compare other properties or calculate ROI projections.",
        "action": "offer_comparison_or_analysis",
        "reframing": "Offer to provide more information, not pressure. Build trust."
    },

    "location_concerns": {
        "arabic_response": "ممتاز إنك بتسأل عن المنطقة. خليني أوريك تحليل السوق لـ {location}. المنطقة دي نموها {growth}% في السنة الأخيرة.",
        "english_response": "Great question about the location. Let me show you market analysis for {location}. This area has grown {growth}% in the last year.",
        "action": "show_market_trends",
        "reframing": "Location concerns are actually opportunities if data shows growth"
    },

    "want_to_see_more_options": {
        "arabic_response": "طبعاً! خليني أوريك مقارنة بين أفضل 3 عقارات ناسبين ميزانيتك. كده هتقدر تشوف الفروقات بوضوح.",
        "english_response": "Of course! Let me show you a comparison of the top 3 properties matching your budget. This will help you see the differences clearly.",
        "action": "show_comparison_matrix",
        "reframing": "More options is good, but guide with structured comparison"
    },

    "timing_not_right": {
        "arabic_response": "فاهم. بس خليني أقولك حاجة: أسعار العقارات في مصر بتزيد باستمرار. العقار ده ممكن يزيد 10-15% في السنة الجاية. لو مستني، ممكن تدفع أكتر بكتير.",
        "english_response": "I understand. But let me tell you something: property prices in Egypt are constantly rising. This property could increase 10-15% next year. If you wait, you might pay significantly more.",
        "action": "show_price_appreciation_trends",
        "reframing": "Timing concerns addressed with opportunity cost of waiting"
    },

    "need_family_approval": {
        "arabic_response": "طبيعي جداً! قرار العقار قرار عائلي. ممكن أعملك ملف PDF كامل بكل تفاصيل العقار علشان تعرضه على عائلتك؟ أو ممكن نعمل meeting مع العائلة؟",
        "english_response": "Completely normal! Property decisions are family decisions. Can I create a complete PDF with all property details for you to show your family? Or we can schedule a family meeting?",
        "action": "prepare_family_presentation",
        "reframing": "Support the family decision process, don't fight it"
    },

    "developer_reputation_concerns": {
        "arabic_response": "سؤال مهم جداً! المطور ده هو {developer}، عندهم سجل حافل. خليني أوريك مشاريعهم السابقة وتقييمات العملاء.",
        "english_response": "Very important question! The developer is {developer}, they have an excellent track record. Let me show you their previous projects and customer reviews.",
        "action": "show_developer_portfolio",
        "reframing": "Developer reputation is data-driven, not opinion"
    },

    "contract_legal_concerns": {
        "arabic_response": "حقك تماماً تتأكد! العقد بيتبع القانون المصري 114. ممكن تاخد العقد تراجعه مع محامي، أو أنا ممكن أشرحلك كل بند فيه.",
        "english_response": "Absolutely right to verify! The contract follows Egyptian Law 114. You can take the contract to review with a lawyer, or I can explain every clause to you.",
        "action": "explain_contract_clause_by_clause",
        "reframing": "Legal concerns are resolved with transparency and lawyer option"
    }
}

MARKET_TRENDS_EGYPT = {
    "2024_overview": {
        "avg_appreciation": "10-12% annually",
        "hot_areas": ["New Cairo", "Mostakbal City", "New Capital"],
        "stable_areas": ["Sheikh Zayed", "Maadi", "Zamalek"],
        "emerging_areas": ["6th October extensions", "Shorouk City", "Obour City"],
        "price_per_sqm_avg": {
            "luxury": "60,000-150,000 EGP/sqm",
            "mid_range": "30,000-60,000 EGP/sqm",
            "affordable": "15,000-30,000 EGP/sqm"
        }
    },

    "factors_driving_growth": [
        "Currency devaluation making real estate hedge against inflation",
        "Population growth in Greater Cairo (500K+ annually)",
        "Government infrastructure projects (New Capital, Monorail)",
        "Limited supply in established areas",
        "Rising rent costs making ownership attractive",
        "Diaspora Egyptian investment increasing"
    ],

    "payment_trends": {
        "down_payment": "10-20% typical",
        "installment_years": "5-8 years most common",
        "interest_rates": "CBE base rate + 3-5% margin",
        "developer_financing": "Often better than bank loans"
    }
}

def get_buyer_persona(conversation_context: dict) -> str:
    """
    Determine buyer persona from conversation context.

    Args:
        conversation_context: Dictionary with keys like 'budget', 'questions_asked', 'concerns'

    Returns:
        Persona key from EGYPTIAN_BUYER_PERSONAS
    """
    budget = conversation_context.get('budget', 0)
    questions = conversation_context.get('questions_asked', [])

    # Budget-based initial classification
    if budget > 0:
        if budget > 5000000:  # 5M+ EGP
            return "upgrader"
        elif budget < 3000000:  # < 3M EGP
            return "first_time_buyer"

    # Question-based classification
    roi_questions = ["roi", "return", "investment", "rental", "yield"]
    if any(q in str(questions).lower() for q in roi_questions):
        return "investor"

    family_questions = ["school", "family", "kids", "safe", "hospital"]
    if any(q in str(questions).lower() for q in family_questions):
        return "first_time_buyer"

    # Default
    return "first_time_buyer"


def get_location_insights(location: str) -> dict:
    """
    Get psychological insights for a specific location.

    Args:
        location: Location name (e.g., "New Cairo", "Sheikh Zayed")

    Returns:
        Dictionary with location psychology data
    """
    # Normalize location name
    location_normalized = location.strip().title()

    # Direct match
    if location_normalized in LOCATION_PSYCHOLOGY:
        return LOCATION_PSYCHOLOGY[location_normalized]

    # Partial match
    for loc_key, loc_data in LOCATION_PSYCHOLOGY.items():
        if loc_key.lower() in location.lower() or location.lower() in loc_key.lower():
            return loc_data

    # Default fallback
    return {
        "buyer_motivation": "Good location with growth potential",
        "selling_points": ["Developing area", "Good value", "Future potential"],
        "typical_buyer": "Investors and families",
        "price_range": "Varies",
        "growth_trend": "Market average",
        "objections": {},
        "hot_compounds": []
    }


def handle_objection(objection_type: str, context: dict = None) -> dict:
    """
    Get Egyptian-market-appropriate response to objection.

    Args:
        objection_type: Key from EGYPTIAN_SALES_OBJECTIONS
        context: Optional context dict with placeholders like {monthly}, {years}

    Returns:
        Dictionary with arabic_response, english_response, action, reframing
    """
    if objection_type in EGYPTIAN_SALES_OBJECTIONS:
        response = EGYPTIAN_SALES_OBJECTIONS[objection_type].copy()

        # Fill in placeholders if context provided
        if context:
            if 'arabic_response' in response:
                response['arabic_response'] = response['arabic_response'].format(**context)
            if 'english_response' in response:
                response['english_response'] = response['english_response'].format(**context)

        return response

    # Default response
    return {
        "arabic_response": "فهمت قلقك. خليني أساعدك أفهم الموضوع أكتر.",
        "english_response": "I understand your concern. Let me help you understand this better.",
        "action": "provide_more_information",
        "reframing": "Convert concern into opportunity for education"
    }
