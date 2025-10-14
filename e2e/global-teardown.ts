import { FullConfig, chromium } from '@playwright/test';
import { cleanDatabase } from './utils/seed-data';

/**
 * Global Teardown - Runs once after all tests
 *
 * Responsibilities:
 * - Clean up test data (optional)
 * - Close persistent connections
 * - Generate summary reports
 */
async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 Starting E2E test cleanup...');

  try {
    // Optionally clean up test data
    // Set CLEANUP_TEST_DATA=true to enable
    const shouldCleanup = process.env.CLEANUP_TEST_DATA === 'true';

    if (shouldCleanup) {
      console.log('  Cleaning up test database...');
      const browser = await chromium.launch();
      const context = await browser.newContext();

      try {
        await cleanDatabase(context.request);
        console.log('  ✓ Test data cleaned');
      } catch (error) {
        console.error('  ⚠️  Cleanup failed (non-critical):', error);
      } finally {
        await context.close();
        await browser.close();
      }
    } else {
      console.log('  Keeping test data for inspection (set CLEANUP_TEST_DATA=true to clean)');
    }

    console.log('✅ E2E test cleanup complete');

  } catch (error) {
    console.error('❌ Global teardown failed:', error);
    // Don't throw - allow tests to complete even if cleanup fails
  }
}

export default globalTeardown;
