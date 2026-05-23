"""
mcp_server_gateway.py
=====================
Production-grade Model Context Protocol (MCP) server exposing the Osool
Egyptian real estate intelligence layer to external autonomous AI agents.

Exposed tools
-------------
* ``osool_fetch_la2ta_deals``
    Queries the ``valuation_listings`` table for algorithmically-flagged
    La2ta (لقطة) market anomalies — listings priced ≥ 15 % below the
    compound's secondary-market mean after NPV normalisation — filtered
    by compound and a cash-equivalent budget ceiling.

* ``osool_compress_payment_plan``
    Computes the true Net Present Value (NPV) cash-equivalent cost of an
    Egyptian property instalment plan using the CBE base corridor rate,
    returning the discount depth versus the nominal sticker price.

Transport
---------
* **SSE over HTTP** (default) — Starlette application running on a
  configurable host/port.  Every connection is gated by Bearer token or
  ``X-Osool-MCP-Token`` header authentication using constant-time
  comparison (``secrets.compare_digest``).  The secret is sourced from
  the ``OSOOL_MCP_SECRET_KEY`` environment variable.  If the variable is
  absent the server refuses all connections in SSE mode (fail-secure).

* **STDIO** (``--stdio`` flag) — standard MCP host-controlled transport.
  Authentication at this layer is delegated to the host process (e.g.
  Claude Desktop's sandboxed subprocess model).

Security
--------
* Tokens never appear in logs.
* Constant-time comparison prevents timing-oracle attacks.
* Parameterised SQL queries (``sqlalchemy.text`` with bound params) are
  used exclusively — no string formatting in DB queries.
* ``compound_id`` and ``max_budget_egp`` are validated before execution.

Usage
-----
::

    # HTTP / SSE mode (default, port 8001)
    python mcp_server_gateway.py --host 0.0.0.0 --port 8001

    # STDIO mode (for Claude Desktop / MCP host integration)
    python mcp_server_gateway.py --stdio

Environment variables
---------------------
OSOOL_MCP_SECRET_KEY   Bearer token for SSE transport auth (required in SSE mode).
CBE_BASE_RATE          CBE corridor discount rate, default 0.22.
DATABASE_URL           PostgreSQL DSN — must be set for DB-backed tools.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import secrets
import sys
from typing import Any, Final, Optional, Sequence

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from pydantic import ValidationError
from sqlalchemy import text
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

# Internal modules — imported lazily inside handlers to avoid circular issues
# when the gateway is cold-started before the FastAPI app is initialised.
from app.valuation_engine import PaymentTimeline, ValuationEngine

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_SERVER_NAME: Final[str] = "osool-real-estate-gateway"
_SERVER_VERSION: Final[str] = "1.0.0"
_SERVER_DESCRIPTION: Final[str] = (
    "Osool Egyptian real estate intelligence layer — La2ta deal scanner "
    "and payment plan NPV compressor."
)

_DEFAULT_CBE_RATE: Final[float] = float(os.getenv("CBE_BASE_RATE", "0.22"))

#: Secret key for SSE transport authentication.
#: Intentionally read once at module load — any change requires restart.
_MCP_SECRET_KEY: Final[Optional[str]] = os.getenv("OSOOL_MCP_SECRET_KEY")

#: Hard limit on DB result rows returned per tool call.
_MAX_LA2TA_RESULTS: Final[int] = 20

#: Minimum compound_id length guard.
_MIN_COMPOUND_ID_LEN: Final[int] = 1

# ---------------------------------------------------------------------------
# Valuation Engine singleton
# ---------------------------------------------------------------------------

_valuation_engine: Final[ValuationEngine] = ValuationEngine(cbe_rate=_DEFAULT_CBE_RATE)

# ---------------------------------------------------------------------------
# MCP Tool Definitions  (Protocol Discovery Manifest)
# ---------------------------------------------------------------------------

_TOOL_FETCH_LA2TA: Final[types.Tool] = types.Tool(
    name="osool_fetch_la2ta_deals",
    description=(
        "Scans the Osool property intelligence database for active listings "
        "flagged as La2ta (لقطة) market anomalies — units priced ≥ 15 % below "
        "their compound's secondary-market mean after NPV normalisation. "
        "Returns structured deal records ordered by value depth "
        "(cheapest normalised price/sqm first). "
        "Use to surface undervalued resale opportunities within a specific "
        "compound under a cash-equivalent budget ceiling."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "compound_id": {
                "type": "string",
                "description": (
                    "Unique compound identifier to scope the scan "
                    "(e.g. 'marassi', 'mountain_view_icity', 'sodic_east'). "
                    "Case-sensitive; must match the value used during ingestion."
                ),
                "minLength": 1,
                "maxLength": 200,
            },
            "max_budget_egp": {
                "type": "number",
                "description": (
                    "Maximum cash-equivalent NPV budget in Egyptian Pounds (EGP). "
                    "Applied as a hard upper bound on the discounted present value "
                    "of all payment obligations — not the nominal sticker price. "
                    "Minimum: 100 000 EGP."
                ),
                "minimum": 100_000,
            },
        },
        "required": ["compound_id", "max_budget_egp"],
        "additionalProperties": False,
    },
)

_TOOL_COMPRESS_PLAN: Final[types.Tool] = types.Tool(
    name="osool_compress_payment_plan",
    description=(
        "Computes the true Net Present Value (NPV) cash-equivalent cost of a "
        "multi-year Egyptian property instalment plan by discounting each "
        "periodic payment at the Central Bank of Egypt (CBE) base corridor rate. "
        "Use when a buyer asks 'what does this plan actually cost in today's "
        "money?' or to compare cash vs. instalment offers on an apples-to-apples "
        "basis. Returns the NPV, the implied cash discount depth, and the "
        "compounding parameters applied."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "total_price": {
                "type": "number",
                "description": "Nominal advertised asking price in EGP.",
                "minimum": 100_000,
            },
            "down_payment": {
                "type": "number",
                "description": "Down payment due at contract signing in EGP (≥ 0).",
                "minimum": 0,
            },
            "total_years": {
                "type": "integer",
                "description": "Total instalment tenure in years.",
                "minimum": 1,
                "maximum": 30,
            },
            "periodic_installment_amount": {
                "type": "number",
                "description": "EGP value of each individual periodic payment (> 0).",
                "minimum": 1,
            },
            "installments_per_year": {
                "type": "integer",
                "description": (
                    "Number of payments per calendar year. "
                    "Defaults to 4 (quarterly). "
                    "Common values: 1 (annual), 2 (semi-annual), "
                    "4 (quarterly), 12 (monthly)."
                ),
                "minimum": 1,
                "maximum": 12,
                "default": 4,
            },
        },
        "required": [
            "total_price",
            "down_payment",
            "total_years",
            "periodic_installment_amount",
        ],
        "additionalProperties": False,
    },
)

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------

server: Final[Server] = Server(_SERVER_NAME)


# ---------------------------------------------------------------------------
# Tool handler: list_tools
# ---------------------------------------------------------------------------


@server.list_tools()
async def _handle_list_tools() -> list[types.Tool]:
    """Advertise the two Osool intelligence tools to the MCP host."""
    return [_TOOL_FETCH_LA2TA, _TOOL_COMPRESS_PLAN]


# ---------------------------------------------------------------------------
# Tool handler: call_tool  (dispatcher)
# ---------------------------------------------------------------------------


@server.call_tool()
async def _handle_call_tool(
    name: str,
    arguments: dict[str, Any] | None,
) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Route an incoming tool invocation to the correct executor."""
    args: dict[str, Any] = arguments or {}

    if name == "osool_fetch_la2ta_deals":
        return await _execute_fetch_la2ta(args)

    if name == "osool_compress_payment_plan":
        return await _execute_compress_plan(args)

    raise ValueError(
        f"Unknown tool name {name!r}. "
        f"Available: osool_fetch_la2ta_deals, osool_compress_payment_plan."
    )


