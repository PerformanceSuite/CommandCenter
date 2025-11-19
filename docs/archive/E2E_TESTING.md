# E2E Testing Guide

Comprehensive guide to end-to-end testing in CommandCenter.

## Overview

CommandCenter uses **Playwright** for end-to-end testing, providing comprehensive coverage of:
- User workflows across all views
- Real-time features (WebSocket)
- Async job processing
- Cross-browser compatibility
- Mobile responsiveness

## Quick Start

```bash
# Install dependencies
cd e2e
npm install
npx playwright install --with-deps

# Run tests
npm test

# UI mode (recommended for development)
npm run test:ui
```

See [`e2e/QUICK_START.md`](../e2e/QUICK_START.md) for detailed quick start guide.

## Test Architecture

### Page Object Model

All tests use the **Page Object Model** pattern for maintainability:

```
e2e/
├── pages/                  # Page object classes
│   ├── BasePage.ts        # Abstract base with common utilities
│   ├── DashboardPage.ts   # Dashboard page object
│   ├── TechnologyRadarPage.ts
│   ├── ResearchHubPage.ts
│   ├── KnowledgeBasePage.ts
│   ├── ProjectsPage.ts
│   └── SettingsPage.ts
├── tests/                  # Test specifications
│   ├── 01-dashboard.spec.ts
│   ├── 02-technology-radar.spec.ts
│   ├── 03-research-hub.spec.ts
│   ├── 04-knowledge-base.spec.ts
│   ├── 05-settings.spec.ts
│   └── 06-async-jobs.spec.ts
└── fixtures/               # Custom Playwright fixtures
    └── base.ts            # Fixture with all page objects
```

### Test Coverage

| Feature | Tests | Coverage |
|---------|-------|----------|
| **Dashboard** | 8 tests | Navigation, stats, responsiveness |
| **Technology Radar** | 9 tests | CRUD, filtering, search, visualization |
| **Research Hub** | 9 tests | Task management, status updates, filtering |
| **Knowledge Base** | 7 tests | RAG search, document management |
| **Settings** | 7 tests | Repository management, configuration |
| **Async Jobs** | 11 tests | Job lifecycle, WebSocket, API integration |
| **Total** | **51 tests** | Full application coverage |

## Running Tests

### Makefile Commands (Recommended)

```bash
# From project root
make test-e2e           # Run all E2E tests
make test-e2e-ui        # Interactive UI mode
make test-e2e-headed    # Watch browser execution
make test-e2e-debug     # Debug mode
make test-all           # Run unit + integration + E2E
```

### Direct Commands

```bash
cd e2e

# All tests
npm test

# Specific browser
npm run test:chromium
npm run test:firefox
npm run test:webkit

# Mobile
npm run test:mobile

# Specific test file
npx playwright test tests/01-dashboard.spec.ts

# Debug single test
npx playwright test tests/01-dashboard.spec.ts --debug
```

## Browser Coverage

### Desktop
- ✅ **Chromium** (Chrome, Edge)
- ✅ **Firefox**
- ✅ **WebKit** (Safari)

### Mobile
- ✅ **Chrome Mobile** (Pixel 5)
- ✅ **Safari Mobile** (iPhone 13)

### Tablet
- ✅ **iPad Pro**

## Writing Tests

### Example Test

```typescript
import { test, expect } from '../fixtures/base';

test.describe('Technology Radar', () => {
  test('should create a new technology', async ({ radarPage }) => {
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
});
```

### Best Practices

**✅ DO:**
- Use page objects for all interactions
- Use `data-testid` attributes for stable selectors
- Wait for loading states: `waitForLoadingComplete()`
- Make tests independent (no dependencies between tests)
- Use meaningful test names and descriptions

**❌ DON'T:**
- Don't use direct CSS selectors in tests
- Don't use `waitForTimeout()` unless necessary
- Don't make tests depend on execution order
- Don't hardcode URLs (use `baseURL` from config)

### Creating Page Objects

1. Extend `BasePage` class
2. Implement required methods: `goto()`, `waitForLoad()`
3. Define locators as getters
4. Add action methods (clicks, fills, etc.)
5. Add verification methods

```typescript
export class MyPage extends BasePage {
  get myButton(): Locator {
    return this.page.locator('[data-testid="my-button"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/my-route');
    await this.waitForLoad();
  }

  async waitForLoad(): Promise<void> {
    await this.myButton.waitFor({ state: 'visible' });
  }

  async clickMyButton(): Promise<void> {
    await this.myButton.click();
    await this.waitForLoadingComplete();
  }
}
```

## CI/CD Integration

### GitHub Actions

E2E tests run automatically on:
- ✅ Push to `main` or `develop`
- ✅ Pull requests
- ✅ Manual trigger

**Workflow:** `.github/workflows/e2e-tests.yml`

### CI Features

- **Multi-browser matrix**: Chromium, Firefox, WebKit
- **Service containers**: PostgreSQL 16, Redis 7
- **Parallel execution**: Tests run concurrently
- **Automatic retries**: 2 retries on failure
- **Artifacts**: HTML reports + screenshots on failure
- **Test reporting**: JUnit XML integration

