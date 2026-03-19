"""
Raw Scraper Validation Schemas
-------------------------------
Pydantic models for validating raw scraped data BEFORE it reaches the LLM
normalizer. Catches broken scrapers early — null prices, missing titles,
garbage data — and triggers alerts instead of polluting the vector DB.
"""

import re
import logging
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


class RawScrapedProperty(BaseModel):
    """
    Validates a single property dict straight from the scraper output
    (NEXT_DATA, XHR intercept, or regex tab-parse).

    Rejects properties with null/zero prices, empty titles, or invalid URLs
    before they reach the expensive LLM normalization step.
    """

    title: str = Field(..., min_length=2, description="Property listing title")
    price: float = Field(..., gt=0, description="Price in EGP — must be positive")
    location: Optional[str] = Field(None, min_length=2)
    area: Optional[float] = Field(None, ge=0, description="Size in sqm")
    type: Optional[str] = None
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    finishing: Optional[str] = None
    nawy_url: Optional[str] = None
    compound: Optional[str] = None
    developer: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_placeholder(cls, v: str) -> str:
        stripped = v.strip()
        if stripped.lower() in {"n/a", "none", "null", "undefined", "test", "---"}:
            raise ValueError(f"Title is a placeholder: '{stripped}'")
        return stripped

    @field_validator("price")
    @classmethod
    def price_sanity_check(cls, v: float) -> float:
        # Egyptian real estate prices: minimum realistic ~100K EGP
        if v < 50_000:
            raise ValueError(f"Price {v} is unrealistically low for Egyptian RE market")
        if v > 500_000_000:
            raise ValueError(f"Price {v} exceeds 500M EGP sanity ceiling")
        return v

    @field_validator("nawy_url")
    @classmethod
    def validate_url_pattern(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"https?://", v):
            raise ValueError(f"Invalid URL pattern: '{v}'")
        return v

    @model_validator(mode="after")
    def at_least_location_or_compound(self):
        """At least one geographic identifier should be present."""
        if not self.location and not self.compound:
            raise ValueError("Property must have at least a location or compound name")
        return self


class ScrapeHealthReport(BaseModel):
    """Summary of a scrape batch validation run."""
    total_raw: int = 0
    valid: int = 0
    rejected: int = 0
    errors: list = Field(default_factory=list)

    # Per-field null rates (0.0 - 1.0)
    null_rate_price: float = 0.0
    null_rate_title: float = 0.0
    null_rate_location: float = 0.0
    null_rate_area: float = 0.0

    # Thresholds — alert if exceeded
    ALERT_NULL_THRESHOLD: float = 0.15

    @property
    def needs_alert(self) -> bool:
        """True if any critical field null rate exceeds threshold."""
        return (
            self.null_rate_price > self.ALERT_NULL_THRESHOLD
            or self.null_rate_title > self.ALERT_NULL_THRESHOLD
            or self.null_rate_location > self.ALERT_NULL_THRESHOLD
        )

    @property
    def summary(self) -> str:
        return (
            f"Scrape Health: {self.valid}/{self.total_raw} valid "
            f"({self.rejected} rejected). "
            f"Null rates: price={self.null_rate_price:.1%}, "
            f"title={self.null_rate_title:.1%}, "
            f"location={self.null_rate_location:.1%}, "
            f"area={self.null_rate_area:.1%}"
        )


def validate_raw_batch(raw_properties: list[dict]) -> tuple[list[dict], ScrapeHealthReport]:
    """
    Validate a batch of raw property dicts.
    Returns (valid_properties, health_report).
    """
    report = ScrapeHealthReport(total_raw=len(raw_properties))

    if not raw_properties:
        return [], report

    valid = []
    null_counts = {"price": 0, "title": 0, "location": 0, "area": 0}

    for i, raw in enumerate(raw_properties):
        # Count nulls before validation
        if not raw.get("price"):
            null_counts["price"] += 1
        if not raw.get("title"):
            null_counts["title"] += 1
        if not raw.get("location") and not raw.get("compound"):
            null_counts["location"] += 1
        if not raw.get("area") and not raw.get("size_sqm"):
            null_counts["area"] += 1

        try:
            # Normalize common field name aliases
            normalized = {**raw}
            if "size_sqm" in normalized and "area" not in normalized:
                normalized["area"] = normalized["size_sqm"]

            RawScrapedProperty.model_validate(normalized)
            valid.append(raw)
        except Exception as e:
            report.rejected += 1
            report.errors.append({
                "index": i,
                "title": raw.get("title", "N/A"),
                "error": str(e)[:200],
            })
            if report.rejected <= 5:
                logger.warning(
                    f"⚠️ Raw validation rejected property {i}: {str(e)[:100]}"
                )

    report.valid = len(valid)
    n = max(len(raw_properties), 1)
    report.null_rate_price = null_counts["price"] / n
    report.null_rate_title = null_counts["title"] / n
    report.null_rate_location = null_counts["location"] / n
    report.null_rate_area = null_counts["area"] / n

    if report.needs_alert:
        logger.error(f"🚨 SCRAPER HEALTH ALERT: {report.summary}")
    else:
        logger.info(f"✅ {report.summary}")

    return valid, report
