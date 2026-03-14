"""
Osool Backend - Shared Test Fixtures
-------------------------------------
Provides common fixtures used across all test files.
"""

import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure we're in dev/test mode
os.environ["ENVIRONMENT"] = "development"
os.environ["BLOCKCHAIN_SIMULATION_MODE"] = "true"
# JWT secret must be set before auth module is imported (it validates at import time)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-minimum-32-chars-long")


@pytest.fixture
def mock_db():
    """Mock synchronous database session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.add = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def mock_async_db():
    """Mock async database session for endpoints using AsyncSession."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()  # add is sync
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.id = 42
    user.email = "test@osool.com"
    user.full_name = "Test User"
    user.phone_number = "+201234567890"
    user.phone_verified = True
    user.wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    user.role = "investor"
    user.is_verified = True
    return user


@pytest.fixture
def mock_property():
    """Mock property model instance."""
    prop = MagicMock()
    prop.id = 1
    prop.title = "Test Villa"
    prop.description = "A test property"
    prop.price = 1_000_000.0
    prop.location = "New Cairo"
    prop.is_available = True
    prop.blockchain_id = 101
    return prop


@pytest.fixture
def mock_transaction():
    """Mock transaction model instance."""
    tx = MagicMock()
    tx.id = 1
    tx.user_id = 42
    tx.property_id = 1
    tx.amount = 100_000.0
    tx.paymob_order_id = "ORD-12345"
    tx.status = "pending"
    tx.blockchain_tx_hash = None
    return tx
