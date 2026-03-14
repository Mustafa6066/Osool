"""
SEO Page Generator — AI Content Module
-----------------------------------------
Generates rich, bilingual SEO content for comparison pages,
project profiles, developer profiles, and area guides using Claude.
"""

import os
import json
import logging
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


DEVELOPER_COMPARISON_PROMPT = """You are Osool's SEO content writer for Egyptian real estate.
Write a detailed comparison between two developers for our website.

Developer 1: {dev1_json}
Developer 2: {dev2_json}

Write in BOTH English and Arabic. Return JSON:
{{
  "en": {{
    "title": "...",
    "intro": "2-3 paragraphs introducing both developers",
    "sections": [
      {{"heading": "Delivery Track Record", "body": "..."}},
      {{"heading": "Finish Quality", "body": "..."}},
      {{"heading": "Resale Value Retention", "body": "..."}},
      {{"heading": "Payment Flexibility", "body": "..."}},
      {{"heading": "Overall Verdict", "body": "..."}}
    ],
    "faq": [{{"q": "...", "a": "..."}}]
  }},
  "ar": {{
    "title": "...",
    "intro": "...",
    "sections": [...],
    "faq": [...]
  }}
}}

Use Egyptian Arabic dialect for the Arabic version.
Include real project names. Be factual, data-driven, and helpful for home buyers.
Keep each section 100-200 words. Target 1500+ total words for SEO."""


AREA_COMPARISON_PROMPT = """You are Osool's SEO content writer for Egyptian real estate.
Write a detailed comparison between two investment areas.

Area 1: {area1_json}
Area 2: {area2_json}

Write in BOTH English and Arabic. Return JSON:
{{
  "en": {{
    "title": "...",
    "intro": "2-3 paragraphs comparing both areas",
    "sections": [
      {{"heading": "Price Per SQM Comparison", "body": "..."}},
      {{"heading": "Year-over-Year Appreciation", "body": "..."}},
      {{"heading": "Rental Yield", "body": "..."}},
      {{"heading": "Infrastructure & Lifestyle", "body": "..."}},
      {{"heading": "Investment Verdict", "body": "..."}}
    ],
    "faq": [{{"q": "...", "a": "..."}}]
  }},
  "ar": {{
    "title": "...",
    "intro": "...",
    "sections": [...],
    "faq": [...]
  }}
}}

Use Egyptian Arabic dialect. Include EGP prices. Be data-driven. 1500+ words."""


PROJECT_PAGE_PROMPT = """You are Osool's SEO content writer. Write a complete project profile page.

Project: {project_json}
Developer: {developer_json}
Area: {area_json}

Return JSON with en/ar sections:
{{
  "en": {{
    "title": "...",
    "intro": "Overview paragraph",
    "sections": [
      {{"heading": "Location & Accessibility", "body": "..."}},
      {{"heading": "Unit Types & Pricing", "body": "..."}},
      {{"heading": "Payment Plans", "body": "..."}},
      {{"heading": "Amenities & Facilities", "body": "..."}},
      {{"heading": "Developer Track Record", "body": "..."}},
      {{"heading": "Investment Potential", "body": "..."}}
    ],
    "faq": [{{"q": "...", "a": "..."}}]
  }},
  "ar": {{ ... }}
}}

Use real EGP prices. Egyptian Arabic dialect. 1500+ words total."""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
async def generate_comparison_content(
    dev1: dict = None, dev2: dict = None,
    area1: dict = None, area2: dict = None,
) -> dict:
    """Generate bilingual comparison content."""
    if dev1 and dev2:
        prompt = DEVELOPER_COMPARISON_PROMPT.format(
            dev1_json=json.dumps(dev1, default=str),
            dev2_json=json.dumps(dev2, default=str),
        )
    elif area1 and area2:
        prompt = AREA_COMPARISON_PROMPT.format(
            area1_json=json.dumps(area1, default=str),
            area2_json=json.dumps(area2, default=str),
        )
    else:
        raise ValueError("Provide either dev1+dev2 or area1+area2")

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


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
async def generate_project_content(
    project: dict, developer: dict, area: dict
) -> dict:
    """Generate bilingual project profile content."""
    prompt = PROJECT_PAGE_PROMPT.format(
        project_json=json.dumps(project, default=str),
        developer_json=json.dumps(developer, default=str),
        area_json=json.dumps(area, default=str),
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
