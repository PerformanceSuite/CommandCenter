import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Projects Page Object
 *
 * Represents the project management view with:
 * - Project list
 * - Project creation/editing
 * - Project switching
 */
export class ProjectsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Selectors
   */
  get projectList(): Locator {
    return this.page.locator('[data-testid="project-list"], .project-list');
  }

  get projectCard(): Locator {
    return this.page.locator('[data-testid="project-card"], .project-card');
  }

  get addProjectButton(): Locator {
    return this.page.getByRole('button', { name: /Add.*Project|New.*Project/i });
  }

  get projectForm(): Locator {
    return this.page.locator('[data-testid="project-form"], form');
  }

  /**
   * Navigation
   */
  async goto(): Promise<void> {
    await this.page.goto('/projects');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.main.waitFor({ state: 'visible' });
    await this.waitForLoadingComplete();
  }

  /**
   * Actions
   */
  async clickAddProject(): Promise<void> {
    await this.addProjectButton.click();
    // Wait for modal to appear
    await this.projectForm.waitFor({ state: 'visible', timeout: 15000 });
    // Wait for form inputs to be ready
    await this.page.locator('[name="name"]').waitFor({ state: 'visible', timeout: 15000 });
    // Small delay for any animations
    await this.page.waitForTimeout(300);
  }

  async createProject(data: {
    name: string;
    description?: string;
  }): Promise<void> {
    await this.clickAddProject();

    // Wait for inputs to be ready and fill them
    const nameInput = this.page.locator('[name="name"]');
    await nameInput.waitFor({ state: 'visible', timeout: 15000 });
    await nameInput.fill(data.name);

    if (data.description) {
      const descInput = this.page.locator('[name="description"]');
      await descInput.waitFor({ state: 'visible', timeout: 15000 });
      await descInput.fill(data.description);
    }

    // Wait for submit button and click
    const submitButton = this.page.getByRole('button', { name: /Create Project|Update Project/i });
    await submitButton.waitFor({ state: 'visible', timeout: 15000 });
    await submitButton.click();

    await this.waitForApiResponse('/api/v1/projects');
    await this.waitForLoadingComplete();
  }

  async selectProject(projectName: string): Promise<void> {
    const projectCard = this.projectCard.filter({ hasText: projectName });
    await projectCard.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Verifications
   */
  async getProjectCount(): Promise<number> {
    return await this.projectCard.count();
  }

  async verifyProjectExists(name: string): Promise<boolean> {
    const projectCard = this.projectCard.filter({ hasText: name });
    return await projectCard.isVisible();
  }
}
