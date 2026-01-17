"""
XGBoost Predictor - The Wolf's Crystal Ball
-------------------------------------------
Machine learning predictions for deal scoring, price prediction,
and urgency detection.

Features:
- Deal Probability: Will this lead convert?
- Price Prediction: Is this property fairly priced?
- Urgency Score: How soon should we close?

Note: Uses heuristic model for Phase 1. Can be upgraded to
trained XGBoost model by loading from pickle file.
"""

import os
from typing import Dict, Any

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
