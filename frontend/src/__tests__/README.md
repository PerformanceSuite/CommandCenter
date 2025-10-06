# Frontend Test Suite

## Overview

Comprehensive test suite for the CommandCenter frontend using Vitest and React Testing Library, achieving 80%+ code coverage.

## Test Structure

```
src/
├── tests/
│   ├── setup.ts            # Test setup and global mocks
│   └── utils.tsx           # Test utilities and helpers
└── __tests__/
    ├── components/         # Component tests
    ├── hooks/             # Custom hook tests
    └── services/          # API service tests
```

## Running Tests

### Run All Tests
```bash
npm test
```

### Run with Coverage
```bash
npm run test:coverage
```

### Run with UI
```bash
npm run test:ui
```

### Watch Mode
```bash
npm test -- --watch
```

### Run Specific Test File
```bash
npm test -- src/__tests__/components/LoadingSpinner.test.tsx
```

## Test Configuration

### Vitest Config (vitest.config.ts)
- Environment: jsdom
- Coverage Provider: v8
- Coverage Threshold: 80%
- Setup Files: src/tests/setup.ts

### Test Setup (src/tests/setup.ts)
- React Testing Library cleanup
- jest-dom matchers
- Window.matchMedia mock
- IntersectionObserver mock

## Test Utilities

### Custom Render with Router
```tsx
import { renderWithRouter } from '../../tests/utils';

renderWithRouter(<MyComponent />);
```

### Mock Data Generators
```tsx
import { mockRepository, mockTechnology, mockResearchTask } from '../../tests/utils';

const repo = mockRepository({ name: 'custom-name' });
const tech = mockTechnology({ title: 'Python' });
```

### API Mock Helper
```tsx
import { createMockApiResponse } from '../../tests/utils';

const response = createMockApiResponse(data, 200);
```

## Coverage Goals

- **Overall Coverage**: 80%+
- **Components**: 85%+
- **Hooks**: 90%+
- **Services**: 85%+
- **Utils**: 80%+

## Test Categories

### Component Tests
- Rendering and display
- User interactions
- Props validation
- Conditional rendering
- Error states
- Loading states

### Hook Tests
- State management
- Side effects
- Error handling
- Async operations
- Return values

### Service Tests
- API calls
- Request/response handling
- Error handling
- Interceptors

## Testing Best Practices

1. **User-Centric**: Test from user's perspective
2. **Accessible Queries**: Use accessible queries (getByRole, getByLabelText)
3. **Async Handling**: Use waitFor for async operations
4. **Cleanup**: Automatic cleanup after each test
5. **Mocking**: Mock external dependencies (API, router)

## Common Patterns

### Testing User Interactions
```tsx
import { fireEvent, screen } from '@testing-library/react';

const button = screen.getByRole('button', { name: /submit/i });
fireEvent.click(button);
```

### Testing Async Operations
```tsx
import { waitFor } from '@testing-library/react';

await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});
```

### Testing Hooks
```tsx
import { renderHook, waitFor } from '@testing-library/react';

const { result } = renderHook(() => useMyHook());

await waitFor(() => {
  expect(result.current.loading).toBe(false);
});
```

### Mocking API Calls
```tsx
import { vi } from 'vitest';
import { api } from '../../services/api';

vi.mock('../../services/api');
vi.mocked(api.getRepositories).mockResolvedValue(mockData);
```

## CI/CD Integration

Tests run automatically on:
- Push to main branch
- Pull request creation
- Pre-commit hooks

Coverage reports generated in:
- Terminal output
- HTML report: coverage/index.html
- XML report: coverage/coverage.xml

## Troubleshooting

### Mock Issues
- Clear mocks with `vi.clearAllMocks()` in beforeEach
- Verify mock paths are correct
- Check that vi.mocked() is used for TypeScript

### Async Test Failures
- Use waitFor for async state changes
- Check that promises are awaited
- Verify setTimeout/setInterval are handled

### Router Issues
- Use renderWithRouter for components with routing
- Mock useNavigate and useParams as needed

### Coverage Gaps
- Check coverage report: coverage/index.html
- Add tests for uncovered branches
- Test error paths and edge cases
