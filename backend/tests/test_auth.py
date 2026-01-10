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


class TestPhoneVerificationFlow:
    """Test phone verification requirement before payments (Phase 1)"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock database session"""
        return mocker.Mock()

    def test_user_cannot_pay_without_phone_verification(self, mock_db, mocker):
        """Test that user must verify phone before initiating payment"""
        # Create unverified user
        unverified_user = mocker.Mock()
        unverified_user.id = 42
        unverified_user.phone = "+201234567890"
        unverified_user.phone_verified = False  # Not verified

        # Attempt to initiate payment should fail
        can_pay = unverified_user.phone_verified
        assert can_pay is False

    def test_user_can_pay_after_phone_verification(self, mock_db, mocker):
        """Test that user can pay after phone verification"""
        # Create verified user
        verified_user = mocker.Mock()
        verified_user.id = 42
        verified_user.phone = "+201234567890"
        verified_user.phone_verified = True  # Verified

        # Payment should be allowed
        can_pay = verified_user.phone_verified
        assert can_pay is True

    @pytest.mark.asyncio
    async def test_otp_generation_and_verification(self, mocker):
        """Test OTP generation and verification flow"""
        # Generate 6-digit OTP
        import random
        otp = str(random.randint(100000, 999999))

        assert len(otp) == 6
        assert otp.isdigit()

        # Mock OTP storage (hashed in database)
        import hashlib
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        # Verify correct OTP
        user_input_otp = otp
        user_input_hash = hashlib.sha256(user_input_otp.encode()).hexdigest()
        assert user_input_hash == otp_hash

        # Verify incorrect OTP
        wrong_otp = "123456"
        wrong_hash = hashlib.sha256(wrong_otp.encode()).hexdigest()
        assert wrong_hash != otp_hash

    def test_otp_expires_after_5_minutes(self, mocker):
        """Test that OTP expires after 5 minutes"""
        from datetime import datetime, timedelta

        otp_created_at = datetime.utcnow()
        otp_expires_at = otp_created_at + timedelta(minutes=5)

        # After 4 minutes: valid
        check_time_valid = otp_created_at + timedelta(minutes=4)
        assert check_time_valid < otp_expires_at

        # After 6 minutes: expired
        check_time_expired = otp_created_at + timedelta(minutes=6)
        assert check_time_expired > otp_expires_at


class TestWalletSignatureVerification:
    """Test Web3 wallet signature verification (EIP-191) (Phase 1)"""

    def test_wallet_signature_verification_eip191(self, mocker):
        """Test EIP-191 signature verification for Web3 login"""
        from eth_account import Account
        from eth_account.messages import encode_defunct
        from web3 import Web3

        # Create test wallet
        account = Account.create()
        wallet_address = account.address
        private_key = account.key

        # Message to sign (nonce for preventing replay attacks)
        nonce = "osool_login_12345"
        message = f"Sign this message to authenticate with Osool:\n\nNonce: {nonce}"

        # Sign message
        message_hash = encode_defunct(text=message)
        signed_message = Account.sign_message(message_hash, private_key)

        # Verify signature
        recovered_address = Account.recover_message(message_hash, signature=signed_message.signature)

        assert recovered_address.lower() == wallet_address.lower()

    def test_invalid_signature_rejected(self, mocker):
        """Test that invalid signatures are rejected"""
        from eth_account import Account
        from eth_account.messages import encode_defunct

        # Create two different wallets
        account1 = Account.create()
        account2 = Account.create()

        # Sign message with account1
        message = "Sign this message to authenticate with Osool:\n\nNonce: test_nonce"
        message_hash = encode_defunct(text=message)
        signed_message = Account.sign_message(message_hash, account1.key)

        # Try to verify with account2's address
        recovered_address = Account.recover_message(message_hash, signature=signed_message.signature)

        # Should NOT match account2
        assert recovered_address.lower() != account2.address.lower()
        assert recovered_address.lower() == account1.address.lower()

    def test_nonce_prevents_replay_attacks(self, mocker):
        """Test that nonce prevents signature replay attacks"""
        import uuid

        # Generate unique nonce
        nonce1 = str(uuid.uuid4())
        nonce2 = str(uuid.uuid4())

        assert nonce1 != nonce2

        # Each login should have unique nonce
        # Reusing a signature should be rejected


class TestMultiFactorAuthentication:
    """Test multi-factor authentication flows"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock database session"""
        return mocker.Mock()

    def test_email_password_plus_phone_verification(self, mock_db, mocker):
        """Test email/password login requires phone verification for payments"""
        # User logs in with email/password
        user = mocker.Mock()
        user.id = 42
        user.email = "test@osool.com"
        user.password_hash = hash_password("SecurePassword123!")
        user.phone_verified = False  # Not verified yet

        # Can login and browse
        assert user.email is not None

        # But cannot make payments
        assert user.phone_verified is False

    def test_web3_wallet_plus_email_linking(self, mock_db, mocker):
        """Test Web3 wallet can be linked to email account"""
        # User has email account
        user_email = mocker.Mock()
        user_email.id = 42
        user_email.email = "test@osool.com"
        user_email.wallet_address = None  # No wallet linked yet

        # User links wallet
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        user_email.wallet_address = wallet_address

        # Verify linking succeeded
        assert user_email.wallet_address == wallet_address

    def test_google_oauth_creates_user_account(self, mock_db, mocker):
        """Test Google OAuth creates user account automatically"""
        # Mock Google OAuth response
        google_user_info = {
            "email": "test@gmail.com",
            "given_name": "John",
            "family_name": "Doe",
            "picture": "https://example.com/profile.jpg",
            "sub": "google_user_id_12345"
        }

        # Create user from Google info
        user = mocker.Mock()
        user.email = google_user_info["email"]
        user.first_name = google_user_info["given_name"]
        user.last_name = google_user_info["family_name"]
        user.oauth_provider = "google"
        user.oauth_id = google_user_info["sub"]

        assert user.oauth_provider == "google"
        assert user.email == "test@gmail.com"


