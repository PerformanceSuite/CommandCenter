import { test as base, Page } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';
import { TechnologyRadarPage } from '../pages/TechnologyRadarPage';
import { ResearchHubPage } from '../pages/ResearchHubPage';
import { KnowledgeBasePage } from '../pages/KnowledgeBasePage';
import { ProjectsPage } from '../pages/ProjectsPage';
import { SettingsPage } from '../pages/SettingsPage';

/**
 * Custom Fixtures for CommandCenter E2E Tests
 *
 * Provides page objects and utilities for all tests
 */

type CommandCenterFixtures = {
  dashboardPage: DashboardPage;
  radarPage: TechnologyRadarPage;
  researchPage: ResearchHubPage;
  knowledgePage: KnowledgeBasePage;
  projectsPage: ProjectsPage;
  settingsPage: SettingsPage;
};

export const test = base.extend<CommandCenterFixtures>({
  // Dashboard page fixture
  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  // Technology Radar page fixture
  radarPage: async ({ page }, use) => {
    const radarPage = new TechnologyRadarPage(page);
    await use(radarPage);
  },

  // Research Hub page fixture
  researchPage: async ({ page }, use) => {
    const researchPage = new ResearchHubPage(page);
    await use(researchPage);
  },

  // Knowledge Base page fixture
  knowledgePage: async ({ page }, use) => {
    const knowledgePage = new KnowledgeBasePage(page);
    await use(knowledgePage);
  },

  // Projects page fixture
  projectsPage: async ({ page }, use) => {
    const projectsPage = new ProjectsPage(page);
    await use(projectsPage);
  },

  // Settings page fixture
  settingsPage: async ({ page }, use) => {
    const settingsPage = new SettingsPage(page);
    await use(settingsPage);
  },
});

export { expect } from '@playwright/test';
