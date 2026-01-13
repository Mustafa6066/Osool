#!/usr/bin/env python3
"""
Configuration Validator for Osool Backend
==========================================
Run this script to validate your .env configuration.

Usage:
    python validate_config.py
"""

import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("ERROR: .env file not found!")
        print(f"Expected location: {env_path}")
        print("\nCreate one by:")
        print("  1. Copy .env.example to .env")
        print("  2. Run: python generate_secrets.py")
        print("  3. Fill in your API keys")
        return False
    return True


def validate_required_vars():
    """Validate required environment variables."""
    required_vars = {
        "DATABASE_URL": "Database connection string",
        "JWT_SECRET_KEY": "JWT secret for authentication",
        "OPENAI_API_KEY": "OpenAI API key for AI features",
        "ANTHROPIC_API_KEY": "Claude API key for AMR",
    }

    missing = []
    placeholder = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  - {var}: {description}")
        elif "your_" in value.lower() or "here" in value.lower() or "run_generate" in value:
            placeholder.append(f"  - {var}: Still has placeholder value")

    return missing, placeholder


def validate_api_keys():
    """Validate API key formats."""
    issues = []

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and not openai_key.startswith("sk-proj-"):
        issues.append("  - OPENAI_API_KEY: Should start with 'sk-proj-'")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and not anthropic_key.startswith("sk-ant-"):
        issues.append("  - ANTHROPIC_API_KEY: Should start with 'sk-ant-'")

    return issues


def validate_database():
    """Validate database configuration."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return ["  - DATABASE_URL is not set"]

    issues = []
    if not (db_url.startswith("postgresql://") or db_url.startswith("sqlite://")):
        issues.append("  - DATABASE_URL: Should start with 'postgresql://' or 'sqlite://'")

    return issues


def check_optional_features():
    """Check optional features and their requirements."""
    features = {
        "ENABLE_BLOCKCHAIN": ["PRIVATE_KEY", "ALCHEMY_RPC_URL"],
        "ENABLE_PAYMENTS": ["PAYMOB_API_KEY"],
        "ENABLE_SMS": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
        "ENABLE_EMAIL": ["SENDGRID_API_KEY"],
    }

    warnings = []
    for feature, required_vars in features.items():
        if os.getenv(feature, "").lower() == "true":
            missing = [var for var in required_vars if not os.getenv(var)]
            if missing:
                warnings.append(f"  - {feature} is enabled but missing: {', '.join(missing)}")

    return warnings


def main():
    print("\n" + "=" * 70)
    print("OSOOL CONFIGURATION VALIDATOR")
    print("=" * 70 + "\n")

    # Load .env file if it exists
    if check_env_file():
        from dotenv import load_dotenv
        load_dotenv()
        print("[OK] .env file found\n")
    else:
        sys.exit(1)

    all_good = True

    # Check required variables
    missing, placeholder = validate_required_vars()
    if missing:
        print("ERROR - Missing required variables:")
        for item in missing:
            print(item)
        print()
        all_good = False
    else:
        print("[OK] All required variables are set\n")

    if placeholder:
        print("WARNING - Variables with placeholder values:")
        for item in placeholder:
            print(item)
        print("\nRun: python generate_secrets.py")
        print()
        all_good = False

    # Validate API keys
    api_issues = validate_api_keys()
    if api_issues:
        print("ERROR - API key format issues:")
        for issue in api_issues:
            print(issue)
        print()
        all_good = False
    else:
        print("[OK] API keys have correct format\n")

    # Validate database
    db_issues = validate_database()
    if db_issues:
        print("ERROR - Database configuration issues:")
        for issue in db_issues:
            print(issue)
        print()
        all_good = False
    else:
        print("[OK] Database configuration looks good\n")

    # Check optional features
    feature_warnings = check_optional_features()
    if feature_warnings:
        print("WARNING - Optional feature configuration:")
        for warning in feature_warnings:
            print(warning)
        print()

    # Final summary
    print("=" * 70)
    if all_good:
        print("SUCCESS - Configuration is valid!")
        print("\nYou can now start the backend server:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
    else:
        print("FAILED - Please fix the errors above")
        print("\nQuick fix guide:")
        print("  1. Run: python generate_secrets.py")
        print("  2. Copy the generated values to your .env file")
        print("  3. Add your API keys (OpenAI, Claude)")
        print("  4. Run this validator again")
    print("=" * 70 + "\n")

    sys.exit(0 if all_good else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)