# ---------------------------------------------------------------------------
# Executor: osool_fetch_la2ta_deals
# ---------------------------------------------------------------------------


async def _execute_fetch_la2ta(
    args: dict[str, Any],
) -> list[types.TextContent]:
    """
    Query ``valuation_listings`` for La2ta-flagged records and return
    structured JSON.

    Validation
    ~~~~~~~~~~
    * ``compound_id`` must be a non-empty string ≤ 200 characters.
    * ``max_budget_egp`` must be a positive finite number ≥ 100 000.

    Returns
    ~~~~~~~
    A single ``TextContent`` block whose ``text`` is a JSON object with
    ``tool``, ``compound_id``, ``max_budget_egp``, ``results_count``, and
    ``listings`` (list of deal records).
    """
    # ---- input validation --------------------------------------------------
    compound_id: str = args.get("compound_id", "")
    if not isinstance(compound_id, str) or not compound_id.strip():
        return _error_content(
            "osool_fetch_la2ta_deals",
            "compound_id must be a non-empty string.",
        )
    compound_id = compound_id.strip()
    if len(compound_id) > 200:
        return _error_content(
            "osool_fetch_la2ta_deals",
            "compound_id exceeds 200-character limit.",
        )

    raw_budget = args.get("max_budget_egp")
    try:
        max_budget_egp = float(raw_budget)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _error_content(
            "osool_fetch_la2ta_deals",
            "max_budget_egp must be a numeric value.",
        )
    if not _is_finite_positive(max_budget_egp) or max_budget_egp < 100_000:
        return _error_content(
            "osool_fetch_la2ta_deals",
            "max_budget_egp must be a finite number ≥ 100 000 EGP.",
        )

    # ---- DB query ----------------------------------------------------------
    try:
        from app.database import AsyncSessionLocal  # deferred import

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                text(
                    """
                    SELECT
                        listing_id,
                        compound_id,
                        geographic_zone,
                        total_price,
                        size_sqm,
                        floor_level,
                        view_orientation,
                        delivery_year,
                        is_secondary_market,
                        cash_npv_egp,
                        normalized_cash_price_sqm,
                        feature_multiplier,
                        effective_multiplier,
                        delivery_lag_penalty_pp,
                        is_la2ta,
                        ingested_at
                    FROM valuation_listings
                    WHERE compound_id = :compound_id
                      AND is_la2ta = TRUE
                      AND cash_npv_egp <= :max_budget_egp
                    ORDER BY normalized_cash_price_sqm ASC
                    LIMIT :limit
                    """
                ),
                {
                    "compound_id": compound_id,
                    "max_budget_egp": max_budget_egp,
                    "limit": _MAX_LA2TA_RESULTS,
                },
            )
            rows = result.mappings().all()

    except Exception as exc:
        logger.error(
            "DB error in osool_fetch_la2ta_deals compound=%s: %s",
            compound_id,
            exc,
            exc_info=True,
        )
        return _error_content(
            "osool_fetch_la2ta_deals",
            f"Database query failed: {type(exc).__name__} — check server logs.",
        )

    # ---- serialise ---------------------------------------------------------
    listings: list[dict[str, Any]] = []
    for row in rows:
        listings.append(
            {
                "listing_id": row["listing_id"],
                "compound_id": row["compound_id"],
                "geographic_zone": row["geographic_zone"],
                "total_price_egp": _round_egp(row["total_price"]),
                "size_sqm": _safe_float(row["size_sqm"]),
                "floor_level": row["floor_level"],
                "view_orientation": row["view_orientation"],
                "delivery_year": row["delivery_year"],
                "is_secondary_market": row["is_secondary_market"],
                "cash_npv_egp": _round_egp(row["cash_npv_egp"]),
                "normalised_price_per_sqm_egp": _round_egp(
                    row["normalized_cash_price_sqm"]
                ),
                "feature_multiplier": _safe_float(row["feature_multiplier"]),
                "effective_multiplier": _safe_float(row["effective_multiplier"]),
                "delivery_lag_penalty_pp": _safe_float(
                    row["delivery_lag_penalty_pp"]
                ),
                "la2ta_flag": bool(row["is_la2ta"]),
                "ingested_at": (
                    row["ingested_at"].isoformat()
                    if row["ingested_at"] is not None
                    else None
                ),
            }
        )

    payload: dict[str, Any] = {
        "tool": "osool_fetch_la2ta_deals",
        "compound_id": compound_id,
        "max_budget_egp": max_budget_egp,
        "results_count": len(listings),
        "listings": listings,
    }

    if not listings:
        payload["note"] = (
            "No La2ta deals found for this compound within the specified budget. "
            "Try increasing max_budget_egp or checking a different compound_id."
        )

    return [
        types.TextContent(
            type="text",
            text=json.dumps(payload, ensure_ascii=False, indent=2),
        )
    ]


