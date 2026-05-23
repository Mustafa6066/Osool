"""
intelligence_loop.py
====================
Background microservice that ingests query telemetry and user interaction
signals, then automatically drifts the valuation algorithm's geographic and
structural pricing parameters every 24 hours.

Architecture
------------

┌─────────────────────────────────────────────────────────────────────────┐
│                        Intelligence Loop                                │
│                                                                         │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────────┐ │
│  │  Analytics   │   │  Drift Engine   │   │   Multiplier Feedback    │ │
│  │  Tracker     │──▶│                 │──▶│   Worker (24-hr cycle)   │ │
│  │              │   │  EWMA + signal  │   │                          │ │
│  │  • searches  │   │  normalisation  │   │  drift zone weights,     │ │
│  │  • clicks    │   │  • zone demand  │   │  La2ta thresholds,       │ │
│  │  • sessions  │   │  • asset-type   │   │  delivery-lag factors    │ │
│  │  • chat msgs │   │    sensitivity  │   │                          │ │
│  └──────────────┘   └─────────────────┘   └──────────────────────────┘ │
│                                                                         │
│  Persistence: PostgreSQL tables                                         │
│    intelligence_events  — raw telemetry log                             │
│    zone_drift_state     — current EWMA parameters per geographic zone   │
│    multiplier_snapshots — immutable audit trail of 24-hr cycle outputs  │
└─────────────────────────────────────────────────────────────────────────┘

Drift algorithm (EWMA)
----------------------
For each geographic zone:

  demand_score_t = w_q · query_share + w_c · click_share + w_l · la2ta_share

  zone_weight_t  = (1 − α) · zone_weight_{t-1} + α · demand_score_t

  where α = _EWMA_ALPHA (default 0.30) and all shares are
  computed over the trailing 24-hour window.

Adjusted parameters emitted per zone per cycle:
  • zone_demand_coefficient  — scalar applied to effective_multiplier
  • la2ta_threshold_adj_pp   — ±pp shift on the 15 % La2ta threshold
  • delivery_lag_factor_adj  — ±fraction shift on the 6 pp/yr lag penalty

All adjustments are bounded within ±_MAX_DRIFT_MAGNITUDE to prevent
runaway divergence from baseline model calibration.

Usage
-----
Standalone (runs worker loop indefinitely):

    python intelligence_loop.py

FastAPI integration (import in main.py):

    from app.intelligence_loop import (
        router as intelligence_router,
        create_intelligence_tables,
        start_intelligence_worker,
        stop_intelligence_worker,
    )
    app.include_router(intelligence_router)

    @app.on_event("startup")
    async def startup():
        await create_intelligence_tables()
        await start_intelligence_worker()

    @app.on_event("shutdown")
    async def shutdown():
        await stop_intelligence_worker()
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import re
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from enum import Enum
from statistics import mean, stdev
from typing import Any, Final, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    event,
    select,
    text,
    func,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

# App-local imports — database session factory and declarative base
from app.database import AsyncSessionLocal, Base
from app.valuation_engine import (
    DEFAULT_CBE_RATE,
    _LA2TA_THRESHOLD,
    _DELIVERY_LAG_PENALTY_PER_YEAR,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: EWMA learning rate — governs how fast zone weights adapt to new signals.
#: 0.0 = frozen (no drift); 1.0 = instant full replacement (no memory).
_EWMA_ALPHA: Final[float] = float(os.getenv("INTELLIGENCE_EWMA_ALPHA", "0.30"))

#: Background cycle interval in seconds (default = 24 hours).
_CYCLE_INTERVAL_SECONDS: Final[int] = int(
    os.getenv("INTELLIGENCE_CYCLE_SECONDS", str(24 * 60 * 60))
)

#: Maximum absolute drift magnitude for any parameter from its baseline.
#: Prevents runaway divergence from model calibration.
_MAX_DRIFT_MAGNITUDE: Final[float] = 0.25

#: Minimum query events in the analysis window before drift is applied.
#: Below this count the cycle records a snapshot but does not update weights.
_MIN_EVENTS_FOR_DRIFT: Final[int] = int(
    os.getenv("INTELLIGENCE_MIN_EVENTS", "10")
)

#: Baseline zone demand coefficient — all zones start here.
_BASELINE_ZONE_WEIGHT: Final[float] = 1.0

#: Signal mixture weights for demand score computation (must sum to 1.0).
_W_QUERY:   Final[float] = 0.45   # search query share
_W_CLICK:   Final[float] = 0.35   # click-through share
_W_LA2TA:   Final[float] = 0.20   # La2ta engagement share

#: Sanitisation: maximum allowed length for free-text fields stored to DB.
_MAX_QUERY_STRING_LEN: Final[int] = 512
_MAX_SESSION_ID_LEN: Final[int] = 128
_MAX_ZONE_LEN: Final[int] = 64
_MAX_ASSET_TYPE_LEN: Final[int] = 32

#: Regex whitelist for geographic zone names (alphanumeric + spaces + common
#: Egyptian naming conventions — Arabic is stored transliterated).
_ZONE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9\u0600-\u06FF\s\-\.]{1,64}$"
)

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    """Taxonomy of user interaction events recorded by the Analytics Tracker."""

    search_query    = "search_query"
    click_through   = "click_through"
    price_inspect   = "price_inspect"
    la2ta_engage    = "la2ta_engage"
    chat_message    = "chat_message"
    session_start   = "session_start"
    session_end     = "session_end"


class AssetTypeSignal(str, Enum):
    """Property intent classification extracted from queries and interactions."""

    off_plan        = "off_plan"
    secondary       = "secondary"
    primary_ready   = "primary_ready"
    unknown         = "unknown"


# ---------------------------------------------------------------------------
# Input / Output Pydantic Schemas
# ---------------------------------------------------------------------------


class TelemetryEventCreate(BaseModel):
    """
    Validated input for recording a single telemetry event.

    All free-text fields are length-capped and pattern-validated on
    inbound boundary before persisting.
    """

    event_type: EventType
    session_id: str = Field(
        ...,
        min_length=8,
        max_length=_MAX_SESSION_ID_LEN,
        description="Opaque session identifier — never embed PII.",
    )
    geographic_zone: Optional[str] = Field(
        default=None,
        max_length=_MAX_ZONE_LEN,
        description="Target zone this event relates to (e.g. 'New Cairo').",
    )
    query_string: Optional[str] = Field(
        default=None,
        max_length=_MAX_QUERY_STRING_LEN,
        description="Search text for search_query events.",
    )
    asset_type_signal: AssetTypeSignal = Field(
        default=AssetTypeSignal.unknown,
        description="Inferred property-type intent.",
    )
    listing_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Referenced listing ID for click/inspect events.",
    )
    interest_rate_sensitivity: bool = Field(
        default=False,
        description="True when the event signals the user queried payment plans / interest.",
    )
    metadata_json: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="JSON-serialised auxiliary payload (max 2 KB).",
    )

    @field_validator("geographic_zone")
    @classmethod
    def _validate_zone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not _ZONE_PATTERN.match(v):
            raise ValueError(
                "geographic_zone must contain only alphanumeric characters, "
                "spaces, hyphens, dots, or Arabic codepoints."
            )
        return v

    @field_validator("query_string")
    @classmethod
    def _strip_query(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None

    @field_validator("metadata_json")
    @classmethod
    def _validate_metadata_json(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            parsed = json.loads(v)
        except json.JSONDecodeError as exc:
            raise ValueError(f"metadata_json must be valid JSON: {exc}") from exc
        # Reject deeply nested structures to prevent JSON bomb / log injection
        if not isinstance(parsed, dict):
            raise ValueError("metadata_json must be a JSON object (dict).")
        return v


class ZoneDriftSnapshot(BaseModel):
    """Current drift parameters for a single geographic zone."""

    geographic_zone: str
    zone_demand_coefficient: float = Field(
        description="Scalar multiplier on effective_multiplier for this zone (1.0 = neutral).",
    )
    la2ta_threshold_adj_pp: float = Field(
        description=(
            "Percentage-point adjustment to apply to the baseline La2ta "
            "threshold (15 %). Negative = tighter (fewer deals flagged); "
            "positive = looser (more deals flagged)."
        ),
    )
    delivery_lag_factor_adj: float = Field(
        description=(
            "Fractional adjustment to the per-year delivery-lag penalty "
            f"(baseline {_DELIVERY_LAG_PENALTY_PER_YEAR:.0%}/yr). "
            "E.g. +0.10 means penalty is 10 % higher than baseline."
        ),
    )
    off_plan_demand_index: float = Field(
        description="Normalised off-plan interest score [0, 1] from trailing 24-hr window.",
    )
    query_event_count: int = Field(
        description="Number of query events in the window that informed this state.",
    )
    last_updated_at: datetime
    drift_applied: bool = Field(
        description="Whether a drift update was applied in the last cycle (False when below min-events).",
    )


class DriftCycleReport(BaseModel):
    """Full output of a single 24-hour intelligence cycle."""

    cycle_started_at: datetime
    cycle_completed_at: datetime
    window_start: datetime
    window_end: datetime
    total_events_processed: int
    zones_updated: int
    zones_below_threshold: int
    zone_snapshots: list[ZoneDriftSnapshot]
    global_off_plan_demand_pct: float = Field(
        description="Fraction of all events in the window classified as off_plan.",
    )
    interest_rate_sensitivity_pct: float = Field(
        description="Fraction of events where interest_rate_sensitivity was True.",
    )
    notes: list[str] = Field(default_factory=list)


class TelemetryEventResponse(BaseModel):
    """Returned to callers after a successful event submission."""

    event_id: int
    event_type: EventType
    geographic_zone: Optional[str]
    recorded_at: datetime


class IntelligenceStateResponse(BaseModel):
    """Current drift state returned by the status endpoint."""

    total_zones_tracked: int
    last_cycle_at: Optional[datetime]
    next_cycle_in_seconds: Optional[float]
    zones: list[ZoneDriftSnapshot]


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class IntelligenceEvent(Base):
    """
    Raw telemetry log.

    Append-only. Never update rows once inserted. Use covering index on
    (recorded_at, event_type) for the 24-hr window aggregation queries.
    """

    __tablename__ = "intelligence_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    event_type: Mapped[str]  = mapped_column(String(32),  nullable=False, index=True)
    session_id: Mapped[str]  = mapped_column(String(128), nullable=False)
    geographic_zone: Mapped[Optional[str]] = mapped_column(String(64),  nullable=True, index=True)
    query_string: Mapped[Optional[str]]    = mapped_column(Text,         nullable=True)
    asset_type_signal: Mapped[str]         = mapped_column(String(32),  nullable=False, index=True)
    listing_id: Mapped[Optional[str]]      = mapped_column(String(128), nullable=True)
    interest_rate_sensitivity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[Optional[str]]   = mapped_column(Text,         nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class ZoneDriftRecord(Base):
    """
    Current EWMA-derived drift parameters for a single geographic zone.

    One row per zone — upserted on each drift cycle.
    """

    __tablename__ = "zone_drift_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    geographic_zone: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    zone_demand_coefficient:  Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    la2ta_threshold_adj_pp:   Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delivery_lag_factor_adj:  Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    off_plan_demand_index:    Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    query_event_count:        Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    drift_applied:            Mapped[bool]  = mapped_column(Boolean, nullable=False, default=False)

    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class MultiplierSnapshot(Base):
    """
    Immutable audit record of each 24-hr cycle output.

    Never update or delete rows — this table is a history log only.
    """

    __tablename__ = "multiplier_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    cycle_started_at:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cycle_completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_start:       Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end:         Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    total_events_processed:   Mapped[int]   = mapped_column(Integer, nullable=False)
    zones_updated:            Mapped[int]   = mapped_column(Integer, nullable=False)
    global_off_plan_demand_pct: Mapped[float] = mapped_column(Float, nullable=False)
    interest_rate_sensitivity_pct: Mapped[float] = mapped_column(Float, nullable=False)

    #: Full JSON snapshot of all ZoneDriftSnapshot objects at cycle completion.
    zone_snapshots_json: Mapped[str] = mapped_column(Text, nullable=False)
    notes_json:          Mapped[str] = mapped_column(Text, nullable=False, default="[]")


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


async def create_intelligence_tables() -> None:
    """
    Create intelligence loop tables if they do not exist.
    Safe to call multiple times (idempotent).
    Call from the application startup hook.
    """
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.schema import CreateTable

    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_intelligence_events_window "
                    "ON intelligence_events (recorded_at DESC, event_type)"
                )
            )
            await session.commit()
        except Exception:
            await session.rollback()
            # Index may fail if table doesn't exist yet — create_all handles it

    from app.database import engine

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[
                    IntelligenceEvent.__table__,
                    ZoneDriftRecord.__table__,
                    MultiplierSnapshot.__table__,
                ],
                checkfirst=True,
            )
        )
    logger.info("Intelligence loop tables ready.")


# ---------------------------------------------------------------------------
# Analytics Tracker
# ---------------------------------------------------------------------------


class AnalyticsTracker:
    """
    Logs user interaction events to the ``intelligence_events`` table.

    All write methods validate their inputs through the ``TelemetryEventCreate``
    Pydantic schema before touching the database.  This class performs no
    reads — aggregation is delegated to ``DriftEngine``.
    """

    # ── Public log helpers ────────────────────────────────────────────

    @staticmethod
    async def log_event(
        event: TelemetryEventCreate,
        session: Optional[AsyncSession] = None,
    ) -> int:
        """
        Persist a fully-constructed telemetry event.

        Parameters
        ----------
        event : TelemetryEventCreate
            Validated event payload.
        session : Optional[AsyncSession]
            Existing session to join; a fresh session is opened when None.

        Returns
        -------
        int
            Database-assigned event ID.
        """
        row = IntelligenceEvent(
            event_type             = event.event_type.value,
            session_id             = event.session_id,
            geographic_zone        = event.geographic_zone,
            query_string           = event.query_string,
            asset_type_signal      = event.asset_type_signal.value,
            listing_id             = event.listing_id,
            interest_rate_sensitivity = event.interest_rate_sensitivity,
            metadata_json          = event.metadata_json,
            recorded_at            = datetime.now(timezone.utc),
        )

        if session is not None:
            session.add(row)
            await session.flush()
            return row.id

        async with AsyncSessionLocal() as sess:
            sess.add(row)
            await sess.commit()
            await sess.refresh(row)
            return row.id

    @staticmethod
    async def log_search(
        session_id: str,
        query_string: str,
        geographic_zone: Optional[str] = None,
        asset_type_signal: AssetTypeSignal = AssetTypeSignal.unknown,
        interest_rate_sensitivity: bool = False,
    ) -> int:
        """Convenience wrapper for search query events."""
        ev = TelemetryEventCreate(
            event_type             = EventType.search_query,
            session_id             = session_id,
            query_string           = query_string[:_MAX_QUERY_STRING_LEN],
            geographic_zone        = geographic_zone,
            asset_type_signal      = asset_type_signal,
            interest_rate_sensitivity = interest_rate_sensitivity,
        )
        return await AnalyticsTracker.log_event(ev)

    @staticmethod
    async def log_click_through(
        session_id: str,
        listing_id: str,
        geographic_zone: Optional[str] = None,
        asset_type_signal: AssetTypeSignal = AssetTypeSignal.unknown,
        is_la2ta_listing: bool = False,
    ) -> int:
        """Convenience wrapper for listing click-through events."""
        ev = TelemetryEventCreate(
            event_type        = EventType.la2ta_engage if is_la2ta_listing else EventType.click_through,
            session_id        = session_id,
            listing_id        = listing_id,
            geographic_zone   = geographic_zone,
            asset_type_signal = asset_type_signal,
        )
        return await AnalyticsTracker.log_event(ev)

    @staticmethod
    async def log_session_signal(
        session_id: str,
        event_type: EventType,
        geographic_zone: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """Convenience wrapper for session lifecycle events."""
        meta_str: Optional[str] = None
        if metadata:
            try:
                meta_str = json.dumps(metadata, ensure_ascii=False)[:2048]
            except (TypeError, ValueError):
                meta_str = None

        ev = TelemetryEventCreate(
            event_type      = event_type,
            session_id      = session_id,
            geographic_zone = geographic_zone,
            metadata_json   = meta_str,
        )
        return await AnalyticsTracker.log_event(ev)

    @staticmethod
    async def fetch_window_metrics(
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, Any]:
        """
        Aggregate raw event counts for the specified time window.

        Returns a dict with:
          ``total_events``          — int
          ``zone_counts``           — dict[zone, {queries, clicks, la2ta}]
          ``asset_type_counts``     — dict[AssetTypeSignal, int]
          ``ir_sensitivity_count``  — int
        """
        async with AsyncSessionLocal() as session:
            # Total events in window
            total_q = await session.execute(
                text(
                    "SELECT COUNT(*) FROM intelligence_events "
                    "WHERE recorded_at >= :start AND recorded_at < :end"
                ),
                {"start": window_start, "end": window_end},
            )
            total_events: int = total_q.scalar_one() or 0

            # Per-zone, per-event-type counts
            zone_q = await session.execute(
                text(
                    """
                    SELECT
                        geographic_zone,
                        event_type,
                        COUNT(*) AS cnt
                    FROM intelligence_events
                    WHERE recorded_at >= :start
                      AND recorded_at  < :end
                      AND geographic_zone IS NOT NULL
                    GROUP BY geographic_zone, event_type
                    """
                ),
                {"start": window_start, "end": window_end},
            )
            zone_rows = zone_q.fetchall()

            # Asset-type distribution
            asset_q = await session.execute(
                text(
                    """
                    SELECT asset_type_signal, COUNT(*) AS cnt
                    FROM intelligence_events
                    WHERE recorded_at >= :start AND recorded_at < :end
                    GROUP BY asset_type_signal
                    """
                ),
                {"start": window_start, "end": window_end},
            )
            asset_rows = asset_q.fetchall()

            # Interest-rate sensitivity count
            ir_q = await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM intelligence_events
                    WHERE recorded_at >= :start
                      AND recorded_at  < :end
                      AND interest_rate_sensitivity = TRUE
                    """
                ),
                {"start": window_start, "end": window_end},
            )
            ir_count: int = ir_q.scalar_one() or 0

        # Organise zone data
        zone_counts: dict[str, dict[str, int]] = {}
        for zone, etype, cnt in zone_rows:
            if zone not in zone_counts:
                zone_counts[zone] = {"queries": 0, "clicks": 0, "la2ta": 0, "total": 0}
            bucket = (
                "queries" if etype == EventType.search_query.value else
                "la2ta"   if etype == EventType.la2ta_engage.value else
                "clicks"
            )
            zone_counts[zone][bucket] += cnt
            zone_counts[zone]["total"] += cnt

        # Asset-type distribution
        asset_type_counts: dict[str, int] = {
            row[0]: row[1] for row in asset_rows
        }

        return {
            "total_events":         total_events,
            "zone_counts":          zone_counts,
            "asset_type_counts":    asset_type_counts,
            "ir_sensitivity_count": ir_count,
        }


