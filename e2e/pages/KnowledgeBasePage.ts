import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Knowledge Base Page Object
 *
 * Represents the RAG-powered knowledge base with:
 * - Search interface
 * - Query results
 * - Document management
 * - Knowledge statistics
 */
export class KnowledgeBasePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Selectors
   */
  get searchInput(): Locator {
    return this.page.locator('[data-testid="knowledge-search"], input[placeholder*="Search"], textarea[placeholder*="query"]');
  }

  get searchButton(): Locator {
    return this.page.getByRole('button', { name: /Search|Query/i });
  }

  get results(): Locator {
    return this.page.locator('[data-testid="search-results"], .results-container');
  }

  get resultItem(): Locator {
    return this.page.locator('[data-testid="result-item"], .result-item');
  }

  get statsContainer(): Locator {
    return this.page.locator('[data-testid="knowledge-stats"], .stats-container');
  }

  get addDocumentButton(): Locator {
    return this.page.getByRole('button', { name: /Add.*Document/i });
  }

  /**
   * Navigation
   */
  async goto(): Promise<void> {
    await this.page.goto('/knowledge');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.main.waitFor({ state: 'visible' });
    await this.waitForLoadingComplete();
  }

  /**
   * Actions
   */
  async searchKnowledge(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchButton.click();
    await this.waitForApiResponse('/api/v1/knowledge/query');
    await this.waitForLoadingComplete();
  }

  async addDocument(data: {
    title: string;
    content: string;
    category?: string;
  }): Promise<void> {
    await this.addDocumentButton.click();

    await this.fillInput('[name="title"]', data.title);
    await this.fillInput('[name="content"]', data.content);
    if (data.category) {
      await this.selectDropdown('[name="category"]', data.category);
    }

    await this.clickButton('Save');
    await this.waitForApiResponse('/api/v1/knowledge');
    await this.waitForLoadingComplete();
  }

  /**
   * Verifications
   */
  async getResultCount(): Promise<number> {
    return await this.resultItem.count();
  }

  async verifyResultsContainText(text: string): Promise<boolean> {
    const results = await this.results.textContent();
    return results?.includes(text) ?? false;
  }

  async getStatistic(statName: string): Promise<string | null> {
    const stat = this.statsContainer.locator(`text="${statName}"`).locator('..');
    return await stat.textContent();
  }
}
