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

    # Maximum number of distinct IPs tracked simultaneously.
    # When this cap is reached the oldest entry is evicted (LRU-lite via insertion order).
    # Prevents unbounded memory growth under sustained traffic / IP churn.
    MAX_TRACKED_IPS = 50_000

    def __init__(self, app, max_requests: int = None, window_seconds: int = None):
        super().__init__(app)
        self.max_requests = int(max_requests or os.getenv("RATE_LIMIT_REQUESTS", "120"))
        self.window = int(window_seconds or os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        self.trust_proxy_headers = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
        # Ordered dict preserves insertion order so we can evict the oldest entry when full.
        self._clients: dict[str, deque] = {}
        self._last_gc = time.time()

    async def dispatch(self, request: Request, call_next):
        # Identify client by IP. Only trust proxy headers when explicitly enabled.
        xf = request.headers.get("x-forwarded-for")
        if self.trust_proxy_headers and xf:
            # Use right-most IP added by trusted proxy to avoid spoofing.
            client_ip = xf.split(",")[-1].strip()
        else:
            client_ip = request.client.host
        client_ip = client_ip or "unknown"

        now = time.time()

        # Periodic GC: sweep entries whose deque is empty (all timestamps expired).
        # Runs at most once per window period to amortize cost over many requests.
        if now - self._last_gc > self.window:
            self._gc(now)
            self._last_gc = now

        dq = self._clients.get(client_ip)
        if dq is None:
            # Evict oldest entry when cap reached to prevent unbounded growth.
            if len(self._clients) >= self.MAX_TRACKED_IPS:
                oldest_ip = next(iter(self._clients))
                del self._clients[oldest_ip]
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

    def _gc(self, now: float) -> None:
        """Remove IPs whose timestamp deques are now empty (all entries expired)."""
        expired = [ip for ip, dq in self._clients.items() if not dq or dq[-1] <= now - self.window]
        for ip in expired:
            del self._clients[ip]
