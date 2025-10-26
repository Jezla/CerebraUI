# Cypress Component Tests for Redis Implementation

This directory contains conceptual Cypress component tests for testing Redis functionality at the UI component level.

## Setup Requirements

To run these component tests, you need to configure Cypress for Svelte component testing:

### 1. Install Required Packages

```bash
npm install --save-dev @cypress/svelte cypress-svelte-unit-test
```

### 2. Configure cypress.config.ts

```typescript
import { defineConfig } from 'cypress'
import svelte from 'cypress-svelte-unit-test/preprocessor'

export default defineConfig({
  component: {
    devServer: {
      framework: 'svelte',
      bundler: 'vite'
    },
    specPattern: 'cypress/component/**/*.cy.ts',
    supportFile: 'cypress/support/component.ts',
    setupNodeEvents(on) {
      on('file:preprocessor', svelte())
    }
  }
})
```

### 3. Create Component Support File

Create `cypress/support/component.ts`:

```typescript
import './commands'
import 'cypress-svelte-unit-test/support'
```

### 4. Update Component Imports

Replace the commented imports in `Redis.cy.ts` with actual component imports:

```typescript
import Chat from '../../../src/lib/components/chat/Chat.svelte'
import Messages from '../../../src/lib/components/chat/Messages.svelte'
import Message from '../../../src/lib/components/chat/Messages/Message.svelte'
```

## Test Coverage

### Chat Component Redis Caching
- **Cached Data Display**: Verifies components correctly display Redis-cached chat data
- **Cache Miss Handling**: Tests graceful handling when cache is empty
- **Loading States**: Tests loading indicators during cache retrieval

### Messages Component Cache Display
- **Message Rendering**: Tests display of cached messages with timestamps
- **Empty Cache States**: Tests handling of empty message caches
- **Cache Metadata**: Tests display of cache-related information

### Individual Message Component
- **Cache Indicators**: Tests display of cache status for individual messages
- **Timestamp Display**: Tests cache timestamp formatting
- **Cache State Differentiation**: Tests visual differences between cached/uncached messages

### OTP Verification Components
- **OTP Input Display**: Tests OTP input UI with Redis-backed state
- **Attempt Counters**: Tests display of attempt counts from Redis
- **TTL Display**: Tests remaining time display from Redis TTL

### Cache Performance Indicators
- **Hit/Miss Status**: Tests display of cache performance metrics
- **Redis Connection Status**: Tests connection health indicators

### Error Handling
- **Redis Failure Graceful Handling**: Tests fallback behavior when Redis fails
- **Cache Error Display**: Tests error message display for cache issues

### Cache Invalidation UI
- **Invalidation Controls**: Tests cache invalidation UI elements
- **Freshness Indicators**: Tests display of cache age and staleness

## Running Component Tests

```bash
# Run all component tests
npx cypress run --component

# Run specific Redis component tests
npx cypress run --component --spec "cypress/component/Redis.cy.ts"

# Open component test runner
npx cypress open --component
```

## Mock Data Strategy

The tests use comprehensive mock data that simulates Redis-backed states:

```typescript
const mockChatData = {
  id: 'chat-123',
  title: 'Redis Cached Chat',
  messages: [...],
  meta: { tags: ['cached', 'redis'] },
  cacheStatus: 'hit',
  cacheLatency: 15
}
```

## Integration with Backend Tests

These component tests complement the E2E tests in `cypress/e2e/redis.cy.ts`:

- **Component Tests**: Test individual UI components with mocked Redis data
- **E2E Tests**: Test complete user flows through the API with real Redis backend

## Benefits of Component Testing for Redis

1. **Isolated Testing**: Test Redis functionality without full backend setup
2. **Fast Execution**: Component tests run faster than E2E tests
3. **UI Verification**: Ensure Redis state changes are properly reflected in UI
4. **Error States**: Test how components handle Redis failures
5. **Performance**: Verify cache performance indicators display correctly

## Current Status

The current `Redis.cy.ts` file contains conceptual tests that demonstrate the testing approach. To make them executable:

1. Complete the Cypress Svelte component testing setup
2. Uncomment and fix the component imports
3. Ensure components accept the mock props used in tests
4. Add any missing data-cy attributes for element selection

The tests provide a comprehensive framework for validating Redis functionality at the component level.
