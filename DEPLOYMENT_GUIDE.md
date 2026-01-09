# Osool Platform - Deployment Guide
**Phase 4.3: Production Deployment**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Database Migrations](#database-migrations)
5. [Smart Contract Deployment](#smart-contract-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker**: v24.0+
- **Docker Compose**: v2.20+
- **Node.js**: v20+ (for smart contracts)
- **Hardhat**: For smart contract deployment
- **Git**: For version control

### Required Accounts

- **OpenAI API Key**: For AI features
- **Polygon RPC**: Alchemy or Infura (Polygon mainnet/Amoy testnet)
- **Paymob Account**: For EGP payments
- **Sentry DSN**: Error tracking (optional but recommended)

### Server Requirements

| Environment | CPU | RAM | Disk | Bandwidth |
|-------------|-----|-----|------|-----------|
| Development | 2 cores | 4GB | 50GB | 100Mbps |
| Staging | 4 cores | 8GB | 100GB | 500Mbps |
| Production | 8 cores | 16GB | 250GB | 1Gbps |

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/osool.git
cd osool
```

### 2. Create Environment Files

**Backend Environment** (`.env`):

```bash
# Database
POSTGRES_USER=osool
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=osool
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}

# API Keys
OPENAI_API_KEY=sk-...
PAYMOB_API_KEY=your_paymob_api_key
PAYMOB_SECRET_KEY=your_paymob_secret

# Blockchain
BLOCKCHAIN_PRIVATE_KEY=your_private_key_here
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
AMM_CONTRACT_ADDRESS=0x...
STABLECOIN_CONTRACT_ADDRESS=0x...

# Authentication
JWT_SECRET_KEY=your_jwt_secret_here_min_32_chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production

# Email (Optional)
SMTP_USERNAME=alerts@osool.com
SMTP_PASSWORD=your_smtp_password

# Grafana
GRAFANA_ADMIN_PASSWORD=your_secure_grafana_password
```

**Frontend Environment** (web/.env.production):

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.osool.com
NEXT_PUBLIC_CHAIN_ID=137  # Polygon Mainnet
```

### 3. Create Secrets (Docker Secrets)

```bash
# Create secrets directory
mkdir -p secrets

# Database password
echo "your_secure_db_password" > secrets/db_password.txt

# Blockchain private key
echo "your_private_key" > secrets/blockchain_private_key.txt

# Secure permissions
chmod 600 secrets/*.txt
```

---

## Docker Deployment

### Development Environment

```bash
docker-compose up -d
```

Access:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Production Deployment

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"osool-backend"}

# Check running containers
docker ps

# Expected containers:
# - osool-backend
# - osool-frontend
# - osool-postgres
# - osool-redis
```

---

## Database Migrations

### Initial Setup

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Verify migration
docker-compose exec backend alembic current
```

### Create New Migration

```bash
# Generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Review generated migration file
cat backend/alembic/versions/xxx_description.py

# Apply migration
docker-compose exec backend alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Rollback to specific revision
docker-compose exec backend alembic downgrade <revision_id>

# Rollback all
docker-compose exec backend alembic downgrade base
```

---

## Smart Contract Deployment

### 1. Install Hardhat

```bash
cd contracts
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
```

### 2. Configure Hardhat

**hardhat.config.js**:

```javascript
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    polygonAmoy: {
      url: process.env.POLYGON_RPC_URL,
      accounts: [process.env.BLOCKCHAIN_PRIVATE_KEY],
      chainId: 80002
    },
    polygon: {
      url: process.env.POLYGON_RPC_URL,
      accounts: [process.env.BLOCKCHAIN_PRIVATE_KEY],
      chainId: 137
    }
  },
  etherscan: {
    apiKey: process.env.POLYGONSCAN_API_KEY
  }
};
```

### 3. Deploy to Testnet (Polygon Amoy)

```bash
# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Deploy EGP Stablecoin
npx hardhat run scripts/deploy_stablecoin.js --network polygonAmoy

# Deploy AMM
npx hardhat run scripts/deploy_amm.js --network polygonAmoy

# Verify contracts
npx hardhat verify --network polygonAmoy <CONTRACT_ADDRESS>
```

