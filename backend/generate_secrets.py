#!/usr/bin/env python3
"""
Secure Secret Generator for Osool Backend
==========================================
Run this script to generate secure random secrets for your .env file.

Usage:
    python generate_secrets.py
"""

import secrets
import string
from cryptography.fernet import Fernet


def generate_jwt_secret(length: int = 64) -> str:
    """Generate a secure JWT secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_admin_api_key(length: int = 32) -> str:
    """Generate a secure admin API key (hex)."""
    return secrets.token_hex(length)


def generate_wallet_encryption_key() -> str:
    """Generate a Fernet encryption key for wallet encryption."""
    return Fernet.generate_key().decode()


def generate_database_url(db_name: str = "osool_dev") -> str:
    """Generate a template DATABASE_URL with a secure password."""
    # Generate a secure database password
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
    return f"postgresql://osool_user:{password}@localhost:5432/{db_name}"


def main():
    print("\n" + "=" * 70)
    print("OSOOL SECURE SECRET GENERATOR")
    print("=" * 70)
    print("\nGenerating secure secrets for your .env file...\n")

    # Generate all secrets
    jwt_secret = generate_jwt_secret()
    admin_api_key = generate_admin_api_key()
    wallet_key = generate_wallet_encryption_key()
    db_url = generate_database_url()

    # Display results
    print("Copy these values to your backend/.env file:\n")
    print("-" * 70)
    print(f"\n# JWT Secret (for access tokens)")
    print(f"JWT_SECRET_KEY={jwt_secret}\n")

    print(f"# Admin API Key (for protected admin endpoints)")
    print(f"ADMIN_API_KEY={admin_api_key}\n")

    print(f"# Wallet Encryption Key (CRITICAL - for encrypting user wallets)")
    print(f"WALLET_ENCRYPTION_KEY={wallet_key}\n")

    print(f"# Database URL (PostgreSQL)")
    print(f"# NOTE: Update username, password, host, port, and db_name as needed")
    print(f"DATABASE_URL={db_url}\n")

    print("-" * 70)

    print("\nSECURITY REMINDERS:")
    print("   1. These secrets are shown ONLY ONCE - copy them now!")
    print("   2. NEVER commit these to git")
    print("   3. Store backups in a password manager (1Password, Bitwarden, etc.)")
    print("   4. For production, use a secret manager (AWS Secrets, Azure Key Vault)")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
