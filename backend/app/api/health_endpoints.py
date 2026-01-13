"""
Health Check API Endpoints
--------------------------
Endpoints for monitoring system health and status.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
from app.monitoring.health import health_checker, HealthStatus
from app.services.circuit_breaker import (
    claude_breaker,
    openai_breaker,
    database_breaker,
    blockchain_breaker,
    CircuitState
)
from app.monitoring.cost_tracker import cost_tracker
import os

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    Quick health check endpoint.

    Returns basic health status for load balancers.
    """
    check = await health_checker.quick_check()

    if check["status"] == HealthStatus.HEALTHY:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=check
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=check
        )


@router.get("/detailed")
async def detailed_health_check():
    """
    Comprehensive health check.

    Returns detailed status of all system components.
    Useful for monitoring dashboards and alerts.
    """
    health = await health_checker.run_all_checks()

    # Return 503 if unhealthy, 200 if healthy or degraded
    status_code = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if health["status"] == HealthStatus.UNHEALTHY
        else status.HTTP_200_OK
    )

    return JSONResponse(
        status_code=status_code,
        content=health
    )


@router.get("/circuits")
async def circuit_breaker_status():
    """
    Get status of all circuit breakers.

    Returns circuit states for monitoring.
    """
    return {
        "circuit_breakers": {
            "claude_api": {
                "state": claude_breaker.state.value,
                "failure_count": claude_breaker.failure_count,
                "threshold": claude_breaker.failure_threshold
            },
            "openai_api": {
                "state": openai_breaker.state.value,
                "failure_count": openai_breaker.failure_count,
                "threshold": openai_breaker.failure_threshold
            },
            "database": {
                "state": database_breaker.state.value,
                "failure_count": database_breaker.failure_count,
                "threshold": database_breaker.failure_threshold
            },
            "blockchain": {
                "state": blockchain_breaker.state.value,
                "failure_count": blockchain_breaker.failure_count,
                "threshold": blockchain_breaker.failure_threshold
            }
        },
        "summary": {
            "all_closed": all(
                b.state == CircuitState.CLOSED
                for b in [claude_breaker, openai_breaker, database_breaker, blockchain_breaker]
            )
        }
    }


@router.get("/costs")
async def cost_summary():
    """
    Get cost tracking summary.

    Returns daily cost summary (no session_id needed).
    """
    # Get daily cost without specific session
    daily_cost = cost_tracker._get_daily_cost()

    return {
        "daily_cost_usd": round(daily_cost, 4),
        "daily_limit_usd": cost_tracker.DAILY_COST_LIMIT,
        "daily_usage_percent": round((daily_cost / cost_tracker.DAILY_COST_LIMIT) * 100, 1),
        "limit_reached": daily_cost >= cost_tracker.DAILY_COST_LIMIT,
        "pricing": {
            "claude_input_per_1m": cost_tracker.CLAUDE_INPUT_COST_PER_1M,
            "claude_output_per_1m": cost_tracker.CLAUDE_OUTPUT_COST_PER_1M,
            "openai_gpt4o_input_per_1m": cost_tracker.OPENAI_GPT4O_INPUT_COST_PER_1M,
            "openai_gpt4o_output_per_1m": cost_tracker.OPENAI_GPT4O_OUTPUT_COST_PER_1M,
            "openai_embedding_per_1m": cost_tracker.OPENAI_EMBEDDING_COST_PER_1M
        }
    }


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes-style readiness probe.

    Returns 200 if system is ready to serve traffic.
    Returns 503 if critical services are down.
    """
    # Check critical services
    db_check = await health_checker.check_database()

    is_ready = (
        db_check["status"] == HealthStatus.HEALTHY and
        claude_breaker.state != CircuitState.OPEN and
        openai_breaker.state != CircuitState.OPEN
    )

    if is_ready:
        return {"status": "ready", "message": "System is ready to serve traffic"}
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "message": "System is not ready",
                "details": {
                    "database": db_check["status"],
                    "claude_circuit": claude_breaker.state.value,
                    "openai_circuit": openai_breaker.state.value
                }
            }
        )


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes-style liveness probe.

    Returns 200 if application is alive (even if degraded).
    Only returns 503 if application should be restarted.
    """
    return {"status": "alive", "message": "Application is running"}


@router.get("/version")
async def version_info():
    """
    Get application version and environment info.
    """
    return {
        "version": "1.0.0",
        "phase": "Phase 1 - AI Chat & Sales",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0],
        "features": {
            "claude_ai": True,
            "openai_embeddings": True,
            "blockchain_verification": True,
            "visualizations": True,
            "cost_tracking": True,
            "circuit_breakers": True
        }
    }
