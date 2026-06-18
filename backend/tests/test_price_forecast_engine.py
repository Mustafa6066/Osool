"""
Unit tests for the pure-compute price forecast engine.

No DB / app startup required — exercises the math directly, including the
adversarial-critique must-fixes:
  * finite & bounded posterior on the REAL seed dicts (degenerate n),
  * provenance cap (seed-dominated series can never exceed 'indicative'),
  * log-space CAGR (exp(slope)-1) recovers a known growth rate,
  * CPI index-level deflation makes real_cagr < nominal_cagr under inflation,
  * n<3 -> shrink-to-parent branch is taken and stays finite,
  * forward re-inflation = (1+real)*(1+infl)-1 (no double counting),
  * band half-width floored by tier so smooth data can't look tight.
"""
import math
from datetime import date

import pytest

from app.ai_engine.price_forecast_engine import (
    SeriesPoint, CpiPoint, fit_loglinear, theil_sen, regime_prior,
    eb_update, shrink_chain, assign_tier, compute_forecast,
    MIN_POINTS_FOR_OWN_FIT, REAL_SHARE_FOR_CONFIDENCE, TIER_MIN_HALFWIDTH,
)
from app.ai_engine.analytical_engine import AREA_PRICE_HISTORY, DEVELOPER_PRICE_HISTORY

import numpy as np


def _annual_points(series: dict, source: str):
    """{year: price} -> [SeriesPoint at Jan 1]. Skips non-year metadata keys."""
    years = sorted(y for y in series if isinstance(y, int))
    return [SeriesPoint(observed_at=date(y, 1, 1), nominal_pps=float(series[y]), source=source)
            for y in years]


def _flat_cpi(years=range(2018, 2031), level=100.0):
    return [CpiPoint(observed_at=date(y, 1, 1), level=level) for y in years]


# ── trend fitting ─────────────────────────────────────────────────────────────
def test_theil_sen_recovers_known_log_slope():
    # y = ln(real) with slope 0.20/yr -> real_cagr = exp(0.20)-1 ~= 0.2214
    t = np.array([0, 1, 2, 3, 4, 5], dtype=float)
    y = 0.20 * t + 9.0
    slope, intercept, lo, hi = theil_sen(t, y)
    assert slope == pytest.approx(0.20, abs=1e-6)
    assert lo <= slope <= hi


def test_fit_loglinear_recovers_cagr_with_flat_cpi():
    # 20% nominal annual growth, flat CPI -> real_cagr ~= 0.20
    base = 10000.0
    pts = [SeriesPoint(date(2021 + i, 1, 1), base * (1.20 ** i), "nawy") for i in range(6)]
    fit = fit_loglinear(pts, _flat_cpi())
    assert fit.ok
    assert math.expm1(fit.slope_log) == pytest.approx(0.20, abs=0.01)


def test_theil_sen_resists_single_outlier():
    base = 10000.0
    pts = [SeriesPoint(date(2021 + i, 1, 1), base * (1.15 ** i), "nawy") for i in range(7)]
    clean = fit_loglinear(pts, _flat_cpi())
    pts[3] = SeriesPoint(date(2024, 1, 1), 1_000_000.0, "nawy")  # wild spike
    noisy = fit_loglinear(pts, _flat_cpi())
    # Robust slope barely moves despite a 70x outlier.
    assert abs(noisy.slope_log - clean.slope_log) < 0.05


# ── empirical-Bayes shrinkage ──────────────────────────────────────────────────
def test_regime_prior_is_finite_and_positive_var():
    for key in ("east_cairo", "north_coast", "nac", "red_sea", "west_cairo", "unknown_key"):
        mean, var = regime_prior(key)
        assert math.isfinite(mean) and math.isfinite(var) and var > 0


def test_eb_update_between_obs_and_prior():
    post_mean, post_var = eb_update(0.30, 0.04, 0.10, 0.01)
    assert 0.10 <= post_mean <= 0.30          # blended between prior and obs
    assert post_var < 0.01                    # precision increased


def test_shrink_chain_thin_child_uses_parent():
    # Child with < 3 points -> not ok -> must shrink to parent/prior, stay finite.
    child = fit_loglinear(
        [SeriesPoint(date(2025, 1, 1), 50000, "nawy"), SeriesPoint(date(2026, 1, 1), 55000, "nawy")],
        _flat_cpi(),
    )
    assert not child.ok and child.n < MIN_POINTS_FOR_OWN_FIT
    parent = fit_loglinear(_annual_points(AREA_PRICE_HISTORY["New Cairo"], "nawy"), _flat_cpi())
    mu, var, model = shrink_chain(child, [parent], "east_cairo")
    assert model == "shrinkage_to_parent"
    assert math.isfinite(mu) and math.isfinite(var) and var > 0