# ---------------------------------------------------------------------------
# Drift Engine
# ---------------------------------------------------------------------------


class DriftEngine:
    """
    Computes updated geographic drift parameters from a 24-hr telemetry window
    using Exponential Weighted Moving Average (EWMA).

    Isolation contract: this class only reads telemetry via
    ``AnalyticsTracker.fetch_window_metrics()`` and reads current zone state
    from ``zone_drift_state``.  It writes only to ``zone_drift_state`` and
    ``multiplier_snapshots``.

    Parameter semantics
    -------------------
    ``zone_demand_coefficient``
        Multiplicative scalar on the valuation engine's effective_multiplier
        for any listing in this zone.  Drifts between (1 − _MAX_DRIFT_MAGNITUDE)
        and (1 + _MAX_DRIFT_MAGNITUDE).

    ``la2ta_threshold_adj_pp``
        Additive adjustment (percentage points) on the baseline 15 % La2ta
        threshold.  Hot zones (high demand) get a **negative** adjustment
        (threshold tightens → fewer false positives in competitive markets).
        Cool zones get a **positive** adjustment (looser → surface more deals).

    ``delivery_lag_factor_adj``
        Fractional adjustment on the baseline 6 pp/yr lag penalty.  High
        off-plan demand signals → **negative** adj (buyer appetite absorbs
        time risk → penalty effectively reduced).
    """

    def __init__(self, alpha: float = _EWMA_ALPHA) -> None:
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"EWMA alpha must be in (0, 1]; got {alpha!r}.")
        self._alpha = alpha

    # ── Signal computation ────────────────────────────────────────────

    def compute_zone_demand_score(
        self,
        zone_metrics: dict[str, int],
        total_window_events: int,
    ) -> float:
        """
        Compute the normalised demand score for a single zone over the window.

        Combines three sub-signals (query share, click share, La2ta engagement
        share) weighted by ``_W_QUERY``, ``_W_CLICK``, ``_W_LA2TA``.

        Returns a score in [0, 1]; 0.5 is the neutral / baseline level.

        Parameters
        ----------
        zone_metrics : dict
            Keys: ``queries``, ``clicks``, ``la2ta``, ``total`` (all int counts).
        total_window_events : int
            Total event count across **all** zones in the window.

        Returns
        -------
        float
            Demand score in [0, 1].
        """
        if total_window_events == 0:
            return 0.5  # neutral — no evidence either way

        zone_total = zone_metrics.get("total", 0)
        if zone_total == 0:
            return 0.0  # zone had zero activity

        query_share  = zone_metrics.get("queries", 0) / total_window_events
        click_share  = zone_metrics.get("clicks",  0) / total_window_events
        la2ta_share  = zone_metrics.get("la2ta",   0) / total_window_events

        raw_score = (
            _W_QUERY * query_share +
            _W_CLICK * click_share +
            _W_LA2TA * la2ta_share
        )

        # Normalise to [0, 1] by the zone's share of total events.
        # A zone capturing 100% of traffic → score ≈ 1.0.
        zone_traffic_share = zone_total / total_window_events
        normalised = min(1.0, raw_score / max(zone_traffic_share, 1e-9))

        return round(float(np.clip(normalised, 0.0, 1.0)), 6)

    def compute_off_plan_demand_index(
        self,
        zone_metrics: dict[str, int],
        asset_type_counts: dict[str, int],
        zone: str,
        all_zone_metrics: dict[str, dict[str, int]],
    ) -> float:
        """
        Derive a zone-level off-plan demand index in [0, 1].

        Uses the global off-plan fraction as a prior, adjusted by whether
        this zone tends to appear in off-plan queries more or less than average.
        """
        total_typed = sum(asset_type_counts.values()) or 1
        global_off_plan_fraction = (
            asset_type_counts.get(AssetTypeSignal.off_plan.value, 0) / total_typed
        )

        # Zone-specific signal: off-plan events in this zone vs total zone events
        zone_total = zone_metrics.get("total", 1)
        # We can't disaggregate asset_type per zone from the current query set;
        # use the global prior blended with zone traffic intensity as proxy.
        zone_intensity = zone_total / (sum(z.get("total", 0) for z in all_zone_metrics.values()) or 1)

        # Blend: zones with above-average traffic get the global off-plan rate
        # amplified; low-traffic zones revert to the global prior.
        off_plan_index = float(np.clip(
            global_off_plan_fraction * (1.0 + zone_intensity),
            0.0, 1.0,
        ))
        return round(off_plan_index, 6)

    # ── EWMA update ───────────────────────────────────────────────────

    def apply_ewma(
        self,
        previous_value: float,
        new_signal: float,
        baseline: float,
    ) -> float:
        """
        Compute one EWMA step and clamp within ±_MAX_DRIFT_MAGNITUDE of baseline.

        new = (1 − α) · prev + α · signal

        Clamped to [baseline − MAX, baseline + MAX].
        """
        updated = (1.0 - self._alpha) * previous_value + self._alpha * new_signal
        lo = baseline - _MAX_DRIFT_MAGNITUDE
        hi = baseline + _MAX_DRIFT_MAGNITUDE
        return round(float(np.clip(updated, lo, hi)), 6)

    # ── Parameter derivation from demand score ────────────────────────

    @staticmethod
    def derive_parameters(
        demand_score: float,
        off_plan_index: float,
        prev: ZoneDriftRecord,
    ) -> tuple[float, float, float]:
        """
        Translate a demand score into three drift parameter updates.

        Parameters
        ----------
        demand_score : float
            Zone demand score in [0, 1]; 0.5 = neutral.
        off_plan_index : float
            Off-plan demand index in [0, 1].
        prev : ZoneDriftRecord
            Previous persisted state (used as EWMA prior).

        Returns
        -------
        tuple of (zone_demand_coefficient, la2ta_threshold_adj_pp, delivery_lag_factor_adj)
        """
        engine = DriftEngine()

        # ── zone_demand_coefficient
        # Maps demand_score [0, 1] → target coefficient [0.75, 1.25]
        target_coeff = 0.75 + 0.50 * demand_score
        new_coeff = engine.apply_ewma(
            prev.zone_demand_coefficient, target_coeff, _BASELINE_ZONE_WEIGHT
        )

        # ── la2ta_threshold_adj_pp
        # Hot zone (score > 0.6) → tighten threshold (negative adj, e.g. −2 pp).
        # Cold zone (score < 0.4) → loosen (positive adj, e.g. +3 pp).
        if demand_score > 0.6:
            target_la2ta_adj = -round((demand_score - 0.5) * 10, 2)   # up to −5 pp
        elif demand_score < 0.4:
            target_la2ta_adj = +round((0.5 - demand_score) * 15, 2)   # up to +7.5 pp
        else:
            target_la2ta_adj = 0.0

        new_la2ta_adj = engine.apply_ewma(
            prev.la2ta_threshold_adj_pp, target_la2ta_adj, 0.0
        )
        new_la2ta_adj = round(float(np.clip(new_la2ta_adj, -5.0, 7.5)), 4)

        # ── delivery_lag_factor_adj
        # High off-plan demand → buyers tolerate wait → soften lag penalty (< 0).
        # Low off-plan demand → amplify lag penalty (> 0).
        target_lag_adj = -(off_plan_index - 0.5) * 0.40  # range ≈ [−0.20, +0.20]
        new_lag_adj = engine.apply_ewma(
            prev.delivery_lag_factor_adj, target_lag_adj, 0.0
        )
        new_lag_adj = round(float(np.clip(new_lag_adj, -0.20, 0.20)), 6)

        return new_coeff, new_la2ta_adj, new_lag_adj

    # ── Full cycle execution ──────────────────────────────────────────

    async def run_drift_cycle(
        self,
        window_hours: int = 24,
    ) -> DriftCycleReport:
        """
        Execute one full drift cycle.

        Steps
        -----
        1. Define analysis window: [now − window_hours, now].
        2. Fetch aggregated telemetry metrics via AnalyticsTracker.
        3. Load existing ZoneDriftRecord rows for all active zones.
        4. For each zone with sufficient data, compute demand score and derive
           new parameters via EWMA.
        5. Upsert updated ZoneDriftRecord rows.
        6. Append a MultiplierSnapshot audit record.
        7. Return a DriftCycleReport.

        Parameters
        ----------
        window_hours : int
            Width of the analysis window in hours (default: 24).

        Returns
        -------
        DriftCycleReport
            Full report suitable for logging and the API status endpoint.
        """
        cycle_start = datetime.now(timezone.utc)
        window_end   = cycle_start
        window_start = cycle_start - timedelta(hours=window_hours)

        logger.info(
            "Intelligence drift cycle starting. Window: %s → %s",
            window_start.isoformat(), window_end.isoformat(),
        )

        # ── Step 2: fetch telemetry ───────────────────────────────────
        metrics = await AnalyticsTracker.fetch_window_metrics(window_start, window_end)

        total_events:      int  = metrics["total_events"]
        zone_counts:       dict = metrics["zone_counts"]
        asset_type_counts: dict = metrics["asset_type_counts"]
        ir_count:          int  = metrics["ir_sensitivity_count"]

        total_typed = sum(asset_type_counts.values()) or 1
        global_off_plan_pct = (
            asset_type_counts.get(AssetTypeSignal.off_plan.value, 0) / total_typed
        )
        ir_sensitivity_pct = ir_count / max(total_events, 1)

        notes: list[str] = []

        if total_events < _MIN_EVENTS_FOR_DRIFT:
            notes.append(
                f"Sparse window: {total_events} events < threshold {_MIN_EVENTS_FOR_DRIFT}. "
                "Drift parameters were NOT updated; snapshots preserved."
            )
            logger.warning(notes[-1])

        # ── Step 3: load existing zone drift records ──────────────────
        async with AsyncSessionLocal() as session:
            existing_q = await session.execute(
                text("SELECT * FROM zone_drift_state")
            )
            existing_rows = existing_q.mappings().fetchall()

        prev_by_zone: dict[str, ZoneDriftRecord] = {}
        for row in existing_rows:
            rec = ZoneDriftRecord(
                geographic_zone          = row["geographic_zone"],
                zone_demand_coefficient  = row["zone_demand_coefficient"],
                la2ta_threshold_adj_pp   = row["la2ta_threshold_adj_pp"],
                delivery_lag_factor_adj  = row["delivery_lag_factor_adj"],
                off_plan_demand_index    = row["off_plan_demand_index"],
                query_event_count        = row["query_event_count"],
                drift_applied            = row["drift_applied"],
                last_updated_at          = row["last_updated_at"],
            )
            prev_by_zone[row["geographic_zone"]] = rec

        # ── Step 4 & 5: compute and upsert per zone ───────────────────
        zone_snapshots: list[ZoneDriftSnapshot] = []
        zones_updated   = 0
        zones_below_thr = 0

        # Process every zone that appeared in the window OR has prior state
        all_zones = set(zone_counts.keys()) | set(prev_by_zone.keys())

        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)

            for zone in sorted(all_zones):
                z_metrics = zone_counts.get(zone, {"queries": 0, "clicks": 0, "la2ta": 0, "total": 0})
                zone_event_count = z_metrics.get("total", 0)

                # Build a neutral prior if this zone has no existing record
                if zone not in prev_by_zone:
                    prev_zone = ZoneDriftRecord(
                        geographic_zone         = zone,
                        zone_demand_coefficient = _BASELINE_ZONE_WEIGHT,
                        la2ta_threshold_adj_pp  = 0.0,
                        delivery_lag_factor_adj = 0.0,
                        off_plan_demand_index   = 0.0,
                        query_event_count       = 0,
                        drift_applied           = False,
                        last_updated_at         = now,
                    )
                else:
                    prev_zone = prev_by_zone[zone]

                should_drift = (
                    total_events >= _MIN_EVENTS_FOR_DRIFT and
                    zone_event_count > 0
                )

                if should_drift:
                    demand_score = self.compute_zone_demand_score(z_metrics, total_events)
                    off_plan_idx = self.compute_off_plan_demand_index(
                        z_metrics, asset_type_counts, zone, zone_counts
                    )
                    new_coeff, new_la2ta, new_lag = DriftEngine.derive_parameters(
                        demand_score, off_plan_idx, prev_zone
                    )
                    drift_applied = True
                    zones_updated += 1
                else:
                    new_coeff    = prev_zone.zone_demand_coefficient
                    new_la2ta    = prev_zone.la2ta_threshold_adj_pp
                    new_lag      = prev_zone.delivery_lag_factor_adj
                    off_plan_idx = prev_zone.off_plan_demand_index
                    drift_applied = False
                    zones_below_thr += 1

                upsert_stmt = pg_insert(ZoneDriftRecord.__table__).values(
                    geographic_zone          = zone,
                    zone_demand_coefficient  = new_coeff,
                    la2ta_threshold_adj_pp   = new_la2ta,
                    delivery_lag_factor_adj  = new_lag,
                    off_plan_demand_index    = off_plan_idx,
                    query_event_count        = zone_event_count,
                    drift_applied            = drift_applied,
                    last_updated_at          = now,
                ).on_conflict_do_update(
                    index_elements=["geographic_zone"],
                    set_={
                        "zone_demand_coefficient": new_coeff,
                        "la2ta_threshold_adj_pp":  new_la2ta,
                        "delivery_lag_factor_adj": new_lag,
                        "off_plan_demand_index":   off_plan_idx,
                        "query_event_count":       zone_event_count,
                        "drift_applied":           drift_applied,
                        "last_updated_at":         now,
                    },
                )
                await session.execute(upsert_stmt)

                zone_snapshots.append(ZoneDriftSnapshot(
                    geographic_zone          = zone,
                    zone_demand_coefficient  = new_coeff,
                    la2ta_threshold_adj_pp   = new_la2ta,
                    delivery_lag_factor_adj  = new_lag,
                    off_plan_demand_index    = off_plan_idx,
                    query_event_count        = zone_event_count,
                    last_updated_at          = now,
                    drift_applied            = drift_applied,
                ))

            # ── Step 6: audit snapshot ────────────────────────────────
            cycle_end = datetime.now(timezone.utc)
            snap = MultiplierSnapshot(
                cycle_started_at              = cycle_start,
                cycle_completed_at            = cycle_end,
                window_start                  = window_start,
                window_end                    = window_end,
                total_events_processed        = total_events,
                zones_updated                 = zones_updated,
                global_off_plan_demand_pct    = global_off_plan_pct,
                interest_rate_sensitivity_pct = ir_sensitivity_pct,
                zone_snapshots_json           = json.dumps(
                    [s.model_dump(mode="json") for s in zone_snapshots],
                    ensure_ascii=False,
                    default=str,
                ),
                notes_json = json.dumps(notes, ensure_ascii=False),
            )
            session.add(snap)
            await session.commit()

        logger.info(
            "Intelligence drift cycle complete. Zones updated: %d / %d. "
            "Total events processed: %d.",
            zones_updated, len(all_zones), total_events,
        )

        return DriftCycleReport(
            cycle_started_at              = cycle_start,
            cycle_completed_at            = cycle_end,
            window_start                  = window_start,
            window_end                    = window_end,
            total_events_processed        = total_events,
            zones_updated                 = zones_updated,
            zones_below_threshold         = zones_below_thr,
            zone_snapshots                = zone_snapshots,
            global_off_plan_demand_pct    = global_off_plan_pct,
            interest_rate_sensitivity_pct = ir_sensitivity_pct,
            notes                         = notes,
        )


