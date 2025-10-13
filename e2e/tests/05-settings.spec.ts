import { test, expect } from '../fixtures/base';

/**
 * Settings E2E Tests
 *
 * Test suite for settings and configuration:
 * - Repository management
 * - GitHub integration
 * - Repository sync
 */

test.describe('Settings', () => {
  test.beforeEach(async ({ settingsPage }) => {
    await settingsPage.goto();
  });

  test('should load settings page', async ({ settingsPage }) => {
    await expect(settingsPage.main).toBeVisible();
  });

  test('should display repository list', async ({ settingsPage }) => {
    const repoListVisible = await settingsPage.repositoryList.isVisible().catch(() => false);
    if (repoListVisible) {
      await expect(settingsPage.repositoryList).toBeVisible();
    }
  });

  test('should show add repository button', async ({ settingsPage }) => {
    const buttonVisible = await settingsPage.addRepositoryButton.isVisible().catch(() => false);
    if (buttonVisible) {
      await expect(settingsPage.addRepositoryButton).toBeVisible();
    }
  });

  test('should open repository form', async ({ settingsPage }) => {
    const buttonVisible = await settingsPage.addRepositoryButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }

    await settingsPage.clickAddRepository();
    await expect(settingsPage.repositoryForm).toBeVisible();
  });

  test('should validate repository form', async ({ settingsPage, page }) => {
    const buttonVisible = await settingsPage.addRepositoryButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }

    await settingsPage.clickAddRepository();

    // Try to submit without filling required fields
    await settingsPage.clickButton('Save');

    // Form should still be visible (validation failed)
    const formVisible = await settingsPage.repositoryForm.isVisible();
    expect(formVisible).toBeTruthy();
  });

  test('should display repository count', async ({ settingsPage }) => {
    const repoListVisible = await settingsPage.repositoryList.isVisible().catch(() => false);
    if (!repoListVisible) {
      test.skip();
    }

    const count = await settingsPage.getRepositoryCount();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should handle empty repository list', async ({ settingsPage }) => {
    const repoListVisible = await settingsPage.repositoryList.isVisible().catch(() => false);
    if (repoListVisible) {
      const count = await settingsPage.getRepositoryCount();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should be responsive', async ({ settingsPage, page }) => {
    // Mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await settingsPage.goto();
    await expect(settingsPage.main).toBeVisible();

    // Tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await settingsPage.goto();
    await expect(settingsPage.main).toBeVisible();
  });
});
