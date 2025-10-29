import { defineConfig } from 'cypress';
import { createClient } from 'redis';

export default defineConfig({
        e2e: {
                baseUrl: 'http://localhost:3000',
                setupNodeEvents(on, config) {
                        const redisUrl = process.env.REDIS_URL ?? 'redis://localhost:6379/0';

                        const runWithClient = async <T>(handler: (client: ReturnType<typeof createClient>) => Promise<T>) => {
                                const client = createClient({ url: redisUrl });
                                try {
                                        await client.connect();
                                        return await handler(client);
                                } finally {
                                        await client.disconnect();
                                }
                        };

                        on('task', {
                                async 'redis:get'(key: string) {
                                        return runWithClient(async (client) => client.get(key));
                                },
                                async 'redis:del'(key: string) {
                                        return runWithClient(async (client) => client.del(key));
                                }
                        });

                        return config;
                }
        },
        video: true
});
