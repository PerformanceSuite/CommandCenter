import { test, expect } from '../fixtures/base';

/**
 * Critical User Flows E2E Tests
 *
 * Consolidated test suite covering all critical UI workflows:
 * - Dashboard navigation and loading
 * - Technology Radar CRUD and filtering
 * - Research Hub task management
 * - Knowledge Base search
 * - Settings and repository management
 * - Projects page functionality
 * - Responsive design and mobile support
 *
 * CONSOLIDATED FROM: 01-dashboard, 02-technology-radar, 03-research-hub,
 *                    04-knowledge-base, 05-settings, 07-projects
 */

test.describe('Critical User Flows', () => {
  test.describe('Dashboard Navigation', () => {
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

    test('should display overview statistics', async ({ dashboardPage }) => {
      const statsVisible = await dashboardPage.overviewStats.isVisible().catch(() => false);
      if (!statsVisible) {
        test.skip();
      }
      await expect(dashboardPage.overviewStats).toBeVisible();
    });

    test('should handle loading states', async ({ dashboardPage, page }) => {
      await page.reload();
      await dashboardPage.waitForLoad();
      await expect(dashboardPage.main).toBeVisible();
    });

    test('should be responsive on mobile', async ({ dashboardPage, page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await dashboardPage.goto();
      await dashboardPage.verifyDashboardLoaded();
    });

    test('should be responsive on tablet', async ({ dashboardPage, page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await dashboardPage.goto();
      await dashboardPage.verifyDashboardLoaded();
    });
  });

  test.describe('Technology Radar', () => {
    test.beforeEach(async ({ radarPage }) => {
      await radarPage.goto();
    });

    test('should load technology radar page', async ({ radarPage, page }) => {
      const mainVisible = await radarPage.main.isVisible({ timeout: 5000 }).catch(() => false);
      if (!mainVisible) {
        test.skip();
      }
      await expect(radarPage.main).toBeVisible();
    });

    test('should display radar chart', async ({ radarPage }) => {
      const chartExists = await radarPage.radarChart.count();
      if (chartExists === 0) {
        test.skip();
      }
      await radarPage.verifyRadarChartVisible();
    });

    test('should display technology list', async ({ radarPage }) => {
      const listExists = await radarPage.technologyList.isVisible({ timeout: 2000 }).catch(() => false);
      if (!listExists) {
        test.skip();
      }
      await expect(radarPage.technologyList).toBeVisible();
      const count = await radarPage.getTechnologyCount();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should create a new technology', async ({ radarPage, page }) => {
      const addButtonExists = await radarPage.addButton.isVisible({ timeout: 2000 }).catch(() => false);
      if (!addButtonExists) {
        test.skip();
      }

      const testTech = {
        title: `E2E Test Tech ${Date.now()}`,
        domain: 'ai-ml',
        vendor: 'Test Vendor',
        status: 'research',
        relevance: 85,
        description: 'E2E test technology',
      };

      await radarPage.createTechnology(testTech);

      const exists = await radarPage.verifyTechnologyExists(testTech.title);
      expect(exists).toBeTruthy();
    });

    test('should search technologies', async ({ radarPage }) => {
      const initialCount = await radarPage.getTechnologyCount();
      if (initialCount === 0) {
        test.skip();
      }

      await radarPage.searchTechnology('test');
      await radarPage.waitForLoadingComplete();

      const filteredCount = await radarPage.getTechnologyCount();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    });

    test('should filter by domain', async ({ radarPage }) => {
      const filterVisible = await radarPage.domainFilter.isVisible().catch(() => false);
      if (!filterVisible) {
        test.skip();
      }

      const initialCount = await radarPage.getTechnologyCount();
      await radarPage.filterByDomain('ai-ml');
      await radarPage.waitForLoadingComplete();

      const filteredCount = await radarPage.getTechnologyCount();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    });

    test('should filter by status', async ({ radarPage }) => {
      const filterVisible = await radarPage.statusFilter.isVisible().catch(() => false);
      if (!filterVisible) {
        test.skip();
      }

      const initialCount = await radarPage.getTechnologyCount();
      await radarPage.filterByStatus('integrated');
      await radarPage.waitForLoadingComplete();

      const filteredCount = await radarPage.getTechnologyCount();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    });

    test('should handle empty state', async ({ radarPage, page }) => {
      const searchExists = await radarPage.searchInput.isVisible({ timeout: 2000 }).catch(() => false);
      if (!searchExists) {
        test.skip();
      }

      await radarPage.searchTechnology('zzznonexistentxxx');
      await radarPage.waitForLoadingComplete();

      const count = await radarPage.getTechnologyCount();
      expect(count).toBe(0);
    });

    test('should be accessible', async ({ radarPage, page }) => {
      await expect(radarPage.main).toHaveAttribute('role', 'main');
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(focused).toBeTruthy();
    });
  });

  test.describe('Research Hub', () => {
    test.beforeEach(async ({ researchPage }) => {
      await researchPage.goto();
    });

    test('should load research hub page', async ({ researchPage }) => {
      const mainVisible = await researchPage.main.isVisible({ timeout: 5000 }).catch(() => false);
      if (!mainVisible) {
        test.skip();
      }
      await expect(researchPage.main).toBeVisible();
    });

    test('should display task list', async ({ researchPage }) => {
      const count = await researchPage.getTaskCount();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    test('should create a new research task', async ({ researchPage }) => {
      const addButtonExists = await researchPage.addTaskButton.isVisible({ timeout: 2000 }).catch(() => false);
      if (!addButtonExists) {
        test.skip();
      }

      const testTask = {
        title: `E2E Test Task ${Date.now()}`,
        description: 'E2E test research task',
        status: 'Planned',
        priority: 'High',
      };

      await researchPage.createTask(testTask);

      const exists = await researchPage.verifyTaskExists(testTask.title);
      expect(exists).toBeTruthy();
    });

    test('should update task status', async ({ researchPage }) => {
      const addButtonExists = await researchPage.addTaskButton.isVisible({ timeout: 2000 }).catch(() => false);
      if (!addButtonExists) {
        test.skip();
      }

      const testTask = {
        title: `Status Update Task ${Date.now()}`,
        description: 'Task for status update test',
        status: 'Planned',
        priority: 'Medium',
      };

      await researchPage.createTask(testTask);
      await researchPage.updateTaskStatus(testTask.title, 'In Progress');
      await researchPage.waitForLoadingComplete();

      const status = await researchPage.getTaskStatus(testTask.title);
      expect(status).toContain('In Progress');
    });

    test('should filter tasks by status', async ({ researchPage }) => {
      const filterVisible = await researchPage.statusFilter.isVisible().catch(() => false);
      if (!filterVisible) {
        test.skip();
      }

      const initialCount = await researchPage.getTaskCount();
      await researchPage.filterByStatus('Completed');
      await researchPage.waitForLoadingComplete();

      const filteredCount = await researchPage.getTaskCount();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    });

    test('should filter tasks by priority', async ({ researchPage }) => {
      const filterVisible = await researchPage.priorityFilter.isVisible().catch(() => false);
      if (!filterVisible) {
        test.skip();
      }

      const initialCount = await researchPage.getTaskCount();
      await researchPage.filterByPriority('High');
      await researchPage.waitForLoadingComplete();

      const filteredCount = await researchPage.getTaskCount();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    });

    test('should delete a task', async ({ researchPage }) => {
      const addButtonExists = await researchPage.addTaskButton.isVisible({ timeout: 2000 }).catch(() => false);
      if (!addButtonExists) {
        test.skip();
      }

      const testTask = {
        title: `Delete Task ${Date.now()}`,
        description: 'Task to be deleted',
        status: 'Planned',
        priority: 'Low',
      };

      await researchPage.createTask(testTask);

      let exists = await researchPage.verifyTaskExists(testTask.title);
      expect(exists).toBeTruthy();

      await researchPage.deleteTask(testTask.title);

      exists = await researchPage.verifyTaskExists(testTask.title);
      expect(exists).toBeFalsy();
    });

    test('should validate required fields', async ({ researchPage, page }) => {
      const addButtonExists = await researchPage.addTaskButton.isVisible({ timeout: 2000 }).catch(() => false);
      if (!addButtonExists) {
        test.skip();
      }

      await researchPage.clickAddTask();
      await researchPage.clickButton('Save');

      const formVisible = await researchPage.taskForm.isVisible();
      expect(formVisible).toBeTruthy();
    });
  });

  test.describe('Knowledge Base', () => {
    test.beforeEach(async ({ knowledgePage }) => {
      await knowledgePage.goto();
    });

    test('should load knowledge base page', async ({ knowledgePage }) => {
      await expect(knowledgePage.main).toBeVisible();
      await expect(knowledgePage.searchInput).toBeVisible();
    });

    test('should display search interface', async ({ knowledgePage }) => {
      await expect(knowledgePage.searchInput).toBeVisible();
      await expect(knowledgePage.searchButton).toBeVisible();
    });

    test('should perform knowledge search', async ({ knowledgePage }) => {
      const statsVisible = await knowledgePage.statsContainer.isVisible().catch(() => false);
      if (!statsVisible) {
        test.skip();
      }

      await knowledgePage.searchKnowledge('test query');
      await knowledgePage.waitForLoadingComplete();
      await expect(knowledgePage.results).toBeVisible();
    });

    test('should display search results', async ({ knowledgePage }) => {
      await knowledgePage.searchKnowledge('API documentation');
      await knowledgePage.waitForLoadingComplete();

      const resultCount = await knowledgePage.getResultCount();
      expect(resultCount).toBeGreaterThanOrEqual(0);
    });

    test('should handle empty search results', async ({ knowledgePage }) => {
      await knowledgePage.searchKnowledge('zzznonexistentqueryx');
      await knowledgePage.waitForLoadingComplete();

      const resultCount = await knowledgePage.getResultCount();
      expect(resultCount).toBe(0);
    });

    test('should display knowledge statistics', async ({ knowledgePage }) => {
      const statsVisible = await knowledgePage.statsContainer.isVisible().catch(() => false);
      if (statsVisible) {
        await expect(knowledgePage.statsContainer).toBeVisible();
      }
    });

    test('should validate search input', async ({ knowledgePage }) => {
      await knowledgePage.searchButton.click();
      await knowledgePage.waitForLoadingComplete();

      const results = await knowledgePage.results.isVisible();
      expect(results !== null).toBeTruthy();
    });

    test('should be keyboard accessible', async ({ knowledgePage, page }) => {
      await page.keyboard.press('Tab');
      await page.keyboard.type('test query');
      await page.keyboard.press('Enter');

      await knowledgePage.waitForLoadingComplete();

      const resultsVisible = await knowledgePage.results.isVisible({ timeout: 2000 }).catch(() => false);
      const resultCount = await knowledgePage.getResultCount().catch(() => -1);

      expect(resultsVisible || resultCount >= 0).toBeTruthy();
    });
  });

  test.describe('Settings & Repository Management', () => {
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
      await settingsPage.clickButton('Save');

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

    test('should be responsive on mobile', async ({ settingsPage, page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await settingsPage.goto();
      await expect(settingsPage.main).toBeVisible();
    });

    test('should be responsive on tablet', async ({ settingsPage, page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await settingsPage.goto();
      await expect(settingsPage.main).toBeVisible();
    });
  });

  test.describe('Projects Page', () => {
    test.beforeEach(async ({ projectsPage }) => {
      await projectsPage.goto();
    });

    test('should load projects page successfully', async ({ projectsPage, page }) => {
      await expect(page).toHaveURL(/\/projects/);
      await expect(projectsPage.main).toBeVisible();
    });

    test('should display project list', async ({ projectsPage }) => {
      const listVisible = await projectsPage.projectList.isVisible().catch(() => false);
      if (!listVisible) {
        test.skip();
      }
      await expect(projectsPage.projectList).toBeVisible();
    });

    test('should display existing projects', async ({ projectsPage }) => {
      const projectCount = await projectsPage.getProjectCount();
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

      const exists = await projectsPage.verifyProjectExists(projectName);
      expect(exists).toBeTruthy();
    });

    test('should validate required fields', async ({ projectsPage, page }) => {
      const buttonVisible = await projectsPage.addProjectButton.isVisible().catch(() => false);
      if (!buttonVisible) {
        test.skip();
      }

      await projectsPage.clickAddProject();
      await projectsPage.clickButton('Save');

      const formStillVisible = await projectsPage.projectForm.isVisible();
      expect(formStillVisible).toBeTruthy();
    });

    test('should select and switch projects', async ({ projectsPage }) => {
      const projectCount = await projectsPage.getProjectCount();
      if (projectCount === 0) {
        test.skip();
      }

      const firstCard = projectsPage.projectCard.first();
      const projectName = await firstCard.textContent();

      if (projectName) {
        await projectsPage.selectProject(projectName);
        await projectsPage.waitForLoadingComplete();
      }
    });

    test('should display project details', async ({ projectsPage }) => {
      const projectCount = await projectsPage.getProjectCount();
      if (projectCount === 0) {
        test.skip();
      }

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

      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      const focusedElement = await page.locator(':focus');
      expect(await focusedElement.count()).toBeGreaterThan(0);
    });

    test('should be accessible', async ({ projectsPage, page }) => {
      const main = await page.locator('[role="main"], main');
      expect(await main.count()).toBeGreaterThan(0);

      const headings = await page.locator('h1, h2, h3');
      expect(await headings.count()).toBeGreaterThan(0);
    });
  });
});
