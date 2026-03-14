"""
Remove Hardcoded Secrets and Dummy Keys
---------------------------------------
This file documents all hardcoded secrets found and needs to be addressed.

CRITICAL: Remove before deploying to production!
"""

# ═══════════════════════════════════════════════════════════════
# FILE: backend/verify_superhuman.py
# ═══════════════════════════════════════════════════════════════
# ISSUE: Lines 16-17 contain hardcoded DUMMY API keys
# 
# CURRENT CODE:
# os.environ.setdefault("OPENAI_API_KEY", "DUMMY")
# os.environ.setdefault("ANTHROPIC_API_KEY", "DUMMY")
#
# FIX: DELETE THIS FILE OR REFACTOR TO:
# - Require explicit environment variables (no defaults)
# - Fail fast if keys are missing
# - Use pytest fixtures for testing instead
#
# RECOMMENDED FIX:
"""
# Remove the setdefault calls entirely
if not os.getenv("OPENAI_API_KEY") or not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY and ANTHROPIC_API_KEY must be set. "
        "For testing, use pytest fixtures or mock these dependencies."
    )
"""

# ═══════════════════════════════════════════════════════════════
# FILE: backend/seed_test_invite.py
# ═══════════════════════════════════════════════════════════════
# ISSUE: Line 14 - Default admin password generated if not in env
#
# CURRENT CODE:
# seed_password = os.getenv("SEED_ADMIN_PASSWORD", _sec.token_urlsafe(24))
#
# RISK: Random password may not be saved, leading to inaccessible admin account
#
# FIX: Require explicit password, fail if not set
"""
seed_password = os.getenv("SEED_ADMIN_PASSWORD")
if not seed_password:
    raise ValueError(
        "SEED_ADMIN_PASSWORD environment variable required for creating admin user. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
"""

# ═══════════════════════════════════════════════════════════════
# FILE: backend/app/config.py
# ═══════════════════════════════════════════════════════════════
# ISSUE: Some environment variables use defaults in development
#
# CURRENT DEFAULTS:
# - REDIS_URL defaults to "redis://localhost:6379/0"
# - FRONTEND_URL defaults to "https://osool-ten.vercel.app"
# - GPT_MODEL defaults to "gpt-4o"
#
# RISK: Defaults may not match actual infrastructure
#
# FIX: Make all critical configs explicit
"""
# For production, fail fast if not set
if ENVIRONMENT == "production":
    if not os.getenv("REDIS_URL"):
        raise ValueError("REDIS_URL required in production")
    if not os.getenv("FRONTEND_URL"):
        raise ValueError("FRONTEND_URL required in production")
"""

# ═══════════════════════════════════════════════════════════════
# GIT HISTORY CLEANUP
# ═══════════════════════════════════════════════════════════════
# Even after removing hardcoded secrets from current code,
# they remain in Git history!
#
# STEPS TO CLEAN GIT HISTORY:
# 1. Use BFG Repo-Cleaner or git-filter-repo
# 2. Scan for secrets with tools like:
#    - truffleHog
#    - gitleaks
#    - git-secrets
# 3. Rotate ALL secrets that were ever committed
# 4. Force push cleaned repository

# Example using gitleaks:
"""
# Install gitleaks
brew install gitleaks

# Scan repository
gitleaks detect --source . --verbose

# Review findings and rotate any exposed secrets
"""

# Example using BFG Repo-Cleaner:
"""
# Install BFG
brew install bfg

# Create a file with secrets to remove
echo "DUMMY" > secrets.txt
echo "secret123" >> secrets.txt

# Run BFG to remove secrets from all history
bfg --replace-text secrets.txt --no-blob-protection .

# Clean up and force push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
"""

# ═══════════════════════════════════════════════════════════════
# SECRET ROTATION CHECKLIST
# ═══════════════════════════════════════════════════════════════
# After cleaning Git history, rotate ALL secrets:
#
# [ ] JWT_SECRET_KEY - Generate new: openssl rand -hex 32
# [ ] ADMIN_API_KEY - Generate new: openssl rand -hex 32
# [ ] WALLET_ENCRYPTION_KEY - Generate new Fernet key
# [ ] OPENAI_API_KEY - Regenerate on OpenAI dashboard
# [ ] ANTHROPIC_API_KEY - Regenerate on Anthropic dashboard
# [ ] SUPABASE_KEY - Regenerate on Supabase dashboard
# [ ] PAYMOB_API_KEY - Regenerate on Paymob dashboard
# [ ] TWILIO_AUTH_TOKEN - Regenerate on Twilio dashboard
# [ ] SENDGRID_API_KEY - Generate on SendGrid dashboard
# [ ] DATABASE_URL password - Change PostgreSQL password
# [ ] Redis password (if using) - Change Redis password
#
# Update all deployment environments:
# [ ] Railway
# [ ] Vercel
# [ ] Docker secrets
# [ ] CI/CD pipelines
# [ ] Developer machines (.env files)

# ═══════════════════════════════════════════════════════════════
# PREVENT FUTURE SECRET LEAKS
# ═══════════════════════════════════════════════════════════════
# 1. Install pre-commit hook to scan for secrets:
"""
# .git/hooks/pre-commit
#!/bin/bash
gitleaks protect --staged --verbose
if [ $? -ne 0 ]; then
    echo "❌ Secret detected in commit! Aborting."
    exit 1
fi
"""

# 2. Add to .gitignore:
"""
.env
.env.*
*.pem
*.key
secrets/
*_secret.*
*_credentials.*
"""

# 3. Use secret management tools:
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
# - Google Secret Manager
# - Doppler
# - 1Password Secrets Automation

# 4. Implement secret scanning in CI/CD:
"""
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
"""

# ═══════════════════════════════════════════════════════════════
# IMMEDIATE Action items (DO NOW):
# ═══════════════════════════════════════════════════════════════
print("""
🚨 IMMEDIATE SECURITY ACTIONS REQUIRED:

1. Remove DUMMY keys from backend/verify_superhuman.py 
2.Fix seed_test_invite.py to require explicit password
3. Scan Git history for exposed secrets: gitleaks detect
4. If secrets found in Git history:
   a. Rotate ALL secrets immediately
   b. Clean Git history with BFG or git-filter-repo
   c. Force push cleaned repository
   d. Update all deployment environments
5. Install gitleaks pre-commit hook
6. Add secret scanning to CI/CD
7. Review and update .gitignore
8. Document secret rotation procedures

DO NOT DEPLOY TO PRODUCTION UNTIL THESE ARE COMPLETE!
""")
