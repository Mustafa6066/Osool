"""
Osool Backend - Authentication Tests
Phase 4.2: Comprehensive Test Suite
-------------------------------------
Tests for JWT authentication, refresh tokens, and user management.
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from app.auth import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self):
        """Test password is hashed correctly"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self):
        """Test correct password verification"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test incorrect password verification"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)"""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestAccessTokens:
    """Test JWT access token creation and verification"""

    def test_create_access_token(self):
        """Test access token creation"""
        user_id = 42
        token = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verification of valid token"""
        user_id = 42
        token = create_access_token(user_id)
        payload = verify_token(token)

        assert payload is not None
        assert payload["user_id"] == user_id
        assert "exp" in payload

    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.jwt.token"
        payload = verify_token(invalid_token)

        assert payload is None

    def test_token_expiration(self):
        """Test token contains correct expiration"""
        user_id = 42
        token = create_access_token(user_id)
        payload = verify_token(token)

        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Allow 5 second tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 5


class TestRefreshTokens:
    """Test refresh token creation and verification"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock database session"""
        return mocker.Mock()

    def test_create_refresh_token(self, mock_db):
        """Test refresh token creation"""
        user_id = 42
        raw_token = create_refresh_token(mock_db, user_id)

        assert raw_token is not None
        assert isinstance(raw_token, str)
        assert len(raw_token) > 0

        # Verify database add was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_refresh_token_is_hashed_in_db(self, mock_db):
        """Test refresh token is hashed before storing"""
        user_id = 42
        raw_token = create_refresh_token(mock_db, user_id)

        # Get the RefreshToken object that was added
        refresh_token_obj = mock_db.add.call_args[0][0]

        # Raw token should NOT match stored token
        assert refresh_token_obj.token != raw_token

        # Stored token should be SHA-256 hash
        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        assert refresh_token_obj.token == expected_hash

    def test_verify_refresh_token(self, mock_db, mocker):
        """Test refresh token verification"""
        user_id = 42
        raw_token = create_refresh_token(mock_db, user_id)

        # Mock database query
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        mock_token = mocker.Mock()
        mock_token.user_id = user_id
        mock_token.is_revoked = False
        mock_token.expires_at = datetime.utcnow() + timedelta(days=1)

        mock_db.query().filter().first.return_value = mock_token

        # Verify token
        verified_user_id = verify_refresh_token(mock_db, raw_token)

        assert verified_user_id == user_id

    def test_verify_expired_refresh_token(self, mock_db, mocker):
        """Test expired refresh token is rejected"""
        raw_token = "test_token"
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        mock_token = mocker.Mock()
        mock_token.user_id = 42
        mock_token.is_revoked = False
        mock_token.expires_at = datetime.utcnow() - timedelta(days=1)  # Expired

        mock_db.query().filter().first.return_value = mock_token

        verified_user_id = verify_refresh_token(mock_db, raw_token)

        assert verified_user_id is None

    def test_verify_revoked_refresh_token(self, mock_db, mocker):
        """Test revoked refresh token is rejected"""
        raw_token = "test_token"

        mock_token = mocker.Mock()
        mock_token.user_id = 42
        mock_token.is_revoked = True  # Revoked
        mock_token.expires_at = datetime.utcnow() + timedelta(days=1)

        mock_db.query().filter().first.return_value = mock_token

        verified_user_id = verify_refresh_token(mock_db, raw_token)

        assert verified_user_id is None

    def test_revoke_refresh_token(self, mock_db, mocker):
        """Test refresh token revocation"""
        raw_token = "test_token"
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

        mock_token = mocker.Mock()
        mock_token.is_revoked = False

        mock_db.query().filter().first.return_value = mock_token

        revoke_refresh_token(mock_db, raw_token)

        # Verify token was marked as revoked
        assert mock_token.is_revoked is True
        mock_db.commit.assert_called_once()


class TestAuthenticationFlow:
    """Integration tests for authentication flow"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock database session"""
        return mocker.Mock()

    def test_complete_auth_flow(self, mock_db, mocker):
        """Test complete authentication flow: signup → login → refresh → revoke"""
        # 1. User signs up
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # 2. User logs in
        assert verify_password(password, hashed) is True

        # 3. Create access token
        user_id = 42
        access_token = create_access_token(user_id)
        assert access_token is not None

        # 4. Create refresh token
        refresh_token = create_refresh_token(mock_db, user_id)
        assert refresh_token is not None

        # 5. Verify access token
        payload = verify_token(access_token)
        assert payload["user_id"] == user_id

        # 6. Use refresh token (mock)
        hashed_refresh = hashlib.sha256(refresh_token.encode()).hexdigest()
        mock_token = mocker.Mock()
        mock_token.user_id = user_id
        mock_token.is_revoked = False
        mock_token.expires_at = datetime.utcnow() + timedelta(days=1)
        mock_db.query().filter().first.return_value = mock_token

        verified_user_id = verify_refresh_token(mock_db, refresh_token)
        assert verified_user_id == user_id

        # 7. Revoke refresh token
        revoke_refresh_token(mock_db, refresh_token)
        assert mock_token.is_revoked is True

    def test_token_rotation(self, mock_db, mocker):
        """Test refresh token rotation (old token revoked, new token issued)"""
        user_id = 42

        # Create first refresh token
        old_token = create_refresh_token(mock_db, user_id)

        # Simulate token refresh: revoke old, create new
        hashed_old = hashlib.sha256(old_token.encode()).hexdigest()
        mock_old_token = mocker.Mock()
        mock_old_token.is_revoked = False
        mock_db.query().filter().first.return_value = mock_old_token

        revoke_refresh_token(mock_db, old_token)
        assert mock_old_token.is_revoked is True

        # Create new refresh token
        new_token = create_refresh_token(mock_db, user_id)
        assert new_token != old_token


class TestSecurityConstraints:
    """Test security constraints and edge cases"""

    def test_empty_password_hashing(self):
        """Test hashing empty password (should not crash)"""
        hashed = hash_password("")
        assert hashed is not None

    def test_very_long_password(self):
        """Test hashing very long password"""
        long_password = "A" * 1000
        hashed = hash_password(long_password)
        assert verify_password(long_password, hashed)

    def test_special_characters_in_password(self):
        """Test password with special characters"""
        password = "P@ssw0rd!#$%^&*(){}[]|\\<>?/~`"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_unicode_password(self):
        """Test password with unicode characters"""
        password = "Пароль123مرور"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_token_tampering(self):
        """Test that tampered token is rejected"""
        user_id = 42
        token = create_access_token(user_id)

        # Tamper with token (change one character)
        tampered_token = token[:-1] + ("A" if token[-1] != "A" else "B")

        payload = verify_token(tampered_token)
        assert payload is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
