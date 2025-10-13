import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Settings Page Object
 *
 * Represents the settings/configuration view with:
 * - Repository management
 * - GitHub integration
 * - System configuration
 */
export class SettingsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Selectors
   */
  get repositoryList(): Locator {
    return this.page.locator('[data-testid="repository-list"], .repository-list');
  }

  get repositoryItem(): Locator {
    return this.page.locator('[data-testid="repository-item"], .repository-item');
  }

  get addRepositoryButton(): Locator {
    return this.page.getByRole('button', { name: /Add.*Repository/i });
  }

  get repositoryForm(): Locator {
    return this.page.locator('[data-testid="repository-form"], form');
  }

  get syncButton(): Locator {
    return this.page.getByRole('button', { name: /Sync/i });
  }

  /**
   * Navigation
   */
  async goto(): Promise<void> {
    await this.page.goto('/settings');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.main.waitFor({ state: 'visible' });
    await this.waitForLoadingComplete();
  }

  /**
   * Actions
   */
  async clickAddRepository(): Promise<void> {
    await this.addRepositoryButton.click();
    await this.repositoryForm.waitFor({ state: 'visible' });
  }

  async addRepository(data: {
    owner: string;
    name: string;
    accessToken?: string;
  }): Promise<void> {
    await this.clickAddRepository();

    await this.fillInput('[name="owner"]', data.owner);
    await this.fillInput('[name="name"]', data.name);
    if (data.accessToken) {
      await this.fillInput('[name="access_token"]', data.accessToken);
    }

    await this.clickButton('Save');
    await this.waitForApiResponse('/api/v1/repositories');
    await this.waitForLoadingComplete();
  }

  async syncRepository(repositoryName: string): Promise<void> {
    const repoItem = this.repositoryItem.filter({ hasText: repositoryName });
    await repoItem.locator(this.syncButton).click();
    await this.waitForApiResponse('/api/v1/repositories');
    await this.waitForLoadingComplete();
  }

  async deleteRepository(repositoryName: string): Promise<void> {
    const repoItem = this.repositoryItem.filter({ hasText: repositoryName });
    await repoItem.getByRole('button', { name: /delete/i }).click();

    // Confirm deletion if modal appears
    const confirmButton = this.page.getByRole('button', { name: /confirm|yes|delete/i });
    if (await confirmButton.isVisible({ timeout: 2000 })) {
      await confirmButton.click();
    }

    await this.waitForApiResponse('/api/v1/repositories');
    await this.waitForLoadingComplete();
  }

  /**
   * Verifications
   */
  async getRepositoryCount(): Promise<number> {
    return await this.repositoryItem.count();
  }

  async verifyRepositoryExists(name: string): Promise<boolean> {
    const repoItem = this.repositoryItem.filter({ hasText: name });
    return await repoItem.isVisible();
  }
}
