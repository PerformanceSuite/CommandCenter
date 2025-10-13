# E2E Testing - Quick Start Guide

Get up and running with CommandCenter E2E tests in 5 minutes.

## 🚀 Prerequisites

- Node.js 18+ installed
- CommandCenter services running (backend + frontend)

## 📦 Installation

```bash
cd e2e
npm install
npx playwright install --with-deps
```

## ▶️ Run Tests

### Start Services First

```bash
# From project root
make start

# Wait for services to be healthy
make health
```

### Run E2E Tests

```bash
cd e2e

# All tests with UI (recommended)
npm run test:ui

# All tests in terminal
npm test

# Single browser
npm run test:chromium

# Specific test file
npx playwright test tests/01-dashboard.spec.ts
```

## 📊 View Results

```bash
# Open HTML report
npm run report
```

## 🐛 Debug Failed Tests

```bash
# Run in debug mode
npm run test:debug

# Run in headed mode (see browser)
npm run test:headed
```

## 🎯 Common Commands

```bash
# Development
npm run test:ui          # Interactive UI mode
npm run test:headed      # Watch browser execution
npm run test:debug       # Step-by-step debugging
npm run codegen          # Record new tests

# Testing
npm test                 # Run all tests
npm run test:chromium    # Chromium only
npm run test:firefox     # Firefox only
npm run test:webkit      # WebKit (Safari) only
npm run test:mobile      # Mobile browsers

# Reports
npm run report           # View test report
```

## ⚙️ Configuration

Create `e2e/.env`:

```bash
BASE_URL=http://localhost:3000
API_URL=http://localhost:8000
```

## 📁 Project Structure

```
e2e/
├── pages/              # Page objects
├── tests/              # Test specs
├── fixtures/           # Custom fixtures
├── playwright.config.ts
└── README.md          # Full documentation
```

## 🆘 Troubleshooting

### Services Not Running
```bash
make start
curl http://localhost:8000/health
```

### Port Conflicts
```bash
# Kill processes
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Browser Not Found
```bash
npx playwright install --with-deps chromium
```

## 📚 Next Steps

1. Read full [E2E README](./README.md)
2. Explore test examples in `tests/`
3. Learn about [Page Objects](./pages/)
4. Review [CI/CD integration](./.github/workflows/e2e-tests.yml)

## 💡 Tips

- Use `test:ui` for development - it's interactive and visual
- Run `test:headed` to watch what Playwright is doing
- Tests are isolated - each runs independently
- Use `data-testid` attributes for stable selectors
- Check HTML report after test runs for detailed results

---

**Happy Testing! 🎉**
