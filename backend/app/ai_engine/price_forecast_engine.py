"""
Scientific price-per-sqm forecasting engine (per developer / compound / area).

This is a PURE-COMPUTE module — it takes already-fetched series (own points +
an ordered parent chain + a CPI index-level series) and returns a JSON-ready
ForecastBundle. All DB access lives in `forecast_series_builder.py`, which keeps
this layer unit-testable with fixtures (see tests/test_price_forecast_engine.py).

Method (deliberately defensible for SHORT, IRREGULAR, INFLATION-DISTORTED data):

1. Deflate nominal EGP/m² to REAL terms with a CPI INDEX LEVEL series:
   real(t) = nominal(t) * cpi(base) / cpi(t).  A single scalar inflation rate
   cannot deflate 2021 and 2024 points differently — which is the whole point
   around the 2022/2024 EGP devaluations.
2. Fit a robust trend in LOG space: Theil-Sen on ln(real) vs years (29% breakdown
   point tolerates the devaluation outliers OLS would chase). real_cagr = exp(slope)-1.
   Working in log space makes the band multiplicative/asymmetric — the honest shape
   for compounding growth.
3. Empirical-Bayes SHRINKAGE of the log-growth toward parents
   (compound -> developer -> area -> national), with the institutional
   APPRECIATION_BY_REGIME range used as the Bayesian PRIOR variance. Sparse/noisy
   children collapse toward their parent; data-rich children keep their own slope.
   Closed-form normal-normal conjugate update — no MCMC, Railway-friendly.
4. Confidence gated by PROVENANCE first: a series dominated by curated SEED points
   is capped at "indicative" no matter how many points it has — seeded data must
   never be re-served as a high-confidence "data-driven" forecast.
5. Prediction bands floored by the regime spread so smooth seed data cannot yield a
   falsely tight interval. The band is labelled INDICATIVE, not a calibrated
   posterior credible interval.
6. Re-inflate real -> nominal using a FORWARD CPI assumption ONLY (property
   appreciation is already inside real_cagr; adding regime appreciation here would
   double-count growth).

Confidence labels reuse comparison_service's vocabulary: high / moderate / indicative.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Sequence

import numpy as np

try:
    from scipy.stats import theilslopes as _scipy_theilslopes
except Exception:  # pragma: no cover - scipy ships transitively via scikit-learn
    _scipy_theilslopes = None

from app.ai_engine.analytical_engine import (
    APPRECIATION_BY_REGIME,
    MARKET_DATA,
    calculate_real_vs_nominal_appreciation,
    get_regime_key,
)

# Canonical provenance label for the curated seed corpus (scripts/seed_forecast_history.py).
SEED_SOURCE = "analytical_engine_seed_2026"
# Only LIVE-scraped observations count as "real" toward confidence. Curated seeds,
# synthetic 'osool-analytics' simulations, manual entries and backfill anchors do NOT —
# so a forecast can only earn a label above "indicative" once real listing data accrues.
REAL_SOURCES = frozenset({"nawy", "aqarmap"})
# A series must be at least this fraction real observations before it can earn a
# confidence label above "indicative".
REAL_SHARE_FOR_CONFIDENCE = 0.5
# Minimum distinct observations for a series to fit its OWN trend; below this it is
# fully shrunk to its parent (must-fix: n_c < 3 -> use parent entirely).
MIN_POINTS_FOR_OWN_FIT = 3
# Sample-count gates for the data-driven tiers (only reachable when real-dominant).
TIER_HIGH_N = 30
TIER_MODERATE_N = 10
# Floor on the slope sampling SD so a fluke-tight Theil-Sen CI cannot dominate the prior.
SIGMA_FLOOR_LOG = 0.02
# Tier -> minimum band half-width (fraction of point) at the 12-month horizon. Wider
# horizons scale this by sqrt(years). Guarantees an honest band on smooth seed data.
TIER_MIN_HALFWIDTH = {"high": 0.10, "moderate": 0.15, "indicative": 0.30}

DEFAULT_HORIZONS = (6, 12, 24)


# ── Inputs ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SeriesPoint:
    observed_at: date
    nominal_pps: float          # nominal EGP / m²
    source: str                 # 'analytical_engine_seed_2026' | 'nawy' | 'aqarmap' | 'manual' | 'backfill'

    @property
    def is_real(self) -> bool:
        """Only live-scraped observations count as real toward confidence."""
        return self.source.lower() in REAL_SOURCES


@dataclass(frozen=True)
class CpiPoint:
    observed_at: date
    level: float                # CPI INDEX LEVEL (not a rate)


# ── Internal fit result ──────────────────────────────────────────────────────
@dataclass
class TrendFit:
    ok: bool
    n: int
    share_real: float
    slope_log: float = 0.0          # d ln(real_pps) / d year  (continuous real growth)
    sigma_log: float = float("inf") # sampling SD of slope_log
    rel_ci_width: float = float("inf")
    base_pps: Optional[float] = None  # latest NOMINAL price/m² (present-day anchor)
    base_date: Optional[date] = None
    cpi_available: bool = True


# ── Utilities ─────────────────────────────────────────────────────────────────
def _as_date(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    return d


def _years_between(a: date, b: date) -> float:
    return (a - b).days / 365.25


def _interp_cpi(cpi: Sequence[CpiPoint], when: date) -> Optional[float]:
    """Linear-interpolate the CPI index level at `when`; clamp to the series ends."""
    if not cpi:
        return None
    pts = sorted(cpi, key=lambda p: p.observed_at)
    if when <= pts[0].observed_at:
        return pts[0].level
    if when >= pts[-1].observed_at:
        return pts[-1].level
    for lo, hi in zip(pts, pts[1:]):
        if lo.observed_at <= when <= hi.observed_at:
            span = (hi.observed_at - lo.observed_at).days or 1
            frac = (when - lo.observed_at).days / span
            return lo.level + frac * (hi.level - lo.level)
    return pts[-1].level


def theil_sen(t: np.ndarray, y: np.ndarray):
    """Return (slope, intercept, lo_slope, hi_slope). Pure-numpy fallback if scipy absent."""
    if _scipy_theilslopes is not None:
        slope, intercept, lo, hi = _scipy_theilslopes(y, t)
        return float(slope), float(intercept), float(lo), float(hi)
    # Fallback: median of pairwise slopes + percentile band.
    slopes = []
    n = len(t)
    for i in range(n):
        for j in range(i + 1, n):
            dt = t[j] - t[i]
            if dt != 0:
                slopes.append((y[j] - y[i]) / dt)
    slopes = np.asarray(slopes)
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * t))
    lo = float(np.percentile(slopes, 2.5))
    hi = float(np.percentile(slopes, 97.5))
    return slope, intercept, lo, hi


# ── Trend fitting (deflate -> log -> robust slope) ────────────────────────────
def fit_loglinear(points: Sequence[SeriesPoint], cpi: Sequence[CpiPoint]) -> TrendFit:
    """Fit a robust log-linear real-price trend. Returns ok=False when too thin."""
    pts = [p for p in points if p.nominal_pps and p.nominal_pps > 0]
    n = len(pts)
    if n == 0:
        return TrendFit(ok=False, n=0, share_real=0.0)

    pts.sort(key=lambda p: p.observed_at)
    base_pt = pts[-1]
    share_real = sum(1 if p.is_real else 0 for p in pts) / n
    cpi_available = bool(cpi)

    base_date = base_pt.observed_at
    cpi_base = _interp_cpi(cpi, base_date) if cpi_available else None

    t_list, y_list = [], []
    for p in pts:
        if cpi_available and cpi_base:
            cpi_t = _interp_cpi(cpi, p.observed_at) or cpi_base
            real = p.nominal_pps * (cpi_base / cpi_t) if cpi_t else p.nominal_pps
        else:
            real = p.nominal_pps  # no CPI -> nominal trend (flagged; confidence capped)
        t_list.append(_years_between(p.observed_at, base_date))
        y_list.append(math.log(real))

    t = np.asarray(t_list, dtype=float)
    y = np.asarray(y_list, dtype=float)

    # Need >= MIN_POINTS_FOR_OWN_FIT distinct time points to fit an own slope.
    if n < MIN_POINTS_FOR_OWN_FIT or len(np.unique(t)) < 2:
        return TrendFit(ok=False, n=n, share_real=share_real,
                        base_pps=base_pt.nominal_pps, base_date=base_date,
                        cpi_available=cpi_available)

    slope, intercept, lo, hi = theil_sen(t, y)
    if not all(math.isfinite(v) for v in (slope, intercept, lo, hi)):
        return TrendFit(ok=False, n=n, share_real=share_real,
                        base_pps=base_pt.nominal_pps, base_date=base_date,
                        cpi_available=cpi_available)

    sigma = max((hi - lo) / (2 * 1.96), SIGMA_FLOOR_LOG)
    rel_ci = abs(hi - lo) / (abs(slope) + 1e-9)
    return TrendFit(
        ok=True, n=n, share_real=share_real,
        slope_log=slope, sigma_log=sigma, rel_ci_width=rel_ci,
        base_pps=base_pt.nominal_pps, base_date=base_date,
        cpi_available=cpi_available,
    )


# ── Empirical-Bayes shrinkage (normal-normal conjugate) ───────────────────────
def regime_prior(regime_key: str) -> tuple[float, float]:
    """Prior (mean log-growth, variance) from the institutional stabilized-rate range."""
    regime = APPRECIATION_BY_REGIME.get(regime_key, APPRECIATION_BY_REGIME["east_cairo"])
    lo_r, hi_r = regime["stabilized_run_rate_2025_2026"]
    mid = (lo_r + hi_r) / 2.0
    mean_log = math.log1p(mid)
    # Treat the documented band as a ~95% prior interval on annual log-growth.
    tau = (math.log1p(hi_r) - math.log1p(lo_r)) / (2 * 1.96)
    tau2 = max(tau * tau, SIGMA_FLOOR_LOG ** 2)
    return mean_log, tau2


def eb_update(obs_mean: float, obs_var: float, prior_mean: float, prior_var: float) -> tuple[float, float]:
    """Closed-form normal-normal posterior: precision-weighted blend of obs and prior."""
    wp = 1.0 / prior_var
    wo = 1.0 / obs_var
    post_var = 1.0 / (wo + wp)
    post_mean = (obs_mean * wo + prior_mean * wp) * post_var
    return post_mean, post_var


def shrink_chain(own: TrendFit, parents: Sequence[TrendFit], regime_key: str) -> tuple[float, float, str]:
    """
    Cascade prior from national -> ... -> immediate parent -> own.

    `parents` is ordered MOST-GENERAL first (e.g. [national, area, developer]).
    Returns (posterior_log_slope, posterior_var, model_type).
    """
    prior_mean, prior_var = regime_prior(regime_key)
    used_own = False
    # Fold each parent that has a usable own fit; undefined parents leave the prior untouched.
    for p in parents:
        if p.ok:
            prior_mean, prior_var = eb_update(p.slope_log, p.sigma_log ** 2, prior_mean, prior_var)
    # Now the child.
    if own.ok and own.n >= MIN_POINTS_FOR_OWN_FIT:
        post_mean, post_var = eb_update(own.slope_log, own.sigma_log ** 2, prior_mean, prior_var)
        used_own = True
        model_type = "theil_sen_eb"
    else:
        # n_c < 3 (or unusable) -> use the parent/prior entirely.
        post_mean, post_var = prior_mean, prior_var
        model_type = "shrinkage_to_parent"
    if not (math.isfinite(post_mean) and math.isfinite(post_var) and post_var > 0):
        # Degenerate guard: fall back to the regime prior.
        post_mean, post_var = regime_prior(regime_key)
        model_type = "regime_prior"
    return post_mean, post_var, model_type


# ── Confidence tier (provenance first) ────────────────────────────────────────
def assign_tier(own: TrendFit) -> str:
    if not own.cpi_available:
        # Without a CPI index we cannot deflate honestly -> never claim "high".
        return "moderate" if own.share_real >= REAL_SHARE_FOR_CONFIDENCE and own.n >= TIER_MODERATE_N else "indicative"
    if own.share_real < REAL_SHARE_FOR_CONFIDENCE:
        return "indicative"  # seed-dominated: cap regardless of n
    if own.ok and own.n >= TIER_HIGH_N and own.rel_ci_width < 0.5:
        return "high"
    if own.n >= TIER_MODERATE_N:
        return "moderate"
    return "indicative"


# ── Forecast assembly ─────────────────────────────────────────────────────────
def _horizon_forecast(base_pps: float, post_mu: float, post_var: float,
                      fwd_infl_log: float, tier: str, horizon_months: int) -> dict:
    hy = horizon_months / 12.0
    sd = math.sqrt(post_var)
    real_cagr = math.expm1(post_mu)
    nominal_cagr = math.expm1(post_mu + fwd_infl_log)

    point = base_pps * math.exp((post_mu + fwd_infl_log) * hy)
    lo_growth = (post_mu - 1.96 * sd + fwd_infl_log) * hy
    hi_growth = (post_mu + 1.96 * sd + fwd_infl_log) * hy
    lower = base_pps * math.exp(lo_growth)
    upper = base_pps * math.exp(hi_growth)

    # Floor band width by tier (scaled by sqrt horizon) so smooth data can't look tight.
    floor = TIER_MIN_HALFWIDTH.get(tier, 0.30) * math.sqrt(max(hy, 0.5))
    lower = min(lower, point * (1 - floor))
    upper = max(upper, point * (1 + floor))
    lower = max(lower, 1.0)

    return {
        "horizon_months": horizon_months,
        "point": round(point),
        "lower": round(lower),
        "upper": round(upper),
        "real_cagr": round(real_cagr, 4),
        "nominal_cagr": round(nominal_cagr, 4),
    }


def compute_forecast(
    *,
    entity: str,
    level: str,                                  # 'compound' | 'developer' | 'area' | 'national'
    own_points: Sequence[SeriesPoint],
    parent_chain: Sequence[Sequence[SeriesPoint]] = (),   # most-general first
    cpi_points: Sequence[CpiPoint] = (),
    location: str = "",
    developer_name: str = "",
    latest_inflation: Optional[float] = None,
    horizons: Sequence[int] = DEFAULT_HORIZONS,
) -> dict:
    """Compute a full ForecastBundle (JSON-ready dict). Never raises on thin data."""
    regime_key = get_regime_key(location or entity)
    fwd_infl = latest_inflation if latest_inflation is not None else MARKET_DATA.get("inflation_rate", 0.136)
    fwd_infl_log = math.log1p(max(fwd_infl, -0.99))

    own_fit = fit_loglinear(own_points, cpi_points)
    parent_fits = [fit_loglinear(p, cpi_points) for p in parent_chain]

    tier = assign_tier(own_fit)
    post_mu, post_var, model_type = shrink_chain(own_fit, parent_fits, regime_key)

    # Present-day anchor: own latest nominal, else nearest parent's latest nominal.
    base_pps = own_fit.base_pps
    base_date = own_fit.base_date
    if not base_pps:
        for pf in reversed(parent_fits):  # nearest (most specific) parent first
            if pf.base_pps:
                base_pps, base_date = pf.base_pps, pf.base_date
                break

    horizons_out: list[dict] = []
    if base_pps:
        for h in horizons:
            horizons_out.append(_horizon_forecast(base_pps, post_mu, post_var, fwd_infl_log, tier, h))

    # Reuse the canonical real-vs-nominal helper so chat narrative and chart agree.
    rvn = calculate_real_vs_nominal_appreciation(location or entity, inflation_rate=fwd_infl)

    seed_dominated = own_fit.share_real < REAL_SHARE_FOR_CONFIDENCE
    disclaimer_en = (
        "Indicative forecast based on curated market estimates; not investment advice "
        "or a guarantee. Accuracy improves as live transaction data accrues."
        if seed_dominated else
        "Indicative forecast; not investment advice or a guarantee. Forecasts carry "
        "uncertainty bands and may not be realised."
    )
    disclaimer_ar = (
        "توقع استرشادي مبني على تقديرات سوقية منسّقة؛ ليس نصيحة استثمارية أو ضماناً. "
        "تتحسن الدقة مع تراكم بيانات التداول الفعلية."
        if seed_dominated else
        "توقع استرشادي؛ ليس نصيحة استثمارية أو ضماناً. تحمل التوقعات هوامش عدم يقين وقد لا تتحقق."
    )

    headline = horizons_out[1] if len(horizons_out) > 1 else (horizons_out[0] if horizons_out else None)
    headline_12mo_pct = None
    direction = "flat"
    if headline and base_pps:
        headline_12mo_pct = round((headline["point"] / base_pps - 1) * 100, 1)
        direction = "up" if headline_12mo_pct > 1.5 else ("down" if headline_12mo_pct < -1.5 else "flat")

    return {
        "entity": entity,
        "level": level,
        "as_of": base_date.isoformat() if base_date else None,
        "base_price_per_m2": round(base_pps) if base_pps else None,
        "confidence_tier": tier,                       # high | moderate | indicative
        "model_type": model_type,
        "sample_size": own_fit.n,
        "share_real_observations": round(own_fit.share_real, 3),
        "seed_dominated": seed_dominated,
        "cpi_available": own_fit.cpi_available,
        "headline_12mo_pct": headline_12mo_pct,
        "trend_direction": direction,
        "horizons": horizons_out,
        "real_vs_nominal": rvn,
        "regime_key": regime_key,
        "disclaimer": {"en": disclaimer_en, "ar": disclaimer_ar},
    }
