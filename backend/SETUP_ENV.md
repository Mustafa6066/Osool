# Environment Setup Guide

This guide helps you set up your `.env` file securely for local development.

## Quick Start (3 Steps)

### Step 1: Generate Secure Secrets

```bash
cd backend
python generate_secrets.py
```

This will generate:
- `JWT_SECRET_KEY` - For access token signing
- `ADMIN_API_KEY` - For admin endpoint protection
- `WALLET_ENCRYPTION_KEY` - For encrypting user wallets (CRITICAL!)
- `DATABASE_URL` - PostgreSQL connection with secure password

**IMPORTANT:** Copy these values immediately - they're shown only once!

### Step 2: Create Your .env File

```bash
# Copy the example template
cp .env.example .env
```

Then edit `backend/.env` and paste:
1. The secrets from Step 1
2. Your **NEW** OpenAI API key (from https://platform.openai.com/api-keys)
3. Your **NEW** Claude API key (from https://console.anthropic.com/settings/keys)

Your `.env` should look like:

```env
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://osool_user:m0IYkqx1sFxvp5Y0KYJcBzUA@localhost:5432/osool_dev

# Security Keys
JWT_SECRET_KEY=$hPw_UOPEaIIS_j*+uZlR(0oHcX3R#tBY&yEf8fhgMrJJnPos6yY38Q0=jnQku3V
ADMIN_API_KEY=bcc0e9313e4fc76cd0fb4767efdafe76d9974292cb777899ef18b8abfb594de3
WALLET_ENCRYPTION_KEY=sxMNZF7cdaODTTmG8kMM7XShG-hJb6P7rUwhL9Pnv_8=

# AI APIs (use your NEW keys!)
OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_NEW_KEY_HERE

# Claude Config
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.3

# App Settings
FRONTEND_URL=http://localhost:3000
PORT=8000
LOG_LEVEL=debug

# Optional Services (Phase 1: keep these disabled)
ENABLE_BLOCKCHAIN=false
ENABLE_PAYMENTS=false
ENABLE_SMS=false
ENABLE_EMAIL=false
```

### Step 3: Validate Configuration

```bash
python validate_config.py
```

This will check:
- All required variables are set
- API keys have correct format
- Database URL is valid
- Optional features are configured correctly

## Database Setup

### Option A: PostgreSQL (Recommended)

1. Install PostgreSQL:
   ```bash
   # Windows: Download from https://www.postgresql.org/download/windows/
   # Mac: brew install postgresql
   # Linux: sudo apt install postgresql
   ```

2. Create database and user:
   ```bash
   # Connect to PostgreSQL
   psql -U postgres

   # Run these commands:
   CREATE USER osool_user WITH PASSWORD 'your_password_from_generate_secrets';
   CREATE DATABASE osool_dev OWNER osool_user;
   \q
   ```

3. Update `.env` with your DATABASE_URL from `generate_secrets.py`

### Option B: SQLite (Quick testing)

For quick local testing without PostgreSQL:

```env
DATABASE_URL=sqlite:///./osool_dev.db
```

**Note:** SQLite is fine for development but NOT recommended for production.

## Security Checklist

- [ ] Generated secrets using `generate_secrets.py`
- [ ] Created new OpenAI API key (not the old one!)
- [ ] Created new Claude API key
- [ ] Copied all values to `.env` file
- [ ] Verified `.env` is in `.gitignore` (it is by default)
- [ ] Backed up secrets to password manager (1Password, Bitwarden, etc.)
- [ ] Validated config with `validate_config.py`
- [ ] **NEVER** shared `.env` file or API keys in chat/email

## What's in .env?

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `DATABASE_URL` | ✅ Yes | PostgreSQL or SQLite connection |
| `JWT_SECRET_KEY` | ✅ Yes | Signs access tokens |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI embeddings & fallback |
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude AMR reasoning |
| `WALLET_ENCRYPTION_KEY` | ✅ Yes | Encrypts user wallets (BACKUP THIS!) |
| `ADMIN_API_KEY` | ⚠️ Recommended | Protects admin endpoints |
| `SENTRY_DSN` | 🔵 Optional | Error tracking |
| `REDIS_URL` | 🔵 Optional | Caching & rate limiting |

## Troubleshooting

### "DATABASE_URL environment variable is required"
- Make sure you created `.env` file in `backend/` directory
- Check that `DATABASE_URL` is set in `.env`

### "API key format incorrect"
- OpenAI keys should start with `sk-proj-`
- Claude keys should start with `sk-ant-api03-`

### "Module not found: dotenv"
```bash
pip install python-dotenv
```

## Need Help?

1. Run the validator: `python validate_config.py`
2. Check [.env.example](./env.example) for reference
3. Re-generate secrets: `python generate_secrets.py`

## Next Steps

Once your configuration is validated:

```bash
# Start the development server
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation!