# ---------------------------------------------------------------------------
# Executor: osool_compress_payment_plan
# ---------------------------------------------------------------------------


async def _execute_compress_plan(
    args: dict[str, Any],
) -> list[types.TextContent]:
    """
    Wrap ``ValuationEngine.calculate_effective_cash_npv`` and return a
    structured NPV analysis block.

    Validation
    ~~~~~~~~~~
    * ``total_price`` ≥ 100 000 EGP.
    * ``down_payment`` ≥ 0 EGP.
    * ``total_years`` ∈ [1, 30].
    * ``periodic_installment_amount`` > 0 EGP.
    * ``installments_per_year`` ∈ [1, 12], default 4.

    Returns
    ~~~~~~~
    A single ``TextContent`` block with the NPV analysis JSON containing
    nominal price, cash NPV, discount in EGP and percentage, and all
    compounding parameters applied.
    """
    # ---- parse and validate inputs ----------------------------------------
    try:
        total_price = float(args["total_price"])
        down_payment = float(args["down_payment"])
        total_years = int(args["total_years"])
        periodic_installment_amount = float(args["periodic_installment_amount"])
        installments_per_year = int(args.get("installments_per_year", 4))
    except (KeyError, TypeError, ValueError) as exc:
        return _error_content(
            "osool_compress_payment_plan",
            f"Invalid argument type: {exc}",
        )

    if total_price < 100_000 or not _is_finite_positive(total_price):
        return _error_content(
            "osool_compress_payment_plan",
            "total_price must be a finite number ≥ 100 000 EGP.",
        )
    if down_payment < 0 or not _is_finite(down_payment):
        return _error_content(
            "osool_compress_payment_plan",
            "down_payment must be ≥ 0 EGP.",
        )
    if not (1 <= total_years <= 30):
        return _error_content(
            "osool_compress_payment_plan",
            "total_years must be an integer in [1, 30].",
        )
    if periodic_installment_amount <= 0 or not _is_finite(periodic_installment_amount):
        return _error_content(
            "osool_compress_payment_plan",
            "periodic_installment_amount must be > 0 EGP.",
        )
    if not (1 <= installments_per_year <= 12):
        return _error_content(
            "osool_compress_payment_plan",
            "installments_per_year must be an integer in [1, 12].",
        )

    # ---- build PaymentTimeline and run NPV ---------------------------------
    try:
        plan = PaymentTimeline(
            down_payment=down_payment if down_payment > 0 else 1.0,
            installments_per_year=installments_per_year,
            total_years=total_years,
            periodic_installment_amount=periodic_installment_amount,
        )
        # If down_payment was 0, patch it back after Pydantic construction
        # (Pydantic requires gt=0, so we substitute 1.0 temporarily and
        # note the override.  The NPV computation is still correct because
        # down_payment enters the formula at t=0 with no discounting.)
        _down_payment_for_npv = down_payment

        # Re-compute with corrected down_payment if it was zero
        if down_payment == 0.0:
            # Monkey-patch the validated model using __dict__ bypass.
            # This is intentional: we want the full NPV formula path
            # even when down_payment = 0.
            plan = plan.model_copy(update={"down_payment": 0.0})
            cash_npv = _valuation_engine.calculate_effective_cash_npv(
                total_price, plan
            )
        else:
            cash_npv = _valuation_engine.calculate_effective_cash_npv(
                total_price, plan
            )

    except (ValidationError, ValueError, AssertionError) as exc:
        return _error_content(
            "osool_compress_payment_plan",
            f"NPV computation failed: {exc}",
        )

    # ---- build response ----------------------------------------------------
    discount_egp = total_price - cash_npv
    discount_pct = discount_egp / total_price if total_price > 0 else 0.0
    periodic_rate = _DEFAULT_CBE_RATE / installments_per_year
    n_periods = installments_per_year * total_years

    payload: dict[str, Any] = {
        "tool": "osool_compress_payment_plan",
        "analysis": {
            "nominal_price_egp": _round_egp(total_price),
            "cash_npv_egp": _round_egp(cash_npv),
            "discount_egp": _round_egp(discount_egp),
            "discount_pct": round(discount_pct * 100, 2),
            "interpretation": (
                f"The instalment plan's true cost in today's EGP is "
                f"{cash_npv:,.0f} — a {discount_pct * 100:.1f} % "
                f"implied discount vs the {total_price:,.0f} EGP sticker price."
            ),
        },
        "plan_parameters": {
            "down_payment_egp": _round_egp(down_payment),
            "total_years": total_years,
            "installments_per_year": installments_per_year,
            "periodic_installment_amount_egp": _round_egp(
                periodic_installment_amount
            ),
            "total_periods": n_periods,
            "total_nominal_outflow_egp": _round_egp(
                down_payment + periodic_installment_amount * n_periods
            ),
        },
        "discount_model": {
            "method": "CBE_corridor_NPV_annuity",
            "cbe_annual_rate_pct": round(_DEFAULT_CBE_RATE * 100, 2),
            "periodic_discount_rate_pct": round(periodic_rate * 100, 4),
            "n_discount_periods": n_periods,
        },
    }

    return [
        types.TextContent(
            type="text",
            text=json.dumps(payload, ensure_ascii=False, indent=2),
        )
    ]


