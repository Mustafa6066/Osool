"""
XGBoost Predictor - The Wolf's Crystal Ball V2
----------------------------------------------
Machine learning predictions for deal scoring, price prediction,
urgency detection, inflation hedging, and bargain detection.

Features:
- Deal Probability: Will this lead convert?
- Price Prediction: Is this property fairly priced?
- Urgency Score: How soon should we close?
- Inflation Hedge Score: How well does this property protect against inflation?
- La2ta Detection: Find bargains >10% below market value

Note: Uses heuristic model for Phase 1. Can be upgraded to
trained XGBoost model by loading from pickle file.
"""

import os
from typing import Dict, Any, List

# Try to import XGBoost and sklearn
try:
    import xgboost as xgb
    import numpy as np
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    print("XGBoost/sklearn not available. Using heuristic model.")


# Egyptian real estate market constants
LOCATION_POPULARITY = {
    "new cairo": 0.9,
    "التجمع": 0.9,
    "tagamoa": 0.9,
    "sheikh zayed": 0.85,
    "زايد": 0.85,
    "6th october": 0.8,
    "أكتوبر": 0.8,
    "new capital": 0.75,
    "العاصمة": 0.75,
    "maadi": 0.8,
    "المعادي": 0.8,
    "madinaty": 0.85,
    "مدينتي": 0.85,
    "rehab": 0.8,
    "الرحاب": 0.8,
}

# Average price per sqm by location (EGP, 2024 data)
PRICE_PER_SQM = {
    "new cairo": 45000,
    "التجمع": 45000,
    "sheikh zayed": 40000,
    "زايد": 40000,
    "6th october": 25000,
    "أكتوبر": 25000,
    "new capital": 35000,
    "العاصمة": 35000,
    "maadi": 50000,
    "المعادي": 50000,
    "madinaty": 38000,
    "مدينتي": 38000,
}

# Finishing multipliers
FINISHING_MULTIPLIERS = {
    "core & shell": 0.7,
    "core": 0.7,
    "semi finished": 0.85,
    "semi": 0.85,
    "fully finished": 1.0,
    "finished": 1.0,
    "ultra lux": 1.25,
    "super lux": 1.2,
}


