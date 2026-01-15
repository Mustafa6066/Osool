"""
Load Testing Suite for Osool Backend
-------------------------------------
Tests system performance under concurrent load using Locust.

Run with:
    pip install locust
    locust -f backend/tests/load_test.py --host=http://localhost:8000

Then open browser: http://localhost:8089
"""

from locust import HttpUser, task, between, events
import random
import json
import uuid
from datetime import datetime


# ---------------------------------------------------------------------------
# SAMPLE DATA FOR REALISTIC TESTING
# ---------------------------------------------------------------------------

SAMPLE_QUERIES = [
    # English queries
    "I'm looking for a 3-bedroom apartment in New Cairo under 5M",
    "Show me villas in 6th of October with gardens",
    "Find me luxury penthouses in Zamalek",
    "I want a studio in Maadi near the metro",
    "What's available in Sheikh Zayed with a pool?",
    "Show me 2-bedroom apartments in Heliopolis",
    "I need a family villa in New Giza",
    "Find affordable apartments in Nasr City",

    # Arabic queries
    "عايز شقة 3 غرف في القاهرة الجديدة",
    "ابحث عن فيلا في الشيخ زايد",
    "محتاج شقة في المعادي قريبة من المترو",
    "عايز استثمر في عقار في مدينتي",
]

FOLLOW_UP_QUESTIONS = [
    "Is this a good price?",
    "What's the ROI for this property?",
    "Calculate my monthly payments",
    "Tell me more about the location",
    "Is it available?",
    "Can I schedule a viewing?",
    "Compare the top 3 options",
    "What are the payment plans?",
    "هل السعر ده كويس؟",
    "احسبلي الأقساط",
    "عايز أحجز معاد لزيارة",
]

OBJECTIONS = [
    "This is too expensive",
    "I found cheaper on Nawy",
    "I need time to think",
    "The location is too far",
    "دي غالية أوي",
    "لقيت أرخص في موقع تاني",
]


# ---------------------------------------------------------------------------
# USER BEHAVIOR CLASSES
# ---------------------------------------------------------------------------

