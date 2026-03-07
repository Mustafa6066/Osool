"""
Osool Conversation Memory Engine V2
-------------------------------------
Tracks key facts across conversation turns to make CoInvestor smarter.
Extracts and remembers budget, preferences, objections, and shown properties.

V2 Enhancements:
- Emotional journey tracking (turn-by-turn emotional state recording)
- Objection resolution tracking (raised vs. resolved objections)
- Commitment level (0-100 micro-commitment score)
- Competitor mentions (track what user is comparing to)
- Family members mentioned (individual stakeholder tracking)
- Preferred payment structure (down payment, installment preference)
- Visit scheduling state
- Properties liked/rejected with reasons
- Cross-session strategy intelligence
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CrossSessionIntelligence:
    """Analyze return behavior patterns to adapt sales strategy."""

    @staticmethod
    def analyze_return_behavior(
        last_session_time: Optional[str],
        current_time: Optional[datetime] = None,
        previous_sessions_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Determine user's return pattern and adapt strategy.

        Return types:
        - hot_return (<24h): High intent, push for close
        - comparison_return (1-7d): Comparing options, differentiate
        - cold_return (>30d): Re-engage, refresh context
        - fresh_start: First session
        """
        if not last_session_time:
            return {
                "return_type": "fresh_start",
                "strategy_hint": "discovery",
                "message_ar": "أهلاً بيك في أصول! خليني أساعدك تلاقي أحسن فرصة.",
                "message_en": "Welcome to Osool! Let me help you find the best opportunity.",
                "sessions_count": 0,
            }

        now = current_time or datetime.utcnow()
        try:
            last_dt = datetime.fromisoformat(last_session_time.replace("Z", "+00:00"))
            if last_dt.tzinfo:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            hours_since = (now - last_dt).total_seconds() / 3600
        except Exception:
            hours_since = 999

        if hours_since < 24:
            return {
                "return_type": "hot_return",
                "hours_since": round(hours_since, 1),
                "strategy_hint": "close",
                "message_ar": "رجعت بسرعة! يبان إنك مهتم جداً. خلينا نكمل من حيث وقفنا.",
                "message_en": "You're back quickly! Seems like you're very interested. Let's pick up where we left off.",
                "sessions_count": previous_sessions_count,
            }
        elif hours_since < 168:  # 7 days
            return {
                "return_type": "comparison_return",
                "hours_since": round(hours_since, 1),
                "strategy_hint": "differentiate",
                "message_ar": "نورت تاني! لو كنت بتقارن عروض، خليني أوريك ليه اختياراتنا أحسن.",
                "message_en": "Welcome back! If you've been comparing, let me show you why our picks stand out.",
                "sessions_count": previous_sessions_count,
            }
        elif hours_since < 720:  # 30 days
            return {
                "return_type": "warm_return",
                "hours_since": round(hours_since, 1),
                "strategy_hint": "re_engage",
                "message_ar": "وحشتنا! السوق اتغير شوية من آخر مرة. خليني أورديك الجديد.",
                "message_en": "We missed you! The market has shifted since your last visit. Let me update you.",
                "sessions_count": previous_sessions_count,
            }
        else:
            return {
                "return_type": "cold_return",
                "hours_since": round(hours_since, 1),
                "strategy_hint": "re_discover",
                "message_ar": "أهلاً تاني! عدى وقت من آخر زيارة. عايز نبدأ من الأول ولا نكمل؟",
                "message_en": "Welcome back! It's been a while. Want to start fresh or continue where we left off?",
                "sessions_count": previous_sessions_count,
            }