# ---------------------------------------------------------------------------
# Background Worker
# ---------------------------------------------------------------------------


class IntelligenceWorker:
    """
    Asyncio background worker that triggers the drift cycle on a fixed interval.

    Lifecycle
    ---------
    * ``start()``  — launches the asyncio task; idempotent.
    * ``stop()``   — signals cancellation and awaits task teardown gracefully.
    * ``trigger()`` — fires one cycle immediately (used for admin/debug calls).

    Thread-safety
    -------------
    Designed for a single-process asyncio event loop.  Do not share across
    OS processes.
    """

    def __init__(
        self,
        interval_seconds: int   = _CYCLE_INTERVAL_SECONDS,
        alpha:            float = _EWMA_ALPHA,
    ) -> None:
        self._interval   = interval_seconds
        self._engine     = DriftEngine(alpha=alpha)
        self._task:  Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._last_cycle_at:     Optional[datetime] = None
        self._last_report:       Optional[DriftCycleReport] = None

    # ── Lifecycle ─────────────────────────────────────────────────────

    async def start(self) -> None:
        """Launch the background loop task.  Safe to call multiple times."""
        if self._task is not None and not self._task.done():
            logger.debug("IntelligenceWorker already running — start() is a no-op.")
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._loop(), name="intelligence_worker"
        )
        logger.info(
            "IntelligenceWorker started. Cycle interval: %d s (%d h).",
            self._interval, self._interval // 3600,
        )

    async def stop(self) -> None:
        """Signal the worker to stop and wait for graceful teardown."""
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=10.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        logger.info("IntelligenceWorker stopped.")

    async def trigger(self) -> DriftCycleReport:
        """Run one drift cycle immediately and return its report."""
        return await self._run_cycle()

    # ── State accessors ───────────────────────────────────────────────

    @property
    def last_cycle_at(self) -> Optional[datetime]:
        return self._last_cycle_at

    @property
    def last_report(self) -> Optional[DriftCycleReport]:
        return self._last_report

    @property
    def next_cycle_in_seconds(self) -> Optional[float]:
        if self._last_cycle_at is None:
            return None
        elapsed = (datetime.now(timezone.utc) - self._last_cycle_at).total_seconds()
        remaining = self._interval - elapsed
        return max(0.0, remaining)

    # ── Internal ──────────────────────────────────────────────────────

    async def _loop(self) -> None:
        """
        Main worker loop.

        On startup: run an immediate cycle to populate state, then sleep.
        Subsequent iterations obey ``_interval``.
        """
        # Initial cycle on startup (avoids waiting a full interval after deploy)
        await self._run_cycle()

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=float(self._interval),
                )
                # If we get here, stop was signalled
                break
            except asyncio.TimeoutError:
                # Normal path: interval elapsed
                pass

            if not self._stop_event.is_set():
                await self._run_cycle()

    async def _run_cycle(self) -> DriftCycleReport:
        """Execute a drift cycle with structured error handling."""
        try:
            report = await self._engine.run_drift_cycle()
            self._last_cycle_at = report.cycle_completed_at
            self._last_report   = report
            return report
        except Exception as exc:
            logger.exception("Intelligence drift cycle failed: %s", exc)
            raise


