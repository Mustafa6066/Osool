"""
valuation_engine.py
===================
Production-grade property intrinsic value calculator for the Egyptian real
estate market.

Implements
----------
* NPV-based financial timeline flattening using the CBE base corridor rate.
* Structural feature normalization (floor, view orientation, delivery lag).
* La2ta (لقطة) arbitrage opportunity detection against compound mean and
  developer rack rate.

Design constraints
------------------
* Fully isolated from transaction execution scripts — no DB writes, no side
  effects, no external HTTP calls.
* All domain I/O uses Pydantic v2 schemas with explicit validation.
* NumPy is used exclusively for numerical precision in vectorised discount
  factor calculations.
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Final, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Central Bank of Egypt base corridor interest rate. Last-resort fallback
#: used only when neither the ``MarketIndicator`` row nor the
#: ``CBE_BASE_RATE`` env var is set. Resolution order at startup:
#:   1. ``MarketIndicator`` row keyed by ``bank_cd_rate`` (refreshed by admin)
#:   2. ``CBE_BASE_RATE`` env var (operational override)
#:   3. This constant
DEFAULT_CBE_RATE: Final[float] = 0.22

#: Discount threshold below the compound mean that flags a La2ta anomaly.
_LA2TA_THRESHOLD: Final[float] = 0.15

_GROUND_FLOOR: Final[int] = 0
_ELEVATED_FLOOR_MIN: Final[int] = 5           # strictly greater than this
_GROUND_GARDEN_PREMIUM: Final[float] = 0.12   # +12 pp to feature multiplier
_ELEVATED_PREMIUM: Final[float] = 0.05        # +5 pp to feature multiplier
_DELIVERY_LAG_PENALTY_PER_YEAR: Final[float] = 0.06  # −6 pp per off-plan year
_MIN_FEATURE_MULTIPLIER: Final[float] = 0.10  # hard floor to prevent negatives

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ViewOrientation(str, Enum):
    """Spatial view classification for a residential unit."""

    premium_pool = "premium_pool"
    open_landscape = "open_landscape"
    side_street = "side_street"
    rear_view = "rear_view"


#: Signed premium weights (percentage points added to feature multiplier).
_VIEW_WEIGHTS: Final[dict[ViewOrientation, float]] = {
    ViewOrientation.premium_pool: 0.15,
    ViewOrientation.open_landscape: 0.08,
    ViewOrientation.side_street: 0.00,
    ViewOrientation.rear_view: -0.10,
}

# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------


class PaymentTimeline(BaseModel):
    """Describes the instalment structure of a property purchase."""

    down_payment: float = Field(
        ...,
        gt=0,
        description="Upfront payment due at contract signing (EGP).",
    )
    installments_per_year: int = Field(
        ...,
        ge=1,
        le=12,
        description="Number of periodic instalments per calendar year (e.g. 4 = quarterly).",
    )
    total_years: int = Field(
        ...,
        ge=1,
        le=30,
        description="Total instalment tenure in years.",
    )
    periodic_installment_amount: float = Field(
        ...,
        gt=0,
        description="EGP value of each individual periodic payment.",
    )
    upfront_cash_discount_pct: float = Field(
        default=0.0,
        ge=0.0,
        lt=1.0,
        description=(
            "Fractional discount offered by the developer/seller for full "
            "upfront cash settlement (e.g. 0.10 = 10 %). "
            "When non-zero, this path is preferred over NPV discounting."
        ),
    )

    @model_validator(mode="after")
    def _plan_total_must_be_positive(self) -> "PaymentTimeline":
        plan_total = (
            self.down_payment
            + self.installments_per_year
            * self.total_years
            * self.periodic_installment_amount
        )
        if plan_total <= 0:
            raise ValueError(
                f"Computed payment plan total ({plan_total:,.2f} EGP) must be positive."
            )
        return self


class PropertyListing(BaseModel):
    """Full descriptor for a property unit submitted for valuation."""

    listing_id: str = Field(..., min_length=1, description="Unique listing identifier.")
    compound_id: str = Field(..., min_length=1, description="Parent compound identifier.")
    geographic_zone: str = Field(
        ...,
        min_length=1,
        description="Area / district label (e.g. 'New Cairo', 'Sheikh Zayed').",
    )
    total_price: float = Field(..., gt=0, description="Nominal asking price in EGP.")
    size_sqm: float = Field(..., gt=0, description="Net usable area in square metres.")
    floor_level: int = Field(..., ge=0, description="Floor number — 0 denotes ground floor.")
    has_private_garden: bool = Field(
        ...,
        description="True when the unit has exclusive garden access.",
    )
    view_orientation: ViewOrientation
    delivery_year: int = Field(
        ...,
        ge=2020,
        le=2040,
        description="Calendar year in which the unit is contractually delivered.",
    )
    current_academic_year: int = Field(
        default=2026,
        ge=2020,
        le=2040,
        description="Reference year for off-plan lag calculation (default: 2026).",
    )
    payment_timeline: Optional[PaymentTimeline] = Field(
        default=None,
        description="Instalment plan; None implies a full cash transaction.",
    )
    is_secondary_market: bool = Field(
        default=True,
        description="True when this is a resale listing (not developer primary stock).",
    )

    @field_validator("delivery_year")
    @classmethod
    def _delivery_year_range(cls, v: int) -> int:
        # Range already enforced by Field(ge=, le=); secondary-market units
        # may legitimately have delivery_year <= current_academic_year.
        return v

    @model_validator(mode="after")
    def _garden_requires_ground_floor(self) -> "PropertyListing":
        # Private garden is physically plausible on any floor (roof terraces
        # exist), but ground-floor gardens receive a specific valuation bonus.
        # No hard rejection — the feature multiplier handles the economics.
        return self


# ---------------------------------------------------------------------------
# Output / response schemas
# ---------------------------------------------------------------------------


class NormalizedAssetMetrics(BaseModel):
    """Result of structural feature normalization for a single listing."""

    listing_id: str
    compound_id: str
    cash_npv_egp: float = Field(
        description="Cash-equivalent NPV of all payment obligations (EGP)."
    )
    normalized_price_per_sqm: float = Field(
        description="Feature- and lag-adjusted NPV price per square metre (EGP/m²)."
    )
    feature_multiplier: float = Field(
        description="Combined structural and orientation adjustment factor before lag."
    )
    delivery_lag_penalty_pp: float = Field(
        description=(
            "Percentage-point penalty deducted from feature multiplier for "
            "off-plan delivery lag (0.0 if already delivered)."
        )
    )
    effective_multiplier: float = Field(
        description="Final multiplier after lag penalty (feature_multiplier − lag_penalty_pp)."
    )


class La2taOpportunity(BaseModel):
    """Per-listing La2ta classification within a compound."""

    listing_id: str
    compound_id: str
    normalized_price_per_sqm: float
    compound_mean_price_per_sqm: float
    discount_vs_mean_pct: float = Field(
        description=(
            "How much cheaper the listing is vs. compound mean, as a percentage. "
            "Positive = cheaper; negative = premium over mean."
        )
    )
    is_la2ta: bool = Field(
        description=(
            "True when the unit is on the secondary market AND its normalised "
            "price/sqm is ≥ 15 % below the compound mean."
        )
    )
    developer_rack_rate_sqm: float
    discount_vs_rack_rate_pct: float = Field(
        description=(
            "Discount relative to the developer's published rack rate. "
            "Positive = cheaper than developer pricing."
        )
    )


class La2taAnalysisResult(BaseModel):
    """Aggregated La2ta analysis for a target listing and its compound peers."""

    target_listing_id: str
    compound_id: str
    compound_mean_price_per_sqm: float
    developer_rack_rate_sqm: float
    secondary_benchmark_count: int = Field(
        description="Number of secondary-market listings used to compute the compound mean."
    )
    opportunities: list[La2taOpportunity] = Field(
        description="La2ta classification for the target and every benchmark in the compound."
    )


# ---------------------------------------------------------------------------
# Valuation Engine
# ---------------------------------------------------------------------------


class ValuationEngine:
    """
    Core quantitative valuation engine for Egyptian real estate.

    Parameters
    ----------
    cbe_rate : float
        Central Bank of Egypt base corridor interest rate used as the
        discount rate for NPV calculations.  Must be in the open interval
        (0, 1).  Defaults to ``DEFAULT_CBE_RATE`` (0.22).
    """

    def __init__(self, cbe_rate: float = DEFAULT_CBE_RATE) -> None:
        if not (0.0 < cbe_rate < 1.0):
            raise ValueError(
                f"cbe_rate must be in the open interval (0, 1), got {cbe_rate!r}."
            )
        self._cbe_rate: float = cbe_rate

    # ------------------------------------------------------------------
    # Public property — read-only access for observability
    # ------------------------------------------------------------------

    @property
    def cbe_rate(self) -> float:
        """Active CBE discount rate (read-only)."""
        return self._cbe_rate

    # ------------------------------------------------------------------
    # 1.  Financial Timeline Mathematical Flattening
    # ------------------------------------------------------------------

    def calculate_effective_cash_npv(
        self,
        total_price: float,
        plan: Optional[PaymentTimeline],
    ) -> float:
        """
        Flatten a multi-year payment plan to its cash-equivalent NPV in EGP.

        Decision tree
        ~~~~~~~~~~~~~
        1. **No plan supplied** — listing is a full cash transaction; return
           ``total_price`` unmodified (no time-value adjustment needed).
        2. **``upfront_cash_discount_pct > 0``** — the seller has already
           embedded a cash-settlement discount; apply it directly:
           ``npv = total_price × (1 − discount_pct)``.
        3. **Instalment plan without explicit cash discount** — compute the
           NPV of the full cash-flow stream:

           * Down payment at *t = 0* (no discounting).
           * *N = installments_per_year × total_years* periodic payments,
             each discounted at the periodic CBE rate
             *r_p = cbe_rate / installments_per_year*.

           Uses the closed-form present-value-of-annuity formula, validated
           numerically with NumPy for large *N*:

           .. math::

               \\text{NPV} = DP + PMT \\cdot
               \\frac{1 - (1 + r_p)^{-N}}{r_p}

        Parameters
        ----------
        total_price : float
            Nominal asking price in EGP.
        plan : Optional[PaymentTimeline]
            Instalment plan descriptor; ``None`` implies outright cash.

        Returns
        -------
        float
            Cash-equivalent NPV in EGP (always ≤ ``total_price``).

        Raises
        ------
        ValueError
            If ``total_price`` is non-positive.
        AssertionError
            If the computed NPV exceeds ``total_price`` by more than 5 %,
            indicating a data inconsistency in the payment plan.
        """
        if total_price <= 0:
            raise ValueError(
                f"total_price must be positive, got {total_price!r}."
            )

        # Path 1: outright cash — no discounting
        if plan is None:
            return total_price

        # Path 2: seller-quoted cash discount applied directly
        if plan.upfront_cash_discount_pct > 0.0:
            return total_price * (1.0 - plan.upfront_cash_discount_pct)

        # Path 3: NPV of instalment stream
        n_periods: int = plan.installments_per_year * plan.total_years
        r_p: float = self._cbe_rate / plan.installments_per_year
        pmt: float = plan.periodic_installment_amount

        if r_p == 0.0:
            # Degenerate case: zero discount rate (should not occur at CBE = 22 %)
            pv_instalments: float = float(pmt * n_periods)
        else:
            # Vectorised discount: PV = Σ PMT / (1 + r_p)^t,  t = 1 … N
            t_vec = np.arange(1, n_periods + 1, dtype=np.float64)
            pv_instalments = float(pmt * np.sum(np.power(1.0 + r_p, -t_vec)))

        npv: float = plan.down_payment + pv_instalments

        # Sanity assertion: NPV must not exceed nominal price by > 5 %
        if npv > total_price * 1.05:
            raise AssertionError(
                f"Computed NPV ({npv:,.0f} EGP) exceeds the nominal price "
                f"({total_price:,.0f} EGP) by more than 5 %. "
                "Verify payment plan field values for internal consistency."
            )

        return npv

    # ------------------------------------------------------------------
    # 2.  Structural Feature Normalization
    # ------------------------------------------------------------------

    def normalize_asset_price_per_sqm(
        self,
        listing: PropertyListing,
    ) -> NormalizedAssetMetrics:
        """
        Convert a raw listing to a feature-adjusted NPV price per square metre.

        Adjustment cascade
        ~~~~~~~~~~~~~~~~~~
        1. Compute cash NPV via :meth:`calculate_effective_cash_npv`.
        2. Derive *base price/sqm* = NPV ÷ ``size_sqm``.
        3. Build the **feature multiplier** from structural and orientation
           premiums / discounts:

           ========================================  ==========
           Condition                                  Δ (pp)
           ========================================  ==========
           Ground floor **with** private garden       +12 pp
           Floor > 5 (elevated premium)               +5 pp
           View: ``premium_pool``                     +15 pp
           View: ``open_landscape``                   +8 pp
           View: ``side_street``                      0 pp
           View: ``rear_view``                        −10 pp
           ========================================  ==========

        4. Apply **delivery-lag penalty**: deduct 6 pp from the feature
           multiplier for each year between ``current_academic_year`` and
           ``delivery_year``.  The effective multiplier is floored at
           ``_MIN_FEATURE_MULTIPLIER`` (0.10) to prevent degenerate outputs.

        5. ``normalized_price_per_sqm`` = base_per_sqm × effective_multiplier.

        Parameters
        ----------
        listing : PropertyListing
            Full listing descriptor.

        Returns
        -------
        NormalizedAssetMetrics
            Contains the NPV, per-component multipliers, and final
            normalized price/sqm.
        """
        # Step 1 – cash NPV
        cash_npv: float = self.calculate_effective_cash_npv(
            listing.total_price, listing.payment_timeline
        )

        # Step 2 – raw baseline per sqm
        base_per_sqm: float = cash_npv / listing.size_sqm

        # Step 3 – structural & orientation feature multiplier
        feature_multiplier: float = 1.0

        if listing.floor_level == _GROUND_FLOOR and listing.has_private_garden:
            feature_multiplier += _GROUND_GARDEN_PREMIUM

        if listing.floor_level > _ELEVATED_FLOOR_MIN:
            feature_multiplier += _ELEVATED_PREMIUM

        feature_multiplier += _VIEW_WEIGHTS[listing.view_orientation]

        # Step 4 – delivery-lag penalty (percentage points deducted)
        lag_years: int = max(0, listing.delivery_year - listing.current_academic_year)
        lag_penalty_pp: float = _DELIVERY_LAG_PENALTY_PER_YEAR * lag_years

        effective_multiplier: float = max(
            _MIN_FEATURE_MULTIPLIER,
            feature_multiplier - lag_penalty_pp,
        )

        normalized_per_sqm: float = base_per_sqm * effective_multiplier

        return NormalizedAssetMetrics(
            listing_id=listing.listing_id,
            compound_id=listing.compound_id,
            cash_npv_egp=round(cash_npv, 2),
            normalized_price_per_sqm=round(normalized_per_sqm, 2),
            feature_multiplier=round(feature_multiplier, 6),
            delivery_lag_penalty_pp=round(lag_penalty_pp, 6),
            effective_multiplier=round(effective_multiplier, 6),
        )

    # ------------------------------------------------------------------
    # 3.  La2ta (لقطة) Arbitrage Detection
    # ------------------------------------------------------------------

    def identify_la2ta_opportunities(
        self,
        target_listing: PropertyListing,
        benchmark_listings: list[PropertyListing],
        developer_rack_rate_sqm: float,
    ) -> La2taAnalysisResult:
        """
        Identify undervalued secondary-market units relative to compound peers.

        A listing is classified as a *La2ta* (لقطة — "a great market find")
        anomaly when **all** of the following hold:

        * ``is_secondary_market`` is ``True``.
        * Its normalised cash-equivalent price/sqm is ≥ 15 % **below** the
          mathematical mean of normalised prices across all active secondary-
          market listings in the same compound.

        The compound mean is computed exclusively from secondary-market
        benchmarks to avoid contamination by developer primary pricing.

        The analysis evaluates the target listing **and** every benchmark
        that shares the same ``compound_id``, producing a ranked
        opportunities list.

        Parameters
        ----------
        target_listing : PropertyListing
            The primary unit under analysis.
        benchmark_listings : list[PropertyListing]
            Active comparable listings.  At minimum one entry must share
            ``compound_id`` with the target and have ``is_secondary_market``
            set to ``True``.
        developer_rack_rate_sqm : float
            Developer's published primary-market rack rate per sqm (EGP/m²),
            used as an additional reference anchor.

        Returns
        -------
        La2taAnalysisResult
            Full analysis including compound mean, La2ta classification for
            each candidate, and comparison against the developer rack rate.

        Raises
        ------
        ValueError
            If ``benchmark_listings`` is empty, ``developer_rack_rate_sqm``
            is non-positive, no benchmarks share the compound, or no
            secondary-market benchmarks exist in the compound.
        AssertionError
            If the computed compound mean is non-positive (data integrity
            failure).
        """
        if not benchmark_listings:
            raise ValueError(
                "benchmark_listings must contain at least one listing."
            )
        if developer_rack_rate_sqm <= 0:
            raise ValueError(
                f"developer_rack_rate_sqm must be positive, "
                f"got {developer_rack_rate_sqm!r}."
            )

        compound_id: str = target_listing.compound_id

        # Restrict benchmarks to the same compound
        same_compound: list[PropertyListing] = [
            b for b in benchmark_listings if b.compound_id == compound_id
        ]
        if not same_compound:
            raise ValueError(
                f"No benchmark listings found for compound_id={compound_id!r}. "
                "Ensure benchmark_listings include listings from the same compound."
            )

        # Secondary-market subset used to derive the compound mean
        secondary_benchmarks: list[PropertyListing] = [
            b for b in same_compound if b.is_secondary_market
        ]
        if not secondary_benchmarks:
            raise ValueError(
                f"Compound {compound_id!r} has no secondary-market benchmark "
                "listings.  La2ta detection requires at least one active resale "
                "comparable to establish the compound reference mean."
            )

        # Normalise all secondary benchmarks
        benchmark_metrics: list[NormalizedAssetMetrics] = [
            self.normalize_asset_price_per_sqm(b) for b in secondary_benchmarks
        ]

        # Compound mean over secondary normalised prices
        prices_arr = np.array(
            [m.normalized_price_per_sqm for m in benchmark_metrics],
            dtype=np.float64,
        )
        compound_mean: float = float(np.mean(prices_arr))

        assert compound_mean > 0, (
            f"Compound mean ({compound_mean}) must be positive — "
            "verify benchmark listing data integrity."
        )

        # Evaluate the target + all compound-scoped benchmarks
        # Deduplicate by listing_id so the target is not double-counted
        # if it is already present in benchmark_listings.
        seen_ids: set[str] = set()
        candidates: list[PropertyListing] = []
        for listing in [target_listing] + same_compound:
            if listing.listing_id not in seen_ids:
                candidates.append(listing)
                seen_ids.add(listing.listing_id)

        opportunities: list[La2taOpportunity] = []
        for candidate in candidates:
            metrics = self.normalize_asset_price_per_sqm(candidate)

            discount_vs_mean: float = (
                compound_mean - metrics.normalized_price_per_sqm
            ) / compound_mean

            discount_vs_rack: float = (
                developer_rack_rate_sqm - metrics.normalized_price_per_sqm
            ) / developer_rack_rate_sqm

            is_la2ta: bool = (
                candidate.is_secondary_market
                and discount_vs_mean >= _LA2TA_THRESHOLD
            )

            opportunities.append(
                La2taOpportunity(
                    listing_id=candidate.listing_id,
                    compound_id=candidate.compound_id,
                    normalized_price_per_sqm=round(metrics.normalized_price_per_sqm, 2),
                    compound_mean_price_per_sqm=round(compound_mean, 2),
                    discount_vs_mean_pct=round(discount_vs_mean * 100, 4),
                    is_la2ta=is_la2ta,
                    developer_rack_rate_sqm=round(developer_rack_rate_sqm, 2),
                    discount_vs_rack_rate_pct=round(discount_vs_rack * 100, 4),
                )
            )

        # Sort: confirmed La2ta first, then deepest discount-to-mean
        opportunities.sort(
            key=lambda o: (-int(o.is_la2ta), -o.discount_vs_mean_pct)
        )

        return La2taAnalysisResult(
            target_listing_id=target_listing.listing_id,
            compound_id=compound_id,
            compound_mean_price_per_sqm=round(compound_mean, 2),
            developer_rack_rate_sqm=round(developer_rack_rate_sqm, 2),
            secondary_benchmark_count=len(secondary_benchmarks),
            opportunities=opportunities,
        )


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Osool Valuation Engine",
    description=(
        "Property intrinsic value calculator for the Egyptian real estate market.\n\n"
        "Provides NPV-based financial flattening, structural feature normalization, "
        "and La2ta (لقطة) arbitrage detection against compound secondary-market peers."
    ),
    version="1.0.0",
    docs_url="/valuation/docs",
    redoc_url="/valuation/redoc",
)

# Module-level engine singleton. The startup rate is the env override
# (CBE_BASE_RATE) if present, falling back to DEFAULT_CBE_RATE. The
# FastAPI app's lifespan handler should call set_cbe_rate() after reading
# the MarketIndicator row keyed by bank_cd_rate, giving DB the final word.
def _resolve_startup_cbe_rate() -> float:
    """Resolve the boot-time CBE rate from env or constant."""
    raw = os.getenv("CBE_BASE_RATE")
    if raw is None or raw.strip() == "":
        return DEFAULT_CBE_RATE
    try:
        rate = float(raw)
    except ValueError:
        _logger.warning(
            "CBE_BASE_RATE=%r is not a number; falling back to %.4f",
            raw,
            DEFAULT_CBE_RATE,
        )
        return DEFAULT_CBE_RATE
    if not (0.0 < rate < 1.0):
        _logger.warning(
            "CBE_BASE_RATE=%.4f outside (0,1); falling back to %.4f",
            rate,
            DEFAULT_CBE_RATE,
        )
        return DEFAULT_CBE_RATE
    return rate


_engine: ValuationEngine = ValuationEngine(cbe_rate=_resolve_startup_cbe_rate())


def set_cbe_rate(new_rate: float, *, source: str = "runtime") -> float:
    """
    Replace the module engine with one using ``new_rate``.

    Called by the FastAPI startup hook after reading the latest CBE rate
    from the ``MarketIndicator`` table. Safe to call repeatedly; raises
    ``ValueError`` if the rate is outside the open interval (0, 1).

    Returns the rate now in use so callers can log it.
    """
    if not (0.0 < new_rate < 1.0):
        raise ValueError(
            f"new_rate must be in the open interval (0, 1), got {new_rate!r}."
        )
    global _engine
    previous = _engine.cbe_rate
    _engine = ValuationEngine(cbe_rate=new_rate)
    _logger.info(
        "CBE rate updated: %.4f -> %.4f (source=%s)", previous, new_rate, source
    )
    return new_rate


def get_cbe_rate() -> float:
    """Return the CBE rate currently in use by the module engine."""
    return _engine.cbe_rate


# ---------------------------------------------------------------------------
# Down-payment normalization
# ---------------------------------------------------------------------------


def normalize_down_payment_to_egp(down_payment: object, total_price: float) -> float:
    """Coerce a down-payment value to an absolute EGP amount.

    Listings store the down payment inconsistently:
      * a fraction (``0.10`` = 10 %),
      * a percentage (``10`` = 10 %), or
      * an absolute EGP figure (``500000``).

    Real EGP down payments are always > 100 and percentages are <= 100, so the
    magnitude disambiguates safely. Returns 0.0 on bad/non-positive input.
    """
    try:
        dp = float(down_payment)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0
    if dp <= 0 or total_price <= 0:
        return 0.0
    if dp <= 1.0:
        return total_price * dp
    if dp <= 100.0:
        return total_price * (dp / 100.0)
    return dp


# ---------------------------------------------------------------------------
# Request bodies for composite endpoints
# ---------------------------------------------------------------------------


class NpvRequest(BaseModel):
    """Request body for the NPV flattening endpoint."""

    total_price: float = Field(..., gt=0, description="Nominal asking price in EGP.")
    payment_timeline: Optional[PaymentTimeline] = Field(
        default=None,
        description="Optional instalment plan; omit for a full cash transaction.",
    )


class La2taRequest(BaseModel):
    """Request body for the La2ta arbitrage detection endpoint."""

    target_listing: PropertyListing
    benchmark_listings: list[PropertyListing] = Field(..., min_length=1)
    developer_rack_rate_sqm: float = Field(
        ..., gt=0, description="Developer primary-market rack rate per sqm (EGP/m²)."
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get(
    "/valuation/health",
    tags=["ops"],
    summary="Engine health check",
)
def health_check() -> dict[str, object]:
    """Return service liveness and active CBE rate."""
    return {"status": "ok", "cbe_rate": _engine.cbe_rate}


@app.post(
    "/valuation/npv",
    tags=["valuation"],
    summary="Flatten a payment plan to its cash-equivalent NPV",
    response_model=dict,
)
def api_calculate_npv(body: NpvRequest) -> dict[str, float]:
    """
    Convert a multi-year instalment plan to a single cash-equivalent NPV.

    - If no ``payment_timeline`` is supplied, the nominal price is returned
      unchanged (outright cash transaction).
    - If ``upfront_cash_discount_pct > 0``, the cash discount path is used.
    - Otherwise the CBE corridor rate is applied to discount future outflows.
    """
    try:
        npv = _engine.calculate_effective_cash_npv(
            body.total_price, body.payment_timeline
        )
        return {
            "total_price_egp": round(body.total_price, 2),
            "cash_npv_egp": round(npv, 2),
            "cbe_rate_applied": _engine.cbe_rate,
        }
    except (ValueError, AssertionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@app.post(
    "/valuation/normalize",
    response_model=NormalizedAssetMetrics,
    tags=["valuation"],
    summary="Normalize a listing to feature-adjusted price per sqm",
)
def api_normalize_listing(listing: PropertyListing) -> NormalizedAssetMetrics:
    """
    Return the structural-feature-adjusted NPV price per square metre
    for a single listing, including the breakdown of floor, view, and
    delivery-lag components.
    """
    try:
        return _engine.normalize_asset_price_per_sqm(listing)
    except (ValueError, AssertionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@app.post(
    "/valuation/la2ta",
    response_model=La2taAnalysisResult,
    tags=["valuation"],
    summary="Identify La2ta (لقطة) arbitrage opportunities in a compound",
)
def api_identify_la2ta(request: La2taRequest) -> La2taAnalysisResult:
    """
    Detect secondary-market listings priced ≥ 15 % below the compound mean.

    The compound mean is computed from secondary-market benchmarks only.
    Results are sorted: confirmed La2ta anomalies first, then by depth of
    discount relative to the compound mean.
    """
    try:
        return _engine.identify_la2ta_opportunities(
            target_listing=request.target_listing,
            benchmark_listings=request.benchmark_listings,
            developer_rack_rate_sqm=request.developer_rack_rate_sqm,
        )
    except (ValueError, AssertionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
