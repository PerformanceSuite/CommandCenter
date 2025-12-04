# P0-1: Add Output Schema Validation to Dagger Executor

## Objective
Add Zod validation for agent outputs in the Dagger executor to prevent runtime errors from unvalidated data.

## File to Modify
`hub/orchestration/src/dagger/executor.ts`

## Task

1. **Find the TODO comment** at approximately line 70:
   ```typescript
   // TODO: Validate against outputSchema using Zod
   ```

2. **Implement Zod validation**:
   - Import Zod if not already imported
   - Create a validation function that takes output and schema
   - Wrap the output parsing in proper error handling
   - Throw a descriptive `AgentOutputValidationError` on failure

3. **Example implementation**:
   ```typescript
   import { z } from 'zod';

   class AgentOutputValidationError extends Error {
     constructor(public errors: z.ZodError) {
       super(`Agent output validation failed: ${errors.message}`);
       this.name = 'AgentOutputValidationError';
     }
   }

   const validateAgentOutput = <T>(output: unknown, schema: z.ZodSchema<T>): T => {
     const result = schema.safeParse(output);
     if (!result.success) {
       throw new AgentOutputValidationError(result.error);
     }
     return result.data;
   };
   ```

4. **Apply the validation** where agent outputs are processed

5. **Add tests** for the validation:
   - Test valid output passes
   - Test invalid output throws AgentOutputValidationError
   - Test edge cases (null, undefined, wrong types)

## Acceptance Criteria
- [ ] TODO comment removed
- [ ] Zod validation implemented
- [ ] AgentOutputValidationError class created
- [ ] Tests added and passing
- [ ] No TypeScript errors

## Branch Name
`fix/p0-output-schema-validation`

## After Completion
1. Commit changes with message: `fix(orchestration): Add Zod output schema validation`
2. Push branch to origin
3. Do NOT create PR (will be done by orchestrator)
