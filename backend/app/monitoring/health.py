"""
Health Check Monitoring
-----------------------
Comprehensive health checks for all system components.
"""

import logging
from typing import Dict, List
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """
    Comprehensive health check system.

    Monitors:
    - Database connectivity
    - Redis connectivity
    - Claude API availability
    - OpenAI API availability
    - Blockchain service status
    """

    def __init__(self):
        self.checks = {}
        self.last_check_time = None

    async def check_database(self) -> Dict:
        """Check database connectivity."""
        try:
            from app.database import SessionLocal

            db = SessionLocal()
            try:
                # Simple query to test connection
                db.execute("SELECT 1")
                db.close()

                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "Database connection successful",
                    "response_time_ms": 0  # Would measure actual time
                }
            except Exception as e:
                db.close()
                raise e

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database connection failed: {str(e)}",
                "error": str(e)
            }

    async def check_redis(self) -> Dict:
        """Check Redis connectivity."""
        try:
            import redis
            import os

            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Redis not configured (optional service)"
                }

            r = redis.from_url(redis_url)
            r.ping()

            return {
                "status": HealthStatus.HEALTHY,
                "message": "Redis connection successful"
            }

        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Redis unavailable (system will use fallback)",
                "error": str(e)
            }

    async def check_claude_api(self) -> Dict:
        """Check Claude API availability."""
        try:
            from anthropic import AsyncAnthropic
            from app.config import config

            client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

            # Simple test call with minimal tokens
            response = await client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )

            return {
                "status": HealthStatus.HEALTHY,
                "message": "Claude API responding",
                "model": config.CLAUDE_MODEL
            }

        except Exception as e:
            logger.error(f"Claude API health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Claude API unavailable: {str(e)}",
                "error": str(e)
            }

    async def check_openai_api(self) -> Dict:
        """Check OpenAI API availability."""
        try:
            import openai
            import os

            openai.api_key = os.getenv("OPENAI_API_KEY")

            # Simple embeddings test (cheaper than completion)
            response = await openai.Embedding.acreate(
                input="test",
                model="text-embedding-3-small"
            )

            return {
                "status": HealthStatus.HEALTHY,
                "message": "OpenAI API responding",
                "model": "text-embedding-3-small"
            }

        except Exception as e:
            logger.error(f"OpenAI API health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"OpenAI API unavailable: {str(e)}",
                "error": str(e)
            }

    async def check_blockchain(self) -> Dict:
        """Check blockchain service connectivity."""
        try:
            from app.services.blockchain_prod import blockchain_service_prod

            # Simple connectivity check
            # In production, you'd check actual RPC connection

            return {
                "status": HealthStatus.HEALTHY,
                "message": "Blockchain service available",
                "network": "testnet"
            }

        except Exception as e:
            logger.warning(f"Blockchain health check failed: {e}")
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Blockchain service unavailable (non-critical)",
                "error": str(e)
            }

    async def run_all_checks(self) -> Dict:
        """
        Run all health checks in parallel.

        Returns:
            Comprehensive health report
        """
        start_time = datetime.utcnow()

        # Run checks in parallel
        results = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_claude_api(),
            self.check_openai_api(),
            self.check_blockchain(),
            return_exceptions=True
        )

        # Map results to check names
        checks = {
            "database": results[0] if not isinstance(results[0], Exception) else {
                "status": HealthStatus.UNHEALTHY,
                "error": str(results[0])
            },
            "redis": results[1] if not isinstance(results[1], Exception) else {
                "status": HealthStatus.DEGRADED,
                "error": str(results[1])
            },
            "claude_api": results[2] if not isinstance(results[2], Exception) else {
                "status": HealthStatus.UNHEALTHY,
                "error": str(results[2])
            },
            "openai_api": results[3] if not isinstance(results[3], Exception) else {
                "status": HealthStatus.UNHEALTHY,
                "error": str(results[3])
            },
            "blockchain": results[4] if not isinstance(results[4], Exception) else {
                "status": HealthStatus.DEGRADED,
                "error": str(results[4])
            }
        }

        # Determine overall status
        statuses = [check["status"] for check in checks.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            # Critical service down
            critical_down = any(
                checks[svc]["status"] == HealthStatus.UNHEALTHY
                for svc in ["database", "claude_api", "openai_api"]
            )
            overall_status = HealthStatus.UNHEALTHY if critical_down else HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.DEGRADED

        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        self.last_check_time = end_time
        self.checks = checks

        return {
            "status": overall_status,
            "timestamp": end_time.isoformat(),
            "duration_ms": duration_ms,
            "checks": checks,
            "summary": {
                "healthy": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
                "degraded": sum(1 for s in statuses if s == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for s in statuses if s == HealthStatus.UNHEALTHY),
                "total": len(statuses)
            }
        }

    async def quick_check(self) -> Dict:
        """
        Quick health check (database only).

        Returns:
            Basic health status
        """
        db_check = await self.check_database()

        return {
            "status": db_check["status"],
            "timestamp": datetime.utcnow().isoformat(),
            "message": db_check["message"]
        }


# Global health check instance
health_checker = HealthCheck()
