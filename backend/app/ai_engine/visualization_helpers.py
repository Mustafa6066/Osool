"""
Visualization Data Helpers for AMR
-----------------------------------
Generate structured data for frontend visualization components.
These helpers transform raw AI analysis into chart-ready formats.
"""

import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


def generate_investment_scorecard(
    property_data: Dict[str, Any],
    valuation_result: Optional[Dict] = None,
    roi_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Investment Scorecard visualization data.

    Args:
        property_data: Basic property info (id, title, price, location)
        valuation_result: Result from run_valuation_ai tool
        roi_data: Result from calculate_investment_roi tool

    Returns:
        Structured data for InvestmentScorecard component
    """

    # Extract valuation data
    predicted_price = valuation_result.get("predicted_price", 0) if valuation_result else 0
    market_status = valuation_result.get("market_status", "Stable ⚖️") if valuation_result else "Stable ⚖️"

    # Parse market status
    if "Hot" in market_status or "📈" in market_status or "Bullish" in market_status:
        trend = "Bullish"
    elif "Cool" in market_status or "📉" in market_status or "Bearish" in market_status:
        trend = "Bearish"
    else:
        trend = "Stable"

    # Calculate match score (based on various factors)
    match_score = 0

    # Price fairness (0-40 points)
    if predicted_price > 0:
        price = property_data.get("price", 0)
        price_diff = ((predicted_price - price) / predicted_price) * 100
        if price_diff > 10:  # 10%+ undervalued
            match_score += 40
        elif price_diff > 0:  # Some undervalued
            match_score += 30
        elif price_diff > -10:  # Fair price
            match_score += 20
        else:  # Overpriced
            match_score += 10
    else:
        match_score += 25  # Neutral if no valuation

    # Location quality (0-20 points)
    location = property_data.get("location", "")
    hot_locations = ["New Cairo", "Sheikh Zayed", "New Capital", "Madinaty"]
    if any(loc in location for loc in hot_locations):
        match_score += 20
        location_quality = 4.2
    else:
        match_score += 10
        location_quality = 3.5

    # Market trend (0-20 points)
    if trend == "Bullish":
        match_score += 20
    elif trend == "Stable":
        match_score += 15
    else:
        match_score += 10

    # Property features (0-20 points)
    bedrooms = property_data.get("bedrooms", 0)
    size_sqm = property_data.get("size_sqm", 0)
    if bedrooms >= 3 and size_sqm >= 120:
        match_score += 20
    elif bedrooms >= 2 and size_sqm >= 80:
        match_score += 15
    else:
        match_score += 10

    # Extract ROI data
    roi_projection = 0
    annual_return = 0
    break_even_years = 0

    if roi_data:
        # Parse ROI data (assuming it returns percentage and yearly income)
        roi_projection = roi_data.get("annual_yield_percentage", 0)
        annual_return = roi_data.get("annual_rent", 0)
        break_even_years = roi_data.get("break_even_years", 0)
    else:
        # Estimate based on location and price
        price = property_data.get("price", 0)
        if price > 0:
            # Egyptian real estate typical rental yield: 5-8%
            roi_projection = 6.5 if trend == "Bullish" else 5.5
            annual_return = price * (roi_projection / 100)
            break_even_years = int(100 / roi_projection) if roi_projection > 0 else 15

    # Determine risk level
    risk_score = 0
    if trend == "Bearish":
        risk_score += 30
    elif trend == "Stable":
        risk_score += 15

    if roi_projection < 5:
        risk_score += 20

    if predicted_price > 0:
        price = property_data.get("price", 0)
        if price > predicted_price * 1.15:  # 15%+ overpriced
            risk_score += 30

    if risk_score < 20:
        risk_level = "Low"
    elif risk_score < 50:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # Price verdict
    price_verdict = "Fair market value"
    if predicted_price > 0:
        price = property_data.get("price", 0)
        price_diff = ((predicted_price - price) / predicted_price) * 100
        if price_diff > 15:
            price_verdict = f"{int(price_diff)}% undervalued ✅"
        elif price_diff > 5:
            price_verdict = f"{int(price_diff)}% below market ✅"
        elif price_diff > -5:
            price_verdict = "Fair market value"
        elif price_diff > -15:
            price_verdict = f"{abs(int(price_diff))}% above market ⚠️"
        else:
            price_verdict = f"{abs(int(price_diff))}% overpriced 🚫"

    return {
        "type": "investment_scorecard",
        "property": {
            "id": property_data.get("id"),
            "title": property_data.get("title"),
            "price": property_data.get("price"),
            "location": property_data.get("location")
        },
        "analysis": {
            "match_score": min(100, match_score),
            "roi_projection": round(roi_projection, 1),
            "risk_level": risk_level,
            "market_trend": trend,
            "price_verdict": price_verdict,
            "location_quality": location_quality,
            "annual_return": int(annual_return),
            "break_even_years": break_even_years
        }
    }


def generate_comparison_matrix(
    properties: List[Dict[str, Any]],
    recommended_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate Comparison Matrix visualization data.

    Args:
        properties: List of property dictionaries
        recommended_id: Optional ID of recommended property

    Returns:
        Structured data for ComparisonMatrix component
    """

    if not properties:
        return None

    # Find best value (lowest price per sqm)
    best_value_id = None
    min_price_per_sqm = float('inf')

    for prop in properties:
        price_per_sqm = prop.get("price_per_sqm", 0)
        if price_per_sqm > 0 and price_per_sqm < min_price_per_sqm:
            min_price_per_sqm = price_per_sqm
            best_value_id = prop.get("id")

    # Auto-recommend based on best value if not specified
    if recommended_id is None:
        recommended_id = best_value_id

    return {
        "type": "comparison_matrix",
        "properties": properties,
        "best_value_id": best_value_id,
        "recommended_id": recommended_id
    }


def generate_payment_timeline(
    property_data: Dict[str, Any],
    mortgage_result: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate Payment Timeline visualization data.

    Args:
        property_data: Property with price and payment terms
        mortgage_result: Optional result from calculate_mortgage tool

    Returns:
        Structured data for PaymentTimeline component
    """

    price = property_data.get("price", 0)
    down_payment_percent = property_data.get("down_payment", 10)
    installment_years = property_data.get("installment_years", 7)
    monthly_installment = property_data.get("monthly_installment", 0)

    # Calculate values
    down_payment_amount = int(price * (down_payment_percent / 100))

    # If monthly installment not provided, calculate it
    if monthly_installment == 0 and installment_years > 0:
        remaining = price - down_payment_amount
        total_months = installment_years * 12
        monthly_installment = remaining / total_months if total_months > 0 else 0

    # Parse interest rate from mortgage result if available
    interest_rate = 0
    if mortgage_result and isinstance(mortgage_result, str):
        # Extract rate from string like "50,000 EGP/month (Rate: 8.5%)"
        if "Rate:" in mortgage_result:
            try:
                rate_str = mortgage_result.split("Rate:")[1].split("%")[0].strip()
                interest_rate = float(rate_str)
            except:
                interest_rate = 0

    # Calculate total paid (including interest if any)
    total_months = installment_years * 12
    installment_total = monthly_installment * total_months
    total_paid = down_payment_amount + installment_total

    return {
        "type": "payment_timeline",
        "property": {
            "title": property_data.get("title"),
            "price": price
        },
        "payment": {
            "down_payment_percent": down_payment_percent,
            "down_payment_amount": down_payment_amount,
            "installment_years": installment_years,
            "monthly_installment": int(monthly_installment),
            "total_paid": int(total_paid),
            "interest_rate": interest_rate
        }
    }


def generate_market_trend_chart(
    location: str,
    current_price_per_sqm: int = 45000
) -> Dict[str, Any]:
    """
    Generate Market Trend Chart visualization data.

    Args:
        location: Property location
        current_price_per_sqm: Current average price per sqm

    Returns:
        Structured data for MarketTrendChart component
    """

    # Generate historical data (last 4 quarters)
    historical = []
    base_price = int(current_price_per_sqm * 0.85)  # Start 15% lower

    quarters = ["2023 Q1", "2023 Q2", "2023 Q3", "2023 Q4"]
    for i, quarter in enumerate(quarters):
        # Simulate growth
        price = int(base_price * (1 + (i * 0.04)))  # 4% growth per quarter
        historical.append({
            "period": quarter,
            "avg_price": price,
            "volume": random.randint(50, 150)
        })

    # Generate forecast (next 2 quarters)
    forecast = []
    forecast_quarters = ["2024 Q1", "2024 Q2"]

    # Determine trend based on location
    hot_locations = ["New Cairo", "Sheikh Zayed", "New Capital", "Madinaty"]
    is_hot = any(loc in location for loc in hot_locations)

    if is_hot:
        trend = "Bullish"
        growth_rate = 0.03  # 3% per quarter
        yoy_change = 12.5
        momentum = "Strong upward momentum"
    else:
        trend = "Stable"
        growth_rate = 0.01  # 1% per quarter
        yoy_change = 4.0
        momentum = "Steady growth"

    for i, quarter in enumerate(forecast_quarters):
        predicted_price = int(current_price_per_sqm * (1 + ((i + 1) * growth_rate)))
        forecast.append({
            "period": quarter,
            "predicted_price": predicted_price
        })

    return {
        "type": "market_trend_chart",
        "location": location,
        "data": {
            "historical": historical,
            "forecast": forecast,
            "current_price": current_price_per_sqm,
            "trend": trend,
            "yoy_change": yoy_change,
            "momentum": momentum
        }
    }


def attach_visualizations_to_response(
    properties: List[Dict[str, Any]],
    valuation_results: Optional[List[Dict]] = None,
    show_scorecard: bool = False,
    show_comparison: bool = False,
    show_payment: bool = False,
    show_trends: bool = False
) -> Dict[str, Any]:
    """
    Attach visualization data to chat response.

    Args:
        properties: List of properties
        valuation_results: Optional valuation results for each property
        show_scorecard: Whether to include investment scorecard
        show_comparison: Whether to include comparison matrix
        show_payment: Whether to include payment timeline
        show_trends: Whether to include market trends

    Returns:
        Dictionary with visualization data
    """

    visualizations = {}

    if not properties:
        return visualizations

    # Get first property for scorecard and payment
    first_property = properties[0]

    if show_scorecard and valuation_results:
        visualizations["investment_scorecard"] = generate_investment_scorecard(
            first_property,
            valuation_results[0] if valuation_results else None
        )

    if show_comparison and len(properties) > 1:
        visualizations["comparison_matrix"] = generate_comparison_matrix(properties)

    if show_payment:
        visualizations["payment_timeline"] = generate_payment_timeline(first_property)

    if show_trends:
        location = first_property.get("location", "New Cairo")
        price_per_sqm = first_property.get("price_per_sqm", 45000)
        visualizations["market_trend_chart"] = generate_market_trend_chart(
            location,
            price_per_sqm
        )

    return visualizations
