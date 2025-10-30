# Known Issues

## Test Failures (28 tests)

**Status**: IN PROGRESS - Partially Fixed
**Created**: 2025-10-29
**Priority**: HIGH

### Summary

After fixing ESLint type safety issues (commit `4ddc2a0`), 28 frontend tests are now failing due to mock configuration issues with fake timers.

### Affected Tests

**ResearchSummary.test.tsx** (7 failures):
- All tests timeout after 5 seconds
- Root cause: `vi.runAllTimersAsync()` creates infinite loop with `setInterval` in component
- Tests use fake timers but component has `setInterval(loadData, 10000)` recurring timer

**ResearchTaskList.test.tsx** (6 failures):
- Similar timer-related issues
- Needs mock setup fixes

**Other component tests** (15 failures):
- Various timer and mock-related issues

### Root Cause

Changed from:
```typescript
(researchApi.getResearchSummary as any).mockResolvedValue(...)
```

To:
```typescript
vi.mocked(researchApi.getResearchSummary).mockResolvedValue(...)
// Then changed to:
mockGetResearchSummary.mockResolvedValue(...)
```

The mock setup now correctly types the mocks but the interaction with fake timers needs adjustment.

### Attempted Fixes

1. ✅ Created proper mock constants: `const mockGetResearchSummary = researchApi.getResearchSummary as ReturnType<typeof vi.fn>`
2. ❌ Added `vi.runAllTimersAsync()` - caused infinite loops
3. ❌ Switched to `vi.advanceTimersByTimeAsync(0)` - still timing out

### Next Steps

**Option 1**: Use real timers for tests with intervals
```typescript
beforeEach(() => {
  vi.clearAllMocks();
  // Don't use fake timers for tests with setInterval
});
```

**Option 2**: Mock the setInterval behavior specifically
```typescript
beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: false });
});
```

**Option 3**: Refactor components to make intervals more testable
- Extract interval logic
- Make interval duration configurable for tests

### Impact

- ❌ 28 tests failing (110 passing)
- ❌ Cannot merge to main until fixed
- ✅ ESLint clean (0 warnings)
- ✅ Type safety improved

### Estimated Effort

- 1-2 hours to fix all timer-related test issues
- Requires understanding of vitest fake timer API
- May need component refactoring for better testability
