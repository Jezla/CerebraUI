import json
import pytest
from unittest.mock import Mock, patch
import hashlib
import time

# Import the functions to test
from backend.cerebraui.utils.auth import (
    _otp_redis_key,
    _load_otp_from_redis,
    _store_otp_in_redis,
    _update_redis_record,
    generate_otp,
    verify_otp,
    check_email_attempts,
)


class TestOTPRedis:
    def test_otp_redis_key(self):
        email = "test@example.com"
        expected = "cerebraui:otp:test@example.com"
        assert _otp_redis_key(email) == expected

    def test_load_otp_from_redis_with_data(self):
        redis_client = Mock()
        email = "test@example.com"
        payload = {"otp": "hashed_otp", "attempts": 1, "is_used": False}
        redis_client.get.return_value = json.dumps(payload)

        result = _load_otp_from_redis(redis_client, email)
        assert result == payload
        redis_client.get.assert_called_once_with("cerebraui:otp:test@example.com")

    def test_load_otp_from_redis_no_client(self):
        result = _load_otp_from_redis(None, "test@example.com")
        assert result is None

    def test_load_otp_from_redis_no_data(self):
        redis_client = Mock()
        redis_client.get.return_value = None

        result = _load_otp_from_redis(redis_client, "test@example.com")
        assert result is None

    def test_load_otp_from_redis_invalid_json(self):
        redis_client = Mock()
        redis_client.get.return_value = "invalid json"
        redis_client.delete = Mock()

        result = _load_otp_from_redis(redis_client, "test@example.com")
        assert result is None
        redis_client.delete.assert_called_once_with("cerebraui:otp:test@example.com")

    def test_store_otp_in_redis(self):
        redis_client = Mock()
        email = "test@example.com"
        payload = {"otp": "hashed_otp", "attempts": 1, "is_used": False}

        _store_otp_in_redis(redis_client, email, payload)
        redis_client.set.assert_called_once_with(
            "cerebraui:otp:test@example.com",
            json.dumps(payload),
            ex=600
        )

    def test_store_otp_in_redis_no_client(self):
        # Should not raise error
        _store_otp_in_redis(None, "test@example.com", {})

    def test_update_redis_record(self):
        redis_client = Mock()
        email = "test@example.com"
        payload = {"otp": "new_otp", "attempts": 2, "is_used": True}

        _update_redis_record(redis_client, email, payload)
        redis_client.set.assert_called_once_with(
            "cerebraui:otp:test@example.com",
            json.dumps(payload),
            ex=600
        )

    def test_update_redis_record_with_ttl(self):
        redis_client = Mock()
        email = "test@example.com"
        payload = {"otp": "new_otp", "attempts": 2, "is_used": True}

        _update_redis_record(redis_client, email, payload, ttl=300)
        redis_client.set.assert_called_once_with(
            "cerebraui:otp:test@example.com",
            json.dumps(payload),
            ex=300
        )

    def test_update_redis_record_no_client(self):
        # Should not raise error
        _update_redis_record(None, "test@example.com", {})

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    @patch('backend.cerebraui.utils.auth._store_otp_in_redis')
    @patch('backend.cerebraui.utils.auth.Users.get_user_by_email')
    @patch('backend.cerebraui.utils.auth.create_token')
    @patch('backend.cerebraui.utils.auth.pyotp')
    def test_generate_otp_with_redis(self, mock_pyotp, mock_create_token, mock_get_user, mock_store, mock_load):
        # Setup mocks
        mock_get_user.return_value = Mock()  # User exists
        mock_pyotp.random_base32.return_value = "SECRET"
        mock_pyotp.TOTP.return_value.now.return_value = "123456"
        mock_create_token.return_value = "token123"
        mock_load.return_value = None  # No existing record

        redis_client = Mock()
        result = generate_otp("test@example.com", "signup", redis_client)

        assert result.email == "test@example.com"
        assert result.otp == hashlib.sha256("123456".encode()).hexdigest()
        assert result.attempts == 1
        mock_store.assert_called_once()

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    @patch('backend.cerebraui.utils.auth._update_redis_record')
    @patch('backend.cerebraui.utils.auth.Users.get_user_by_email')
    @patch('backend.cerebraui.utils.auth.create_token')
    @patch('backend.cerebraui.utils.auth.pyotp')
    def test_generate_otp_with_existing_attempts(self, mock_pyotp, mock_create_token, mock_get_user, mock_update, mock_load):
        # Setup mocks
        mock_get_user.return_value = Mock()
        mock_pyotp.random_base32.return_value = "SECRET"
        mock_pyotp.TOTP.return_value.now.return_value = "123456"
        mock_create_token.return_value = "token123"
        mock_load.return_value = {"attempts": 1, "is_used": False}

        redis_client = Mock()
        result = generate_otp("test@example.com", "signup", redis_client)

        assert result.attempts == 2  # Existing 1 + 1
        mock_update.assert_called_once()

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    @patch('backend.cerebraui.utils.auth.Users.get_user_by_email')
    @patch('backend.cerebraui.utils.auth.create_token')
    @patch('backend.cerebraui.utils.auth.pyotp')
    def test_generate_otp_max_attempts(self, mock_pyotp, mock_create_token, mock_get_user, mock_load):
        mock_get_user.return_value = Mock()
        mock_load.return_value = {"attempts": 3, "is_used": False}

        redis_client = Mock()
        with pytest.raises(Exception):  # Should raise HTTPException
            generate_otp("test@example.com", "signup", redis_client)

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    @patch('backend.cerebraui.utils.auth._update_redis_record')
    @patch('backend.cerebraui.utils.auth.Users.get_user_by_email')
    @patch('backend.cerebraui.utils.auth.create_token')
    def test_verify_otp_success_with_redis(self, mock_create_token, mock_get_user, mock_update, mock_load):
        email = "test@example.com"
        otp = "123456"
        hashed_otp = hashlib.sha256(otp.encode()).hexdigest()

        mock_load.return_value = {
            "otp": hashed_otp,
            "token": "token123",
            "attempts": 1,
            "is_used": False
        }
        mock_create_token.side_effect = ["auth_token", "verify_token"]
        mock_get_user.return_value = Mock(id=1)

        redis_client = Mock()
        redis_client.ttl.return_value = 500

        result = verify_otp(email, otp, redis_client)

        assert result["result"] is True
        mock_update.assert_called_once()

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    def test_verify_otp_max_attempts(self, mock_load):
        mock_load.return_value = {
            "otp": "hashed",
            "attempts": 3,
            "is_used": False
        }

        result = verify_otp("test@example.com", "123456", Mock())
        assert result is False

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    def test_check_email_attempts_with_redis(self, mock_load):
        mock_load.return_value = {"attempts": 2}

        redis_client = Mock()
        attempts = check_email_attempts("test@example.com", redis_client)
        assert attempts == 2

    @patch('backend.cerebraui.utils.auth._load_otp_from_redis')
    def test_check_email_attempts_no_data(self, mock_load):
        mock_load.return_value = None

        redis_client = Mock()
        attempts = check_email_attempts("test@example.com", redis_client)
        assert attempts == 0