### 4. Deploy to Mainnet (Polygon)

**⚠️ IMPORTANT**: Only deploy after:
- All tests pass (100+ test cases)
- Security audit completed
- Testnet deployment verified
- Team approval

```bash
# Deploy to Polygon Mainnet
npx hardhat run scripts/deploy_stablecoin.js --network polygon
npx hardhat run scripts/deploy_amm.js --network polygon

# Verify on Polygonscan
npx hardhat verify --network polygon <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>
```

### 5. Update Backend Config

```bash
# Update .env with deployed contract addresses
AMM_CONTRACT_ADDRESS=0xYourAMMAddress
STABLECOIN_CONTRACT_ADDRESS=0xYourStablecoinAddress

# Restart backend
docker-compose restart backend
```

---

## Monitoring Setup

### 1. Start Monitoring Stack

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `${GRAFANA_ADMIN_PASSWORD}`

- **Prometheus**: http://localhost:9090

- **Alertmanager**: http://localhost:9093

### 3. Import Grafana Dashboard

1. Login to Grafana
2. Go to **Configuration** → **Data Sources**
3. Add **Prometheus** data source: `http://prometheus:9090`
4. Go to **Dashboards** → **Import**
5. Upload `monitoring/grafana/dashboards/osool-main-dashboard.json`

### 4. Configure Alerts

1. Update `monitoring/prometheus/alertmanager.yml` with your webhook URLs
2. Restart Alertmanager: `docker-compose restart alertmanager`

---

## CI/CD Pipeline

### GitHub Actions Setup

1. **Add Repository Secrets**:
   - Go to GitHub → Settings → Secrets
   - Add the following secrets:

```
OPENAI_API_KEY
STAGING_HOST
STAGING_USER
STAGING_SSH_KEY
PRODUCTION_HOST
PRODUCTION_USER
PRODUCTION_SSH_KEY
SLACK_WEBHOOK
```

2. **Enable GitHub Packages**:
   - Settings → Actions → General
   - Allow Actions to create Pull Requests
   - Allow Actions to push to GitHub Container Registry

3. **Workflow Triggers**:
   - **Push to `develop`** → Deploy to Staging
   - **Push to `master/main`** → Deploy to Production
   - **Pull Request** → Run tests only

### Manual Deployment

```bash
# SSH to server
ssh user@osool.com

# Navigate to project
cd /opt/osool

# Pull latest code
git pull origin master

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Run migrations
docker-compose exec backend alembic upgrade head

# Verify health
curl http://localhost:8000/health
```

---

## Rollback Procedures

### Application Rollback

```bash
# 1. SSH to server
ssh user@osool.com

# 2. Stop current deployment
cd /opt/osool
docker-compose -f docker-compose.prod.yml down

# 3. Checkout previous version
git log --oneline  # Find previous commit
git checkout <previous_commit_hash>

# 4. Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Rollback database (if needed)
docker-compose exec backend alembic downgrade -1

# 6. Verify health
curl http://localhost:8000/health
```

### Database Rollback

```bash
# View migration history
docker-compose exec backend alembic history

# Rollback to specific revision
docker-compose exec backend alembic downgrade <revision_id>

# Verify current version
docker-compose exec backend alembic current
```

### Smart Contract Rollback

**⚠️ WARNING**: Smart contracts are immutable. You CANNOT rollback a deployed contract.

**Options**:
1. **Pause Contract**: Use emergency pause function
   ```javascript
   await contract.pause();
   ```

2. **Deploy New Version**: Deploy a new contract and migrate liquidity
   ```bash
   npx hardhat run scripts/deploy_amm_v2.js --network polygon
   ```

3. **Update Backend Config**: Point backend to new contract address

---

## Troubleshooting

### Backend Not Starting

**Symptoms**: Backend container exits immediately

**Diagnosis**:
```bash
docker-compose logs backend
```