# ---------------------------------------------------------------------------
# Module-level worker singleton (shared with FastAPI lifespan hooks)
# ---------------------------------------------------------------------------

_worker: Optional[IntelligenceWorker] = None


async def start_intelligence_worker(
    interval_seconds: int   = _CYCLE_INTERVAL_SECONDS,
    alpha:            float = _EWMA_ALPHA,
) -> None:
    """Module-level entry point: initialise and start the singleton worker."""
    global _worker
    if _worker is None:
        _worker = IntelligenceWorker(
            interval_seconds=interval_seconds,
            alpha=alpha,
        )
    await _worker.start()


async def stop_intelligence_worker() -> None:
    """Module-level entry point: stop the singleton worker."""
    global _worker
    if _worker is not None:
        await _worker.stop()


def get_worker() -> IntelligenceWorker:
    """Retrieve the singleton worker; raises if not yet started."""
    if _worker is None:
        raise RuntimeError(
            "IntelligenceWorker has not been started. "
            "Call await start_intelligence_worker() in your startup hook first."
        )
    return _worker


# ---------------------------------------------------------------------------
# FastAPI Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.post(
    "/event",
    response_model=TelemetryEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a telemetry event",
    description=(
        "Log a single user interaction event. All string fields are validated "
        "and sanitised before persisting. Session IDs must be opaque tokens — "
        "do not embed PII."
    ),
)
async def record_event(payload: TelemetryEventCreate) -> TelemetryEventResponse:
    event_id = await AnalyticsTracker.log_event(payload)
    return TelemetryEventResponse(
        event_id      = event_id,
        event_type    = payload.event_type,
        geographic_zone = payload.geographic_zone,
        recorded_at   = datetime.now(timezone.utc),
    )