class ConversationMemory:
    """Cross-turn and cross-session fact extraction and memory for CoInvestor (V2)."""

    def __init__(self):
        self.budget_range: Optional[Dict[str, int]] = None  # {'min': X, 'max': Y}
        self.preferred_areas: List[str] = []
        self.preferred_developers: List[str] = []
        self.deal_breakers: List[str] = []
        self.shown_properties: List[Dict] = []
        self.liked_properties: List[str] = []
        self.objections_raised: List[str] = []
        self.timeline: Optional[str] = None
        self.family_size: Optional[int] = None
        self.investment_vs_living: Optional[str] = None  # 'investment' | 'living' | 'both'
        self.discovery_answers: Dict[str, str] = {}
        self.preferences: List[str] = []  # Free-text preferences ("wife hates open kitchens")

        # ═══ V2 Enhanced Memory Fields ═══
        self.emotional_journey: List[Dict] = []  # [{"turn": N, "state": "fomo", "intensity": 0.7}]
        self.objections_resolved: Dict[str, bool] = {}  # {"price": True, "delivery": False}
        self.commitment_level: int = 0  # 0-100 micro-commitment score
        self.competitors_mentioned: List[str] = []  # ["Nawy", "Aqarmap"]
        self.family_members_mentioned: List[str] = []  # ["wife", "father"]
        self.preferred_payment: Optional[Dict] = None  # {"down_pct": 10, "years": 8, "quarterly": True}
        self.visit_scheduled: bool = False
        self.properties_liked_with_reasons: List[Dict] = []  # [{"title": "X", "reason": "good view"}]
        self.properties_rejected_with_reasons: List[Dict] = []  # [{"title": "X", "reason": "too far"}]
        self.last_session_time: Optional[str] = None  # ISO timestamp
        self.session_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMemory':
        """Hydrate memory from a saved dict (e.g., from DB JSON)."""
        mem = cls()
        if not data:
            return mem
        mem.budget_range = data.get('budget_range')
        mem.preferred_areas = data.get('preferred_areas', [])
        mem.preferred_developers = data.get('preferred_developers', [])
        mem.deal_breakers = data.get('deal_breakers', [])
        mem.liked_properties = data.get('liked_properties', [])
        mem.objections_raised = data.get('objections_raised', [])
        mem.timeline = data.get('timeline')
        mem.family_size = data.get('family_size')
        mem.investment_vs_living = data.get('investment_vs_living')
        mem.discovery_answers = data.get('discovery_answers', {})
        mem.preferences = data.get('preferences', [])
        # V2 fields
        mem.emotional_journey = data.get('emotional_journey', [])
        mem.objections_resolved = data.get('objections_resolved', {})
        mem.commitment_level = data.get('commitment_level', 0)
        mem.competitors_mentioned = data.get('competitors_mentioned', [])
        mem.family_members_mentioned = data.get('family_members_mentioned', [])
        mem.preferred_payment = data.get('preferred_payment')
        mem.visit_scheduled = data.get('visit_scheduled', False)
        mem.properties_liked_with_reasons = data.get('properties_liked_with_reasons', [])
        mem.properties_rejected_with_reasons = data.get('properties_rejected_with_reasons', [])
        mem.last_session_time = data.get('last_session_time')
        mem.session_count = data.get('session_count', 0)
        return mem

    def merge(self, other: 'ConversationMemory'):
        """Merge another memory (e.g., from DB) into this one. Current session wins on conflicts."""
        # Budget: current session wins if set
        if not self.budget_range and other.budget_range:
            self.budget_range = other.budget_range
        # Lists: union without duplicates
        for area in other.preferred_areas:
            if area not in self.preferred_areas:
                self.preferred_areas.append(area)
        for dev in other.preferred_developers:
            if dev not in self.preferred_developers:
                self.preferred_developers.append(dev)
        for db in other.deal_breakers:
            if db not in self.deal_breakers:
                self.deal_breakers.append(db)
        for lp in other.liked_properties:
            if lp not in self.liked_properties:
                self.liked_properties.append(lp)
        for obj in other.objections_raised:
            if obj not in self.objections_raised:
                self.objections_raised.append(obj)
        for pref in other.preferences:
            if pref not in self.preferences:
                self.preferences.append(pref)
        # Scalars: current session wins if set
        if not self.timeline and other.timeline:
            self.timeline = other.timeline
        # V4 FIX: Allow purpose correction — latest session wins, not first-write-wins
        if other.investment_vs_living:
            self.investment_vs_living = other.investment_vs_living
        if not self.family_size and other.family_size:
            self.family_size = other.family_size

        # V2 merge: union lists, preserve scores
        for comp in other.competitors_mentioned:
            if comp not in self.competitors_mentioned:
                self.competitors_mentioned.append(comp)
        for fam in other.family_members_mentioned:
            if fam not in self.family_members_mentioned:
                self.family_members_mentioned.append(fam)
        # Emotional journey: append previous session's journey
        if other.emotional_journey:
            self.emotional_journey = other.emotional_journey + self.emotional_journey
        # Objection resolution: merge (current wins on conflict)
        for obj_key, resolved in other.objections_resolved.items():
            if obj_key not in self.objections_resolved:
                self.objections_resolved[obj_key] = resolved
        # Commitment: take maximum (progress should never decrease)
        self.commitment_level = max(self.commitment_level, other.commitment_level)
        # Payment preference: current session wins
        if not self.preferred_payment and other.preferred_payment:
            self.preferred_payment = other.preferred_payment
        # Visit: once scheduled, stays true
        if other.visit_scheduled:
            self.visit_scheduled = True
        # Properties liked/rejected with reasons: union by title
        existing_liked_titles = {p.get("title") for p in self.properties_liked_with_reasons}
        for entry in other.properties_liked_with_reasons:
            if entry.get("title") not in existing_liked_titles:
                self.properties_liked_with_reasons.append(entry)
        existing_rejected_titles = {p.get("title") for p in self.properties_rejected_with_reasons}
        for entry in other.properties_rejected_with_reasons:
            if entry.get("title") not in existing_rejected_titles:
                self.properties_rejected_with_reasons.append(entry)
        # Shown properties: union by id/title to avoid re-showing
        existing_shown_ids = {p.get("id", p.get("title", "")) for p in self.shown_properties}
        for prop in other.shown_properties:
            prop_key = prop.get("id", prop.get("title", ""))
            if prop_key and prop_key not in existing_shown_ids:
                self.shown_properties.append(prop)
        # Cross-session: carry over
        if not self.last_session_time and other.last_session_time:
            self.last_session_time = other.last_session_time
        self.session_count = max(self.session_count, other.session_count)

    def extract_from_message(self, message: str, ai_analysis: Optional[Dict] = None):
        """Extract and remember key facts from each exchange."""
        if not message:
            return

        msg_lower = message.lower()

        self._extract_budget(message)
        self._extract_areas(msg_lower)
        self._extract_purpose(msg_lower)
        self._extract_objections(msg_lower)
        self._extract_timeline(msg_lower)
        # V2 extractors
        self._extract_competitors(msg_lower)
        self._extract_family_members(msg_lower)
        self._extract_payment_preferences(msg_lower)
        self._extract_visit_intent(msg_lower)

        if ai_analysis:
            filters = ai_analysis.get('filters', {})
            if filters.get('location') and filters['location'] not in self.preferred_areas:
                self.preferred_areas.append(filters['location'])
            if filters.get('budget_max') and not self.budget_range:
                self.budget_range = {'min': filters.get('budget_min', 0), 'max': filters['budget_max']}
            # V4 FIX: Use GPT-4o's purpose field — it understands Arabic negation
            gpt_purpose = filters.get('purpose')
            if gpt_purpose and gpt_purpose in ('investment', 'living', 'rental', 'both'):
                # GPT's structured output is more reliable than regex for purpose
                self.investment_vs_living = gpt_purpose

    def record_shown_properties(self, properties: List[Dict]):
        """Record properties that were shown to the user."""
        for prop in properties:
            prop_id = prop.get('id') or prop.get('title', '')
            if prop_id and prop_id not in [p.get('id', p.get('title', '')) for p in self.shown_properties]:
                self.shown_properties.append(prop)

    def record_liked_property(self, property_title: str):
        """Record when a user shows interest in a property."""
        if property_title and property_title not in self.liked_properties:
            self.liked_properties.append(property_title)

    def get_context_summary(self) -> str:
        """Return a concise summary for the AI prompt context."""
        parts = ["CUSTOMER PROFILE (from conversation):"]

        if self.budget_range:
            min_m = self.budget_range.get('min', 0) / 1_000_000
            max_m = self.budget_range.get('max', 0) / 1_000_000
            if min_m > 0 and max_m > 0:
                parts.append(f"- Budget: {min_m:.1f}M - {max_m:.1f}M EGP")
            elif max_m > 0:
                parts.append(f"- Budget: Up to {max_m:.1f}M EGP")
            else:
                parts.append("- Budget: Not specified yet - ASK")
        else:
            parts.append("- Budget: Not specified yet - ASK")

        parts.append(f"- Areas: {', '.join(self.preferred_areas) if self.preferred_areas else 'Not specified'}")
        parts.append(f"- Purpose: {self.investment_vs_living or 'Not specified - ASK'}")
        parts.append(f"- Liked: {', '.join(self.liked_properties) if self.liked_properties else 'None shown yet'}")
        parts.append(f"- Objections: {', '.join(self.objections_raised) if self.objections_raised else 'None'}")
        parts.append(f"- Timeline: {self.timeline or 'Not specified'}")
        parts.append(f"- Properties shown: {len(self.shown_properties)}")
        if self.preferences:
            parts.append(f"- Key Preferences: {'; '.join(self.preferences)}")

        # V2 enhanced context
        if self.commitment_level > 0:
            parts.append(f"- Commitment Level: {self.commitment_level}/100")
        if self.competitors_mentioned:
            parts.append(f"- Competitors Compared: {', '.join(self.competitors_mentioned)}")
        if self.family_members_mentioned:
            parts.append(f"- Family Stakeholders: {', '.join(self.family_members_mentioned)}")
        if self.preferred_payment:
            dp = self.preferred_payment.get('down_pct', '?')
            yrs = self.preferred_payment.get('years', '?')
            parts.append(f"- Payment Preference: {dp}% down, {yrs} years")
        if self.visit_scheduled:
            parts.append("- Visit: SCHEDULED ✓")
        if self.objections_resolved:
            resolved = [k for k, v in self.objections_resolved.items() if v]
            unresolved = [k for k, v in self.objections_resolved.items() if not v]
            if resolved:
                parts.append(f"- Objections Resolved: {', '.join(resolved)}")
            if unresolved:
                parts.append(f"- Objections UNRESOLVED: {', '.join(unresolved)}")
        if self.emotional_journey:
            recent = self.emotional_journey[-3:]
            journey_str = " → ".join(e.get('state', '?') for e in recent)
            parts.append(f"- Emotional Journey (recent): {journey_str}")

        return '\n'.join(parts)

    def _extract_budget(self, message: str):
        """Extract budget information from message.
        Supports: Arabic (مليون), English (million/M), Franco-Arab (melyoon/malyoon).
        """
        # Normalize Franco-Arab budget words to standard form
        msg_normalized = message.lower()
        msg_normalized = re.sub(r'\bmelyoon\b|\bmalyoon\b|\bmelyon\b', 'مليون', msg_normalized)

        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:مليون|million|مليار|billion|M\b)',
            r'(?:budget|ميزانية|ميزانيتي|mizaneyty|mizanyti)\s*(?:is|حوالي|تقريبا|من|7awaly)?\s*(\d+(?:\.\d+)?)',
            r'(?:من|from)\s*(\d+(?:\.\d+)?)\s*(?:مليون|million|M)?\s*(?:ل|لـ|to|إلى|le|l)\s*(\d+(?:\.\d+)?)\s*(?:مليون|million|M)?',
            r'(?:تحت|under|less than|أقل من|a2al men)\s*(\d+(?:\.\d+)?)\s*(?:مليون|million|M)?',
            # Full EGP amounts (e.g., "5000000" or "5,000,000")
            r'(\d{1,3}(?:,\d{3})+)\s*(?:جنيه|egp|EGP|pound)',
        ]

        for pattern in patterns:
            match = re.search(pattern, msg_normalized, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 2 and groups[1]:
                        min_val = float(groups[0]) * 1_000_000
                        max_val = float(groups[1]) * 1_000_000
                        self.budget_range = {'min': int(min_val), 'max': int(max_val)}
                    elif len(groups) >= 1 and groups[0]:
                        raw = groups[0].replace(',', '')
                        val = float(raw)
                        # If number is > 100000, treat as raw EGP, not millions
                        if val > 100000:
                            budget_val = int(val)
                        else:
                            budget_val = int(val * 1_000_000)
                        if 'تحت' in msg_normalized or 'under' in msg_normalized or 'a2al' in msg_normalized:
                            self.budget_range = {'min': 0, 'max': budget_val}
                        elif not self.budget_range:
                            self.budget_range = {'min': 0, 'max': budget_val}
                except (ValueError, IndexError):
                    pass
                break

    def _extract_areas(self, msg_lower: str):
        """Extract area preferences. Supports Arabic, English, and Franco-Arab."""
        area_map = {
            # Arabic
            'التجمع': 'New Cairo', 'القاهرة الجديدة': 'New Cairo', 'new cairo': 'New Cairo',
            'زايد': 'Sheikh Zayed', 'الشيخ زايد': 'Sheikh Zayed', 'sheikh zayed': 'Sheikh Zayed',
            'أكتوبر': '6th October', '6th october': '6th October', 'اكتوبر': '6th October',
            'العاصمة': 'New Capital', 'العاصمة الإدارية': 'New Capital', 'new capital': 'New Capital',
            'الساحل': 'North Coast', 'الساحل الشمالي': 'North Coast', 'north coast': 'North Coast',
            'مدينتي': 'Madinaty', 'madinaty': 'Madinaty',
            'المعادي': 'Maadi', 'maadi': 'Maadi',
            'مصر الجديدة': 'Heliopolis', 'heliopolis': 'Heliopolis',
            'السخنة': 'Ain Sokhna', 'ain sokhna': 'Ain Sokhna', 'sokhna': 'Ain Sokhna',
            'الرحاب': 'Rehab', 'rehab': 'Rehab',
            # Franco-Arab (Arabizi)
            'tagamo3': 'New Cairo', 'tagammo3': 'New Cairo', 'el tagamo3': 'New Cairo',
            'el sahel': 'North Coast', 'sahel': 'North Coast',
            'el sokhna': 'Ain Sokhna', '3ein sokhna': 'Ain Sokhna',
            'el ma3ady': 'Maadi', 'ma3adi': 'Maadi',
            'oktobar': '6th October', 'october': '6th October',
            'el 3asma': 'New Capital', '3asma': 'New Capital',
            'mostakbal': 'Mostakbal City', 'mostaqbal': 'Mostakbal City',
            'madinity': 'Madinaty',
        }

        for keyword, area in area_map.items():
            if keyword in msg_lower and area not in self.preferred_areas:
                self.preferred_areas.append(area)

    def _extract_purpose(self, msg_lower: str):
        """Extract investment vs living purpose with negation awareness."""
        import re
        # Arabic negation patterns: مش، مو، لا، بلاش
        # Must be standalone words (preceded by space/start, followed by space)
        # to avoid false matches inside words like وكمان, مثلاً, لأن
        _NEGATION_RE = re.compile(r'(?:^|\s)(?:مش|مو|ما|لا|بلاش|مني)\s')

        investment_keywords = [
            'استثمار', 'أستثمر', 'استثمر', 'بستثمر', 'هستثمر', 'نستثمر',
            'investment', 'invest',
            'عائد', 'return', 'roi', 'إيجار', 'rental', 'ربح', 'profit',
            'محفظة', 'portfolio', 'yield', 'كام في السنة'
        ]
        living_keywords = [
            'سكن', 'أسكن', 'هسكن', 'بسكن', 'نسكن', 'عايش', 'هعيش',
            'living', 'live in',
            'عائلة', 'family', 'أولاد', 'kids', 'children'
        ]

        def _keyword_active(kw: str) -> bool:
            """Check if keyword appears AND is NOT negated."""
            idx = msg_lower.find(kw)
            if idx < 0:
                return False
            # Check the ~20 chars before the keyword for negation
            prefix = msg_lower[max(0, idx - 20):idx]
            if _NEGATION_RE.search(prefix):
                return False  # Keyword is negated
            return True

        has_investment = any(_keyword_active(kw) for kw in investment_keywords)
        has_living = any(_keyword_active(kw) for kw in living_keywords)

        if has_investment and has_living:
            self.investment_vs_living = 'both'
        elif has_investment:
            self.investment_vs_living = 'investment'
        elif has_living:
            self.investment_vs_living = 'living'

    def _extract_objections(self, msg_lower: str):
        """Extract objections from message."""
        objection_patterns = {
            'غالي': 'price', 'expensive': 'price', 'مكلف': 'price',
            'مش متأكد': 'uncertainty', 'not sure': 'uncertainty',
            'هفكر': 'delay', 'let me think': 'delay', 'محتاج وقت': 'delay',
            'في أرخص': 'price_comparison', 'cheaper': 'price_comparison',
            'بعيد': 'location', 'far': 'location',
            'صغير': 'size', 'small': 'size', 'too small': 'size',
        }

        for keyword, objection_type in objection_patterns.items():
            if keyword in msg_lower and objection_type not in self.objections_raised:
                self.objections_raised.append(objection_type)

    def _extract_timeline(self, msg_lower: str):
        """Extract timeline/urgency."""
        if any(kw in msg_lower for kw in ['فوري', 'immediately', 'دلوقتي', 'now', 'urgent', 'ضروري']):
            self.timeline = 'immediate'
        elif any(kw in msg_lower for kw in ['شهر', 'month', 'قريب', 'soon']):
            self.timeline = '1-3 months'
        elif any(kw in msg_lower for kw in ['سنة', 'year', 'بعدين', 'later']):
            self.timeline = '6-12 months'

    # ═══════════════════════════════════════════════════════════════
    # V2: NEW EXTRACTOR METHODS
    # ═══════════════════════════════════════════════════════════════

    def _extract_competitors(self, msg_lower: str):
        """Extract competitor platform mentions."""
        competitor_map = {
            'ناوي': 'Nawy', 'nawy': 'Nawy',
            'عقارماب': 'Aqarmap', 'aqarmap': 'Aqarmap',
            'أولكس': 'OLX', 'olx': 'OLX',
            'بروبرتي فايندر': 'Property Finder', 'property finder': 'Property Finder',
            'دوبيزل': 'Dubizzle', 'dubizzle': 'Dubizzle',
            'بيوت': 'Bayut', 'bayut': 'Bayut',
            'سمسار': 'Local Broker', 'broker': 'Local Broker',
        }
        for keyword, name in competitor_map.items():
            if keyword in msg_lower and name not in self.competitors_mentioned:
                self.competitors_mentioned.append(name)

    def _extract_family_members(self, msg_lower: str):
        """Extract family member mentions for committee mode."""
        family_map = {
            'مراتي': 'wife', 'زوجتي': 'wife', 'wife': 'wife', 'my wife': 'wife',
            'جوزي': 'husband', 'زوجي': 'husband', 'husband': 'husband',
            'أبويا': 'father', 'والدي': 'father', 'father': 'father', 'my dad': 'father',
            'أمي': 'mother', 'والدتي': 'mother', 'mother': 'mother', 'my mom': 'mother',
            'أخويا': 'brother', 'brother': 'brother',
            'أختي': 'sister', 'sister': 'sister',
            'ابني': 'son', 'son': 'son',
            'بنتي': 'daughter', 'daughter': 'daughter',
            'العيلة': 'family', 'family': 'family',
            'خطيبتي': 'fiancée', 'خطيبي': 'fiancé',
        }
        for keyword, member in family_map.items():
            if keyword in msg_lower and member not in self.family_members_mentioned:
                self.family_members_mentioned.append(member)

    def _extract_payment_preferences(self, msg_lower: str):
        """Extract installment/payment plan preferences."""
        # Down payment extraction
        dp_match = re.search(r'(?:مقدم|down\s*payment|dp)\s*(\d+)\s*%?', msg_lower)
        if dp_match:
            dp_val = int(dp_match.group(1))
            if dp_val <= 50:  # Reasonable down payment %
                if not self.preferred_payment:
                    self.preferred_payment = {}
                self.preferred_payment['down_pct'] = dp_val

        # Installment years extraction
        years_match = re.search(r'(\d+)\s*(?:سنة|سنين|year|years|سنوات)', msg_lower)
        if years_match:
            years_val = int(years_match.group(1))
            if 1 <= years_val <= 15:
                if not self.preferred_payment:
                    self.preferred_payment = {}
                self.preferred_payment['years'] = years_val

        # Quarterly / semi-annual preference
        if any(kw in msg_lower for kw in ['ربع سنوي', 'quarterly', 'كل 3 شهور']):
            if not self.preferred_payment:
                self.preferred_payment = {}
            self.preferred_payment['quarterly'] = True
        elif any(kw in msg_lower for kw in ['نص سنوي', 'semi-annual', 'كل 6 شهور']):
            if not self.preferred_payment:
                self.preferred_payment = {}
            self.preferred_payment['semi_annual'] = True

    def _extract_visit_intent(self, msg_lower: str):
        """Detect if user is scheduling or interested in a property visit."""
        visit_keywords = [
            'معاينة', 'زيارة', 'أشوف', 'أعاين', 'visit', 'see it',
            'viewing', 'show me in person', 'أروح', 'go there', 'site visit',
            'هروح', 'نشوفها', 'نزورها',
        ]
        if any(kw in msg_lower for kw in visit_keywords):
            self.visit_scheduled = True

    def record_emotional_state(self, turn_number: int, state: str, intensity: float = 0.5):
        """V2: Record emotional state for this turn."""
        self.emotional_journey.append({
            "turn": turn_number,
            "state": state,
            "intensity": round(intensity, 2),
            "timestamp": datetime.utcnow().isoformat(),
        })

    def resolve_objection(self, objection_type: str):
        """V2: Mark an objection as resolved."""
        self.objections_resolved[objection_type] = True

    def raise_objection(self, objection_type: str):
        """V2: Register a new objection."""
        if objection_type not in self.objections_resolved:
            self.objections_resolved[objection_type] = False
        if objection_type not in self.objections_raised:
            self.objections_raised.append(objection_type)

    def update_commitment(self, delta: int):
        """V2: Adjust commitment level (clamped 0-100)."""
        self.commitment_level = max(0, min(100, self.commitment_level + delta))

    def to_dict(self) -> Dict:
        """Serialize memory to dict."""
        return {
            'budget_range': self.budget_range,
            'preferred_areas': self.preferred_areas,
            'preferred_developers': self.preferred_developers,
            'deal_breakers': self.deal_breakers,
            'shown_properties_count': len(self.shown_properties),
            'liked_properties': self.liked_properties,
            'objections_raised': self.objections_raised,
            'timeline': self.timeline,
            'investment_vs_living': self.investment_vs_living,
            'preferences': self.preferences,
            # V2 fields
            'emotional_journey': self.emotional_journey,
            'objections_resolved': self.objections_resolved,
            'commitment_level': self.commitment_level,
            'competitors_mentioned': self.competitors_mentioned,
            'family_members_mentioned': self.family_members_mentioned,
            'preferred_payment': self.preferred_payment,
            'visit_scheduled': self.visit_scheduled,
            'properties_liked_with_reasons': self.properties_liked_with_reasons,
            'properties_rejected_with_reasons': self.properties_rejected_with_reasons,
            'last_session_time': self.last_session_time,
            'session_count': self.session_count,
        }

    def check_repetitive_loop(self, history: List[Dict], current_response: str) -> bool:
        """
        Check if the AI is stuck in a loop repeating the same content (Loop Trap Fix).
        Returns True if the response is dangerously similar to the last AI message.
        """
        if not history:
            return False
            
        last_ai_msg = next((m for m in reversed(history) if m.get("role") == "assistant"), None)
        if not last_ai_msg:
            return False
            
        last_content = last_ai_msg.get("content", "").strip().lower()
        current_content = current_response.strip().lower()
        
        if not last_content or not current_content:
            return False
            
        # 1. Exact match check
        if last_content == current_content:
            return True
            
        # 2. Sequence Matcher for similarity
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, last_content, current_content).ratio()
        
        # If > 85% similarity, it's a loop
        if similarity > 0.85:
            return True
            
        return False