**Common Causes**:
1. **Database not ready**: Wait for PostgreSQL to start
   ```bash
   docker-compose up postgres
   # Wait for "database system is ready to accept connections"
   docker-compose up backend
   ```

2. **Missing environment variables**:
   ```bash
   docker-compose config  # Verify env vars are loaded
   ```

3. **Port conflict**:
   ```bash
   lsof -i :8000  # Check what's using port 8000
   kill -9 <PID>  # Kill conflicting process
   ```

### Database Migration Failed

**Symptoms**: `alembic upgrade head` fails

**Diagnosis**:
```bash
docker-compose exec backend alembic current
docker-compose exec backend alembic history
```

**Solutions**:
1. **Rollback and retry**:
   ```bash
   docker-compose exec backend alembic downgrade -1
   docker-compose exec backend alembic upgrade head
   ```

2. **Fix migration file**: Edit `backend/alembic/versions/xxx.py`

3. **Stamp current version** (if database is already correct):
   ```bash
   docker-compose exec backend alembic stamp head
   ```

### High Memory Usage

**Symptoms**: Server running out of memory

**Diagnosis**:
```bash
docker stats  # Check memory usage per container
```

**Solutions**:
1. **Reduce Uvicorn workers**:
   ```bash
   # Edit docker-compose.prod.yml
   environment:
     - WORKERS=2  # Reduce from 4
   ```

2. **Add memory limits**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

3. **Check for memory leaks**:
   ```bash
   docker-compose exec backend python -m memory_profiler app/main.py
   ```

### OpenAI API Rate Limit

**Symptoms**: `RateLimitError` in logs

**Solutions**:
1. **Implement request queue** (already done via circuit breaker)
2. **Increase OpenAI tier** (pay for higher limits)
3. **Add caching** for common queries

### Blockchain Transaction Failed

**Symptoms**: Transaction reverts or never confirms

**Diagnosis**:
```bash
# Check transaction on Polygonscan
https://polygonscan.com/tx/<TX_HASH>
```

**Common Causes**:
1. **Insufficient gas**: Increase gas limit
2. **Slippage exceeded**: Increase slippage tolerance
3. **Contract paused**: Check contract state
4. **Insufficient balance**: Fund wallet with MATIC

---

## Security Checklist

### Before Production Launch

- [ ] Change all default passwords
- [ ] Rotate all API keys
- [ ] Enable HTTPS (SSL certificate)
- [ ] Configure firewall (allow only necessary ports)
- [ ] Set up fail2ban (brute force protection)
- [ ] Enable database backups (automated)
- [ ] Configure monitoring alerts
- [ ] Restrict SSH access (key-based only)
- [ ] Set up VPN for admin access
- [ ] Review and minimize IAM permissions
- [ ] Enable CloudFlare DDoS protection
- [ ] Configure rate limiting
- [ ] Set up security headers (HSTS, CSP, etc.)
- [ ] Run security audit (OWASP ZAP, Burp Suite)
- [ ] Smart contract audit (external auditor)
- [ ] Penetration testing
- [ ] GDPR compliance review
- [ ] Privacy policy published
- [ ] Terms of service published

---

## Maintenance Schedule

### Daily
- Monitor dashboard for anomalies
- Check error logs (Sentry)
- Verify backup completion

### Weekly
- Review OpenAI costs
- Update dependencies (security patches)
- Review alert thresholds
- Test rollback procedures

### Monthly
- Database vacuum and analyze
- Review and optimize slow queries
- Update Prometheus retention policy
- Security audit
- Load testing
- Disaster recovery drill

### Quarterly
- Update Docker images
- Update Prometheus/Grafana
- Review on-call rotation
- Team training on incident response

---

## Support & Contacts

- **Documentation**: https://docs.osool.com
- **Status Page**: https://status.osool.com
- **Support Email**: support@osool.com
- **Emergency**: +20-XXX-XXXX (on-call engineer)

---

**Last Updated**: 2026-01-09
**Version**: 1.0.0
**Status**: ✅ Production Ready