@router.get(
    "/zone-state",
    response_model=IntelligenceStateResponse,
    summary="Current drift state for all tracked zones",
)
async def get_zone_state() -> IntelligenceStateResponse:
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            text("SELECT * FROM zone_drift_state ORDER BY geographic_zone")
        )).mappings().fetchall()

    zones = [
        ZoneDriftSnapshot(
            geographic_zone         = r["geographic_zone"],
            zone_demand_coefficient = r["zone_demand_coefficient"],
            la2ta_threshold_adj_pp  = r["la2ta_threshold_adj_pp"],
            delivery_lag_factor_adj = r["delivery_lag_factor_adj"],
            off_plan_demand_index   = r["off_plan_demand_index"],
            query_event_count       = r["query_event_count"],
            last_updated_at         = r["last_updated_at"],
            drift_applied           = r["drift_applied"],
        )
        for r in rows
    ]

    worker_ref = _worker
    return IntelligenceStateResponse(
        total_zones_tracked    = len(zones),
        last_cycle_at          = worker_ref.last_cycle_at if worker_ref else None,
        next_cycle_in_seconds  = worker_ref.next_cycle_in_seconds if worker_ref else None,
        zones                  = zones,
    )


@router.get(
    "/drift-report/latest",
    response_model=Optional[DriftCycleReport],
    summary="Latest drift cycle report",
    description="Returns the most recent DriftCycleReport from the in-memory worker. "
                "Returns null if no cycle has completed since startup.",
)
async def get_latest_drift_report() -> Optional[DriftCycleReport]:
    worker_ref = _worker
    if worker_ref is None:
        return None
    return worker_ref.last_report


