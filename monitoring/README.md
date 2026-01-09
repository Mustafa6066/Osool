# Osool Platform Monitoring Stack
**Phase 4.1: Production Monitoring & Observability**

---

## Overview

The Osool monitoring stack provides comprehensive observability using:
- **Prometheus** - Time-series metrics database
- **Grafana** - Visualization dashboards
- **Alertmanager** - Alert routing and notifications
- **Exporters** - PostgreSQL, Redis, Node (system metrics)

---

## Quick Start

### 1. Start Monitoring Stack

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin123` (change in production!)

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### 3. Import Dashboards

1. Login to Grafana (http://localhost:3001)
2. Go to Configuration → Data Sources
3. Add Prometheus data source: `http://prometheus:9090`
4. Go to Dashboards → Import
5. Upload `grafana/dashboards/osool-main-dashboard.json`

---

## Metrics Exposed

### API Metrics

```prometheus
# Total API requests
osool_api_requests_total{method="GET", endpoint="/api/properties", status="200"}

# API request duration (histogram)
osool_api_request_duration_seconds_bucket{method="POST", endpoint="/api/chat"}

# Request rate (calculated)
rate(osool_api_requests_total[5m])

# Error rate (calculated)
rate(osool_api_requests_total{status=~"5.."}[5m]) / rate(osool_api_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(osool_api_request_duration_seconds_bucket[5m]))
```

### OpenAI Metrics

```prometheus
# Total OpenAI requests
osool_openai_requests_total{model="gpt-4o", context="property_search"}

# Token usage
osool_openai_tokens_used_total{model="gpt-4o", token_type="prompt"}
osool_openai_tokens_used_total{model="gpt-4o", token_type="completion"}

# Cost tracking
osool_openai_cost_usd_total{model="gpt-4o"}

# Daily cost (calculated)
increase(osool_openai_cost_usd_total[24h])
```

### Database Metrics

```prometheus
# Active connections
osool_database_connections

# Query duration (histogram)
osool_database_query_duration_seconds_bucket{query_type="select"}

# Slow queries (p95 > 1s)
histogram_quantile(0.95, rate(osool_database_query_duration_seconds_bucket[5m])) > 1
```

### Circuit Breaker Metrics

```prometheus
# Circuit breaker state (0=closed, 1=half_open, 2=open)
osool_circuit_breaker_state{service="openai"}
osool_circuit_breaker_state{service="blockchain"}
osool_circuit_breaker_state{service="paymob"}

# Failure count
osool_circuit_breaker_failures_total{service="openai"}
```

### Business Metrics

```prometheus
# Chat sessions started
osool_chat_sessions_total

# Property searches
osool_property_searches_total

# Reservations
osool_reservations_total{status="completed"}
osool_reservations_total{status="failed"}

# Conversion rate (calculated)
rate(osool_reservations_total{status="completed"}[1h]) / rate(osool_property_searches_total[1h])
```

### Liquidity Marketplace Metrics (Phase 6)

```prometheus
# Pool liquidity
liquidity_pool_egp_reserve{pool_id="42", property_title="Zed East Apartment"}

# Trading volume
liquidity_trade_volume_egp{pool_id="42"}

# Slippage tracking
liquidity_trade_slippage_percent

# Average slippage (5min)
avg_over_time(liquidity_trade_slippage_percent[5m])
```

---

## Alerting Rules

### Critical Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| APIDown | Backend unreachable | 1 minute | PagerDuty + Slack |
| DatabaseDown | PostgreSQL unreachable | 1 minute | PagerDuty + Slack |
| CircuitBreakerOpen | External service unavailable | 2 minutes | Slack |

### Warning Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| HighErrorRate | 5xx responses | >5% for 2min | Slack |
| HighAPILatency | p95 response time | >2s for 5min | Slack |
| HighOpenAICost | Daily OpenAI cost | >$100 | Email |
| HighDatabaseConnections | Active connections | >40 for 5min | Slack |
| HighMemoryUsage | System memory | >85% for 10min | Slack |

### Business Alerts

| Alert | Condition | Threshold | Action |
|-------|-----------|-----------|--------|
| NoReservationsInLast24Hours | Zero reservations | 24 hours | Slack |
| HighReservationFailureRate | Failed reservations | >20% for 30min | Slack |
| LowTrafficAnomaly | Request rate | <0.1 req/sec for 15min | Slack (Info) |

