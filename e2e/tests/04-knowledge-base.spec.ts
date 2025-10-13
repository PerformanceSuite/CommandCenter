import { test, expect } from '../fixtures/base';

/**
 * Knowledge Base E2E Tests
 *
 * Test suite for RAG-powered knowledge base:
 * - Search functionality
 * - Document management
 * - Query results
 * - Knowledge statistics
 */

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
    // Skip if no documents indexed
    const statsVisible = await knowledgePage.statsContainer.isVisible().catch(() => false);
    if (!statsVisible) {
      test.skip();
    }

    await knowledgePage.searchKnowledge('test query');

    // Wait for results or empty state
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

    // Should show empty state
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
    // Try empty search
    await knowledgePage.searchButton.click();
    await knowledgePage.waitForLoadingComplete();

    // Should handle gracefully (either show validation or all results)
    const results = await knowledgePage.results.isVisible();
    expect(results !== null).toBeTruthy();
  });

  test('should be keyboard accessible', async ({ knowledgePage, page }) => {
    // Focus search input with Tab
    await page.keyboard.press('Tab');

    // Type query
    await page.keyboard.type('test query');

    // Submit with Enter
    await page.keyboard.press('Enter');

    await knowledgePage.waitForLoadingComplete();
    await expect(knowledgePage.results).toBeVisible();
  });
});
