import json
import pytest
from unittest.mock import Mock

# Import the functions to test
from backend.cerebraui.routers.chats import (
    _chat_cache_key,
    _set_chat_cache,
    _delete_chat_cache,
)


class TestChatCacheRedis:
    def test_chat_cache_key(self):
        user_id = "user123"
        chat_id = "chat456"
        expected = "cerebraui:chat:user123:chat456"
        assert _chat_cache_key(user_id, chat_id) == expected

    def test_set_chat_cache(self):
        redis_client = Mock()
        user_id = "user123"
        chat_id = "chat456"
        chat_mock = Mock()
        chat_mock.model_dump.return_value = {"id": chat_id, "title": "Test Chat"}

        _set_chat_cache(redis_client, user_id, chat_id, chat_mock)

        expected_key = "cerebraui:chat:user123:chat456"
        expected_value = json.dumps({"id": chat_id, "title": "Test Chat"})
        redis_client.set.assert_called_once_with(expected_key, expected_value, ex=300)

    def test_set_chat_cache_no_redis(self):
        # Should not raise error when redis is None
        chat_mock = Mock()
        _set_chat_cache(None, "user123", "chat456", chat_mock)

    def test_delete_chat_cache(self):
        redis_client = Mock()
        user_id = "user123"
        chat_id = "chat456"

        _delete_chat_cache(redis_client, user_id, chat_id)

        expected_key = "cerebraui:chat:user123:chat456"
        redis_client.delete.assert_called_once_with(expected_key)

    def test_delete_chat_cache_no_redis(self):
        # Should not raise error when redis is None
        _delete_chat_cache(None, "user123", "chat456")


# Additional integration-style tests for chat caching behavior
class TestChatCacheIntegration:
    def test_cache_set_and_get_workflow(self):
        """Test the typical workflow of setting and getting cache"""
        redis_client = Mock()
        user_id = "user123"
        chat_id = "chat456"
        chat_data = {"id": chat_id, "title": "Test Chat", "messages": []}

        # Mock chat object
        chat_mock = Mock()
        chat_mock.model_dump.return_value = chat_data

        # Set cache
        _set_chat_cache(redis_client, user_id, chat_id, chat_mock)

        # Verify set was called
        expected_key = "cerebraui:chat:user123:chat456"
        expected_value = json.dumps(chat_data)
        redis_client.set.assert_called_once_with(expected_key, expected_value, ex=300)

    def test_cache_delete_workflow(self):
        """Test cache deletion workflow"""
        redis_client = Mock()
        user_id = "user123"
        chat_id = "chat456"

        # Delete cache
        _delete_chat_cache(redis_client, user_id, chat_id)

        # Verify delete was called
        expected_key = "cerebraui:chat:user123:chat456"
        redis_client.delete.assert_called_once_with(expected_key)

    def test_cache_key_uniqueness(self):
        """Test that cache keys are unique per user and chat"""
        user1 = "user1"
        user2 = "user2"
        chat1 = "chat1"
        chat2 = "chat2"

        key1 = _chat_cache_key(user1, chat1)
        key2 = _chat_cache_key(user1, chat2)
        key3 = _chat_cache_key(user2, chat1)

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

        assert "user1" in key1
        assert "chat1" in key1
        assert "user1" in key2
        assert "chat2" in key2
        assert "user2" in key3
        assert "chat1" in key3

    def test_cache_ttl_configuration(self):
        """Test that cache TTL is set correctly"""
        redis_client = Mock()
        user_id = "user123"
        chat_id = "chat456"
        chat_mock = Mock()
        chat_mock.model_dump.return_value = {"id": chat_id}

        _set_chat_cache(redis_client, user_id, chat_id, chat_mock)

        # Verify TTL is 300 seconds (5 minutes)
        call_args = redis_client.set.call_args
        assert call_args[1]['ex'] == 300
