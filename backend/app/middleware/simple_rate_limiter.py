from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
import os
from collections import deque


class SimpleRateLimiterMiddleware(BaseHTTPMiddleware):
    """A simple in-memory rate limiter middleware.

    Note: This is an in-memory implementation intended as a safety net
    for single-instance deployments or for development. For production,
    use a distributed store (Redis) and a robust library (e.g., slowapi
    or a WAF) to avoid bypasses and shared state issues.
    """

    def __init__(self, app, max_requests: int = None, window_seconds: int = None):
        super().__init__(app)
        self.max_requests = int(max_requests or os.getenv("RATE_LIMIT_REQUESTS", "120"))
        self.window = int(window_seconds or os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        # store timestamps per client IP
        self._clients = {}  # ip -> deque[timestamps]

    async def dispatch(self, request: Request, call_next):
        # Identify client by IP (use X-Forwarded-For if behind proxy)
        xf = request.headers.get("x-forwarded-for")
        client_ip = (xf.split(",")[0].strip() if xf else request.client.host) or "unknown"

        now = time.time()
        dq = self._clients.get(client_ip)
        if dq is None:
            dq = deque()
            self._clients[client_ip] = dq

        # purge old timestamps
        while dq and dq[0] <= now - self.window:
            dq.popleft()

        if len(dq) >= self.max_requests:
            # Rate limit exceeded
            retry_after = int(dq[0] + self.window - now) + 1
            return JSONResponse(
                status_code=429,
                content={"error": "Too many requests", "retry_after": retry_after},
                headers={"Retry-After": str(retry_after)},
            )

        dq.append(now)
        return await call_next(request)