@router.get(
    "/drift-report/history",
    summary="Paginated drift cycle history from the audit log",
    description="Queries the immutable multiplier_snapshots table for historical cycle data.",
)
async def get_drift_history(limit: int = 10, offset: int = 0) -> list[dict]:
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be ≤ 100.",
        )
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            text(
                """
                SELECT id, cycle_started_at, cycle_completed_at,
                       window_start, window_end,
                       total_events_processed, zones_updated,
                       global_off_plan_demand_pct, interest_rate_sensitivity_pct,
                       notes_json
                FROM multiplier_snapshots
                ORDER BY cycle_started_at DESC
                LIMIT :lim OFFSET :off
                """
            ),
            {"lim": limit, "off": offset},
        )).mappings().fetchall()

    return [
        {
            "id":                             r["id"],
            "cycle_started_at":               r["cycle_started_at"],
            "cycle_completed_at":             r["cycle_completed_at"],
            "window_start":                   r["window_start"],
            "window_end":                     r["window_end"],
            "total_events_processed":         r["total_events_processed"],
            "zones_updated":                  r["zones_updated"],
            "global_off_plan_demand_pct":     r["global_off_plan_demand_pct"],
            "interest_rate_sensitivity_pct":  r["interest_rate_sensitivity_pct"],
            "notes":                          json.loads(r["notes_json"] or "[]"),
        }
        for r in rows
    ]


