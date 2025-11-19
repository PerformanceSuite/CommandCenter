/**
 * Test setup for orchestration service
 *
 * Note: Integration tests require a running PostgreSQL database.
 * Set DATABASE_URL environment variable before running tests.
 *
 * For CI/CD: Use a test database or docker-compose test setup
 * For local: Can use existing CommandCenter database or separate test database
 */

import { beforeAll } from 'vitest';

beforeAll(async () => {
  // Ensure required environment variables are set
  if (!process.env.DATABASE_URL) {
    console.warn(
      'WARNING: DATABASE_URL not set. Integration tests may fail.\n' +
      'Set DATABASE_URL to a test PostgreSQL database to run tests.\n' +
      'Example: DATABASE_URL=postgresql://user:pass@localhost:5432/testdb'
    );
  }
});
