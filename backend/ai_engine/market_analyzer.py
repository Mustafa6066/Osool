"""
Osool Market Analyzer Module
----------------------------
Handles predictive analytics, price forecasting, and ROI calculations
using historical data and market signals.
"""

import random
from typing import Dict, List

class MarketAnalyzer:
    def __init__(self, region: str = "EG-Cairo"):
        self.region = region
        self.supported_areas = ["New Cairo", "New Capital", "Sheikh Zayed", "October"]

    def predict_price_trend(self, location: str, months_ahead: int = 12) -> Dict:
        """
        Predict future property prices based on historical trends,
        inflation, and demand indicators.
        """
        if location not in self.supported_areas:
            return {"error": "Location data insufficient"}

        # Simulation logic for MVP
        base_growth = 0.15  # 15% base inflation/growth
        location_factor = 1.0
        
        if location == "New Capital":
            location_factor = 1.25 # Higher growth potential
        elif location == "Sheikh Zayed":
            location_factor = 1.1

        predicted_growth = base_growth * location_factor * (months_ahead / 12)
        
        return {
            "location": location,
            "forecast_period": f"{months_ahead} months",
            "predicted_growth_percentage": round(predicted_growth * 100, 2),
            "confidence_score": 0.85,
            "factors": ["Government Move", "New Monorail", "Global Demand"]
        }

    def calculate_compound_roi(self, purchase_price: float, rental_income: float, years: int) -> Dict:
        """
        Calculate Compound ROI considering appreciation and rental reinvestment.
        """
        appreciation_rate = 0.12 # Conservative estimate
        current_value = purchase_price
        total_rental_income = 0

        for _ in range(years):
            current_value *= (1 + appreciation_rate)
            total_rental_income += rental_income
            rental_income *= 1.05 # 5% annual rent increase

        gross_profit = (current_value + total_rental_income) - purchase_price
        roi_percent = (gross_profit / purchase_price) * 100

        return {
            "years": years,
            "future_value": round(current_value, 2),
            "total_rental_income": round(total_rental_income, 2),
            "total_roi_percent": round(roi_percent, 2),
            "annualized_roi": round(roi_percent / years, 2)
        }