# ---------------------------------------------------------------------------
# Security middleware (SSE / HTTP transport only)
# ---------------------------------------------------------------------------


class _TokenAuthMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that enforces Bearer token authentication on every
    incoming request to the MCP SSE server.

    Security properties
    ~~~~~~~~~~~~~~~~~~~
    * Constant-time comparison via ``secrets.compare_digest`` prevents
      timing-oracle attacks.
    * Tokens are never logged.
    * If ``OSOOL_MCP_SECRET_KEY`` is absent the middleware rejects all
      connections with HTTP 503 (fail-secure, not fail-open).
    * Both ``Authorization: Bearer <token>`` and the custom
      ``X-Osool-MCP-Token: <token>`` header are accepted to allow clients
      that cannot set standard auth headers.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Fail-secure when the secret is not configured in SSE mode.
        if _MCP_SECRET_KEY is None:
            logger.critical(
                "OSOOL_MCP_SECRET_KEY is not set. "
                "Refusing all SSE connections (fail-secure). "
                "Set the env var to enable SSE transport."
            )
            return JSONResponse(
                {
                    "error": "ServiceUnavailable",
                    "detail": (
                        "MCP gateway is not configured for SSE transport. "
                        "OSOOL_MCP_SECRET_KEY environment variable is missing."
                    ),
                },
                status_code=503,
            )

        # Extract provided token from standard or custom header.
        auth_header: str = request.headers.get("Authorization", "")
        custom_header: str = request.headers.get("X-Osool-MCP-Token", "")

        provided: str = ""
        if auth_header.lower().startswith("bearer "):
            provided = auth_header[7:].strip()
        elif custom_header:
            provided = custom_header.strip()

        # Constant-time comparison — both operands must be same type (bytes).
        try:
            token_match = secrets.compare_digest(
                provided.encode("utf-8"),
                _MCP_SECRET_KEY.encode("utf-8"),
            )
        except Exception:
            token_match = False

        if not token_match:
            logger.warning(
                "MCP SSE auth failure — path=%s method=%s source=%s",
                request.url.path,
                request.method,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                {
                    "error": "Unauthorized",
                    "detail": (
                        "Valid Bearer token required in the Authorization header "
                        "or X-Osool-MCP-Token header."
                    ),
                },
                status_code=401,
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Starlette app with SSE transport
# ---------------------------------------------------------------------------


def _build_starlette_app() -> Starlette:
    """
    Construct and return the Starlette ASGI application that wraps the MCP
    SSE transport.

    Topology
    ~~~~~~~~
    * ``GET  /sse``        — long-lived Server-Sent Events stream (MCP host connects here).
    * ``POST /messages/``  — inbound message channel (MCP host posts tool calls here).
    * ``GET  /health``     — lightweight health probe (does not require auth).

    The ``_TokenAuthMiddleware`` is applied globally and runs before any
    route handler.  The ``/health`` path is intentionally also behind the
    middleware to prevent unauthenticated information disclosure.
    """
    sse_transport = SseServerTransport("/messages/")

    init_options = InitializationOptions(
        server_name=_SERVER_NAME,
        server_version=_SERVER_VERSION,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
        instructions=_SERVER_DESCRIPTION,
    )

    async def handle_sse(request: Request) -> None:
        """Accept and serve the long-lived SSE connection."""
        async with sse_transport.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001  (ASGI direct access required by MCP transport)
        ) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                init_options,
                raise_exceptions=False,
            )

    async def handle_messages(request: Request) -> Response:
        """Relay inbound MCP messages from the host to the SSE transport."""
        await sse_transport.handle_post_message(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        )
        return Response()

    async def handle_health(request: Request) -> JSONResponse:
        """Lightweight health probe for load balancers and uptime monitors."""
        return JSONResponse(
            {
                "status": "ok",
                "server": _SERVER_NAME,
                "version": _SERVER_VERSION,
                "tools": [
                    _TOOL_FETCH_LA2TA.name,
                    _TOOL_COMPRESS_PLAN.name,
                ],
                "transport": "sse",
            }
        )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Route("/messages/", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=handle_health, methods=["GET"]),
        ],
        middleware=[
            Middleware(_TokenAuthMiddleware),
        ],
    )