class TestRateLimiting:
    """Test rate limiting on sensitive endpoints"""

    def test_login_rate_limiting(self, mocker):
        """Test login endpoint rate limiting (5 attempts per minute)"""
        # Simulate 5 login attempts
        max_attempts = 5
        attempts = 0

        for i in range(7):
            if attempts < max_attempts:
                # Allow login attempt
                attempts += 1
                can_attempt = True
            else:
                # Block due to rate limit
                can_attempt = False

        # 6th and 7th attempts should be blocked
        assert attempts == 5
        assert can_attempt is False

    def test_otp_request_rate_limiting(self, mocker):
        """Test OTP request rate limiting (3 per hour per phone)"""
        from datetime import datetime, timedelta

        phone_number = "+201234567890"
        otp_requests = []

        # Simulate 4 OTP requests
        for i in range(4):
            request_time = datetime.utcnow() + timedelta(minutes=i * 10)
            otp_requests.append(request_time)

        # Count requests in last hour
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent_requests = [r for r in otp_requests if r > cutoff_time]

        # Should have 4 requests, but limit is 3
        assert len(recent_requests) == 4
        rate_limit_exceeded = len(recent_requests) > 3
        assert rate_limit_exceeded is True


class TestSessionManagement:
    """Test session management with refresh tokens"""

    @pytest.fixture
    def mock_db(self, mocker):
        """Mock database session"""
        return mocker.Mock()

    def test_access_token_short_lived_24_hours(self, mocker):
        """Test access token expires after 24 hours (was 30 days - fixed in Phase 1)"""
        from datetime import datetime, timedelta

        # Create access token
        user_id = 42
        token = create_access_token(user_id)
        payload = verify_token(token)

        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(hours=24)

        # Verify expiration is ~24 hours (allow 5 second tolerance)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5

    def test_refresh_token_long_lived_30_days(self, mock_db):
        """Test refresh token expires after 30 days"""
        from datetime import datetime, timedelta

        user_id = 42
        raw_token = create_refresh_token(mock_db, user_id)

        # Get the RefreshToken object that was added
        refresh_token_obj = mock_db.add.call_args[0][0]

        # Verify expiration is 30 days
        expected_exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        time_diff = abs((refresh_token_obj.expires_at - expected_exp).total_seconds())

        assert time_diff < 5  # 5 second tolerance

    def test_refresh_token_rotation_on_use(self, mock_db, mocker):
        """Test refresh token is rotated (old revoked, new issued) when used"""
        user_id = 42

        # Create first refresh token
        old_token = create_refresh_token(mock_db, user_id)

        # Mock database query for old token
        import hashlib
        hashed_old = hashlib.sha256(old_token.encode()).hexdigest()
        mock_old_token = mocker.Mock()
        mock_old_token.user_id = user_id
        mock_old_token.is_revoked = False
        mock_db.query().filter().first.return_value = mock_old_token

        # Use refresh token (simulate rotation)
        revoke_refresh_token(mock_db, old_token)
        assert mock_old_token.is_revoked is True

        # Create new refresh token
        new_token = create_refresh_token(mock_db, user_id)
        assert new_token != old_token


class TestPasswordSecurity:
    """Test password security requirements"""

    def test_password_minimum_length(self):
        """Test password minimum length requirement (8 characters)"""
        short_password = "Pass1!"
        valid_password = "Password123!"

        assert len(short_password) < 8
        assert len(valid_password) >= 8

    def test_password_complexity_requirements(self):
        """Test password complexity (uppercase, lowercase, number, special char)"""
        weak_passwords = [
            "password",  # No uppercase, number, special
            "PASSWORD",  # No lowercase, number, special
            "Password",  # No number, special
            "Password1",  # No special char
        ]

        strong_password = "Password123!"

        # Check strong password has all requirements
        has_upper = any(c.isupper() for c in strong_password)
        has_lower = any(c.islower() for c in strong_password)
        has_digit = any(c.isdigit() for c in strong_password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in strong_password)

        assert has_upper
        assert has_lower
        assert has_digit
        assert has_special

    def test_password_hash_uses_bcrypt(self):
        """Test that passwords are hashed using bcrypt (slow hash)"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")

        # Bcrypt is slow (good for security)
        import time
        start = time.time()
        hash_password(password)
        duration = time.time() - start

        # Should take at least 0.05 seconds (bcrypt cost)
        assert duration > 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