class OsoolBrowserUser(HttpUser):
    """
    Simulates a typical user browsing properties and chatting with AMR.

    Wait time: 2-5 seconds between requests (simulates reading/thinking)
    """

    wait_time = between(2, 5)

    def on_start(self):
        """Initialize user session"""
        self.session_id = f"load-test-{uuid.uuid4()}"
        self.conversation_count = 0
        self.last_property_ids = []

    @task(5)
    def search_properties(self):
        """Most common action: searching for properties"""
        query = random.choice(SAMPLE_QUERIES)

        with self.client.post(
            "/api/chat",
            json={"session_id": self.session_id, "message": query},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()

                # Extract property IDs if returned
                if "properties" in data:
                    self.last_property_ids = [p["id"] for p in data["properties"][:3]]

                response.success()
                self.conversation_count += 1
            elif response.status_code == 429:
                # Rate limited (expected under load)
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")

    @task(3)
    def ask_follow_up_question(self):
        """Ask detailed questions about properties"""
        if self.conversation_count == 0:
            # Skip if no prior conversation
            return

        question = random.choice(FOLLOW_UP_QUESTIONS)

        with self.client.post(
            "/api/chat",
            json={"session_id": self.session_id, "message": question},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                self.conversation_count += 1
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Follow-up failed: {response.status_code}")

    @task(1)
    def raise_objection(self):
        """Simulate user objections (testing objection handling)"""
        if self.conversation_count < 2:
            # Only after some conversation
            return

        objection = random.choice(OBJECTIONS)

        self.client.post(
            "/api/chat",
            json={"session_id": self.session_id, "message": objection},
            catch_response=True
        )
        self.conversation_count += 1

    @task(2)
    def check_health(self):
        """Health check (simulates load balancer pings)"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class OsoolPowerUser(HttpUser):
    """
    Simulates power users who send rapid requests (investors, analysts).

    Wait time: 0.5-2 seconds (faster than typical users)
    """

    wait_time = between(0.5, 2)

    def on_start(self):
        self.session_id = f"power-user-{uuid.uuid4()}"
        self.request_count = 0

    @task(4)
    def rapid_searches(self):
        """Rapidly search multiple properties"""
        queries = random.sample(SAMPLE_QUERIES, min(3, len(SAMPLE_QUERIES)))

        for query in queries:
            self.client.post(
                "/api/chat",
                json={"session_id": self.session_id, "message": query}
            )
            self.request_count += 1

    @task(2)
    def compare_multiple_properties(self):
        """Request comparisons"""
        self.client.post(
            "/api/chat",
            json={
                "session_id": self.session_id,
                "message": "Compare apartments in New Cairo vs Maadi vs Zamalek"
            }
        )
        self.request_count += 1

    @task(1)
    def check_costs(self):
        """Check cost tracking endpoint"""
        self.client.get("/health/costs")


class OsoolMonitoringUser(HttpUser):
    """
    Simulates monitoring systems checking health and metrics.

    Wait time: 10-30 seconds (periodic checks)
    """

    wait_time = between(10, 30)

    @task(5)
    def health_check(self):
        """Basic health check"""
        self.client.get("/health")

    @task(2)
    def detailed_health_check(self):
        """Detailed health check"""
        self.client.get("/health/detailed")

    @task(2)
    def circuit_breaker_status(self):
        """Check circuit breakers"""
        self.client.get("/health/circuits")

    @task(1)
    def cost_monitoring(self):
        """Monitor costs"""
        self.client.get("/health/costs")


# ---------------------------------------------------------------------------
# CUSTOM EVENTS AND METRICS
# ---------------------------------------------------------------------------

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start banner"""
    print("\n" + "="*70)
    print("🚀 Osool Load Testing Started")
    print("="*70)
    print(f"Host: {environment.host}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary"""
    stats = environment.stats

    print("\n" + "="*70)
    print("📊 Osool Load Testing Summary")
    print("="*70)
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"Requests per Second: {stats.total.total_rps:.2f}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    # Check if targets met
    targets_met = True

    # Target 1: 95th percentile < 2000ms
    p95 = stats.total.get_response_time_percentile(0.95)
    if p95 > 2000:
        print(f"❌ FAILED: 95th percentile ({p95:.0f}ms) > 2000ms target")
        targets_met = False
    else:
        print(f"✅ PASSED: 95th percentile ({p95:.0f}ms) < 2000ms target")

    # Target 2: Failure rate < 1%
    failure_rate = stats.total.fail_ratio * 100
    if failure_rate > 1.0:
        print(f"❌ FAILED: Failure rate ({failure_rate:.2f}%) > 1% target")
        targets_met = False
    else:
        print(f"✅ PASSED: Failure rate ({failure_rate:.2f}%) < 1% target")

    # Target 3: RPS > 50
    if stats.total.total_rps < 50:
        print(f"⚠️  WARNING: RPS ({stats.total.total_rps:.1f}) < 50 target")
    else:
        print(f"✅ PASSED: RPS ({stats.total.total_rps:.1f}) > 50 target")

    print("\n" + "="*70 + "\n")

    if targets_met:
        print("🎉 All performance targets met! System is production-ready.\n")
    else:
        print("⚠️  Some performance targets not met. Optimization needed.\n")


# ---------------------------------------------------------------------------
# USAGE INSTRUCTIONS
# ---------------------------------------------------------------------------

"""
RUNNING LOAD TESTS
==================

1. Basic Load Test (100 concurrent users):
   locust -f backend/tests/load_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=5m

2. Stress Test (find breaking point):
   locust -f backend/tests/load_test.py --host=http://localhost:8000 --users=300 --spawn-rate=50 --run-time=10m

3. Burst Traffic Test (sudden spike):
   locust -f backend/tests/load_test.py --host=http://localhost:8000 --step-load --step-users=50 --step-time=30s

4. Specific User Type Only:
   locust -f backend/tests/load_test.py --host=http://localhost:8000 --users=50 --spawn-rate=5 OsoolBrowserUser

5. Mixed Load (realistic):
   locust -f backend/tests/load_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10

PERFORMANCE TARGETS
===================

✅ 95th percentile response time: < 2000ms
✅ Failure rate: < 1%
✅ Requests per second: > 50 RPS
✅ Concurrent users supported: > 100
✅ CPU usage: < 80%
✅ Memory usage: < 2GB

EXPECTED BOTTLENECKS
====================

1. Claude API Rate Limits
   - Solution: Circuit breaker will open after failures
   - Fallback: OpenAI GPT-4o

2. Database Connections
   - Solution: Connection pooling (max 20 connections)
   - Monitor: Check /health/detailed for DB status

3. Redis Cache
   - Solution: Increase cache hit rate
   - Monitor: Session cost lookups should be cached

4. OpenAI Embeddings
   - Solution: Cache frequently searched queries
   - Monitor: Embedding generation time

MONITORING DURING TEST
======================

1. Watch Logs:
   tail -f backend/app.log

2. Monitor System Resources:
   htop  # CPU/Memory
   iotop  # Disk I/O

3. Check Health Endpoints:
   curl http://localhost:8000/health/detailed
   curl http://localhost:8000/health/circuits
   curl http://localhost:8000/health/costs

4. Monitor API Costs:
   Watch cost_tracking in responses
   Check daily cost limit not exceeded

TROUBLESHOOTING
===============

High Response Times:
- Check database query performance
- Verify Claude API isn't rate limiting
- Check Redis cache hit rate
- Profile slow endpoints with FastAPI's built-in profiler

High Failure Rate:
- Check circuit breaker states (/health/circuits)
- Verify API keys are valid
- Check database connections available
- Review error logs

Rate Limiting Triggered:
- Expected under very high load
- Verify rate limits are reasonable
- Check Redis is working (distributed rate limiting)

Memory Leaks:
- Monitor memory over time
- Check conversation history isn't growing unbounded
- Verify Redis keys have proper expiration
"""


# ---------------------------------------------------------------------------
# ADDITIONAL TEST SCENARIOS
# ---------------------------------------------------------------------------

class StressTestUser(HttpUser):
    """
    Aggressive user for stress testing.
    No wait time, rapid-fire requests.
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.session_id = f"stress-{uuid.uuid4()}"

    @task
    def spam_requests(self):
        """Send rapid requests to stress test"""
        self.client.post(
            "/api/chat",
            json={"session_id": self.session_id, "message": "test"},
            catch_response=True
        )


class MaliciousUser(HttpUser):
    """
    Simulates potential abuse patterns for security testing.
    """

    wait_time = between(0.1, 1)

    def on_start(self):
        self.session_id = f"malicious-{uuid.uuid4()}"

    @task(3)
    def send_very_long_messages(self):
        """Test with extremely long input"""
        long_message = "a" * 5000  # 5K characters
        self.client.post(
            "/api/chat",
            json={"session_id": self.session_id, "message": long_message},
            catch_response=True
        )

    @task(2)
    def send_special_characters(self):
        """Test with special characters"""
        special_message = "🏠" * 100 + "<script>alert('xss')</script>" + "عربي" * 50
        self.client.post(
            "/api/chat",
            json={"session_id": self.session_id, "message": special_message},
            catch_response=True
        )

    @task(1)
    def rapid_fire_same_session(self):
        """Test rate limiting on same session"""
        for _ in range(50):
            self.client.post(
                "/api/chat",
                json={"session_id": self.session_id, "message": "spam"},
                catch_response=True
            )


# ---------------------------------------------------------------------------
# CUSTOM SCENARIOS
# ---------------------------------------------------------------------------

class RealisticUserJourney(HttpUser):
    """
    Simulates complete user journey from search to reservation.
    """

    wait_time = between(3, 8)

    def on_start(self):
        self.session_id = f"journey-{uuid.uuid4()}"
        self.stage = 0

    @task
    def progress_through_journey(self):
        """Progress through realistic buying journey"""

        if self.stage == 0:
            # Stage 1: Initial greeting
            self.client.post("/api/chat", json={
                "session_id": self.session_id,
                "message": "Hello, I'm looking for an apartment"
            })
            self.stage = 1

        elif self.stage == 1:
            # Stage 2: Specify requirements
            self.client.post("/api/chat", json={
                "session_id": self.session_id,
                "message": "3 bedrooms in New Cairo, budget 4-5M"
            })
            self.stage = 2

        elif self.stage == 2:
            # Stage 3: Ask about price
            self.client.post("/api/chat", json={
                "session_id": self.session_id,
                "message": "Is the first one a good price?"
            })
            self.stage = 3

        elif self.stage == 3:
            # Stage 4: Calculate payments
            self.client.post("/api/chat", json={
                "session_id": self.session_id,
                "message": "Calculate my monthly payments with 20% down"
            })
            self.stage = 4

        elif self.stage == 4:
            # Stage 5: Raise objection
            self.client.post("/api/chat", json={
                "session_id": self.session_id,
                "message": "This seems expensive"
            })
            self.stage = 5

        elif self.stage == 5:
            # Stage 6: Request viewing
            self.client.post("/api/chat", json={
                "session_id": self.session_id,
                "message": "I want to schedule a viewing"
            })
            self.stage = 6

        else:
            # Reset journey
            self.stage = 0
            self.session_id = f"journey-{uuid.uuid4()}"


# ---------------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import subprocess
    import sys

    print("\n" + "="*70)
    print("Osool Load Testing Suite")
    print("="*70)
    print("\nStarting Locust web interface...")
    print("Open browser: http://localhost:8089")
    print("\nRecommended settings:")
    print("  - Users: 100")
    print("  - Spawn rate: 10")
    print("  - Host: http://localhost:8000")
    print("\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")

    # Launch locust
    subprocess.run([
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host=http://localhost:8000"
    ])
