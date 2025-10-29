// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="../support/index.d.ts" />

describe('Redis chat caching', () => {
        const getAuthHeaders = () =>
                cy.window().then((win) => {
                        const token = win.localStorage.getItem('token');
                        expect(token, 'auth token in localStorage').to.be.a('string').and.not.be.empty;
                        return { Authorization: `Bearer ${token as string}` };
                });

        before(() => {
                cy.loginAdmin();
        });

        beforeEach(() => {
                cy.loginAdmin();
                cy.visit('/');
        });

        it('stores chats in redis and reduces subsequent fetch time', () => {
                let headers: Record<string, string>;
                let chatId: string;
                let userId: string;
                let cacheKey: string;
                const durations = { miss: 0, hit: 0 };

                getAuthHeaders().then((resolvedHeaders) => {
                        headers = resolvedHeaders;
                });

                cy.then(() => {
                        expect(headers, 'auth headers ready').to.exist;
                        const body = {
                                chat: {
                                        title: `Redis Cache Test ${Date.now()}`,
                                        messages: []
                                }
                        };

                        return cy
                                .request({
                                        method: 'POST',
                                        url: '/api/v1/chats/new',
                                        headers,
                                        body
                                })
                                .then((response) => {
                                        expect(response.status).to.eq(200);
                                        expect(response.body).to.have.property('id');
                                        expect(response.body).to.have.property('user_id');
                                        chatId = response.body.id as string;
                                        userId = response.body.user_id as string;
                                        cacheKey = `cerebraui:chat:${userId}:${chatId}`;
                                });
                });

                cy.then(() => {
                        expect(cacheKey, 'cache key defined').to.be.a('string');
                });

                cy.task('redis:del', cacheKey);

                cy.task<string | null>('redis:get', cacheKey).should('be.null');

                cy.then(() =>
                        cy
                                .request({
                                        method: 'GET',
                                        url: `/api/v1/chats/${chatId}`,
                                        headers
                                })
                                .then((response) => {
                                        expect(response.status).to.eq(200);
                                        expect(response.body.id).to.eq(chatId);
                                        const missDuration = response.duration ?? 0;
                                        expect(missDuration, 'cache miss duration').to.be.greaterThan(0);
                                        durations.miss = missDuration;
                                })
                );

                cy.task<string | null>('redis:get', cacheKey).then((cached) => {
                        expect(cached, 'cached chat payload').to.be.a('string');
                        const parsed = JSON.parse(cached as string) as { id: string };
                        expect(parsed.id).to.eq(chatId);
                });

                cy.then(() =>
                        cy
                                .request({
                                        method: 'GET',
                                        url: `/api/v1/chats/${chatId}`,
                                        headers
                                })
                                .then((response) => {
                                        expect(response.status).to.eq(200);
                                        expect(response.body.id).to.eq(chatId);
                                        const hitDuration = response.duration ?? 0;
                                        expect(hitDuration, 'cache hit duration').to.be.greaterThan(0);
                                        durations.hit = hitDuration;
                                })
                );

                cy.then(() => {
                        expect(durations.hit, 'cache hit duration').to.be.lessThan(durations.miss);
                        expect(durations.miss - durations.hit, 'cache speed improvement').to.be.greaterThan(0);
                        const logMessage = `Cache miss duration: ${durations.miss.toFixed(2)}ms, cache hit duration: ${durations.hit.toFixed(2)}ms`;
                        cy.log(logMessage);
                });

                cy.request({
                        method: 'DELETE',
                        url: `/api/v1/chats/${chatId}`,
                        headers
                })
                        .its('status')
                        .should('eq', 200);

                cy.task('redis:del', cacheKey);
        });
});
