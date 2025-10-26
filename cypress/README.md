# CerebraUI Cypress Tests for Redis Implementation

This directory contains Cypress end-to-end tests that verify the Redis implementation for chat retrieval caching and OTP storage through API testing.

## Redis Test Coverage

### OTP Redis Storage Tests
- **OTP Generation**: Tests that signup triggers OTP storage in Redis
- **OTP Verification**: Tests OTP verification process (requires OTP retrieval mechanism)
- **Attempt Limits**: Tests that Redis properly enforces maximum OTP attempt limits
- **TTL Handling**: Tests OTP expiration after TTL

### Chat Cache Redis Tests
- **Cache Storage**: Tests that chat data is cached in Redis upon retrieval
- **Cache Retrieval**: Tests that subsequent requests use cached data
- **Cache Invalidation**: Tests that chat updates invalidate cache
- **Cache Miss Handling**: Tests graceful handling of non-existent chats
- **Tag Caching**: Tests separate caching for chat tags with proper invalidation

### Performance and Reliability Tests
- **Redis Failure Graceful Handling**: Tests fallback to database when Redis is unavailable
- **TTL Expiration**: Tests proper expiration of cached data

## Running the Redis Tests

### Prerequisites

1. Ensure the CerebraUI backend is running on `http://localhost:8080`
2. Redis must be available and configured
3. Admin user should exist (`admin@example.com` / `password`)

### Run Tests

```bash
# Run all Cypress tests
npx cypress run

# Run only Redis tests
npx cypress run --spec "cypress/e2e/redis.cy.ts"

# Run in interactive mode
npx cypress open
# Then select "redis.cy.ts" from the test list
```

### Test Configuration

The tests use the following setup:
- Base URL: `http://localhost:8080` (configured in `cypress.config.ts`)
- Admin credentials: `admin@example.com` / `password`
- Automatic admin registration before test suite runs

## Test Architecture

### Custom Commands
- `cy.getAdminToken()`: Retrieves authentication token for admin user
- `cy.getAuthToken(email, password)`: Retrieves token for any user
- `cy.loginAdmin()`: Logs in admin user in browser session

### Test Structure
- **Before Each**: Setup authentication tokens for API calls
- **API-First Approach**: Tests use `cy.request()` for direct API testing
- **State Isolation**: Each test creates its own test data to avoid interference

## Key Testing Strategies

### OTP Testing Challenges
OTP testing requires access to the generated OTP. Current implementation includes:
- Placeholder for OTP retrieval (would need email interception or admin endpoint)
- Attempt limit testing without actual OTP verification
- TTL testing framework (requires timing adjustments for realistic testing)

### Cache Testing Approach
- **Creation**: Create test chats via API
- **Caching**: First retrieval caches data
- **Verification**: Second retrieval should be faster (from cache)
- **Invalidation**: Updates should clear cache
- **Fallback**: Tests verify DB fallback when Redis unavailable

### Performance Metrics
Tests measure response times to verify caching effectiveness:
```typescript
const startTime = Date.now();
// API call
const endTime = Date.now();
const duration = endTime - startTime;
cy.log(`Request took ${duration}ms`);
```

## Environment Setup

### Required Services
- **Backend**: FastAPI application running on port 8080
- **Redis**: Redis server for caching and OTP storage
- **Database**: PostgreSQL/MySQL for persistent storage

### Environment Variables
Ensure these are set in your `.env` file:
```
REDIS_URL=redis://localhost:6379
WEBUI_SECRET_KEY=your-secret-key
# ... other required variables
```

## Test Data Management

Tests create temporary data with unique identifiers:
```typescript
const testEmail = `redis-test-${Date.now()}@example.com`;
```

This ensures test isolation and prevents conflicts between test runs.

## Limitations and Future Improvements

### Current Limitations
1. **OTP Retrieval**: No mechanism to capture generated OTPs for verification tests
2. **Redis Mocking**: No direct Redis mocking - tests rely on live Redis instance
3. **TTL Testing**: Long TTL values make real expiration testing impractical

### Potential Enhancements
1. **Email Interception**: Mock email sending to capture OTPs
2. **Admin Endpoints**: Create test-only endpoints to retrieve OTPs
3. **Redis Mocking**: Use proxy or test Redis instance
4. **Performance Benchmarks**: Establish baseline performance metrics

## Troubleshooting

### Common Issues
- **Authentication Failures**: Ensure admin user exists and credentials are correct
- **Redis Connection**: Verify Redis is running and accessible
- **API Timeouts**: Check backend is responding on localhost:8080
- **Test Flakiness**: Run tests individually to isolate issues

### Debug Tips
- Use `cy.log()` statements to track test execution
- Check browser console for API errors
- Verify Redis contains expected keys during debugging
- Use `cy.debug()` to pause test execution
