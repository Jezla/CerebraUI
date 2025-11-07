# CerebraUI Redis Implementation Unit Tests

This directory contains unit tests for the Redis implementation used in CerebraUI for chat retrieval caching and OTP storage.

## Test Structure

- `unit/test_redis_otp.py` - Tests for OTP-related Redis functions in `backend/cerebraui/utils/auth.py`
- `unit/test_redis_chat_cache.py` - Tests for chat caching Redis functions in `backend/cerebraui/routers/chats.py`
- `conftest.py` - Shared pytest fixtures

## Running the Tests

### Prerequisites

Ensure you have the project dependencies installed:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test/unit/test_redis_otp.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_otp_redis_key"
```

## Test Coverage

The tests cover:

### OTP Redis Functions
- `_otp_redis_key()` - Key generation
- `_load_otp_from_redis()` - Data retrieval with error handling
- `_store_otp_in_redis()` - Data storage with TTL
- `_update_redis_record()` - Record updates with custom TTL
- `generate_otp()` - OTP generation with Redis integration
- `verify_otp()` - OTP verification with Redis
- `check_email_attempts()` - Attempt counting

### Chat Cache Functions
- `_chat_cache_key()` - Cache key generation
- `_set_chat_cache()` - Cache storage with TTL
- `_delete_chat_cache()` - Cache deletion

## Mocking Strategy

Tests use `unittest.mock` to mock Redis client interactions, ensuring:
- No external Redis dependency for testing
- Fast execution
- Isolation of Redis logic
- Verification of correct Redis method calls

## Notes

- Tests assume Redis TTL is 600 seconds for OTP and 300 seconds for chat cache
- All Redis operations are mocked to avoid requiring a running Redis instance
- Tests validate both success and error paths
- Integration with database operations is mocked where necessary
