import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Research Hub Page Object
 *
 * Represents the research task management view with:
 * - Research task list
 * - Task creation/editing
 * - Status management
 * - Task filtering
 */
export class ResearchHubPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Selectors
   */
  get taskList(): Locator {
    return this.page.locator('[data-testid="research-task-list"], .task-list');
  }

  get taskItem(): Locator {
    return this.page.locator('[data-testid="research-task-item"], .task-item');
  }

  get addTaskButton(): Locator {
    return this.page.getByRole('button', { name: /Add.*Task|New.*Task/i });
  }

  get taskForm(): Locator {
    return this.page.locator('[data-testid="task-form"], form');
  }

  get statusFilter(): Locator {
    return this.page.locator('[data-testid="status-filter"], select[name="status"]');
  }

  get priorityFilter(): Locator {
    return this.page.locator('[data-testid="priority-filter"], select[name="priority"]');
  }

  /**
   * Navigation
   */
  async goto(): Promise<void> {
    await this.page.goto('/research');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.main.waitFor({ state: 'visible' });
    await this.waitForLoadingComplete();
  }

  /**
   * Actions
   */
  async clickAddTask(): Promise<void> {
    await this.addTaskButton.click();
    await this.taskForm.waitFor({ state: 'visible' });
  }

  async createTask(data: {
    title: string;
    description?: string;
    status: string;
    priority: string;
  }): Promise<void> {
    await this.clickAddTask();

    await this.fillInput('[name="title"]', data.title);
    if (data.description) {
      await this.fillInput('[name="description"]', data.description);
    }
    await this.selectDropdown('[name="status"]', data.status);
    await this.selectDropdown('[name="priority"]', data.priority);

    await this.clickButton('Save');
    await this.waitForApiResponse('/api/v1/research');
    await this.waitForLoadingComplete();
  }

  async updateTaskStatus(taskTitle: string, newStatus: string): Promise<void> {
    const taskItem = this.taskItem.filter({ hasText: taskTitle });
    const statusDropdown = taskItem.locator('select[name="status"]');
    await statusDropdown.selectOption(newStatus);
    await this.waitForApiResponse('/api/v1/research');
    await this.waitForLoadingComplete();
  }

  async deleteTask(taskTitle: string): Promise<void> {
    const taskItem = this.taskItem.filter({ hasText: taskTitle });
    await taskItem.getByRole('button', { name: /delete/i }).click();

    // Confirm deletion if modal appears
    const confirmButton = this.page.getByRole('button', { name: /confirm|yes|delete/i });
    if (await confirmButton.isVisible({ timeout: 2000 })) {
      await confirmButton.click();
    }

    await this.waitForApiResponse('/api/v1/research');
    await this.waitForLoadingComplete();
  }

  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.selectOption(status);
    await this.waitForLoadingComplete();
  }

  async filterByPriority(priority: string): Promise<void> {
    await this.priorityFilter.selectOption(priority);
    await this.waitForLoadingComplete();
  }

  /**
   * Verifications
   */
  async getTaskCount(): Promise<number> {
    return await this.taskItem.count();
  }

  async verifyTaskExists(title: string): Promise<boolean> {
    const taskItem = this.taskItem.filter({ hasText: title });
    return await taskItem.isVisible();
  }

  async getTaskStatus(taskTitle: string): Promise<string | null> {
    const taskItem = this.taskItem.filter({ hasText: taskTitle });
    const statusElement = taskItem.locator('[data-testid="task-status"], .task-status');
    return await statusElement.textContent();
  }
}
