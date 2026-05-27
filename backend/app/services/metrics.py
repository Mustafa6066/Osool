"""
Prometheus Metrics Service - Phase 5: Production Monitoring
------------------------------------------------------------
Exposes application metrics for Prometheus/Grafana monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# API Request Metrics
api_requests_total = Counter(
    'osool_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'osool_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# AI/OpenAI Metrics
openai_requests_total = Counter(
    'osool_openai_requests_total',
    'Total OpenAI API requests',
    ['model', 'context']
)

openai_tokens_used = Counter(
    'osool_openai_tokens_used_total',
    'Total OpenAI tokens consumed',
    ['model', 'token_type']
)

openai_cost_usd = Counter(
    'osool_openai_cost_usd_total',
    'Total OpenAI cost in USD',
    ['model']
)

# Database Metrics
database_connections = Gauge(
    'osool_database_connections',
    'Current database connections'
)

database_query_duration = Histogram(
    'osool_database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    'osool_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half_open, 2=open)',
    ['service']
)

circuit_breaker_failures = Counter(
    'osool_circuit_breaker_failures_total',
    'Circuit breaker failure count',
    ['service']
)

# Business Metrics
chat_sessions_total = Counter(
    'osool_chat_sessions_total',
    'Total chat sessions started'
)

property_searches_total = Counter(
    'osool_property_searches_total',
    'Total property searches'
)

reservations_total = Counter(
    'osool_reservations_total',
    'Total property reservations',
    ['status']
)


def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