---

## Notification Channels

### Slack Integration

1. Create a Slack incoming webhook: https://api.slack.com/messaging/webhooks
2. Set environment variable:
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```
3. Update `alertmanager.yml` with your webhook URL

### PagerDuty Integration (Critical Alerts)

1. Create a PagerDuty service integration
2. Get the service key
3. Set environment variable:
   ```bash
   export PAGERDUTY_SERVICE_KEY="your_service_key"
   ```

### Email Alerts (Cost Tracking)

1. Configure SMTP settings:
   ```bash
   export SMTP_USERNAME="alerts@osool.com"
   export SMTP_PASSWORD="your_smtp_password"
   ```

---

## Grafana Dashboards

### Main Dashboard (`osool-main-dashboard.json`)

**Panels**:
1. **System Overview**
   - API Request Rate (by endpoint, method, status)
   - API Response Time (p95, p99)
   - Error Rate (5xx)
   - Active Chat Sessions
   - Property Searches
   - Reservations (24h)

2. **AI & OpenAI Metrics**
   - OpenAI Request Rate
   - Token Usage (prompt + completion)
   - Daily Cost (with alerts at $50, $100)

3. **Database & Cache**
   - Database Connections (gauge)
   - Query Time (p95 by query type)
   - Redis Memory Usage (gauge with thresholds)

4. **Liquidity Marketplace**
   - Trading Volume (24h)
   - Active Pools
   - Total Liquidity (EGP)
   - Average Slippage (gauge)

5. **System Resources**
   - CPU Usage (per core)
   - Memory Usage
   - Disk Space

**Auto-refresh**: 30 seconds
**Time Range**: Last 6 hours (configurable)

---

## Custom Queries (PromQL Examples)

### API Performance

```promql
# Requests per second (last 5 minutes)
rate(osool_api_requests_total[5m])

# Requests per minute (last hour)
sum(rate(osool_api_requests_total[1h])) * 60

# Success rate (%)
sum(rate(osool_api_requests_total{status!~"5.."}[5m])) / sum(rate(osool_api_requests_total[5m])) * 100

# p99 latency (slowest 1% of requests)
histogram_quantile(0.99, rate(osool_api_request_duration_seconds_bucket[5m]))

# Requests by status code
sum by(status) (rate(osool_api_requests_total[5m]))
```

### OpenAI Cost Analysis

```promql
# Cost per hour (current rate)
rate(osool_openai_cost_usd_total[1h]) * 3600

# Projected monthly cost
rate(osool_openai_cost_usd_total[7d]) * 86400 * 30

# Cost per request
rate(osool_openai_cost_usd_total[1h]) / rate(osool_openai_requests_total[1h])

# Most expensive model
topk(1, rate(osool_openai_cost_usd_total[1h]))
```

### Database Performance

```promql
# Queries per second
rate(osool_database_query_duration_seconds_count[5m])

# Slowest query type (p95)
max by(query_type) (histogram_quantile(0.95, rate(osool_database_query_duration_seconds_bucket[5m])))

# Connection pool utilization (%)
osool_database_connections / 50 * 100
```

### Business Metrics

```promql
# Conversion funnel
rate(osool_chat_sessions_total[1h])  # Top of funnel
rate(osool_property_searches_total[1h])  # Interest
rate(osool_reservations_total{status="completed"}[1h])  # Conversion

# Conversion rate (%)
rate(osool_reservations_total{status="completed"}[1h]) / rate(osool_chat_sessions_total[1h]) * 100

