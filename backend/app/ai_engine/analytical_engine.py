"""
Analytical Engine - The Wolf's Ledger
-------------------------------------
Consolidated analytics functions for deal scoring, ROI calculation,
inflation hedging, and market analysis.

CRITICAL: Never let the LLM do math. All calculations are code-based.

Functions:
- calculate_true_roi(property): Rental yield + appreciation
- calculate_inflation_hedge(investment): Cash vs Property comparison
- score_property(property): Osool Score calculation
- detect_bargains(properties): Find below-market deals
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Market data constants (Egyptian market 2024-2025)
MARKET_DATA = {
    "inflation_rate": 0.33,           # 33% annual inflation
    "bank_cd_rate": 0.27,             # 27% bank CD interest
    "property_appreciation": 0.18,     # 18% annual property appreciation
    "rental_yield_avg": 0.065,         # 6.5% rental yield
    "rent_increase_rate": 0.10,        # 10% annual rent increase
    "gold_appreciation": 0.25,         # 25% annual gold appreciation
}

# Area price data (EGP per sqm, 2024)
AREA_PRICES = {
    "New Cairo": 65000,
    "Sheikh Zayed": 60000,
    "New Capital": 45000,
    "6th October": 35000,
    "North Coast": 80000,
    "Maadi": 70000,
    "Madinaty": 55000,
    "Rehab": 50000,
}

# Area growth rates
AREA_GROWTH = {
    "New Cairo": 0.15,
    "Sheikh Zayed": 0.12,
    "New Capital": 0.25,
    "6th October": 0.10,
    "North Coast": 0.20,
    "Maadi": 0.08,
    "Madinaty": 0.12,
    "Rehab": 0.10,
}

# ═══════════════════════════════════════════════════════════════
# COMPREHENSIVE AREA BENCHMARKS (Wolf Intelligence Layer)
# ═══════════════════════════════════════════════════════════════
AREA_BENCHMARKS = {
    "new cairo": {
        "ar_name": "التجمع الخامس",
        "avg_price_sqm": 65000,
        "rental_yield": 0.065,
        "growth_rate": 0.15,
        "property_minimums": {
            "apartment": 3_500_000,
            "villa": 12_000_000,
            "townhouse": 8_000_000,
            "duplex": 5_500_000,
        },
        "tier1_developers": ["اعمار", "سوديك", "ماونتن ڤيو", "بالم هيلز", "هايد بارك"],
        "tier2_developers": ["لافيستا", "تطوير مصر", "المقاصد"],
        "tier3_developers": ["كابيتال جروب", "السعودية المصرية"],
    },
    "sheikh zayed": {
        "ar_name": "الشيخ زايد",
        "avg_price_sqm": 72000,
        "rental_yield": 0.06,
        "growth_rate": 0.12,
        "property_minimums": {
            "apartment": 4_000_000,
            "villa": 15_000_000,
            "townhouse": 9_000_000,
            "duplex": 6_000_000,
        },
        "tier1_developers": ["سوديك", "أورا", "بالم هيلز", "إعمار"],
        "tier2_developers": ["زيد ويست", "O ويست"],
        "tier3_developers": [],
    },
    "new capital": {
        "ar_name": "العاصمة الإدارية",
        "avg_price_sqm": 45000,
        "rental_yield": 0.05,
        "growth_rate": 0.25,
        "property_minimums": {
            "apartment": 1_800_000,
            "villa": 6_000_000,
            "townhouse": 4_000_000,
            "duplex": 3_000_000,
        },
        "tier1_developers": ["المقاولون العرب", "المراسم"],
        "tier2_developers": ["مصر إيطاليا", "بيتر هوم"],
        "tier3_developers": ["كابيتال جروب"],
    },
    "6th october": {
        "ar_name": "السادس من أكتوبر",
        "avg_price_sqm": 35000,
        "rental_yield": 0.075,
        "growth_rate": 0.10,
        "property_minimums": {
            "apartment": 1_500_000,
            "villa": 5_000_000,
            "townhouse": 3_500_000,
            "duplex": 2_500_000,
        },
        "tier1_developers": ["بالم هيلز"],
        "tier2_developers": ["دريم لاند"],
        "tier3_developers": [],
    },
    "north coast": {
        "ar_name": "الساحل الشمالي",
        "avg_price_sqm": 80000,
        "rental_yield": 0.04,
        "growth_rate": 0.20,
        "property_minimums": {
            "chalet": 4_000_000,
            "villa": 20_000_000,
            "townhouse": 12_000_000,
        },
        "tier1_developers": ["اعمار", "سوديك", "ماونتن ڤيو", "سيتي إيدج"],
        "tier2_developers": ["لافيستا", "تطوير مصر"],
        "tier3_developers": [],
    },
    "maadi": {
        "ar_name": "المعادي",
        "avg_price_sqm": 70000,
        "rental_yield": 0.07,
        "growth_rate": 0.08,
        "property_minimums": {
            "apartment": 4_000_000,
            "villa": 20_000_000,
        },
        "tier1_developers": [],
        "tier2_developers": [],
        "tier3_developers": [],
    },
}

# Property type mappings (Arabic to English)
PROPERTY_TYPE_MAP = {
    "شقة": "apartment",
    "شقق": "apartment",
    "فيلا": "villa",
    "فلل": "villa",
    "تاون هاوس": "townhouse",
    "تاونهاوس": "townhouse",
    "دوبلكس": "duplex",
    "شاليه": "chalet",
}

# Developer tiers
TIER1_DEVELOPERS = [
    "tmg", "talaat moustafa", "emaar", "sodic", "mountain view", 
    "palm hills", "ora", "city edge", "المراسم", "إعمار", "سوديك"
]
TIER2_DEVELOPERS = [
    "hyde park", "hydepark", "tatweer misr", "misr italia", 
    "better home", "gates", "iq", "حسن علام"
]


@dataclass
class ROIAnalysis:
    """ROI calculation result."""
    rental_yield: float
    capital_appreciation: float
    total_annual_return: float
    break_even_years: float
    annual_rent_income: int
    
    def to_dict(self) -> Dict:
        return {
            "rental_yield": self.rental_yield,
            "capital_appreciation": self.capital_appreciation,
            "total_annual_return": self.total_annual_return,
            "break_even_years": self.break_even_years,
            "annual_rent_income": self.annual_rent_income
        }


@dataclass
class OsoolScore:
    """Property scoring result (formerly Wolf Score)."""
    total_score: int
    value_score: int
    growth_score: int
    developer_score: int
    verdict: str  # BARGAIN, FAIR, PREMIUM
    
    def to_dict(self) -> Dict:
        return {
            "osool_score": self.total_score,
            "score_breakdown": {
                "value": self.value_score,
                "growth": self.growth_score,
                "developer": self.developer_score
            },
            "verdict": self.verdict
        }


class AnalyticalEngine:
    """
    The Wolf's Ledger - Zero hallucination analytics.
    
    All calculations are performed in code, never by LLM.
    """
    
    def calculate_true_roi(self, property_data: Dict) -> ROIAnalysis:
        """
        Calculate true ROI for a property.
        
        Formula: (Annual Rent) + (Appreciation % * Price) = Total Return
        
        Args:
            property_data: Property with price, location, size_sqm
            
        Returns:
            ROIAnalysis with detailed breakdown
        """
        price = property_data.get("price", 0)
        location = property_data.get("location", "")
        size_sqm = property_data.get("size_sqm", 100)
        
        if price <= 0:
            return ROIAnalysis(
                rental_yield=0,
                capital_appreciation=0,
                total_annual_return=0,
                break_even_years=0,
                annual_rent_income=0
            )
        
        # Get location-specific rates
        appreciation_rate = self._get_appreciation_rate(location)
        rental_yield_rate = self._get_rental_yield(location)
        
        # Calculate returns
        annual_rent = int(price * rental_yield_rate)
        capital_appreciation = price * appreciation_rate
        total_return = annual_rent + capital_appreciation
        total_return_percent = (total_return / price) * 100
        
        # Break-even: years to recover investment from rent
        break_even = price / annual_rent if annual_rent > 0 else 99
        
        return ROIAnalysis(
            rental_yield=round(rental_yield_rate * 100, 1),
            capital_appreciation=round(appreciation_rate * 100, 1),
            total_annual_return=round(total_return_percent, 1),
            break_even_years=round(break_even, 1),
            annual_rent_income=annual_rent
        )
    
    def calculate_inflation_hedge(
        self,
        initial_investment: int,
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate inflation hedge comparison: Cash vs Gold vs Property.
        
        Shows purchasing power erosion of cash vs real asset growth.
        
        Args:
            initial_investment: Amount in EGP
            years: Projection period
            
        Returns:
            Comparison data with projections
        """
        inflation_rate = MARKET_DATA["inflation_rate"]
        gold_rate = MARKET_DATA["gold_appreciation"]
        property_rate = MARKET_DATA["property_appreciation"]
        rental_yield = MARKET_DATA["rental_yield_avg"]
        rent_increase = MARKET_DATA["rent_increase_rate"]
        
        projections = []
        
        for year in range(years + 1):
            # Cash: Loses purchasing power
            cash_real_value = int(initial_investment / ((1 + inflation_rate) ** year))
            
            # Gold: Appreciates
            gold_value = int(initial_investment * ((1 + gold_rate) ** year))
            
            # Property: Appreciates + rental income
            property_value = int(initial_investment * ((1 + property_rate) ** year))
            
            # Cumulative rent
            cumulative_rent = 0
            for y in range(year):
                yearly_rent = initial_investment * rental_yield * ((1 + rent_increase) ** y)
                cumulative_rent += yearly_rent
            cumulative_rent = int(cumulative_rent)
            
            property_total = property_value + cumulative_rent
            
            projections.append({
                "year": year,
                "cash": cash_real_value,
                "gold": gold_value,
                "property": property_total,
                "property_value": property_value,
                "rent_earned": cumulative_rent
            })
        
        final = projections[-1]
        
        return {
            "initial_investment": initial_investment,
            "years": years,
            "projections": projections,
            "summary": {
                "cash_final": final["cash"],
                "cash_loss_percent": round((1 - final["cash"] / initial_investment) * 100, 1),
                "gold_final": final["gold"],
                "gold_gain_percent": round((final["gold"] / initial_investment - 1) * 100, 1),
                "property_final": final["property"],
                "property_gain_percent": round((final["property"] / initial_investment - 1) * 100, 1),
                "rent_earned": final["rent_earned"],
                "property_vs_cash_advantage": final["property"] - final["cash"]
            },
            "verdict": {
                "winner": "property",
                "message_ar": "العقار بيحميك من التضخم + بيجيبلك إيجار. الكاش بيخسر قيمته كل يوم.",
                "message_en": "Property protects against inflation + generates rent. Cash loses value daily."
            }
        }
    
    def calculate_bank_vs_property(
        self,
        initial_investment: int,
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Compare Bank CD (27%) vs Property investment.
        
        Key insight: Bank CD 27% looks good, but inflation 33% = net negative.
        """
        cd_rate = MARKET_DATA["bank_cd_rate"]
        inflation_rate = MARKET_DATA["inflation_rate"]
        property_rate = MARKET_DATA["property_appreciation"]
        rental_yield = MARKET_DATA["rental_yield_avg"]
        rent_increase = MARKET_DATA["rent_increase_rate"]
        
        projections = []
        
        for year in range(years + 1):
            # Bank CD: Nominal growth but inflation erosion
            bank_nominal = int(initial_investment * ((1 + cd_rate) ** year))
            bank_real = int(bank_nominal / ((1 + inflation_rate) ** year))
            
            # Property: Real asset appreciation
            property_value = int(initial_investment * ((1 + property_rate) ** year))
            
            # Cumulative rent
            cumulative_rent = 0
            for y in range(year):
                yearly_rent = initial_investment * rental_yield * ((1 + rent_increase) ** y)
                cumulative_rent += yearly_rent
            cumulative_rent = int(cumulative_rent)
            
            property_total = property_value + cumulative_rent
            
            projections.append({
                "year": year,
                "bank_nominal": bank_nominal,
                "bank_real": bank_real,
                "property": property_total
            })
        
        final = projections[-1]
        bank_real_loss = initial_investment - final["bank_real"]
        
        return {
            "initial_investment": initial_investment,
            "years": years,
            "projections": projections,
            "summary": {
                "bank_nominal_final": final["bank_nominal"],
                "bank_nominal_gain": final["bank_nominal"] - initial_investment,
                "bank_real_final": final["bank_real"],
                "bank_real_loss": bank_real_loss,
                "bank_real_loss_percent": round((bank_real_loss / initial_investment) * 100, 1),
                "property_final": final["property"],
                "property_gain_percent": round((final["property"] / initial_investment - 1) * 100, 1),
                "difference": final["property"] - final["bank_real"]
            },
            "verdict": {
                "winner": "property",
                "headline_ar": "الحقيقة اللي البنوك مش بتقولهالك",
                "headline_en": "The Truth Banks Don't Tell You",
                "message_ar": f"🔴 شهادات البنك 27% بس التضخم 33% = خسارة حقيقية",
                "message_en": f"🔴 Bank CDs give 27% but inflation is 33% = real loss"
            }
        }
    
    def score_property(self, property_data: Dict) -> OsoolScore:
        """
        Calculate Osool Score (formerly Wolf Score) for a property.
        
        Components:
        - Value Score (35%): Price per sqm vs market average
        - Growth Score (30%): Location appreciation potential
        - Developer Score (35%): Developer reputation
        
        Args:
            property_data: Property with price, location, size_sqm, developer
            
        Returns:
            OsoolScore with breakdown
        """
        price = property_data.get("price", 0)
        size_sqm = property_data.get("size_sqm", 1) or 1
        location = property_data.get("location", "")
        developer = property_data.get("developer", "").lower()
        
        # 1. VALUE SCORE (Price per sqm vs market)
        price_per_sqm = price / size_sqm
        market_avg = self._get_area_avg_price(location)
        
        value_ratio = market_avg / (price_per_sqm or 1)
        value_score = min(100, max(0, int(value_ratio * 70)))
        
        # 2. GROWTH SCORE (Location potential)
        growth_rate = self._get_appreciation_rate(location)
        # Convert to 0-100 scale (10% = 70, 25% = 100)
        growth_score = min(100, max(50, int(50 + (growth_rate * 200))))
        
        # 3. DEVELOPER SCORE
        if any(d in developer for d in TIER1_DEVELOPERS):
            developer_score = 95
        elif any(d in developer for d in TIER2_DEVELOPERS):
            developer_score = 80
        else:
            developer_score = 60
        
        # Final weighted score
        total_score = int(
            (value_score * 0.35) +
            (developer_score * 0.35) +
            (growth_score * 0.30)
        )
        
        # Verdict
        if value_score > 85:
            verdict = "BARGAIN"
        elif value_score > 60:
            verdict = "FAIR"
        else:
            verdict = "PREMIUM"
        
        return OsoolScore(
            total_score=total_score,
            value_score=value_score,
            growth_score=growth_score,
            developer_score=developer_score,
            verdict=verdict
        )
    
    def score_properties(self, properties: List[Dict]) -> List[Dict]:
        """
        Score and rank multiple properties.
        
        Returns properties with osool_score added, sorted best-first.
        """
        if not properties:
            return []
        
        scored = []
        for prop in properties:
            score = self.score_property(prop)
            prop_copy = prop.copy()
            prop_copy.update(score.to_dict())
            scored.append(prop_copy)
        
        # Sort by score (highest first)
        return sorted(scored, key=lambda x: x.get("osool_score", 0), reverse=True)
    
    def detect_bargains(
        self,
        properties: List[Dict],
        threshold_percent: float = 10.0
    ) -> List[Dict]:
        """
        Find properties significantly below market value.
        
        Args:
            properties: List of properties
            threshold_percent: Minimum discount to qualify as bargain
            
        Returns:
            List of bargain properties with discount info
        """
        bargains = []
        
        for prop in properties:
            price = prop.get("price", 0)
            size_sqm = prop.get("size_sqm", 1) or 1
            location = prop.get("location", "")
            
            price_per_sqm = price / size_sqm
            market_avg = self._get_area_avg_price(location)
            
            if market_avg > 0:
                discount_percent = ((market_avg - price_per_sqm) / market_avg) * 100
                
                if discount_percent >= threshold_percent:
                    bargain = prop.copy()
                    bargain["la2ta_score"] = round(discount_percent, 1)
                    bargain["savings"] = int((market_avg - price_per_sqm) * size_sqm)
                    bargain["market_price_estimate"] = int(market_avg * size_sqm)
                    bargains.append(bargain)
        
        # Sort by best discount
        return sorted(bargains, key=lambda x: x.get("la2ta_score", 0), reverse=True)
    
    def _get_area_avg_price(self, location: str) -> int:
        """Get average price per sqm for location."""
        for area, price in AREA_PRICES.items():
            if area.lower() in location.lower() or location.lower() in area.lower():
                return price
        return 50000  # Default
    
    def _get_appreciation_rate(self, location: str) -> float:
        """Get appreciation rate for location."""
        for area, rate in AREA_GROWTH.items():
            if area.lower() in location.lower() or location.lower() in area.lower():
                return rate
        return 0.12  # Default 12%
    
    def _get_rental_yield(self, location: str) -> float:
        """Get rental yield for location."""
        # Premium areas have lower yield but higher appreciation
        high_yield_areas = ["6th October", "Rehab", "Madinaty"]
        for area in high_yield_areas:
            if area.lower() in location.lower():
                return 0.075  # 7.5%
        
        low_yield_areas = ["New Capital", "North Coast"]
        for area in low_yield_areas:
            if area.lower() in location.lower():
                return 0.05  # 5% (seasonal/new)
        
        return 0.065  # Default 6.5%


# ═══════════════════════════════════════════════════════════════
# MARKET INTELLIGENCE CLASS (The Wolf's Gatekeeper)
# ═══════════════════════════════════════════════════════════════

@dataclass
class FeasibilityResult:
    """Result of feasibility screening."""
    is_feasible: bool
    message_ar: str
    message_en: str
    budget_gap: int  # How much more they need
    alternatives: List[Dict]  # Alternative suggestions
    
    def to_dict(self) -> Dict:
        return {
            "is_feasible": self.is_feasible,
            "message_ar": self.message_ar,
            "message_en": self.message_en,
            "budget_gap": self.budget_gap,
            "alternatives": self.alternatives
        }


@dataclass
class PropertyBenchmark:
    """Property benchmarking result."""
    wolf_analysis: str  # BARGAIN_DEAL, FAIR_VALUE, PREMIUM
    price_vs_market_percent: float  # -15% = 15% below market
    market_price_sqm: int
    actual_price_sqm: int
    verdict_ar: str
    verdict_en: str
    
    def to_dict(self) -> Dict:
        return {
            "wolf_analysis": self.wolf_analysis,
            "price_vs_market_percent": self.price_vs_market_percent,
            "market_price_sqm": self.market_price_sqm,
            "actual_price_sqm": self.actual_price_sqm,
            "verdict_ar": self.verdict_ar,
            "verdict_en": self.verdict_en
        }


class MarketIntelligence:
    """
    The Wolf's Gatekeeper - Market intelligence and feasibility screening.
    
    Features:
    1. screen_feasibility() - Check if request is realistic
    2. benchmark_property() - Compare property to market averages
    3. get_area_context() - Get market context for an area
    """
    
    def screen_feasibility(
        self,
        location: str,
        property_type: str,
        budget: int
    ) -> FeasibilityResult:
        """
        Screen if user request is feasible given market realities.
        
        The Gatekeeper Protocol: Never search for impossible requests.
        
        Args:
            location: Requested area (e.g., "new cairo", "التجمع")
            property_type: Type of property (e.g., "villa", "apartment")
            budget: User's budget in EGP
            
        Returns:
            FeasibilityResult with alternatives if not feasible
        """
        # Normalize inputs
        location_key = self._normalize_location(location)
        prop_type = self._normalize_property_type(property_type)
        
        # Get area benchmarks
        area_data = AREA_BENCHMARKS.get(location_key, {})
        
        if not area_data:
            # Unknown area - allow search
            return FeasibilityResult(
                is_feasible=True,
                message_ar="",
                message_en="",
                budget_gap=0,
                alternatives=[]
            )
        
        # Get minimum for property type
        minimums = area_data.get("property_minimums", {})
        min_price = minimums.get(prop_type, 0)
        
        if min_price == 0:
            # Property type not tracked, allow
            return FeasibilityResult(
                is_feasible=True,
                message_ar="",
                message_en="",
                budget_gap=0,
                alternatives=[]
            )
        
        # Check feasibility
        if budget >= min_price:
            return FeasibilityResult(
                is_feasible=True,
                message_ar="",
                message_en="",
                budget_gap=0,
                alternatives=[]
            )
        
        # NOT FEASIBLE - Generate alternatives
        gap = min_price - budget
        alternatives = self._generate_alternatives(location_key, prop_type, budget)
        
        area_name_ar = area_data.get("ar_name", location)
        min_price_m = min_price / 1_000_000
        budget_m = budget / 1_000_000
        gap_m = gap / 1_000_000
        
        message_ar = f"""🛑 **واقع السوق:**
{prop_type.capitalize()} في {area_name_ar} بتبدأ من **{min_price_m:.1f} مليون**.
ميزانيتك {budget_m:.1f} مليون = فرق {gap_m:.1f} مليون.

خليني أوريك بدائل تناسب ميزانيتك."""
        
        message_en = f"""🛑 **Market Reality Check:**
{prop_type.capitalize()}s in {location} start at **{min_price_m:.1f}M EGP**.
Your budget {budget_m:.1f}M = {gap_m:.1f}M gap.

Let me show you alternatives within your budget."""
        
        return FeasibilityResult(
            is_feasible=False,
            message_ar=message_ar,
            message_en=message_en,
            budget_gap=gap,
            alternatives=alternatives
        )
    
    def benchmark_property(
        self,
        property_data: Dict
    ) -> PropertyBenchmark:
        """
        Benchmark a property against market averages.
        
        The Value Anchor: A price means nothing without context.
        
        Args:
            property_data: Property with price, size_sqm, location
            
        Returns:
            PropertyBenchmark with wolf_analysis tag
        """
        price = property_data.get("price", 0)
        size_sqm = property_data.get("size_sqm", 1) or 1
        location = property_data.get("location", "")
        
        actual_price_sqm = int(price / size_sqm)
        
        # Get market average
        location_key = self._normalize_location(location)
        area_data = AREA_BENCHMARKS.get(location_key, {})
        market_price_sqm = area_data.get("avg_price_sqm", AREA_PRICES.get("New Cairo", 50000))
        
        # Calculate difference
        diff_percent = ((actual_price_sqm - market_price_sqm) / market_price_sqm) * 100
        
        # Determine wolf analysis tag
        if diff_percent <= -10:
            wolf_analysis = "BARGAIN_DEAL"
            verdict_ar = f"🔥 **لقطة!** أقل من السوق بـ {abs(diff_percent):.0f}%"
            verdict_en = f"🔥 **Bargain!** {abs(diff_percent):.0f}% below market"
        elif diff_percent <= 5:
            wolf_analysis = "FAIR_VALUE"
            verdict_ar = "✅ سعر عادل - متوافق مع السوق"
            verdict_en = "✅ Fair value - aligned with market"
        elif diff_percent <= 15:
            wolf_analysis = "PREMIUM"
            verdict_ar = f"💎 Premium - أعلى من السوق بـ {diff_percent:.0f}% (مبرر لو الموقع مميز)"
            verdict_en = f"💎 Premium - {diff_percent:.0f}% above market (justified if prime location)"
        else:
            wolf_analysis = "OVERPRICED"
            verdict_ar = f"⚠️ أعلى من السوق بـ {diff_percent:.0f}% - تفاوض!"
            verdict_en = f"⚠️ {diff_percent:.0f}% above market - negotiate!"
        
        return PropertyBenchmark(
            wolf_analysis=wolf_analysis,
            price_vs_market_percent=round(diff_percent, 1),
            market_price_sqm=market_price_sqm,
            actual_price_sqm=actual_price_sqm,
            verdict_ar=verdict_ar,
            verdict_en=verdict_en
        )
    
    def get_area_context(self, location: str) -> Dict:
        """
        Get comprehensive market context for an area.
        
        Used during discovery phase to educate the user.
        """
        location_key = self._normalize_location(location)
        area_data = AREA_BENCHMARKS.get(location_key, {})
        
        if not area_data:
            return {
                "found": False,
                "message": "Area not in database"
            }
        
        avg_sqm = area_data.get("avg_price_sqm", 50000)
        minimums = area_data.get("property_minimums", {})
        tier1 = area_data.get("tier1_developers", [])
        tier2 = area_data.get("tier2_developers", [])
        
        return {
            "found": True,
            "ar_name": area_data.get("ar_name", location),
            "avg_price_sqm": avg_sqm,
            "rental_yield": area_data.get("rental_yield", 0.065),
            "growth_rate": area_data.get("growth_rate", 0.12),
            "apartment_start": minimums.get("apartment", 0),
            "villa_start": minimums.get("villa", 0),
            "tier1_developers": tier1,
            "tier2_developers": tier2,
            "price_context_ar": f"متوسط السعر: {avg_sqm:,} جنيه/متر",
            "price_context_en": f"Average: {avg_sqm:,} EGP/sqm"
        }
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location to benchmark key."""
        loc_lower = location.lower().strip()
        
        # Direct matches
        if loc_lower in AREA_BENCHMARKS:
            return loc_lower
        
        # Arabic to English mapping
        arabic_map = {
            "التجمع": "new cairo",
            "القاهرة الجديدة": "new cairo",
            "الشيخ زايد": "sheikh zayed",
            "زايد": "sheikh zayed",
            "العاصمة": "new capital",
            "العاصمة الإدارية": "new capital",
            "اكتوبر": "6th october",
            "الساحل": "north coast",
            "المعادي": "maadi",
        }
        
        for ar, en in arabic_map.items():
            if ar in location:
                return en
        
        # Partial matches
        for key in AREA_BENCHMARKS.keys():
            if key in loc_lower or loc_lower in key:
                return key
        
        return "new cairo"  # Default
    
    def _normalize_property_type(self, prop_type: str) -> str:
        """Normalize property type."""
        prop_lower = prop_type.lower().strip()
        
        # Check Arabic mapping
        for ar, en in PROPERTY_TYPE_MAP.items():
            if ar in prop_type:
                return en
        
        # English normalization
        if "villa" in prop_lower:
            return "villa"
        elif "town" in prop_lower:
            return "townhouse"
        elif "duplex" in prop_lower:
            return "duplex"
        elif "chalet" in prop_lower or "شاليه" in prop_type:
            return "chalet"
        else:
            return "apartment"
    
    def _generate_alternatives(
        self,
        location_key: str,
        property_type: str,
        budget: int
    ) -> List[Dict]:
        """Generate alternative suggestions for unfeasible request."""
        alternatives = []
        
        # Alternative 1: Different property type in same area
        area_data = AREA_BENCHMARKS.get(location_key, {})
        minimums = area_data.get("property_minimums", {})
        
        for ptype, min_price in minimums.items():
            if min_price <= budget and ptype != property_type:
                alternatives.append({
                    "type": "same_area_different_type",
                    "property_type": ptype,
                    "location": location_key,
                    "min_price": min_price,
                    "message_ar": f"{ptype.capitalize()} في نفس المنطقة (من {min_price/1_000_000:.1f}M)",
                    "message_en": f"{ptype.capitalize()} in same area (from {min_price/1_000_000:.1f}M)"
                })
        
        # Alternative 2: Same property type in cheaper area
        for area_key, area_info in AREA_BENCHMARKS.items():
            if area_key != location_key:
                other_minimums = area_info.get("property_minimums", {})
                other_min = other_minimums.get(property_type, 0)
                
                if other_min > 0 and other_min <= budget:
                    alternatives.append({
                        "type": "same_type_different_area",
                        "property_type": property_type,
                        "location": area_key,
                        "location_ar": area_info.get("ar_name", area_key),
                        "min_price": other_min,
                        "message_ar": f"{property_type.capitalize()} في {area_info.get('ar_name', area_key)} (من {other_min/1_000_000:.1f}M)",
                        "message_en": f"{property_type.capitalize()} in {area_key.title()} (from {other_min/1_000_000:.1f}M)"
                    })
        
        return alternatives[:3]  # Max 3 alternatives


# Singleton instances
analytical_engine = AnalyticalEngine()
market_intelligence = MarketIntelligence()

__all__ = [
    "AnalyticalEngine", 
    "analytical_engine", 
    "MarketIntelligence",
    "market_intelligence",
    "ROIAnalysis", 
    "OsoolScore",
    "FeasibilityResult",
    "PropertyBenchmark",
    "MARKET_DATA",
    "AREA_PRICES",
    "AREA_GROWTH",
    "AREA_BENCHMARKS"
]
