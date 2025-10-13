import { FullConfig } from '@playwright/test';

/**
 * Global Teardown - Runs once after all tests
 *
 * Responsibilities:
 * - Clean up test data
 * - Close persistent connections
 * - Generate summary reports
 */
async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 Starting E2E test cleanup...');

  try {
    // Cleanup tasks would go here
    // For example: clearing test database records, closing connections, etc.

    console.log('✅ E2E test cleanup complete');

  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw - allow tests to complete even if cleanup fails
  }
}

export default globalTeardown;