class OsoolXGBoostPredictor:
    """
    Hybrid predictor combining XGBoost (when available) with
    sophisticated heuristics for Egyptian real estate.

    The Wolf's data-driven brain.
    """

    def __init__(self):
        self.deal_model = None
        self.price_model = None
        self.location_encoder = None

        # Try to load trained models
        self._load_models()

    def _load_models(self):
        """Load trained XGBoost models if available."""
        model_dir = os.path.dirname(os.path.abspath(__file__))

        # Try to load deal scoring model
        deal_model_path = os.path.join(model_dir, "deal_scoring_model.json")
        if XGB_AVAILABLE and os.path.exists(deal_model_path):
            try:
                self.deal_model = xgb.Booster()
                self.deal_model.load_model(deal_model_path)
                print("✅ Loaded deal scoring model")
            except Exception as e:
                print(f"⚠️ Could not load deal model: {e}")

        # Try to load price prediction model
        price_model_path = os.path.join(model_dir, "osool_xgboost.pkl")
        if XGB_AVAILABLE and os.path.exists(price_model_path):
            try:
                import joblib
                self.price_model = joblib.load(price_model_path)
                print("✅ Loaded price prediction model")
            except Exception as e:
                print(f"⚠️ Could not load price model: {e}")

        # Try to load location encoder
        encoder_path = os.path.join(model_dir, "location_encoder.pkl")
        if os.path.exists(encoder_path):
            try:
                import joblib
                self.location_encoder = joblib.load(encoder_path)
                print("✅ Loaded location encoder")
            except:
                pass

    def predict_deal_probability(self, session_features: Dict[str, Any]) -> float:
        """
        Predict probability of deal closing based on session behavior.

        Features:
        - messages_count: Number of messages in session
        - budget_mentioned: Whether budget was discussed
        - location_specified: Whether location preference given
        - properties_viewed: Number of properties viewed
        - objections_raised: Number of objections detected
        - closing_language: Whether closing intent detected
        - lead_score: Current lead score (0-100)

        Returns:
            Float between 0.0 and 1.0
        """
        # If trained model available, use it
        if self.deal_model and XGB_AVAILABLE:
            return self._predict_with_model(session_features)

        # Otherwise use sophisticated heuristics
        return self._heuristic_deal_probability(session_features)

    def _heuristic_deal_probability(self, features: Dict[str, Any]) -> float:
        """
        Heuristic-based deal probability scoring.
        Based on sales psychology and Egyptian buyer patterns.
        """
        score = 0.5  # Start neutral

        # Message engagement (more messages = more engaged)
        msg_count = features.get("messages_count", 0)
        if msg_count >= 10:
            score += 0.15
        elif msg_count >= 5:
            score += 0.10
        elif msg_count >= 3:
            score += 0.05

        # Budget mentioned is strong signal
        if features.get("budget_mentioned", False):
            score += 0.15

        # Location specified shows seriousness
        if features.get("location_specified", False):
            score += 0.10

        # Properties viewed
        props_viewed = features.get("properties_viewed", 0)
        if props_viewed >= 5:
            score += 0.10
        elif props_viewed >= 2:
            score += 0.05

        # Objections (some objections = engaged, many = cold)
        objections = features.get("objections_raised", 0)
        if objections == 1:
            score += 0.05  # Engaged enough to object
        elif objections >= 3:
            score -= 0.10  # Too many objections

        # Closing language is very strong signal
        if features.get("closing_language", False):
            score += 0.20

        # Factor in existing lead score
        lead_score = features.get("lead_score", 50)
        score += (lead_score - 50) / 200  # Normalize to -0.25 to +0.25

        # Clamp to valid range
        return max(0.05, min(0.95, score))

    def predict_urgency(self, session_features: Dict[str, Any]) -> float:
        """
        Predict urgency level - how soon the client needs to decide.

        Returns:
            Float between 0.0 (not urgent) and 1.0 (very urgent)
        """
        urgency = 0.5

        # Closing language = high urgency
        if session_features.get("closing_language", False):
            urgency += 0.25

        # Budget mentioned = medium urgency
        if session_features.get("budget_mentioned", False):
            urgency += 0.10

        # Many messages in short time = high urgency
        if session_features.get("messages_count", 0) >= 8:
            urgency += 0.10

        # Few objections = ready to move
        if session_features.get("objections_raised", 0) <= 1:
            urgency += 0.10

        return max(0.1, min(0.95, urgency))

    def predict_fair_price(
        self,
        property_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict fair market price for a property.

        Features:
        - location: Property location
        - size_sqm: Size in square meters
        - bedrooms: Number of bedrooms
        - bathrooms: Number of bathrooms
        - finishing: Finishing level
        - floor: Floor number
        - is_compound: Whether in gated compound

        Returns:
            Dict with predicted_price, confidence, price_range, market_status
        """
        # If trained model available
        if self.price_model and XGB_AVAILABLE:
            return self._predict_price_with_model(property_features)

        # Otherwise use heuristic pricing
        return self._heuristic_price_prediction(property_features)

    def _heuristic_price_prediction(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Heuristic-based price prediction using Egyptian market data.
        """
        location = features.get("location", "").lower()
        size_sqm = features.get("size_sqm", 150)
        bedrooms = features.get("bedrooms", 3)
        finishing = features.get("finishing", "fully finished").lower()
        floor = features.get("floor", 3)
        is_compound = features.get("is_compound", True)

        # Get base price per sqm for location
        base_price_sqm = 35000  # Default
        for loc_key, price in PRICE_PER_SQM.items():
            if loc_key.lower() in location:
                base_price_sqm = price
                break

        # Apply finishing multiplier
        finishing_mult = 1.0
        for fin_key, mult in FINISHING_MULTIPLIERS.items():
            if fin_key in finishing:
                finishing_mult = mult
                break

        # Compound premium
        compound_mult = 1.1 if is_compound else 1.0

        # Floor adjustment (ground and top floors slightly cheaper)
        floor_mult = 1.0
        if floor == 0 or floor >= 10:
            floor_mult = 0.95
        elif 2 <= floor <= 5:
            floor_mult = 1.02

        # Bedroom efficiency (smaller units have higher per-sqm price)
        bedroom_mult = 1.0
        if bedrooms <= 1:
            bedroom_mult = 1.1
        elif bedrooms >= 4:
            bedroom_mult = 0.95

        # Calculate predicted price
        price_per_sqm = (
            base_price_sqm
            * finishing_mult
            * compound_mult
            * floor_mult
            * bedroom_mult
        )
        predicted_price = int(price_per_sqm * size_sqm)

        # Calculate confidence based on how much data we have
        confidence = 0.75
        if location in PRICE_PER_SQM or any(k in location for k in PRICE_PER_SQM.keys()):
            confidence = 0.85

        # Price range (±10%)
        price_low = int(predicted_price * 0.9)
        price_high = int(predicted_price * 1.1)

        return {
            "predicted_price": predicted_price,
            "price_per_sqm": int(price_per_sqm),
            "price_range": (price_low, price_high),
            "confidence": confidence,
            "market_status": "fair",  # Would be dynamic with real model
            "factors": {
                "location_factor": base_price_sqm,
                "finishing_factor": finishing_mult,
                "compound_premium": compound_mult,
            }
        }

    def compare_price_to_market(
        self,
        asking_price: float,
        property_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare asking price to predicted market price.

        Returns verdict: BARGAIN, FAIR, OVERPRICED
        """
        prediction = self.predict_fair_price(property_features)
        predicted = prediction["predicted_price"]
        price_low, price_high = prediction["price_range"]

        diff_percent = ((asking_price - predicted) / predicted) * 100

        if asking_price < price_low:
            verdict = "BARGAIN"
            message_ar = f"لقطة! السعر أقل من السوق بـ {abs(diff_percent):.0f}%"
            message_en = f"Bargain! {abs(diff_percent):.0f}% below market"
        elif asking_price > price_high:
            verdict = "OVERPRICED"
            message_ar = f"السعر أعلى من السوق بـ {diff_percent:.0f}%"
            message_en = f"Overpriced by {diff_percent:.0f}%"
        else:
            verdict = "FAIR"
            message_ar = "سعر عادل، في نطاق السوق"
            message_en = "Fair price, within market range"

        return {
            "verdict": verdict,
            "asking_price": asking_price,
            "predicted_price": predicted,
            "difference_percent": round(diff_percent, 1),
            "price_range": prediction["price_range"],
            "message_ar": message_ar,
            "message_en": message_en,
            "confidence": prediction["confidence"]
        }

    def calculate_inflation_hedge_score(
        self,
        property_features: Dict[str, Any],
        investment_horizon_years: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate how well this property hedges against inflation vs alternatives.
        The "Inflation Killer" - shows property vs cash vs gold over time.

        Uses Egyptian market data:
        - Inflation Rate: ~28% (2024)
        - Gold Appreciation: ~35% annually in EGP terms
        - Property Appreciation: ~18% annually + rental yield
        - Rental Yield: ~6.5% annually

        Args:
            property_features: Dict with 'price' and optionally 'location', 'size_sqm'
            investment_horizon_years: Projection period (default 5 years)

        Returns:
            Dict with projections, hedge_score, and comparison data
        """
        # Egyptian market constants (2024 data)
        INFLATION_RATE = 0.28  # 28% annual inflation
        GOLD_APPRECIATION = 0.35  # Gold in EGP terms
        PROPERTY_APPRECIATION = 0.18  # Property appreciation
        RENTAL_YIELD = 0.065  # 6.5% annual rental yield
        RENT_INCREASE_RATE = 0.10  # 10% annual rent increase

        initial_investment = property_features.get('price', 5_000_000)

        # Calculate year-by-year projections
        projections = []

        cash_value = initial_investment
        gold_value = initial_investment
        property_value = initial_investment
        cumulative_rent = 0

        for year in range(investment_horizon_years + 1):
            if year == 0:
                projections.append({
                    "year": 2024,
                    "cash_real_value": initial_investment,
                    "gold_value": initial_investment,
                    "property_value": initial_investment,
                    "property_total": initial_investment,
                    "annual_rent": 0
                })
            else:
                # Cash loses value to inflation (real purchasing power)
                cash_value = initial_investment / ((1 + INFLATION_RATE) ** year)

                # Gold appreciates in EGP terms
                gold_value = initial_investment * ((1 + GOLD_APPRECIATION) ** year)

                # Property appreciates + generates rent
                property_value = initial_investment * ((1 + PROPERTY_APPRECIATION) ** year)
                annual_rent = initial_investment * RENTAL_YIELD * ((1 + RENT_INCREASE_RATE) ** (year - 1))
                cumulative_rent += annual_rent
                property_total = property_value + cumulative_rent

                projections.append({
                    "year": 2024 + year,
                    "cash_real_value": int(cash_value),
                    "gold_value": int(gold_value),
                    "property_value": int(property_value),
                    "property_total": int(property_total),
                    "annual_rent": int(annual_rent)
                })

        # Final values
        final = projections[-1]

        # Calculate advantages
        advantage_vs_cash = final["property_total"] - final["cash_real_value"]
        advantage_vs_gold = final["property_total"] - final["gold_value"]

        # Property beats both = high score
        # Property beats cash but not gold = medium score
        # Property beats neither = low score
        if advantage_vs_cash > 0 and advantage_vs_gold > 0:
            hedge_score = min(100, 70 + int((advantage_vs_gold / initial_investment) * 100))
        elif advantage_vs_cash > 0:
            hedge_score = 50 + int((advantage_vs_cash / initial_investment) * 30)
        else:
            hedge_score = max(10, 30 + int((advantage_vs_cash / initial_investment) * 30))

        # Calculate percentage changes
        cash_change_pct = ((final["cash_real_value"] - initial_investment) / initial_investment) * 100
        gold_change_pct = ((final["gold_value"] - initial_investment) / initial_investment) * 100
        property_change_pct = ((final["property_total"] - initial_investment) / initial_investment) * 100

        return {
            "hedge_score": min(100, max(0, hedge_score)),
            "initial_investment": initial_investment,
            "investment_horizon_years": investment_horizon_years,
            "projections": projections,
            "final_values": {
                "cash_real_value": final["cash_real_value"],
                "gold_value": final["gold_value"],
                "property_value": final["property_value"],
                "property_total": final["property_total"],
                "total_rent_earned": int(cumulative_rent)
            },
            "percentage_changes": {
                "cash": round(cash_change_pct, 1),
                "gold": round(gold_change_pct, 1),
                "property": round(property_change_pct, 1)
            },
            "advantages": {
                "vs_cash": int(advantage_vs_cash),
                "vs_gold": int(advantage_vs_gold)
            },
            "verdict": {
                "message_ar": f"العقار هيكسبك {int(advantage_vs_cash/1_000_000):.1f} مليون جنيه أكتر من لو فلوسك فضلت كاش!",
                "message_en": f"Property gains {int(advantage_vs_cash/1_000_000):.1f}M EGP more than keeping cash!",
                "beats_cash": advantage_vs_cash > 0,
                "beats_gold": advantage_vs_gold > 0
            },
            "summary_cards": [
                {
                    "label": "Cash (Bank)",
                    "label_ar": "كاش (بنك)",
                    "value": final["cash_real_value"],
                    "change_pct": round(cash_change_pct, 1),
                    "color": "red"
                },
                {
                    "label": "Gold",
                    "label_ar": "دهب",
                    "value": final["gold_value"],
                    "change_pct": round(gold_change_pct, 1),
                    "color": "yellow"
                },
                {
                    "label": "Property",
                    "label_ar": "عقار",
                    "value": final["property_total"],
                    "change_pct": round(property_change_pct, 1),
                    "color": "green"
                }
            ]
        }

    def detect_la2ta(
        self,
        properties: List[Dict[str, Any]],
        threshold_percent: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        Detect "La2ta" (bargain) properties that are significantly below market.
        The Wolf's Radar for finding deals.

        Args:
            properties: List of property dicts with 'price', 'location', 'size_sqm', etc.
            threshold_percent: Minimum discount percentage to qualify as La2ta (default 10%)

        Returns:
            List of properties with la2ta metadata, sorted by discount (best first)
        """
        la2ta_properties = []

        for prop in properties:
            # Get property features for valuation
            property_features = {
                "location": prop.get('location', ''),
                "size_sqm": prop.get('size_sqm', 150),
                "bedrooms": prop.get('bedrooms', 3),
                "finishing": prop.get('finishing', 'fully finished'),
                "floor": prop.get('floor', 3),
                "is_compound": prop.get('compound') is not None
            }

            # Get predicted fair price
            prediction = self.predict_fair_price(property_features)
            predicted_price = prediction.get('predicted_price', 0)
            asking_price = prop.get('price', 0)

            if predicted_price > 0 and asking_price > 0:
                # Calculate discount percentage
                discount_percent = ((predicted_price - asking_price) / predicted_price) * 100

                if discount_percent >= threshold_percent:
                    # This is a La2ta!
                    savings = predicted_price - asking_price

                    la2ta_prop = {
                        **prop,
                        "la2ta_score": round(discount_percent, 1),
                        "predicted_price": predicted_price,
                        "savings": int(savings),
                        "savings_formatted": f"{int(savings/1000):,}K" if savings < 1_000_000 else f"{savings/1_000_000:.1f}M",
                        "is_la2ta": True,
                        "la2ta_message_ar": f"🐺 لقطة! تحت السوق بـ {discount_percent:.0f}% - توفير {int(savings/1000):,} ألف",
                        "la2ta_message_en": f"Bargain! {discount_percent:.0f}% below market - Save {int(savings/1000):,}K EGP",
                        "urgency_message_ar": "فرصة نادرة، الأسعار دي مش بتدوم!",
                        "urgency_message_en": "Rare opportunity, prices like this don't last!"
                    }
                    la2ta_properties.append(la2ta_prop)

        # Sort by la2ta_score (highest discount first)
        return sorted(la2ta_properties, key=lambda x: x.get('la2ta_score', 0), reverse=True)

    def get_market_comparison_data(
        self,
        property_features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive market comparison data for a property.
        Used for detailed analysis views.
        """
        price_prediction = self.predict_fair_price(property_features)
        asking_price = property_features.get('price', price_prediction['predicted_price'])

        price_comparison = self.compare_price_to_market(asking_price, property_features)
        inflation_hedge = self.calculate_inflation_hedge_score(property_features)

        return {
            "price_analysis": price_prediction,
            "market_comparison": price_comparison,
            "inflation_hedge": inflation_hedge,
            "wolf_recommendation": {
                "score": price_comparison.get('verdict') == 'BARGAIN' and 90 or
                         price_comparison.get('verdict') == 'FAIR' and 70 or 50,
                "action_ar": "اشتري دلوقتي!" if price_comparison.get('verdict') == 'BARGAIN' else
                            "سعر معقول" if price_comparison.get('verdict') == 'FAIR' else "فاوض على السعر",
                "action_en": "Buy now!" if price_comparison.get('verdict') == 'BARGAIN' else
                            "Fair price" if price_comparison.get('verdict') == 'FAIR' else "Negotiate"
            }
        }

    def _predict_with_model(self, features: Dict[str, Any]) -> float:
        """Use trained XGBoost model for deal prediction."""
        try:
            import numpy as np

            # Prepare features array
            feature_array = np.array([[
                features.get("messages_count", 0),
                1 if features.get("budget_mentioned", False) else 0,
                1 if features.get("location_specified", False) else 0,
                features.get("properties_viewed", 0),
                features.get("objections_raised", 0),
                1 if features.get("closing_language", False) else 0,
                features.get("lead_score", 50)
            ]])

            dmatrix = xgb.DMatrix(feature_array)
            prediction = self.deal_model.predict(dmatrix)[0]
            return float(prediction)

        except Exception as e:
            print(f"Model prediction error: {e}")
            return self._heuristic_deal_probability(features)

    def _predict_price_with_model(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use trained XGBoost model for price prediction."""
        try:
            import numpy as np

            location = features.get("location", "new cairo")
            if self.location_encoder:
                location_encoded = self.location_encoder.transform([location])[0]
            else:
                location_encoded = 0

            feature_array = np.array([[
                location_encoded,
                features.get("size_sqm", 150),
                features.get("bedrooms", 3),
                self._encode_finishing(features.get("finishing", "finished")),
                features.get("floor", 3),
                1 if features.get("is_compound", True) else 0
            ]])

            predicted_price = self.price_model.predict(feature_array)[0]

            return {
                "predicted_price": int(predicted_price),
                "price_per_sqm": int(predicted_price / features.get("size_sqm", 150)),
                "price_range": (int(predicted_price * 0.9), int(predicted_price * 1.1)),
                "confidence": 0.85,
                "market_status": "model_predicted"
            }

        except Exception as e:
            print(f"Price model error: {e}")
            return self._heuristic_price_prediction(features)

    def _encode_finishing(self, finishing: str) -> int:
        """Encode finishing level to numeric."""
        finishing_map = {
            "core & shell": 0,
            "core": 0,
            "semi finished": 1,
            "semi": 1,
            "fully finished": 2,
            "finished": 2,
            "super lux": 3,
            "ultra lux": 4
        }
        return finishing_map.get(finishing.lower(), 2)


# Backward compatibility - async wrapper
async def predict_deal_probability(property_data: dict) -> float:
    """
    Legacy async function for backward compatibility.
    """
    predictor = OsoolXGBoostPredictor()
    return predictor.predict_deal_probability(property_data)


# Singleton instance
xgboost_predictor = OsoolXGBoostPredictor()

# Export
__all__ = [
    "OsoolXGBoostPredictor",
    "xgboost_predictor",
    "predict_deal_probability"
]
