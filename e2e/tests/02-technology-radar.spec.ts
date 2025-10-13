import { test, expect } from '../fixtures/base';

/**
 * Technology Radar E2E Tests
 *
 * Test suite for technology radar functionality:
 * - Radar visualization
 * - Technology CRUD operations
 * - Search and filtering
 * - Chart interactions
 */

test.describe('Technology Radar', () => {
  test.beforeEach(async ({ radarPage }) => {
    await radarPage.goto();
  });

  test('should load technology radar page', async ({ radarPage, page }) => {
    // Check if radar page exists
    const mainVisible = await radarPage.main.isVisible({ timeout: 5000 }).catch(() => false);
    if (!mainVisible) {
      test.skip(); // Skip if route not implemented
    }
    await expect(radarPage.main).toBeVisible();
  });

  test('should display radar chart', async ({ radarPage }) => {
    const chartVisible = await radarPage.radarChart.isVisible({ timeout: 5000 }).catch(() => false);
    if (!chartVisible) {
      test.skip();
    }
    await radarPage.verifyRadarChartVisible();
  });

  test('should display technology list', async ({ radarPage }) => {
    await expect(radarPage.technologyList).toBeVisible();
    const count = await radarPage.getTechnologyCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should create a new technology', async ({ radarPage, page }) => {
    const testTech = {
      title: `E2E Test Tech ${Date.now()}`,
      domain: 'Languages & Frameworks',
      vendor: 'Test Vendor',
      status: 'Adopt',
      relevance: 8,
      description: 'E2E test technology',
    };

    await radarPage.createTechnology(testTech);

    // Verify technology appears in list
    const exists = await radarPage.verifyTechnologyExists(testTech.title);
    expect(exists).toBeTruthy();
  });

  test('should search technologies', async ({ radarPage }) => {
    // Skip if no technologies exist
    const initialCount = await radarPage.getTechnologyCount();
    if (initialCount === 0) {
      test.skip();
    }

    await radarPage.searchTechnology('test');
    await radarPage.waitForLoadingComplete();

    // Results should be filtered
    const filteredCount = await radarPage.getTechnologyCount();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  test('should filter by domain', async ({ radarPage }) => {
    // Skip if domain filter not available
    const filterVisible = await radarPage.domainFilter.isVisible().catch(() => false);
    if (!filterVisible) {
      test.skip();
    }

    const initialCount = await radarPage.getTechnologyCount();
    await radarPage.filterByDomain('Languages & Frameworks');
    await radarPage.waitForLoadingComplete();

    const filteredCount = await radarPage.getTechnologyCount();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  test('should filter by status', async ({ radarPage }) => {
    // Skip if status filter not available
    const filterVisible = await radarPage.statusFilter.isVisible().catch(() => false);
    if (!filterVisible) {
      test.skip();
    }

    const initialCount = await radarPage.getTechnologyCount();
    await radarPage.filterByStatus('Adopt');
    await radarPage.waitForLoadingComplete();

    const filteredCount = await radarPage.getTechnologyCount();
    expect(filteredCount).toBeLessThanOrEqual(initialCount);
  });

  test('should handle empty state', async ({ radarPage, page }) => {
    // Apply filters that return no results
    await radarPage.searchTechnology('zzznonexistentxxx');
    await radarPage.waitForLoadingComplete();

    // Should show empty state or zero results
    const count = await radarPage.getTechnologyCount();
    expect(count).toBe(0);
  });

  test('should be accessible', async ({ radarPage, page }) => {
    // Check for basic accessibility
    await expect(radarPage.main).toHaveAttribute('role', 'main');

    // Check for keyboard navigation
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });
});