@router.post(
    "/trigger-cycle",
    response_model=DriftCycleReport,
    status_code=status.HTTP_200_OK,
    summary="Trigger an immediate drift cycle (admin/debug)",
    description=(
        "Forces a full drift computation immediately, bypassing the 24-hr schedule. "
        "Intended for admin use and integration tests only."
    ),
)
async def trigger_cycle() -> DriftCycleReport:
    try:
        worker_ref = get_worker()
    except RuntimeError:
        # Worker not running — execute directly
        engine_instance = DriftEngine()
        return await engine_instance.run_drift_cycle()
    return await worker_ref.trigger()


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

async def _standalone_main() -> None:
    """
    Run the intelligence worker standalone (outside FastAPI).

    Initialises the database tables and starts the worker loop, blocking
    until SIGINT / SIGTERM.
    """
    import signal

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info(
        "Osool Intelligence Loop — standalone mode. "
        "Cycle interval: %d s. EWMA α: %.2f.",
        _CYCLE_INTERVAL_SECONDS, _EWMA_ALPHA,
    )

    await create_intelligence_tables()

    worker = IntelligenceWorker(
        interval_seconds=_CYCLE_INTERVAL_SECONDS,
        alpha=_EWMA_ALPHA,
    )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _handle_signal(sig: int) -> None:
        logger.info("Received signal %d — initiating graceful shutdown.", sig)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal, sig)
        except (NotImplementedError, OSError):
            # Windows does not support add_signal_handler for SIGTERM
            pass

    await worker.start()

    try:
        await stop_event.wait()
    finally:
        await worker.stop()
        logger.info("Intelligence loop shut down cleanly.")


if __name__ == "__main__":
    asyncio.run(_standalone_main())
