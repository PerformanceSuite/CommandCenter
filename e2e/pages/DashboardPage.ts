import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Dashboard Page Object
 *
 * Represents the main dashboard view with:
 * - Repository selector
 * - Overview statistics
 * - Recent activity
 * - Quick actions
 */
export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Selectors
   */
  get repositorySelector(): Locator {
    return this.page.locator('[data-testid="repository-selector"], select[name="repository"]');
  }

  get overviewStats(): Locator {
    return this.page.locator('[data-testid="overview-stats"], .stats-container');
  }

  get recentActivity(): Locator {
    return this.page.locator('[data-testid="recent-activity"], .activity-list');
  }

  get quickActions(): Locator {
    return this.page.locator('[data-testid="quick-actions"], .quick-actions');
  }

  get projectCard(): Locator {
    return this.page.locator('[data-testid="project-card"], .project-card');
  }

  /**
   * Navigation
   */
  async goto(): Promise<void> {
    await this.page.goto('/');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.waitForReactLoad();
    await this.main.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
    await this.waitForLoadingComplete();
  }

  /**
   * Actions
   */
  async selectRepository(repositoryName: string): Promise<void> {
    await this.repositorySelector.selectOption({ label: repositoryName });
    await this.waitForLoadingComplete();
    await this.waitForApiResponse('/api/v1/repositories');
  }

  async navigateToTechnologyRadar(): Promise<void> {
    await this.clickSidebarLink('Technology Radar');
  }

  async navigateToResearchHub(): Promise<void> {
    await this.clickSidebarLink('Research Hub');
  }

  async navigateToKnowledgeBase(): Promise<void> {
    await this.clickSidebarLink('Knowledge Base');
  }

  async navigateToProjects(): Promise<void> {
    await this.clickSidebarLink('Projects');
  }

  async navigateToSettings(): Promise<void> {
    await this.clickSidebarLink('Settings');
  }

  /**
   * Verifications
   */
  async verifyDashboardLoaded(): Promise<void> {
    await this.expectVisible('[role="main"]');
    await this.sidebar.waitFor({ state: 'visible' });
    await this.header.waitFor({ state: 'visible' });
  }

  async getStatValue(statName: string): Promise<string | null> {
    const stat = this.overviewStats.locator(`text="${statName}"`).locator('..');
    return await stat.textContent();
  }

  async getRecentActivityCount(): Promise<number> {
    return await this.recentActivity.locator('li, .activity-item').count();
  }
}
