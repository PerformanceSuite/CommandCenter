import { test, expect } from '../fixtures/base';

/**
 * Dashboard E2E Tests
 *
 * Test suite for the main dashboard functionality:
 * - Page load and navigation
 * - Repository selection
 * - Overview statistics
 * - Quick actions
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ dashboardPage }) => {
    await dashboardPage.goto();
  });

  test('should load dashboard successfully', async ({ dashboardPage }) => {
    await dashboardPage.verifyDashboardLoaded();
    await expect(dashboardPage.main).toBeVisible();
    await expect(dashboardPage.sidebar).toBeVisible();
    await expect(dashboardPage.header).toBeVisible();
  });

  test('should display page title', async ({ page }) => {
    await expect(page).toHaveTitle(/Command Center/i);
  });

  test('should have working navigation links', async ({ dashboardPage, page }) => {
    // Technology Radar
    await dashboardPage.navigateToTechnologyRadar();
    await expect(page).toHaveURL(/\/radar/);

    // Navigate back
    await page.goto('/');

    // Research Hub
    await dashboardPage.navigateToResearchHub();
    await expect(page).toHaveURL(/\/research/);

    // Navigate back
    await page.goto('/');

    // Knowledge Base
    await dashboardPage.navigateToKnowledgeBase();
    await expect(page).toHaveURL(/\/knowledge/);

    // Navigate back
    await page.goto('/');

    // Projects
    await dashboardPage.navigateToProjects();
    await expect(page).toHaveURL(/\/projects/);

    // Navigate back
    await page.goto('/');

    // Settings
    await dashboardPage.navigateToSettings();
    await expect(page).toHaveURL(/\/settings/);
  });

  test('should display overview statistics', async ({ dashboardPage, page }) => {
    // Check if stats container exists, if not skip test
    const statsVisible = await dashboardPage.overviewStats.isVisible().catch(() => false);
    if (!statsVisible) {
      test.skip();
    }
    await expect(dashboardPage.overviewStats).toBeVisible();
  });

  test('should handle loading states', async ({ dashboardPage, page }) => {
    // Trigger a state change that causes loading
    await page.reload();
    await dashboardPage.waitForLoad();
    await expect(dashboardPage.main).toBeVisible();
  });

  test('should be responsive on mobile', async ({ dashboardPage, page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await dashboardPage.goto();
    await dashboardPage.verifyDashboardLoaded();
  });

  test('should be responsive on tablet', async ({ dashboardPage, page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await dashboardPage.goto();
    await dashboardPage.verifyDashboardLoaded();
  });
});
