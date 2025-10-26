import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_redis_client():
    """Fixture providing a mock Redis client"""
    return Mock()


@pytest.fixture
def sample_email():
    """Sample email for testing"""
    return "test@example.com"


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "user123"


@pytest.fixture
def sample_chat_id():
    """Sample chat ID for testing"""
    return "chat456"