# ── full bundle on the REAL seed corpus ────────────────────────────────────────
def test_compute_forecast_finite_and_bounded_on_all_seed_areas():
    """Must-fix #1: posterior finite & bounded for the actual seed dicts."""
    for area, series in AREA_PRICE_HISTORY.items():
        bundle = compute_forecast(
            entity=area, level="area",
            own_points=_annual_points(series, "analytical_engine_seed_2026"),
            cpi_points=_flat_cpi(), location=area,
        )
        assert bundle["horizons"], f"no horizons for {area}"
        for h in bundle["horizons"]:
            assert h["lower"] <= h["point"] <= h["upper"], f"band disordered for {area}"
            for k in ("point", "lower", "upper", "real_cagr", "nominal_cagr"):
                assert math.isfinite(h[k]), f"non-finite {k} for {area}"
            # No absurd doublings/quarterings over 2y from a stabilized regime.
            assert h["point"] < bundle["base_price_per_m2"] * 4


def test_compute_forecast_finite_on_all_seed_developers():
    for dev, series in DEVELOPER_PRICE_HISTORY.items():
        bundle = compute_forecast(
            entity=dev, level="developer",
            own_points=_annual_points(series, "analytical_engine_seed_2026"),
            cpi_points=_flat_cpi(), location=series.get("area", ""),
        )
        for h in bundle["horizons"]:
            assert h["lower"] <= h["point"] <= h["upper"]


# ── provenance gate ─────────────────────────────────────────────────────────────
def test_seed_dominated_series_capped_at_indicative_even_with_many_points():
    """Must-fix #2: seed data never earns a confidence label above 'indicative'."""
    # 40 monthly seed points -> n is large but provenance is 100% seed.
    pts = [SeriesPoint(date(2022 + i // 12, i % 12 + 1, 1), 30000 * (1.012 ** i),
                       "analytical_engine_seed_2026") for i in range(40)]
    bundle = compute_forecast(entity="X", level="compound", own_points=pts,
                              cpi_points=_flat_cpi(), location="New Cairo")
    assert bundle["seed_dominated"] is True
    assert bundle["confidence_tier"] == "indicative"


def test_real_dominant_series_can_exceed_indicative():
    pts = [SeriesPoint(date(2022 + i // 12, i % 12 + 1, 1), 30000 * (1.012 ** i), "nawy")
           for i in range(40)]
    fit = fit_loglinear(pts, _flat_cpi())
    assert fit.share_real >= REAL_SHARE_FOR_CONFIDENCE
    assert assign_tier(fit) in ("moderate", "high")


# ── CPI deflation & re-inflation ────────────────────────────────────────────────
def test_cpi_deflation_makes_real_below_nominal():
    """Index-level CPI rising over time -> real growth < nominal growth."""
    nominal = [SeriesPoint(date(2021 + i, 1, 1), 10000 * (1.25 ** i), "nawy") for i in range(6)]
    rising_cpi = [CpiPoint(date(2021 + i, 1, 1), 100 * (1.18 ** i)) for i in range(6)]
    real_fit = fit_loglinear(nominal, rising_cpi)
    nom_fit = fit_loglinear(nominal, _flat_cpi())
    assert real_fit.slope_log < nom_fit.slope_log  # deflation removed inflation


def test_forward_reinflation_is_multiplicative_not_additive():
    pts = [SeriesPoint(date(2021 + i, 1, 1), 10000 * (1.10 ** i), "nawy") for i in range(6)]
    bundle = compute_forecast(entity="X", level="area", own_points=pts,
                              cpi_points=_flat_cpi(), location="New Cairo",
                              latest_inflation=0.13)
    h12 = next(h for h in bundle["horizons"] if h["horizon_months"] == 12)
    expected = (1 + h12["real_cagr"]) * 1.13 - 1
    assert h12["nominal_cagr"] == pytest.approx(expected, abs=1e-3)


# ── band honesty ────────────────────────────────────────────────────────────────
def test_band_halfwidth_floored_by_tier():
    # Seed-dominated -> indicative -> >= 30% half-width at 12mo.
    pts = _annual_points(AREA_PRICE_HISTORY["New Cairo"], "analytical_engine_seed_2026")
    bundle = compute_forecast(entity="New Cairo", level="area", own_points=pts,
                              cpi_points=_flat_cpi(), location="New Cairo")
    h12 = next(h for h in bundle["horizons"] if h["horizon_months"] == 12)
    half = (h12["upper"] - h12["point"]) / h12["point"]
    assert half >= TIER_MIN_HALFWIDTH["indicative"] - 0.001


# ── degenerate inputs ────────────────────────────────────────────────────────────
def test_empty_own_points_falls_back_to_parent_anchor():
    parent = _annual_points(AREA_PRICE_HISTORY["New Cairo"], "analytical_engine_seed_2026")
    bundle = compute_forecast(entity="Empty Compound", level="compound",
                              own_points=[], parent_chain=[parent],
                              cpi_points=_flat_cpi(), location="New Cairo")
    assert bundle["sample_size"] == 0
    assert bundle["base_price_per_m2"]  # anchored from parent
    assert bundle["confidence_tier"] == "indicative"


def test_no_points_anywhere_does_not_crash():
    bundle = compute_forecast(entity="Nowhere", level="compound", own_points=[],
                              parent_chain=[], cpi_points=[], location="New Cairo")
    assert bundle["horizons"] == [] or bundle["base_price_per_m2"] is None
    assert bundle["confidence_tier"] == "indicative"
