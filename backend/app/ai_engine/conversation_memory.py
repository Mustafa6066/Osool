"""
Osool Conversation Memory Engine
---------------------------------
Tracks key facts across conversation turns to make AMR smarter.
Extracts and remembers budget, preferences, objections, and shown properties.
"""

import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Cross-turn and cross-session fact extraction and memory for AMR."""

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
        if not self.investment_vs_living and other.investment_vs_living:
            self.investment_vs_living = other.investment_vs_living
        if not self.family_size and other.family_size:
            self.family_size = other.family_size

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

        if ai_analysis:
            filters = ai_analysis.get('filters', {})
            if filters.get('location') and filters['location'] not in self.preferred_areas:
                self.preferred_areas.append(filters['location'])
            if filters.get('budget_max') and not self.budget_range:
                self.budget_range = {'min': filters.get('budget_min', 0), 'max': filters['budget_max']}

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

        return '\n'.join(parts)

    def _extract_budget(self, message: str):
        """Extract budget information from message."""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:مليون|million|مليار|billion|M\b)',
            r'(?:budget|ميزانية|ميزانيتي)\s*(?:is|حوالي|تقريبا|من)?\s*(\d+(?:\.\d+)?)',
            r'(?:من|from)\s*(\d+(?:\.\d+)?)\s*(?:مليون|million|M)?\s*(?:ل|لـ|to|إلى)\s*(\d+(?:\.\d+)?)\s*(?:مليون|million|M)?',
            r'(?:تحت|under|less than|أقل من)\s*(\d+(?:\.\d+)?)\s*(?:مليون|million|M)?',
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 2 and groups[1]:
                        min_val = float(groups[0]) * 1_000_000
                        max_val = float(groups[1]) * 1_000_000
                        self.budget_range = {'min': int(min_val), 'max': int(max_val)}
                    elif len(groups) >= 1 and groups[0]:
                        val = float(groups[0]) * 1_000_000
                        if 'تحت' in message or 'under' in message.lower():
                            self.budget_range = {'min': 0, 'max': int(val)}
                        elif not self.budget_range:
                            self.budget_range = {'min': 0, 'max': int(val)}
                except (ValueError, IndexError):
                    pass
                break

    def _extract_areas(self, msg_lower: str):
        """Extract area preferences."""
        area_map = {
            'التجمع': 'New Cairo', 'القاهرة الجديدة': 'New Cairo', 'new cairo': 'New Cairo',
            'زايد': 'Sheikh Zayed', 'الشيخ زايد': 'Sheikh Zayed', 'sheikh zayed': 'Sheikh Zayed',
            'أكتوبر': '6th October', '6th october': '6th October', 'اكتوبر': '6th October',
            'العاصمة': 'New Capital', 'العاصمة الإدارية': 'New Capital', 'new capital': 'New Capital',
            'الساحل': 'North Coast', 'الساحل الشمالي': 'North Coast', 'north coast': 'North Coast',
            'مدينتي': 'Madinaty', 'madinaty': 'Madinaty',
            'المعادي': 'Maadi', 'maadi': 'Maadi',
            'مصر الجديدة': 'Heliopolis', 'heliopolis': 'Heliopolis',
        }

        for keyword, area in area_map.items():
            if keyword in msg_lower and area not in self.preferred_areas:
                self.preferred_areas.append(area)

    def _extract_purpose(self, msg_lower: str):
        """Extract investment vs living purpose."""
        investment_keywords = ['استثمار', 'investment', 'عائد', 'return', 'roi', 'إيجار', 'rental', 'ربح', 'profit']
        living_keywords = ['سكن', 'living', 'عايش', 'أسكن', 'عائلة', 'family', 'أولاد', 'kids', 'children']

        has_investment = any(kw in msg_lower for kw in investment_keywords)
        has_living = any(kw in msg_lower for kw in living_keywords)

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
