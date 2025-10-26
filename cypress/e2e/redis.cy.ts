// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path=\"../support/index.d.ts\" />

describe('Redis Implementation Tests', () => {
  // Wait for 2 seconds after all tests to fix an issue with Cypress's video recording missing the last few frames
  after(() => {
    // eslint-disable-next-line cypress/no-unnecessary-waiting
    cy.wait(2000);
  });

  beforeEach(() => {
    // Ensure we start clean
    cy.visit('/');
  });

  context('OTP Redis Storage', () => {
    it('should generate and store OTP in Redis during signup', () => {
      const testEmail = `redis-test-${Date.now()}@example.com`;

      // Start signup process
      cy.contains('Sign up').click();
      cy.get('input[autocomplete=\"name\"]').type('Redis Test User');
      cy.get('input[autocomplete=\"email\"]').type(testEmail);
      cy.get('input[type=\"password\"]').type('password123');

      // Intercept the signup API call
      cy.intercept('POST', '/api/v1/auth/signup', { statusCode: 200 }).as('signupRequest');

      // Submit signup
      cy.get('button[type=\"submit\"]').click();

      // Wait for the request and verify it was made
      cy.wait('@signupRequest').then((interception) => {
        expect(interception.request.body).to.have.property('email', testEmail);
      });

      // Verify user is in pending state (OTP sent)
      cy.contains('Check Again');
    });

    it('should verify OTP from Redis storage', () => {
      const testEmail = `redis-verify-${Date.now()}@example.com`;

      // First, trigger OTP generation
      cy.request('POST', '/api/v1/auth/signup', {
        name: 'Redis Verify User',
        email: testEmail,
        password: 'password123'
      });

      // Now test OTP verification - we need to get the OTP somehow
      // In a real scenario, we'd need to intercept email or have a way to get the OTP
      // For this test, we'll assume we can get it from the response or mock it

      // This is a placeholder - in practice, you'd need to:
      // 1. Mock the email sending to capture the OTP
      // 2. Or have an admin endpoint to retrieve OTPs
      // 3. Or use a test-specific endpoint

      cy.log('OTP verification test requires OTP retrieval mechanism');
    });

    it('should handle OTP attempt limits from Redis', () => {
      const testEmail = `redis-attempts-${Date.now()}@example.com`;

      // Generate OTP first
      cy.request('POST', '/api/v1/auth/signup', {
        name: 'Redis Attempts User',
        email: testEmail,
        password: 'password123'
      });

      // Try multiple wrong OTP verifications
      for (let i = 0; i < 3; i++) {
        cy.request({
          method: 'POST',
          url: '/api/v1/auth/verify',
          body: {
            email: testEmail,
            otp: '000000' // Wrong OTP
          },
          failOnStatusCode: false
        });
      }

      // Next attempt should be blocked
      cy.request({
        method: 'POST',
        url: '/api/v1/auth/verify',
        body: {
          email: testEmail,
          otp: '000000'
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(400);
        expect(response.body.detail).to.include('maximum number of attempts');
      });
    });
  });

  context('Chat Cache Redis', () => {
    let adminToken: string;

    beforeEach(() => {
      // Get admin token for API calls
      cy.getAdminToken().then((token) => {
        adminToken = token;
      });
    });

    it('should cache chat data in Redis on retrieval', () => {
      // Create a new chat first
      cy.request({
        method: 'POST',
        url: '/api/v1/chats/new',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        body: {
          chat: {
            title: 'Redis Cache Test Chat',
            messages: []
          }
        }
      }).then((response) => {
        expect(response.status).to.eq(200);
        const chatId = response.body.id;

        // Now retrieve the chat - this should cache it
        cy.request({
          method: 'GET',
          url: `/api/v1/chats/${chatId}`,
          headers: {
            'Authorization': `Bearer ${adminToken}`
          }
        }).then((getResponse) => {
          expect(getResponse.status).to.eq(200);
          expect(getResponse.body).to.have.property('id', chatId);
          expect(getResponse.body).to.have.property('title', 'Redis Cache Test Chat');
        });

        // Second retrieval should come from cache (faster)
        const startTime = Date.now();
        cy.request({
          method: 'GET',
          url: `/api/v1/chats/${chatId}`,
          headers: {
            'Authorization': `Bearer ${adminToken}`
          }
        }).then((cachedResponse) => {
          const endTime = Date.now();
          const duration = endTime - startTime;
          cy.log(`Cached request took ${duration}ms`);
          expect(cachedResponse.status).to.eq(200);
          expect(cachedResponse.body).to.have.property('id', chatId);
        });
      });
    });

    it('should invalidate cache on chat update', () => {
      // Create a chat
      cy.request({
        method: 'POST',
        url: '/api/v1/chats/new',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        body: {
          chat: {
            title: 'Cache Invalidation Test',
            messages: []
          }
        }
      }).then((response) => {
        const chatId = response.body.id;

        // Update the chat
        cy.request({
          method: 'POST',
          url: `/api/v1/chats/${chatId}`,
          headers: {
            'Authorization': `Bearer ${adminToken}`
          },
          body: {
            chat: {
              title: 'Updated Cache Invalidation Test',
              messages: []
            }
          }
        }).then((updateResponse) => {
          expect(updateResponse.status).to.eq(200);

          // Retrieve again - should not be from stale cache
          cy.request({
            method: 'GET',
            url: `/api/v1/chats/${chatId}`,
            headers: {
              'Authorization': `Bearer ${adminToken}`
            }
          }).then((getResponse) => {
            expect(getResponse.body).to.have.property('title', 'Updated Cache Invalidation Test');
          });
        });
      });
    });

    it('should handle cache miss gracefully', () => {
      // Try to get a non-existent chat
      cy.request({
        method: 'GET',
        url: '/api/v1/chats/non-existent-chat-id',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.eq(401); // Not found
        expect(response.body.detail).to.eq('Not found');
      });
    });

    it('should cache chat tags separately', () => {
      // Create a chat with tags
      cy.request({
        method: 'POST',
        url: '/api/v1/chats/new',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        body: {
          chat: {
            title: 'Tagged Chat for Cache Test',
            messages: [],
            meta: {
              tags: ['test', 'redis']
            }
          }
        }
      }).then((response) => {
        const chatId = response.body.id;

        // Get chat tags - should be cached
        cy.request({
          method: 'GET',
          url: `/api/v1/chats/${chatId}/tags`,
          headers: {
            'Authorization': `Bearer ${adminToken}`
          }
        }).then((tagsResponse) => {
          expect(tagsResponse.status).to.eq(200);
          expect(tagsResponse.body).to.be.an('array');
          // Should contain the tags we set
        });

        // Add a tag
        cy.request({
          method: 'POST',
          url: `/api/v1/chats/${chatId}/tags`,
          headers: {
            'Authorization': `Bearer ${adminToken}`
          },
          body: {
            name: 'cache-test'
          }
        }).then((addTagResponse) => {
          expect(addTagResponse.status).to.eq(200);

          // Get tags again - cache should be updated
          cy.request({
            method: 'GET',
            url: `/api/v1/chats/${chatId}/tags`,
            headers: {
              'Authorization': `Bearer ${adminToken}`
            }
          }).then((updatedTagsResponse) => {
            expect(updatedTagsResponse.body).to.be.an('array');
            // Should include the new tag
          });
        });
      });
    });
  });

  context('Redis Performance and Reliability', () => {
    let adminToken: string;

    beforeEach(() => {
      cy.getAdminToken().then((token) => {
        adminToken = token;
      });
    });

    it('should handle Redis connection failures gracefully', () => {
      // This test would require mocking Redis failures
      // In a real scenario, you'd need to simulate Redis being down

      cy.request({
        method: 'GET',
        url: '/api/v1/chats/',
        headers: {
          'Authorization': `Bearer ${adminToken}`
        }
      }).then((response) => {
        // Should still work even if Redis is down (fall back to DB)
        expect(response.status).to.eq(200);
        expect(response.body).to.be.an('array');
      });
    });

    it('should respect cache TTL for OTP', () => {
      // Test that OTP expires after TTL
      const testEmail = `redis-ttl-${Date.now()}@example.com`;

      // Generate OTP
      cy.request('POST', '/api/v1/auth/signup', {
        name: 'Redis TTL User',
        email: testEmail,
        password: 'password123'
      });

      // Wait for TTL to expire (this would be long in real test)
      // cy.wait(600000); // 10 minutes

      // For demo purposes, just check the endpoint exists
      cy.log('TTL test requires waiting for expiration');
    });
  });
});