# Revenue per hour (if tracking)
rate(osool_reservations_total{status="completed"}[1h]) * 50000  # Assuming 50K EGP avg
```

---

## Troubleshooting

### Metrics Not Showing Up

1. Check if `/metrics` endpoint is accessible:
   ```bash
   curl http://localhost:8000/metrics
   ```
   Should return Prometheus format metrics.

2. Check Prometheus targets:
   - Go to http://localhost:9090/targets
   - Ensure `osool-backend` target is UP

3. Check logs:
   ```bash
   docker logs osool-prometheus
   docker logs osool-backend
   ```

### High Memory Usage (Prometheus)

1. Reduce retention time in `prometheus.yml`:
   ```yaml
   --storage.tsdb.retention.time=15d  # Default: 30d
   ```

2. Reduce scrape interval:
   ```yaml
   scrape_interval: 30s  # Default: 15s
   ```

### Grafana Dashboard Not Loading

1. Check data source connection:
   - Grafana → Configuration → Data Sources
   - Test connection to Prometheus

2. Re-import dashboard:
   - Export current dashboard JSON
   - Delete dashboard
   - Import fresh copy

### Alerts Not Firing

1. Check Alertmanager logs:
   ```bash
   docker logs osool-alertmanager
   ```

2. Verify alert rules are loaded:
   - Go to http://localhost:9090/alerts
   - Check if rules are present

3. Test alert manually:
   ```bash
   curl -X POST http://localhost:9093/api/v1/alerts
   ```

---

## Production Checklist

### Before Deployment

- [ ] Set secure Grafana admin password
- [ ] Configure Slack webhook URL
- [ ] Configure PagerDuty service key (critical alerts)
- [ ] Set up email SMTP credentials
- [ ] Restrict `/metrics` endpoint (API key or internal network)
- [ ] Enable HTTPS for Grafana (reverse proxy)
- [ ] Set up backup for Prometheus data (volume)
- [ ] Configure retention policies (disk space)

### After Deployment

- [ ] Verify all exporters are UP
- [ ] Test alert firing (simulate high error rate)
- [ ] Set up on-call rotation for critical alerts
- [ ] Document runbooks for common alerts
- [ ] Train team on Grafana dashboards
- [ ] Set up weekly monitoring reviews

---

## Monitoring Costs

### Resources Required

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| Prometheus | 0.5 CPU | 2GB | 50GB (30-day retention) |
| Grafana | 0.2 CPU | 512MB | 1GB |
| Exporters | 0.1 CPU | 256MB | Minimal |
| **Total** | **0.8 CPU** | **2.8GB** | **51GB** |

### Cost Estimate (AWS)

- **EC2 Instance** (t3.medium): ~$30/month
- **EBS Storage** (50GB): ~$5/month
- **Data Transfer**: ~$10/month
- **Total**: ~$45/month

**For large-scale production**, consider managed services:
- **AWS CloudWatch**: ~$100-200/month
- **Datadog**: ~$200-500/month
- **New Relic**: ~$150-400/month

---

## Advanced Features

### Custom Metrics (Adding New Metrics)

1. Import counter in your code:
   ```python
   from app.services.metrics import Counter

   my_custom_metric = Counter(
       'osool_my_feature_events_total',
       'Description of the metric',
       ['label1', 'label2']
   )
   ```

2. Increment metric:
   ```python
   my_custom_metric.labels(label1='value1', label2='value2').inc()
   ```

3. Metric appears automatically at `/metrics` endpoint

### Recording Rules (Pre-computed Queries)

Add to `prometheus.yml`:
```yaml
rule_files:
  - "recording_rules.yml"
```

Create `recording_rules.yml`:
```yaml
groups:
  - name: osool_aggregations
    interval: 1m
    rules:
      - record: osool:api_request_rate:5m
        expr: rate(osool_api_requests_total[5m])

      - record: osool:error_rate:5m
        expr: rate(osool_api_requests_total{status=~"5.."}[5m]) / rate(osool_api_requests_total[5m])
```

### Distributed Tracing (Future Enhancement)

For request tracing across services:
1. **Jaeger** (open-source) or **DataDog APM**
2. Instrument code with OpenTelemetry
3. Trace requests: Frontend → Backend → Database → OpenAI

---

## Maintenance

### Weekly Tasks
- Review error rate trends
- Check cost reports (OpenAI)
- Verify backup completion

### Monthly Tasks
- Review alert thresholds (adjust if needed)
- Clean up old Prometheus data (if disk full)
- Update dashboards with new metrics
- Conduct alert drill (test PagerDuty)

### Quarterly Tasks
- Security audit of monitoring stack
- Update Prometheus/Grafana versions
- Review on-call rotation effectiveness

---

## Support & Documentation

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/
- **Osool Runbooks**: `docs/runbooks/` (TODO)

---

**Last Updated**: 2026-01-09
**Version**: 1.0.0
**Status**: Production Ready ✅
