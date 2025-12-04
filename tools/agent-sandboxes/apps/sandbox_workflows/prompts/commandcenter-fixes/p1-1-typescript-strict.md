# P1-1: TypeScript Strict Mode and Type Safety

## Objective
Enable TypeScript strict mode and replace `any`/`unknown` types with proper types in the hub orchestration service.

## Files to Modify
- `hub/orchestration/tsconfig.json`
- All `.ts` files in `hub/orchestration/src/`

## Task

1. **Enable strict mode** in tsconfig.json:
   ```json
   {
     "compilerOptions": {
       "strict": true,
       "noImplicitAny": true,
       "strictNullChecks": true,
       "strictFunctionTypes": true,
       "strictBindCallApply": true,
       "strictPropertyInitialization": true,
       "noImplicitThis": true,
       "alwaysStrict": true
     }
   }
   ```

2. **Find all `any` usages**:
   ```bash
   grep -r ": any" hub/orchestration/src/ --include="*.ts"
   grep -r "as any" hub/orchestration/src/ --include="*.ts"
   ```

3. **Replace with proper types**:
   - Define interfaces for API responses
   - Use generics where appropriate
   - Add type guards for runtime checks
   - Use `unknown` with type narrowing instead of `any`

4. **Common patterns to fix**:
   ```typescript
   // BEFORE
   const data: any = await response.json();

   // AFTER
   interface ApiResponse {
     status: string;
     data: WorkflowResult;
   }
   const data: ApiResponse = await response.json();
   ```

5. **Run type check** to find remaining issues:
   ```bash
   cd hub/orchestration && npx tsc --noEmit
   ```

6. **Fix all type errors** until clean compilation

## Acceptance Criteria
- [ ] strict: true in tsconfig.json
- [ ] Zero `any` types in production code (test files may have some)
- [ ] npx tsc --noEmit passes with no errors
- [ ] All existing tests still pass

## Branch Name
`fix/p1-typescript-strict`

## After Completion
1. Commit changes with message: `fix(orchestration): Enable TypeScript strict mode, replace any types`
2. Push branch to origin
3. Do NOT create PR (will be done by orchestrator)
