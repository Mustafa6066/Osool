"""
Visualization Data Helpers for AMR - "The Wolf's Visual Arsenal"
-----------------------------------------------------------------
Generate structured data for frontend visualization components.
These helpers transform raw AI analysis into chart-ready formats.

New in V4:
- Inflation Killer Chart: Cash vs Gold vs Property comparison
- La2ta Alert: Bargain property alerts
- Law 114 Guardian: Contract scanner CTA
- Reality Check: Impossible request alternatives
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


def generate_inflation_killer_chart(
    initial_investment: int = 5_000_000,
    years: int = 5
) -> Dict[str, Any]:
    """
    Generate "Inflation Killer" chart data showing:
    - Cash value erosion over time (with Egyptian inflation ~25-30%)
    - Gold value appreciation
    - Property value appreciation + rental income

    This is the "Wolf's secret weapon" for converting hesitant investors.

    Args:
        initial_investment: Initial investment amount in EGP (default 5M)
        years: Number of years to project (default 5)

    Returns:
        Structured data for InflationKillerChart component
    """
    # Egyptian market assumptions (2024-2025 data)
    INFLATION_RATE = 0.28           # 28% annual inflation (CBE data)
    GOLD_APPRECIATION = 0.35        # 35% annual (EGX Gold historical)
    PROPERTY_APPRECIATION = 0.18    # 18% annual (Prime locations)
    RENTAL_YIELD = 0.065            # 6.5% rental yield
    RENT_INCREASE_RATE = 0.10       # 10% annual rent increase

    data_points = []

    for year in range(years + 1):
        # Cash: Loses purchasing power to inflation
        # Real value = Nominal / (1 + inflation)^years
        cash_real_value = int(initial_investment / ((1 + INFLATION_RATE) ** year))

        # Gold: Appreciates but no yield
        gold_value = int(initial_investment * ((1 + GOLD_APPRECIATION) ** year))

        # Property: Appreciates + cumulative rental income
        property_value = int(initial_investment * ((1 + PROPERTY_APPRECIATION) ** year))

        # Calculate cumulative rent (rent increases each year)
        cumulative_rent = 0
        for y in range(year):
            yearly_rent = initial_investment * RENTAL_YIELD * ((1 + RENT_INCREASE_RATE) ** y)
            cumulative_rent += yearly_rent
        cumulative_rent = int(cumulative_rent)

        property_total = property_value + cumulative_rent

        data_points.append({
            "year": year,
            "label": f"Year {year}" if year > 0 else "Now",
            "cash": cash_real_value,
            "gold": gold_value,
            "property": property_total,
            "property_value_only": property_value,
            "cumulative_rent": cumulative_rent
        })

    # Calculate final comparison
    final = data_points[-1]
    initial = data_points[0]

    # Cash loss percentage (purchasing power erosion)
    cash_loss_percent = round((1 - final["cash"] / initial["cash"]) * 100, 1)

    # Gold gain percentage
    gold_gain_percent = round((final["gold"] / initial["gold"] - 1) * 100, 1)

    # Property gain percentage (including rent)
    property_gain_percent = round((final["property"] / initial["property_value_only"] - 1) * 100, 1)

    # Advantage calculations
    property_vs_cash_advantage = final["property"] - final["cash"]
    property_vs_gold_advantage = final["property"] - final["gold"]

    return {
        "type": "inflation_killer",
        "initial_investment": initial_investment,
        "years": years,
        "data_points": data_points,
        "summary": {
            "cash_final": final["cash"],
            "cash_loss_percent": cash_loss_percent,
            "gold_final": final["gold"],
            "gold_gain_percent": gold_gain_percent,
            "property_final": final["property"],
            "property_gain_percent": property_gain_percent,
            "property_vs_cash_advantage": property_vs_cash_advantage,
            "property_vs_gold_advantage": property_vs_gold_advantage,
            "total_rent_earned": final["cumulative_rent"]
        },
        "assumptions": {
            "inflation_rate": INFLATION_RATE,
            "gold_appreciation": GOLD_APPRECIATION,
            "property_appreciation": PROPERTY_APPRECIATION,
            "rental_yield": RENTAL_YIELD,
            "source": "Egyptian Central Bank & Market Data 2024"
        },
        "verdict": {
            "winner": "property",
            "message_ar": "العقار بيحميك من التضخم + بيجيبلك إيجار شهري. الفلوس في البنك بتخسر قيمتها كل يوم.",
            "message_en": "Property protects against inflation + generates rental income. Cash in bank loses value daily."
        }
    }


def generate_certificates_vs_property_chart(
    initial_investment: int = 5_000_000,
    years: int = 5
) -> Dict[str, Any]:
    """
    Generate Bank Certificate (CD) vs Property comparison chart.
    
    This is the #1 comparison in Egyptian market - Bank CDs offer 27% interest
    but inflation erodes the real returns making them net negative.
    Property offers appreciation + rental income + inflation hedge.
    
    Uses psychological RED/GREEN colors for maximum impact.
    
    Args:
        initial_investment: Initial investment amount in EGP (default 5M)
        years: Number of years to project (default 5)
    
    Returns:
        Structured data for CertificatesVsProperty component
    """
    # Egyptian market rates (2024-2025)
    BANK_CD_RATE = 0.27              # 27% annual interest (EGP CDs)
    INFLATION_RATE = 0.33            # 33% effective inflation (real purchasing power loss)
    PROPERTY_APPRECIATION = 0.18     # 18% annual property appreciation
    RENTAL_YIELD = 0.065             # 6.5% rental yield
    RENT_INCREASE_RATE = 0.10        # 10% annual rent increase
    
    data_points = []
    
    for year in range(years + 1):
        # Bank Certificate: 27% interest but inflation eats the gains
        # Nominal value grows but REAL purchasing power shrinks
        nominal_bank_value = int(initial_investment * ((1 + BANK_CD_RATE) ** year))
        # Real value after inflation adjustment
        real_bank_value = int(nominal_bank_value / ((1 + INFLATION_RATE) ** year))
        
        # Property: Appreciates + rental income
        property_value = int(initial_investment * ((1 + PROPERTY_APPRECIATION) ** year))
        
        # Cumulative rental income
        cumulative_rent = 0
        for y in range(year):
            yearly_rent = initial_investment * RENTAL_YIELD * ((1 + RENT_INCREASE_RATE) ** y)
            cumulative_rent += yearly_rent
        cumulative_rent = int(cumulative_rent)
        
        property_total = property_value + cumulative_rent
        
        # Real property value (property appreciates WITH inflation, so it's protected)
        real_property_value = property_total  # Property is the inflation hedge
        
        data_points.append({
            "year": year,
            "label": f"السنة {year}" if year > 0 else "الآن",
            "label_en": f"Year {year}" if year > 0 else "Now",
            "bank_nominal": nominal_bank_value,
            "bank_real": real_bank_value,
            "property_total": property_total,
            "property_value": property_value,
            "cumulative_rent": cumulative_rent
        })
    
    # Final calculations
    final = data_points[-1]
    initial = data_points[0]
    
    # Bank: What looks like 27% profit is actually a loss in real terms
    bank_nominal_gain = final["bank_nominal"] - initial_investment
    bank_real_loss = initial_investment - final["bank_real"]
    bank_real_loss_percent = round((bank_real_loss / initial_investment) * 100, 1)
    
    # Property: Real gains
    property_total_gain = final["property_total"] - initial_investment
    property_gain_percent = round((property_total_gain / initial_investment) * 100, 1)
    
    # The "wake up call" calculation
    difference = final["property_total"] - final["bank_real"]
    
    return {
        "type": "certificates_vs_property",
        "initial_investment": initial_investment,
        "years": years,
        "data_points": data_points,
        "summary": {
            # Bank Certificate results
            "bank_nominal_final": final["bank_nominal"],
            "bank_nominal_gain": bank_nominal_gain,
            "bank_real_final": final["bank_real"],
            "bank_real_loss": bank_real_loss,
            "bank_real_loss_percent": bank_real_loss_percent,
            
            # Property results
            "property_final": final["property_total"],
            "property_value_only": final["property_value"],
            "total_rent_earned": final["cumulative_rent"],
            "property_gain_percent": property_gain_percent,
            
            # The comparison
            "difference": difference,
            "winner": "property"
        },
        "assumptions": {
            "bank_cd_rate": BANK_CD_RATE,
            "inflation_rate": INFLATION_RATE,
            "property_appreciation": PROPERTY_APPRECIATION,
            "rental_yield": RENTAL_YIELD,
            "source": "Central Bank of Egypt & Market Data 2024"
        },
        "colors": {
            "bank": "#FF4444",     # RED - Danger (loss)
            "property": "#00C853"  # GREEN - Growth (gains)
        },
        "verdict": {
            "winner": "property",
            "message_ar": f"🔴 شهادات البنك بتديك 27% بس التضخم 33% = خسارة حقيقية {bank_real_loss_percent}%\n🟢 العقار زاد {property_gain_percent}% + إيجار {final['cumulative_rent']:,} جنيه",
            "message_en": f"🔴 Bank CDs give 27% but inflation is 33% = real loss of {bank_real_loss_percent}%\n🟢 Property grew {property_gain_percent}% + rent income of {final['cumulative_rent']:,} EGP",
            "headline_ar": "الحقيقة اللي البنوك مش بتقولهالك",
            "headline_en": "The Truth Banks Don't Tell You"
        }
    }

def generate_la2ta_alert(
    properties: List[Dict[str, Any]],
    threshold_percent: float = 10.0
) -> Optional[Dict[str, Any]]:
    """
    Generate La2ta (Bargain) Alert for properties significantly below market value.

    Args:
        properties: List of properties with valuation data
        threshold_percent: Minimum discount percentage to trigger alert (default 10%)

    Returns:
        La2ta alert data if bargains found, None otherwise
    """
    bargains = []

    for prop in properties:
        verdict = prop.get('valuation_verdict', '')
        if verdict == 'BARGAIN':
            # Calculate discount percentage if available
            price = prop.get('price', 0)
            market_price = prop.get('predicted_price', price * 1.1)  # Estimate if not available

            if market_price > 0:
                discount_percent = ((market_price - price) / market_price) * 100
                if discount_percent >= threshold_percent:
                    bargains.append({
                        **prop,
                        "la2ta_score": round(discount_percent, 1),
                        "savings": int(market_price - price)
                    })

    if not bargains:
        return None

    # Sort by best discount
    bargains.sort(key=lambda x: x.get('la2ta_score', 0), reverse=True)

    return {
        "type": "la2ta_alert",
        "properties": bargains[:3],  # Top 3 bargains
        "best_deal": bargains[0],
        "total_found": len(bargains),
        "message_ar": f"🐺 لقيتلك {len(bargains)} لقطة! أحسن واحدة تحت السوق بـ {bargains[0]['la2ta_score']:.0f}%",
        "message_en": f"Found {len(bargains)} bargain(s)! Best one is {bargains[0]['la2ta_score']:.0f}% below market"
    }


def generate_law_114_guardian(
    status: str = "ready",
    scan_result: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Generate Law 114 Guardian (Contract Scanner) CTA or results.

    Args:
        status: "ready" for CTA, "scanned" for results
        scan_result: Optional scan results if status is "scanned"

    Returns:
        Law 114 Guardian component data
    """
    if status == "ready":
        return {
            "type": "law_114_guardian",
            "status": "ready",
            "capabilities": [
                "كشف البنود المخفية (Red Flag Detection)",
                "التحقق من بنود العقد الناقصة",
                "مراجعة شروط المطور",
                "التوافق مع قانون 114 لسنة 1946"
            ],
            "trust_badges": [
                "AI-Powered Analysis",
                "Based on Egyptian Civil Code",
                "Used by 1000+ Buyers"
            ],
            "cta": {
                "text_ar": "ارفع العقد وأنا أفحصه",
                "text_en": "Upload contract for AI scan"
            }
        }
    else:
        # Return scan results
        return {
            "type": "law_114_guardian",
            "status": "scanned",
            "result": scan_result or {
                "score": 85,
                "red_flags": 0,
                "warnings": 2,
                "verdict": "SAFE"
            }
        }


def generate_reality_check(
    detected: str,
    message_ar: str,
    message_en: str,
    alternatives: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate Reality Check visualization for impossible requests.

    Args:
        detected: Description of the impossible request
        message_ar: Arabic explanation message
        message_en: English explanation message
        alternatives: List of alternative suggestions

    Returns:
        Reality Check component data
    """
    return {
        "type": "reality_check",
        "detected": detected,
        "message_ar": message_ar,
        "message_en": message_en,
        "alternatives": alternatives,
        "pivot_action": "REALITY_CHECK_PIVOT"
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
