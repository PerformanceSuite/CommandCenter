# CommandCenter E2E Testing Suite

Comprehensive end-to-end testing for CommandCenter using Playwright.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Page Objects](#page-objects)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

This E2E testing suite validates the complete CommandCenter application stack:

- **Frontend**: React 18 + TypeScript
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Real-time**: WebSocket connections

### Test Coverage

- ✅ Dashboard navigation and display
- ✅ Technology Radar (CRUD, visualization, filtering)
- ✅ Research Hub (task management, status updates)
- ✅ Knowledge Base (RAG search, document management)
- ✅ Settings (repository management)
- ✅ Async Jobs (creation, progress, WebSocket updates)
- ✅ Cross-browser compatibility (Chromium, Firefox, WebKit)
- ✅ Mobile responsiveness (iOS, Android)

## Features

### Multi-Browser Testing

Tests run across:
- **Desktop**: Chromium, Firefox, WebKit (Safari)
- **Mobile**: Chrome Mobile, Safari Mobile
- **Tablet**: iPad Pro

### Advanced Capabilities

- **Page Object Model**: Maintainable, reusable test code
- **Custom Fixtures**: Pre-configured page objects for all views
- **Real-time Testing**: WebSocket connection and message validation
- **API Testing**: Direct backend API validation
- **Visual Regression**: Screenshot comparison (optional)
- **Accessibility**: ARIA role validation

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (optional, for isolated testing)

### Installation

```bash
# Navigate to E2E directory
cd e2e

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install --with-deps
```

### Environment Configuration

Create `.env` file in `e2e/` directory:

```bash
BASE_URL=http://localhost:3000
API_URL=http://localhost:8000
CLEANUP_TEST_DATA=false  # Set to 'true' to clean up test data after tests
```

###Database Seeding

The E2E test suite automatically seeds the database with test data during global setup:

- **1 Test Project**: "E2E Test Project" for isolation
- **5 Technologies**: FastAPI, React, PostgreSQL, Celery, TypeScript
- **2 Repositories**: tiangolo/fastapi, facebook/react (metadata only)
- **2 Research Tasks**: Example tasks with various statuses

**Seeding Behavior**:
- Runs automatically before tests via `global-setup.ts`
- Skips seeding if data already exists
- Keeps data after tests (set `CLEANUP_TEST_DATA=true` to clean)

**Manual Seeding**:
```typescript
import { seedDatabase } from './utils/seed-data';

// In your test setup
await seedDatabase(context.request);
```

**Test Data Considerations**:
- Export tests expect analysis data (currently skip if missing - this is expected)
- Projects/Technologies tests use seeded data
- Tests are designed to skip gracefully when data is unavailable

## Running Tests

### Local Development

```bash
# Run all tests
npm test

# Run with UI mode (recommended for development)
npm run test:ui

# Run in headed mode (see browser)
npm run test:headed

# Debug mode
npm run test:debug

# Specific browser
npm run test:chromium
npm run test:firefox
npm run test:webkit

# Mobile tests
npm run test:mobile
```

### Specific Test Files

```bash
# Single test file
npx playwright test tests/01-dashboard.spec.ts

# Test suite
npx playwright test tests/02-technology-radar.spec.ts

# With specific browser
npx playwright test tests/01-dashboard.spec.ts --project=chromium
```

### With Services Running

**Option 1: Docker Compose (Recommended)**

```bash
# From project root
cd ..
make start

# Run E2E tests
cd e2e
npm test
```

**Option 2: Manual**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Celery Worker
cd backend
celery -A app.tasks worker --loglevel=info

# Terminal 3 - Frontend
cd frontend
npm run dev

# Terminal 4 - E2E Tests
cd e2e
npm test
```

## Test Structure

### Directory Layout

```
e2e/
├── fixtures/          # Custom Playwright fixtures
│   └── base.ts        # Base fixture with page objects
├── pages/             # Page Object Model classes
│   ├── BasePage.ts    # Abstract base class
│   ├── DashboardPage.ts
│   ├── TechnologyRadarPage.ts
│   ├── ResearchHubPage.ts
│   ├── KnowledgeBasePage.ts
│   ├── ProjectsPage.ts
│   └── SettingsPage.ts
├── tests/             # Test specifications
│   ├── 01-dashboard.spec.ts
│   ├── 02-technology-radar.spec.ts
│   ├── 03-research-hub.spec.ts
│   ├── 04-knowledge-base.spec.ts
│   ├── 05-settings.spec.ts
│   └── 06-async-jobs.spec.ts
├── global-setup.ts    # Pre-test setup (health checks)
├── global-teardown.ts # Post-test cleanup
├── playwright.config.ts
└── README.md
```

### Test Naming Convention

```
XX-feature-name.spec.ts
```

- `01-` = Dashboard/Core
- `02-` = Technology Radar
- `03-` = Research Hub
- `04-` = Knowledge Base
- `05-` = Settings
- `06-` = Async/Jobs

## Page Objects

### Why Page Objects?

- **Maintainability**: Update selectors in one place
- **Reusability**: Share page logic across tests
- **Readability**: Tests read like user actions
- **Type Safety**: Full TypeScript support

### Example Usage

```typescript
import { test, expect } from '../fixtures/base';

test('create technology', async ({ radarPage }) => {
  await radarPage.goto();

  await radarPage.createTechnology({
    title: 'React 19',
    domain: 'Languages & Frameworks',
    status: 'Adopt',
    relevance: 9,
  });

  const exists = await radarPage.verifyTechnologyExists('React 19');
  expect(exists).toBeTruthy();
});
```

### Creating New Page Objects

1. Extend `BasePage` class
2. Implement `goto()` and `waitForLoad()` methods
3. Define locators as getters
4. Add action methods
5. Add verification methods

```typescript
export class MyNewPage extends BasePage {
  get myElement(): Locator {
    return this.page.locator('[data-testid="my-element"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/my-route');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.myElement.waitFor({ state: 'visible' });
  }
}
```

## CI/CD Integration

### GitHub Actions

E2E tests run automatically on:
- Push to `main` or `develop`
- Pull requests
- Manual workflow dispatch

**Workflow**: `.github/workflows/e2e-tests.yml`

#### Features

- ✅ Matrix testing (Chromium, Firefox, WebKit)
- ✅ PostgreSQL & Redis service containers
- ✅ Parallel execution
- ✅ Automatic retries (2x on failure)
- ✅ HTML reports uploaded as artifacts
- ✅ Screenshots on failure
- ✅ JUnit XML for test reporting

### CI Environment

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env:
      POSTGRES_DB: commandcenter_test
      POSTGRES_USER: commandcenter
      POSTGRES_PASSWORD: testpassword

  redis:
    image: redis:7-alpine
```

### Viewing Results

1. Go to Actions tab in GitHub
2. Select E2E Tests workflow
3. Click on specific run
4. Download artifacts:
   - `playwright-results-{browser}` - HTML report
   - `playwright-screenshots-{browser}` - Failure screenshots

## Best Practices

### Writing Tests

#### ✅ DO

```typescript
// Use page objects
await dashboardPage.goto();
await dashboardPage.navigateToRadar();

// Wait for specific conditions
await radarPage.waitForLoadingComplete();

// Use meaningful assertions
expect(await radarPage.getTechnologyCount()).toBeGreaterThan(0);

// Use data-testid for stable selectors
await page.locator('[data-testid="submit-button"]').click();
```

#### ❌ DON'T

```typescript
// Don't use CSS selectors directly in tests
await page.locator('.btn.btn-primary').click();

// Don't use arbitrary waits
await page.waitForTimeout(5000);

// Don't make tests dependent on each other
test('test 2', async () => {
  // Assumes test 1 ran successfully ❌
});
```

### Test Organization

1. **One feature per file**: Group related tests together
2. **Use describe blocks**: Organize test suites logically
3. **beforeEach for navigation**: Navigate to page once per test
4. **Independent tests**: Each test should work in isolation
5. **Meaningful names**: Describe what the test does

### Performance

- **Parallel execution**: Tests run concurrently by default
- **Reuse authentication**: Store auth state between tests
- **Skip slow tests**: Use `test.skip()` for optional tests
- **Optimize waits**: Use `waitForLoadState()` instead of `waitForTimeout()`

### Debugging

```bash
# Run single test in debug mode
npx playwright test tests/01-dashboard.spec.ts --debug

# Use UI mode
npm run test:ui

# Generate test code
npm run codegen
```

## Troubleshooting

### Common Issues

#### Services Not Running

**Error**: `Error: connect ECONNREFUSED`

**Solution**:
```bash
# Start services
cd ..
make start

# Verify health
curl http://localhost:8000/health
curl http://localhost:3000
```

#### Browser Not Installed

**Error**: `Executable doesn't exist`

**Solution**:
```bash
npx playwright install --with-deps chromium
```

#### Port Already in Use

**Error**: `EADDRINUSE: address already in use`

**Solution**:
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

#### Test Timeout

**Error**: `Test timeout of 30000ms exceeded`

**Solution**:
```typescript
// Increase timeout for specific test
test('slow test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ... test code
});
```

#### Flaky Tests

**Symptoms**: Tests pass/fail intermittently

**Solutions**:
1. Add explicit waits: `waitForLoadingComplete()`
2. Use stable selectors: `data-testid` attributes
3. Avoid race conditions: Wait for network idle
4. Enable retries: Already configured in CI (2 retries)

### Debug Logs

```bash
# Enable debug logging
DEBUG=pw:api npm test

# Verbose output
npx playwright test --reporter=list

# Save trace
npx playwright test --trace on
```

### Test Reports

```bash
# View HTML report
npm run report

# Or manually
npx playwright show-report playwright-report
```

## Advanced Features

### Visual Regression Testing

```typescript
await expect(page).toHaveScreenshot('dashboard.png', {
  maxDiffPixels: 100
});
```

### API Testing Integration

```typescript
test('API health check', async ({ request }) => {
  const response = await request.get(`${apiURL}/health`);
  expect(response.ok()).toBeTruthy();
});
```

### WebSocket Testing

```typescript
test('WebSocket updates', async ({ page }) => {
  const messages: any[] = [];

  page.on('websocket', ws => {
    ws.on('framereceived', event => {
      messages.push(JSON.parse(event.payload));
    });
  });

  // Trigger action that sends WebSocket messages
  await page.click('[data-testid="start-job"]');

  // Wait and verify
  await page.waitForTimeout(2000);
  expect(messages.length).toBeGreaterThan(0);
});
```

### Custom Reporters

Add to `playwright.config.ts`:

```typescript
reporter: [
  ['html'],
  ['json', { outputFile: 'results.json' }],
  ['junit', { outputFile: 'junit.xml' }],
  ['./custom-reporter.ts'] // Your custom reporter
]
```

## Resources

- **Playwright Docs**: https://playwright.dev
- **CommandCenter Docs**: `../docs/`
- **API Reference**: `../docs/API.md`
- **Backend Tests**: `../backend/tests/integration/`

## Contributing

When adding new E2E tests:

1. Create/update page object in `pages/`
2. Add test spec in `tests/`
3. Update this README if adding new features
4. Ensure tests pass locally before PR
5. Verify CI pipeline passes

## License

MIT - See LICENSE file

---

**Need Help?** Open an issue or contact the development team.
