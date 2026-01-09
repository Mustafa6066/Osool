# Osool Secrets Management

This directory contains sensitive credentials for production deployment.

## ⚠️ SECURITY WARNING

**NEVER commit these files to git!** The `.gitignore` file excludes this entire directory.

## Required Secret Files

### 1. `db_password.txt`
PostgreSQL database password. Generate a strong password:
```bash
openssl rand -base64 32 > db_password.txt
```

### 2. `blockchain_private_key.txt`
Ethereum/Polygon private key for the admin wallet (without 0x prefix):
```bash
# Generate new key using OpenSSL (for testing only, use hardware wallet for production)
openssl ecparam -genkey -name secp256k1 -noout -outform DER | tail -c +8 | head -c 32 | xxd -p -c 32 > blockchain_private_key.txt
```

**CRITICAL**: For production, use a hardware wallet or secure key management system (AWS KMS, HashiCorp Vault).

## Environment Variables (stored in `.env` file)

Create a `.env` file in the project root with these variables:

```bash
# Database
DATABASE_URL=postgresql://osool_admin:[PASSWORD_FROM_db_password.txt]@db:5432/osool_production
POSTGRES_USER=osool_admin
POSTGRES_DB=osool_production

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=[GENERATE_STRONG_PASSWORD]

# JWT Authentication
JWT_SECRET_KEY=[GENERATE_STRONG_SECRET]
# Generate with: openssl rand -hex 32

# Admin API Key
ADMIN_API_KEY=[GENERATE_STRONG_API_KEY]
# Generate with: openssl rand -hex 16

# OpenAI
OPENAI_API_KEY=sk-...

# Supabase (Vector Store)
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_KEY=eyJ...

# Blockchain
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/[API_KEY]
CHAIN_ID=137
OSOOL_REGISTRY_ADDRESS=0x...
PRIVATE_KEY=[SAME_AS_blockchain_private_key.txt]

# Payment Gateway (Paymob)
PAYMOB_API_KEY=...
PAYMOB_INTEGRATION_ID=...
PAYMOB_WEBHOOK_SECRET=...

# Monitoring
SENTRY_DSN=https://[KEY]@sentry.io/[PROJECT]

# Application
ENVIRONMENT=production
APP_VERSION=1.0.0
FRONTEND_DOMAIN=https://osool.com
```

## Secret Rotation Schedule

| Secret | Rotation Frequency | Last Rotated |
|--------|-------------------|--------------|
| JWT_SECRET_KEY | Every 90 days | TBD |
| ADMIN_API_KEY | Every 90 days | TBD |
| db_password | Every 180 days | TBD |
| PAYMOB_WEBHOOK_SECRET | On compromise | TBD |
| blockchain_private_key | Never (or use new wallet) | TBD |

## Compromised Secret Response Plan

1. **Immediate**: Revoke the compromised secret
2. **Within 1 hour**: Generate and deploy new secret
3. **Within 24 hours**: Review audit logs for unauthorized access
4. **Within 7 days**: Post-mortem and process improvement

## Backup Strategy

- Secrets are stored in AWS Secrets Manager (production)
- Encrypted backup stored offline
- Access restricted to 2 senior engineers only

## Production Deployment Checklist

- [ ] All secret files created with strong random values
- [ ] `.env` file populated with production credentials
- [ ] Secrets directory excluded from version control
- [ ] AWS Secrets Manager configured (optional but recommended)
- [ ] Team trained on secret rotation procedures
- [ ] Incident response plan documented and tested
