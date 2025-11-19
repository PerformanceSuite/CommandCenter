import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/test-setup.ts'],
    testTimeout: 10000,
    env: {
      DATABASE_URL: 'postgresql://test:test@localhost:5432/test',
      NATS_URL: 'nats://localhost:4222',
    },
  },
});
