"""
Scraper Health / Drift Guard
----------------------------
The existing AnomalyDetector watches *price* medians. It is blind to the
failure that actually starves the intelligence loop: a scraper whose target
changed its HTML/CSS or tripped Cloudflare returns ZERO rows, or rows whose
fields all fail to parse (nulls). That batch sails through price checks as
"safe" and — worse — if it becomes the "latest run", the stale-marking job can
flag the entire catalog as unavailable.

This guard adds a STRUCTURAL health check, complementary to AnomalyDetector:
  * empty batch          -> scraper likely broken or blocked (critical)
  * count << baseline     -> partial break / partial block (degraded)
  * required fields mostly null -> schema drift; selectors stopped matching (degraded)

`assess_batch` is pure and fully testable. `record_and_alert` emits Prometheus
gauges (if available) and reuses the existing send_alert (Sentry + Discord).

Callers use `verdict.should_block_downstream` to refuse destructive follow-ups
(e.g. don't register an empty run as "latest" before stale-marking).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)

DEFAULT_REQUIRED_FIELDS = ("price", "compound", "size_sqm")


# ── Prometheus (optional) ────────────────────────────────────────────────────
try:  # pragma: no cover — metrics are best-effort
    from prometheus_client import Gauge, Counter

    _G_LAST_COUNT = Gauge(
        "osool_scraper_last_batch_count",
        "Items in the most recent scrape batch, per source.",
        ["source"],
    )
    _G_HEALTH = Gauge(
        "osool_scraper_health",
        "Scraper structural health (1=ok, 0=degraded/empty), per source.",
        ["source"],
    )
    _C_DRIFT = Counter(
        "osool_scraper_drift_total",
        "Count of degraded/empty scrape batches, per source and status.",
        ["source", "status"],
    )
    _PROM = True
except Exception:  # prometheus_client absent
    _PROM = False


@dataclass
class HealthVerdict:
    source: str
    status: str  # "ok" | "degraded" | "empty"
    count: int
    baseline_count: Optional[int] = None
    field_null_rates: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.status == "ok"

    @property
    def should_block_downstream(self) -> bool:
        """Refuse destructive follow-ups (stale-marking, baseline updates) when
        the batch is empty or degraded — a broken scrape must not be treated as
        a fresh, authoritative view of the catalog."""
        return self.status != "ok"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "count": self.count,
            "baseline_count": self.baseline_count,
            "field_null_rates": self.field_null_rates,
            "reasons": self.reasons,
        }


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (int, float)):
        return v == 0  # a required numeric of 0 (e.g. price) counts as unparsed
    return False


def assess_batch(
    source: str,
    items: Sequence[Any],
    *,
    required_fields: Iterable[str] = (),
    baseline_count: Optional[int] = None,
    min_count: int = 1,
    min_fraction_of_baseline: float = 0.3,
    max_null_rate: float = 0.5,
) -> HealthVerdict:
    """Assess a scrape batch's structural health.

    `items` may be dicts (units — field null-rates computed when
    `required_fields` given) or plain values (e.g. discovered URLs — count only).
    """
    items = list(items or [])
    count = len(items)
    reasons: List[str] = []
    null_rates: Dict[str, float] = {}

    req = tuple(required_fields)
    if req and count and isinstance(items[0], dict):
        for f in req:
            missing = sum(1 for it in items if _is_missing(it.get(f)))
            null_rates[f] = round(missing / count, 3)

    status = "ok"
    if count == 0:
        status = "empty"
        reasons.append("zero items returned — scraper likely broken or blocked")
    else:
        if count < min_count:
            status = "degraded"
            reasons.append(f"count {count} below floor {min_count}")
        if baseline_count and baseline_count > 0 and count < baseline_count * min_fraction_of_baseline:
            status = "degraded"
            reasons.append(
                f"count {count} < {int(min_fraction_of_baseline * 100)}% of baseline {baseline_count}"
            )
        drifted = [f for f, r in null_rates.items() if r > max_null_rate]
        if drifted:
            status = "degraded"
            reasons.append(
                f"schema drift: fields mostly null {drifted} "
                "(selectors may have changed)"
            )

    return HealthVerdict(
        source=source,
        status=status,
        count=count,
        baseline_count=baseline_count,
        field_null_rates=null_rates,
        reasons=reasons,
    )


async def record_and_alert(verdict: HealthVerdict, session: Any = None) -> HealthVerdict:
    """Emit metrics, alert on degradation, and (best-effort) persist run health.
    Never raises — health monitoring must not break ingestion."""
    # Prometheus
    if _PROM:
        try:  # pragma: no cover
            _G_LAST_COUNT.labels(source=verdict.source).set(verdict.count)
            _G_HEALTH.labels(source=verdict.source).set(1 if verdict.healthy else 0)
            if not verdict.healthy:
                _C_DRIFT.labels(source=verdict.source, status=verdict.status).inc()
        except Exception:
            pass

    if verdict.healthy:
        logger.info(
            "[scraper-health] %s OK — %d items", verdict.source, verdict.count
        )
        return verdict

    # Alert on degraded/empty (reuse the existing Sentry + Discord pipe).
    severity = "critical" if verdict.status == "empty" else "warning"
    title = f"{verdict.source}: {verdict.status.upper()}"
    message = (
        f"Scrape batch health = {verdict.status}. "
        f"count={verdict.count}, baseline={verdict.baseline_count}. "
        f"reasons: {'; '.join(verdict.reasons)}. "
        f"null_rates={verdict.field_null_rates}"
    )
    logger.error("[scraper-health] %s", message)
    try:
        from app.ingestion.anomaly_detector import send_alert
        await send_alert(title, message, severity=severity)
    except Exception as e:
        logger.warning("[scraper-health] alert failed: %s", e)

    # Best-effort persistence for after-the-fact staleness audits.
    if session is not None:
        try:
            import json
            from datetime import datetime, timezone
            from app.models import ScrapeRunStats

            session.add(ScrapeRunStats(
                run_id=f"health:{verdict.source}",
                stats_json=json.dumps(verdict.to_dict(), ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
            ))
            await session.commit()
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass

    return verdict


__all__ = ["HealthVerdict", "assess_batch", "record_and_alert", "DEFAULT_REQUIRED_FIELDS"]