# ---------------------------------------------------------------------------
# STDIO transport runner
# ---------------------------------------------------------------------------


async def _run_stdio() -> None:
    """
    Run the MCP server over the standard STDIO transport.

    Security note: STDIO transport does not support header-based auth.
    Security is handled at the OS process level by the MCP host (e.g.
    Claude Desktop runs this as a sandboxed child process).  Do not
    expose this transport directly over a network socket.
    """
    logger.info(
        "Starting %s %s in STDIO mode — security delegated to host process.",
        _SERVER_NAME,
        _SERVER_VERSION,
    )
    init_options = InitializationOptions(
        server_name=_SERVER_NAME,
        server_version=_SERVER_VERSION,
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
        instructions=_SERVER_DESCRIPTION,
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            init_options,
            raise_exceptions=False,
        )


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _error_content(tool_name: str, message: str) -> list[types.TextContent]:
    """Construct a standardised error payload as a TextContent block."""
    payload = {
        "tool": tool_name,
        "error": True,
        "message": message,
    }
    return [
        types.TextContent(
            type="text",
            text=json.dumps(payload, ensure_ascii=False),
        )
    ]


def _round_egp(value: Any) -> Optional[float]:
    """Round a numeric value to the nearest whole EGP, or None if null."""
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> Optional[float]:
    """Convert to float with 4 dp precision, or None if not convertible."""
    if value is None:
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _is_finite_positive(value: float) -> bool:
    """Return True iff *value* is a finite, positive IEEE-754 float."""
    import math

    return math.isfinite(value) and value > 0


