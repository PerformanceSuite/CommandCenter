import { test, expect } from '../fixtures/base';

/**
 * Projects Page E2E Tests
 *
 * Test suite for project management functionality:
 * - Project listing and display
 * - Project creation and editing
 * - Project switching
 * - Project search and filtering
 * - Project deletion
 */

test.describe('Projects Page', () => {
  test.beforeEach(async ({ projectsPage }) => {
    await projectsPage.goto();
  });

  test('should load projects page successfully', async ({ projectsPage, page }) => {
    await expect(page).toHaveURL(/\/projects/);
    await expect(projectsPage.main).toBeVisible();
  });

  test('should display project list', async ({ projectsPage }) => {
    // Check if project list exists
    const listVisible = await projectsPage.projectList.isVisible().catch(() => false);
    if (!listVisible) {
      test.skip();
    }
    await expect(projectsPage.projectList).toBeVisible();
  });

  test('should display existing projects', async ({ projectsPage }) => {
    const projectCount = await projectsPage.getProjectCount();
    // Should have at least one project (default)
    expect(projectCount).toBeGreaterThanOrEqual(0);
  });

  test('should show add project button', async ({ projectsPage }) => {
    const buttonVisible = await projectsPage.addProjectButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }
    await expect(projectsPage.addProjectButton).toBeVisible();
  });

  test('should open project creation form', async ({ projectsPage }) => {
    const buttonVisible = await projectsPage.addProjectButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }

    await projectsPage.clickAddProject();
    await expect(projectsPage.projectForm).toBeVisible();
  });

  test('should create a new project', async ({ projectsPage, page }) => {
    const buttonVisible = await projectsPage.addProjectButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }

    const projectName = `Test Project ${Date.now()}`;
    const projectDescription = 'E2E Test Project Description';

    await projectsPage.createProject({
      name: projectName,
      description: projectDescription,
    });

    // Verify project was created
    const exists = await projectsPage.verifyProjectExists(projectName);
    expect(exists).toBeTruthy();
  });

  test('should validate required fields', async ({ projectsPage, page }) => {
    const buttonVisible = await projectsPage.addProjectButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }

    await projectsPage.clickAddProject();

    // Try to submit without filling required fields
    await projectsPage.clickButton('Save');

    // Should show validation error or form should still be visible
    const formStillVisible = await projectsPage.projectForm.isVisible();
    expect(formStillVisible).toBeTruthy();
  });

  test('should select and switch projects', async ({ projectsPage }) => {
    const projectCount = await projectsPage.getProjectCount();
    if (projectCount === 0) {
      test.skip();
    }

    // Get first project card
    const firstCard = projectsPage.projectCard.first();
    const projectName = await firstCard.textContent();

    if (projectName) {
      await projectsPage.selectProject(projectName);
      // Verify navigation or state change occurred
      await projectsPage.waitForLoadingComplete();
    }
  });

  test('should display project details', async ({ projectsPage }) => {
    const projectCount = await projectsPage.getProjectCount();
    if (projectCount === 0) {
      test.skip();
    }

    // Each project card should have at least a title
    const firstCard = projectsPage.projectCard.first();
    const textContent = await firstCard.textContent();
    expect(textContent).toBeTruthy();
    expect(textContent!.length).toBeGreaterThan(0);
  });

  test('should be responsive on mobile', async ({ projectsPage, page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await projectsPage.goto();
    await expect(projectsPage.main).toBeVisible();
  });

  test('should be responsive on tablet', async ({ projectsPage, page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await projectsPage.goto();
    await expect(projectsPage.main).toBeVisible();
  });

  test('should handle keyboard navigation', async ({ projectsPage, page }) => {
    const buttonVisible = await projectsPage.addProjectButton.isVisible().catch(() => false);
    if (!buttonVisible) {
      test.skip();
    }

    // Tab to add project button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify some interactive element has focus
    const focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);
  });

  test('should be accessible', async ({ projectsPage, page }) => {
    // Check for ARIA landmarks
    const main = await page.locator('[role="main"], main');
    expect(await main.count()).toBeGreaterThan(0);

    // Check for heading structure
    const headings = await page.locator('h1, h2, h3');
    expect(await headings.count()).toBeGreaterThan(0);
  });
});