### CI Environment

```yaml
services:
  postgres:
    image: postgres:16-alpine
  redis:
    image: redis:7-alpine
```

### Viewing CI Results

1. Go to GitHub Actions tab
2. Select "E2E Tests" workflow
3. View test results by browser
4. Download artifacts (reports/screenshots)

## Advanced Features

### WebSocket Testing

```typescript
test('should receive progress updates', async ({ page }) => {
  const messages: any[] = [];

  page.on('websocket', ws => {
    ws.on('framereceived', event => {
      messages.push(JSON.parse(event.payload));
    });
  });

  // Trigger action that sends WebSocket messages
  await page.click('[data-testid="start-job"]');

  await page.waitForTimeout(2000);
  expect(messages.length).toBeGreaterThan(0);
});
```

### API Testing

```typescript
test('should create job via API', async ({ request }) => {
  const response = await request.post('/api/v1/jobs', {
    data: { job_type: 'analyze_repository' }
  });

  expect(response.ok()).toBeTruthy();
  const job = await response.json();
  expect(job).toHaveProperty('id');
});
```

### Visual Regression

```typescript
test('should match screenshot', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('dashboard.png', {
    maxDiffPixels: 100
  });
});
```

## Debugging

### UI Mode (Recommended)

```bash
npm run test:ui
```

**Features:**
- ✅ Interactive test explorer
- ✅ Time travel debugging
- ✅ Watch mode
- ✅ Network inspection

### Debug Mode

```bash
npm run test:debug
```

**Features:**
- ✅ Step through tests
- ✅ Inspect elements
- ✅ Console output
- ✅ Pause on failure

### Headed Mode

```bash
npm run test:headed
```

Watch browser execute tests in real-time.

### Debug Logs

```bash
# Enable verbose logging
DEBUG=pw:api npm test

# Show detailed output
npx playwright test --reporter=list
```

## Troubleshooting

### Services Not Running

**Error:** `connect ECONNREFUSED`

**Solution:**
```bash
make start
make health
```

### Port Already in Use

**Error:** `EADDRINUSE`

**Solution:**
```bash
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Browser Not Installed

**Error:** `Executable doesn't exist`

**Solution:**
```bash
npx playwright install --with-deps chromium
```

### Flaky Tests

**Solutions:**
1. Add explicit waits: `waitForLoadingComplete()`
2. Use stable selectors: `data-testid`
3. Wait for network idle
4. Enable retries (already configured)

### Test Timeout

Increase timeout for slow tests:

```typescript
test('slow operation', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // ... test code
});
```

## Performance

### Parallel Execution

Tests run in parallel by default:
- **Local**: Uses all available CPU cores
- **CI**: 2 workers (configurable)

### Optimization Tips

1. **Reuse browser contexts**: Share setup between tests
2. **Skip unnecessary waits**: Use `networkidle` judiciously
3. **Parallelize test files**: Keep tests independent
4. **Use fixtures**: Share page objects efficiently

## Test Reports

### HTML Report

```bash
npm run report
```

Opens interactive HTML report with:
- Test results by browser
- Screenshots and videos
- Trace files for debugging
- Network logs

### JSON Report

```json
{
  "suites": [...],
  "tests": [...],
  "errors": [...]
}
```

Located at: `e2e/playwright-report/results.json`

### JUnit XML

For CI integration:
- Location: `e2e/playwright-report/junit.xml`
- Compatible with: Jenkins, GitLab CI, GitHub Actions

## Configuration

### `playwright.config.ts`

```typescript
export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
```

### Environment Variables

Create `e2e/.env`:

```bash
BASE_URL=http://localhost:3000
API_URL=http://localhost:8000
```

## Statistics

### Test Suite Size

- **Total Tests**: 51
- **Page Objects**: 7
- **Test Files**: 6
- **Lines of Code**: ~3,500
- **Execution Time**: ~3-5 minutes (parallel)

### Coverage

- ✅ **Views**: 6/6 (100%)
- ✅ **Core Workflows**: Complete
- ✅ **API Endpoints**: Key endpoints covered
- ✅ **WebSocket**: Real-time features tested
- ✅ **Mobile**: iOS + Android emulation

## Resources

### Documentation
- [Full E2E README](../e2e/README.md)
- [Quick Start Guide](../e2e/QUICK_START.md)
- [Playwright Docs](https://playwright.dev)

### Related Docs
- [Backend Integration Tests](./INTEGRATION_TESTING.md)
- [Frontend Testing](../frontend/README.md#testing)
- [API Documentation](./API.md)

## Contributing

When adding E2E tests:

1. ✅ Create/update page object
2. ✅ Add test spec with meaningful names
3. ✅ Ensure tests pass locally
4. ✅ Verify CI pipeline passes
5. ✅ Update documentation if needed

## Support

- **Issues**: [GitHub Issues](https://github.com/yourorg/commandcenter/issues)
- **Documentation**: `docs/` directory
- **Team**: Contact development team

---

**Happy Testing! 🎭**