def _is_finite(value: float) -> bool:
    """Return True iff *value* is a finite IEEE-754 float."""
    import math

    return math.isfinite(value)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point supporting both SSE (HTTP) and STDIO transport modes.

    Flags
    ~~~~~
    ``--stdio``           Switch to STDIO transport mode.
    ``--host HOST``       Bind host for SSE mode (default: ``0.0.0.0``).
    ``--port PORT``       Bind port for SSE mode (default: ``8001``).
    ``--log-level LEVEL`` Python logging level (default: ``INFO``).
    """
    parser = argparse.ArgumentParser(
        prog="mcp_server_gateway",
        description=(
            "Osool Real Estate MCP Server Gateway — "
            "exposes valuation intelligence to autonomous AI agents."
        ),
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        default=False,
        help="Run in STDIO transport mode (for Claude Desktop integration).",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host for SSE/HTTP mode (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Bind port for SSE/HTTP mode (default: 8001).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO).",
    )
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    if args.stdio:
        # ── STDIO transport ──────────────────────────────────────────────
        asyncio.run(_run_stdio())

    else:
        # ── SSE / HTTP transport ─────────────────────────────────────────
        if _MCP_SECRET_KEY is None:
            logger.critical(
                "OSOOL_MCP_SECRET_KEY is not set. "
                "The SSE transport will reject all connections (fail-secure). "
                "Set the environment variable before starting in SSE mode."
            )

        import uvicorn

        starlette_app = _build_starlette_app()

        logger.info(
            "Starting %s %s — SSE transport on http://%s:%d/sse",
            _SERVER_NAME,
            _SERVER_VERSION,
            args.host,
            args.port,
        )
        uvicorn.run(
            starlette_app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),
            access_log=True,
        )


if __name__ == "__main__":
    main()
