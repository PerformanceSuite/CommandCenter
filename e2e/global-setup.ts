import { chromium, FullConfig } from '@playwright/test';
import { seedDatabase, verifyDatabaseReady } from './utils/seed-data';

/**
 * Global Setup - Runs once before all tests
 *
 * Responsibilities:
 * - Verify services are healthy
 * - Setup test database state
 * - Seed database with test data
 * - Initialize authentication state
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test setup...');

  const baseURL = config.use?.baseURL || process.env.BASE_URL || 'http://localhost:3000';
  const apiURL = process.env.API_URL || 'http://localhost:8000';

  // Launch browser for setup tasks
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 1. Verify backend health
    console.log('✓ Checking backend health...');
    const healthResponse = await page.goto(apiURL + '/health', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    if (!healthResponse || !healthResponse.ok()) {
      throw new Error(`Backend health check failed: ${healthResponse?.status()}`);
    }

    console.log('✓ Backend is healthy');

    // 2. Verify frontend loads
    console.log('✓ Checking frontend...');
    const frontendResponse = await page.goto(baseURL, {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    if (!frontendResponse || !frontendResponse.ok()) {
      throw new Error(`Frontend failed to load: ${frontendResponse?.status()}`);
    }

    console.log('✓ Frontend is accessible');

    // 3. Setup test database with seed data
    console.log('✓ Setting up test database...');

    // Check if database already has data
    const hasData = await verifyDatabaseReady(context.request);

    if (!hasData) {
      console.log('  Database is empty, seeding with test data...');
      await seedDatabase(context.request);
    } else {
      console.log('  Database already has test data, skipping seed');
    }

    console.log('✅ E2E test setup complete\n');

  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await page.close();
    await context.close();
    await browser.close();
  }
}

export default globalSetup;
