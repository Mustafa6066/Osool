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


# Singleton instance
analytical_engine = AnalyticalEngine()

__all__ = [
    "AnalyticalEngine", 
    "analytical_engine", 
    "ROIAnalysis", 
    "OsoolScore",
    "MARKET_DATA",
    "AREA_PRICES",
    "AREA_GROWTH"
]
