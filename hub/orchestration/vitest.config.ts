import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/test-setup.ts'],
    // Note: DATABASE_URL must be set in environment before running tests
    // Tests will warn if not set but won't fail immediately
  },
});
