import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Technology Radar Page Object
 *
 * Represents the technology radar visualization with:
 * - Radar chart
 * - Technology list/grid
 * - Filters and search
 * - Technology CRUD operations
 */
export class TechnologyRadarPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Selectors
   */
  get radarChart(): Locator {
    return this.page.locator('canvas, [data-testid="radar-chart"]');
  }

  get technologyList(): Locator {
    return this.page.locator('[data-testid="technology-list"], .technology-list');
  }

  get technologyItem(): Locator {
    return this.page.locator('[data-testid="technology-item"], .technology-item');
  }

  get searchInput(): Locator {
    return this.page.locator('[data-testid="search-technologies"], input[placeholder*="Search"]');
  }

  get addButton(): Locator {
    return this.page.getByRole('button', { name: /Add.*Technology/i });
  }

  get technologyForm(): Locator {
    return this.page.locator('[data-testid="technology-form"], form');
  }

  /**
   * Filter selectors
   */
  get domainFilter(): Locator {
    return this.page.locator('[data-testid="domain-filter"], select[name="domain"]');
  }

  get statusFilter(): Locator {
    return this.page.locator('[data-testid="status-filter"], select[name="status"]');
  }

  /**
   * View mode buttons
   */
  get cardsViewButton(): Locator {
    return this.page.getByRole('button', { name: /Cards/i });
  }

  get matrixViewButton(): Locator {
    return this.page.getByRole('button', { name: /Matrix/i });
  }

  /**
   * Navigation
   */
  async goto(): Promise<void> {
    await this.page.goto('/radar');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.main.waitFor({ state: 'visible' });
    await this.waitForLoadingComplete();
    // Don't wait for radar chart by default since page loads in Cards view
  }

  /**
   * Switch to matrix view to see radar chart
   */
  async switchToMatrixView(): Promise<void> {
    await this.matrixViewButton.click();
    await this.waitForLoadingComplete();
    // Now wait for chart to render
    await this.radarChart.waitFor({ state: 'visible', timeout: 10000 });
  }

  /**
   * Switch to cards view
   */
  async switchToCardsView(): Promise<void> {
    await this.cardsViewButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Actions
   */
  async searchTechnology(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.waitForLoadingComplete();
  }

  async filterByDomain(domain: string): Promise<void> {
    await this.domainFilter.selectOption(domain);
    await this.waitForLoadingComplete();
  }

  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.selectOption(status);
    await this.waitForLoadingComplete();
  }

  async clickAddTechnology(): Promise<void> {
    await this.addButton.click();
    await this.technologyForm.waitFor({ state: 'visible' });
  }

  async createTechnology(data: {
    title: string;
    domain: string;
    vendor?: string;
    status: string;
    relevance: number;
    description?: string;
  }): Promise<void> {
    await this.clickAddTechnology();

    await this.fillInput('[name="title"]', data.title);
    await this.selectDropdown('[name="domain"]', data.domain);
    if (data.vendor) {
      await this.fillInput('[name="vendor"]', data.vendor);
    }
    await this.selectDropdown('[name="status"]', data.status);
    await this.fillInput('[name="relevance"]', data.relevance.toString());
    if (data.description) {
      await this.fillInput('[name="description"]', data.description);
    }

    await this.clickButton('Save');
    await this.waitForApiResponse('/api/v1/technologies');
    await this.waitForLoadingComplete();
  }

  async deleteTechnology(title: string): Promise<void> {
    const techItem = this.technologyItem.filter({ hasText: title });
    await techItem.getByRole('button', { name: /delete/i }).click();

    // Confirm deletion if modal appears
    const confirmButton = this.page.getByRole('button', { name: /confirm|yes|delete/i });
    if (await confirmButton.isVisible({ timeout: 2000 })) {
      await confirmButton.click();
    }

    await this.waitForApiResponse('/api/v1/technologies');
    await this.waitForLoadingComplete();
  }

  /**
   * Verifications
   */
  async getTechnologyCount(): Promise<number> {
    return await this.technologyItem.count();
  }

  async verifyTechnologyExists(title: string): Promise<boolean> {
    const techItem = this.technologyItem.filter({ hasText: title });
    return await techItem.isVisible();
  }

  async verifyRadarChartVisible(): Promise<void> {
    await this.expectVisible('canvas, [data-testid="radar-chart"]');
  }
}
