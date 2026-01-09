# Osool Production Migration Guide

## Phase 1: Data Migration to PostgreSQL

This guide walks you through migrating your 3,274 properties from flat files to PostgreSQL with vector embeddings.

---

## Prerequisites

1. **PostgreSQL 15+** with pgvector extension installed
2. **Python 3.10+** with all dependencies installed
3. **OpenAI API Key** for embedding generation
4. **Environment variables** configured in `.env`

---

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key new dependencies:
- `alembic>=1.13.0` - Database migrations
- `authlib>=1.3.0` - Google OAuth
- `twilio>=8.10.0` - SMS OTP
- `sendgrid>=6.11.0` - Email verification
- `sentry-sdk>=1.40.0` - Error monitoring
- `prometheus-client>=0.19.0` - Metrics

---

## Step 2: Configure Environment Variables

Update your `.env` file with these new variables:

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@localhost:5432/osool

# OpenAI (REQUIRED for embeddings)
OPENAI_API_KEY=sk-...

# Email Verification (Phase 2)
SENDGRID_API_KEY=SG....
FROM_EMAIL=noreply@osool.com
FRONTEND_URL=http://localhost:3000

# Phone OTP (Phase 2)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890

# Google OAuth (Phase 2)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Security (Phase 4 - CRITICAL)
ADMIN_API_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Optional
ENVIRONMENT=development  # development | production
```

---

## Step 3: Set Up PostgreSQL Database

### Create Database

```bash
psql -U postgres
```

```sql
CREATE DATABASE osool;
\c osool;

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Initialize Schema

The migration script will create all tables automatically, but you can also use Alembic:

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

---

## Step 4: Run Data Migration

This will:
1. Load all 3,274 properties from `data/properties.json`
2. Generate OpenAI embeddings for each property
3. Insert into PostgreSQL with deduplication
4. Create vector search index

```bash
cd backend
python ingest_data_postgres.py
```

**Expected output:**
```
======================================================================
🏠 OSOOL DATA MIGRATION TO POSTGRESQL
======================================================================

📂 Loading data from: ../data/properties.json
   - Properties in JSON: 3274

💾 Migrating to PostgreSQL with embeddings...

📊 Processing 3274 properties...
   [100/3274] ✅ Inserted: NC1
   [200/3274] ✅ Inserted: NC2
   ...
   [3274/3274] ✅ Inserted: NC3274

📈 INGESTION SUMMARY:
   ✅ Inserted: 3274
   ⏭️ Skipped (duplicates): 0
   ❌ Failed: 0
   📊 Total processed: 3274

🔢 Total properties in database: 3274

🎉 Done! All properties migrated to PostgreSQL.
   AI can now query directly from the database.
   This prevents hallucinations by enforcing data validation.
```

**Estimated time:** 10-15 minutes (depending on OpenAI API rate limits)

---

## Step 5: Verify Migration

### Check Property Count

```bash
psql -U postgres -d osool
```

```sql
-- Should return 3274
SELECT COUNT(*) FROM properties;

-- Check embeddings are present
SELECT COUNT(*) FROM properties WHERE embedding IS NOT NULL;

-- Sample property
SELECT id, title, location, price FROM properties LIMIT 5;

-- Test vector search
SELECT title, location, price
FROM properties
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

### Test AI Search

```bash
# Start backend server
uvicorn app.main:app --reload
```

```bash
# Test vector search endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "Show me apartments in New Cairo under 5M EGP",
    "session_id": "test-123"
  }'
```

**Expected:** AI returns only properties that exist in the database, with valid IDs.

---

## Step 6: Verify Hallucination Prevention

The new system prevents AI from recommending non-existent properties:

```python
# In backend/app/services/vector_search.py
async def validate_property_exists(db, property_id):
    # Returns False if property doesn't exist
    # Logs warning: "⚠️ HALLUCINATION BLOCKED: Property X does not exist"
```

### Test Hallucination Detection

```bash
# Try to query non-existent property
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Show me property ID 999999", "session_id": "test"}'
```

**Expected:** AI should respond "Property not found" or search for alternatives, NOT hallucinate details.

---

## Troubleshooting

### Issue: "Module 'pgvector' has no attribute 'sqlalchemy'"

```bash
pip install --upgrade pgvector
```

### Issue: "Could not connect to PostgreSQL"

Check your `DATABASE_URL` format:
- ✅ Correct: `postgresql+asyncpg://user:pass@localhost:5432/osool`
- ❌ Wrong: `postgres://user:pass@localhost:5432/osool`

### Issue: "OpenAI rate limit exceeded"

The script processes properties one at a time. If you hit rate limits:

1. Wait 60 seconds
2. Re-run the script - it will skip already-inserted properties
3. Consider upgrading your OpenAI API tier

### Issue: "Embedding generation failed"

Check:
1. OpenAI API key is valid: `echo $OPENAI_API_KEY`
2. You have credits: https://platform.openai.com/account/usage
3. Network connectivity to api.openai.com

---

## Performance Optimization

### Indexing

Create indexes for faster queries:

```sql
-- Create index on location for filtering
CREATE INDEX idx_properties_location ON properties(location);

-- Create index on price for range queries
CREATE INDEX idx_properties_price ON properties(price);

-- Create GIN index for full-text search (fallback)
CREATE INDEX idx_properties_search ON properties USING GIN(
    to_tsvector('english', title || ' ' || description || ' ' || location)
);
```

### Vector Search Optimization

```sql
-- Create IVFFlat index for faster vector search (after data is loaded)
CREATE INDEX ON properties USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Analyze table for query planner
ANALYZE properties;
```

---

## Next Steps

After successful migration:

1. **Phase 2:** Implement authentication endpoints (Google OAuth, Phone OTP)
2. **Phase 3:** Update AI persona and add chat persistence
3. **Phase 4:** Security hardening (remove hardcoded secrets)
4. **Phase 5:** Production monitoring setup
5. **Phase 6:** Write tests
6. **Phase 7:** Blockchain verification

---

## Rollback Plan

If migration fails, you can roll back:

```sql
-- Drop all tables
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS payment_approvals CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS properties CASCADE;
DROP TABLE IF EXISTS users CASCADE;
```

Then restore from backup or re-run migration after fixing issues.

---

## Success Criteria

✅ All 3,274 properties in database
✅ All properties have embeddings (1536 dimensions)
✅ Vector search returns relevant results
✅ AI chat only recommends existing properties
✅ No hallucinations detected in logs

---

## Support

If you encounter issues:
1. Check logs: `tail -f logs/migration.log`
2. Verify environment variables: `env | grep -E '(DATABASE|OPENAI)'`
3. Test database connection: `psql $DATABASE_URL -c "SELECT 1"`

For critical issues, the old Supabase system is still operational as fallback.
