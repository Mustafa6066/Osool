"""
Report Generator — Dual-Engine AI Module
-------------------------------------------
Generates personalized investment reports using AI analysis
of user preferences, market data, and price histories.
"""

import os
import json
import logging
from datetime import datetime
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


REPORT_PROMPT = """You are Osool's investment analyst for Egyptian real estate.
Generate a personalized investment report for this user profile.

User Profile:
- Budget: {budget_min:,.0f} - {budget_max:,.0f} EGP
- Preferred Areas: {areas}
- Property Types: {types}
- Bedrooms: {bedrooms}
- Timeline: {timeline}

Market Data:
{market_data}

Top Matching Projects:
{projects}

Generate a comprehensive investment report in JSON format:
{{
  "en": {{
    "title": "Your Personalized Investment Report",
    "summary": "Executive summary (2-3 sentences)",
    "market_overview": "Current Egyptian market analysis (3-4 paragraphs)",
    "recommendations": [
      {{
        "project": "Project Name",
        "why": "Why this matches your criteria",
        "roi_estimate": "Estimated 3-year ROI percentage",
        "risk_level": "low/medium/high",
        "best_for": "Investment/Primary residence/Holiday home"
      }}
    ],
    "area_insights": [
      {{
        "area": "Area Name",
        "trend": "Appreciation trend analysis",
        "outlook": "12-month outlook"
      }}
    ],
    "action_plan": "Recommended next steps"
  }},
  "ar": {{ ... same structure in Egyptian Arabic ... }}
}}

Be specific with EGP amounts. Use real project names. Max 5 recommendations."""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
async def generate_investment_report(
    budget_min: int,
    budget_max: int,
    areas: list,
    types: list,
    bedrooms: int | None,
    timeline: str | None,
    market_data: list[dict],
    projects: list[dict],
) -> dict:
    """Generate a personalized AI investment report."""
    prompt = REPORT_PROMPT.format(
        budget_min=budget_min or 0,
        budget_max=budget_max or 0,
        areas=", ".join(areas) if areas else "No preference",
        types=", ".join(types) if types else "Any",
        bedrooms=bedrooms or "Any",
        timeline=timeline or "Flexible",
        market_data=json.dumps(market_data[:10], default=str, indent=2),
        projects=json.dumps(projects[:10], default=str, indent=2),
    )

    response = await _client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
