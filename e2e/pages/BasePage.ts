import { Page, Locator, expect } from '@playwright/test';

/**
 * BasePage - Abstract base class for all page objects
 *
 * Provides common functionality:
 * - Navigation helpers
 * - Wait utilities
 * - Common element interactions
 * - Error handling
 */
export abstract class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to the page
   */
  abstract goto(): Promise<void>;

  /**
   * Wait for the page to be fully loaded
   */
  abstract waitForLoad(): Promise<void>;

  /**
   * Wait for React to hydrate/render
   */
  async waitForReactLoad(): Promise<void> {
    // Wait for React root to be populated
    await this.page.waitForSelector('#root > *', { state: 'attached', timeout: 10000 });
    // Additional time for React to fully render
    await this.page.waitForTimeout(500);
  }

  /**
   * Common selectors
   */
  get sidebar(): Locator {
    return this.page.locator('[role="navigation"], nav, .sidebar');
  }

  get header(): Locator {
    return this.page.locator('header, [role="banner"]');
  }

  get main(): Locator {
    return this.page.locator('main, [role="main"]');
  }

  get loadingSpinner(): Locator {
    return this.page.locator('[data-testid="loading-spinner"], .loading-spinner, [role="status"]');
  }

  /**
   * Navigation helpers
   */
  async navigateToRoute(route: string): Promise<void> {
    await this.page.goto(route);
    await this.waitForNetworkIdle();
  }

  async clickSidebarLink(linkText: string): Promise<void> {
    await this.sidebar.getByRole('link', { name: linkText }).click();
    await this.waitForNetworkIdle();
  }

  /**
   * Wait utilities
   */
  async waitForNetworkIdle(timeout: number = 5000): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout });
  }

  async waitForLoadingComplete(timeout: number = 10000): Promise<void> {
    // Wait for loading spinner to appear and disappear
    try {
      await this.loadingSpinner.waitFor({ state: 'visible', timeout: 2000 });
      await this.loadingSpinner.waitFor({ state: 'hidden', timeout });
    } catch {
      // Loading spinner might not appear for fast operations
      await this.waitForNetworkIdle();
    }
  }

  /**
   * Form interaction helpers
   */
  async fillInput(selector: string, value: string, timeout: number = 15000): Promise<void> {
    const input = this.page.locator(selector);
    await input.waitFor({ state: 'visible', timeout });
    await input.clear();
    await input.fill(value);
  }

  async selectDropdown(selector: string, value: string): Promise<void> {
    await this.page.locator(selector).selectOption(value);
  }

  async clickButton(text: string, timeout: number = 15000): Promise<void> {
    const button = this.page.getByRole('button', { name: new RegExp(text, 'i') });
    await button.waitFor({ state: 'visible', timeout });
    await button.click();
  }

  /**
   * Verification helpers
   */
  async expectVisible(selector: string): Promise<void> {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  async expectText(selector: string, text: string | RegExp): Promise<void> {
    await expect(this.page.locator(selector)).toContainText(text);
  }

  async expectCount(selector: string, count: number): Promise<void> {
    await expect(this.page.locator(selector)).toHaveCount(count);
  }

  /**
   * API interaction helpers
   */
  async waitForApiResponse(urlPattern: string | RegExp, timeout: number = 5000): Promise<void> {
    await this.page.waitForResponse(
      response => {
        const url = response.url();
        const matches = typeof urlPattern === 'string'
          ? url.includes(urlPattern)
          : urlPattern.test(url);
        return matches && response.status() === 200;
      },
      { timeout }
    );
  }

  /**
   * Screenshot helper
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({
      path: `e2e/screenshots/${name}.png`,
      fullPage: true
    });
  }

  /**
   * Error handling
   */
  async getErrorMessage(): Promise<string | null> {
    const errorElement = this.page.locator('[role="alert"], .error-message, .alert-error');
    if (await errorElement.isVisible()) {
      return await errorElement.textContent();
    }
    return null;
  }
}
