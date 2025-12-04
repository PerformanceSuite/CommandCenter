import { z } from 'zod';

export const InputSchema = z.object({
  repositoryPath: z.string().describe('Path to repository to check'),
  rules: z
    .array(z.enum(['licenses', 'security-headers', 'secrets', 'all']))
    .default(['all'])
    .describe('Compliance rules to check'),
  strictMode: z.boolean().default(false).describe('Fail on any violation'),
});

export const ViolationSchema = z.object({
  rule: z.string(),
  severity: z.enum(['info', 'warning', 'critical']),
  file: z.string(),
  line: z.number().optional(),
  message: z.string(),
  remediation: z.string().optional(),
});

export const OutputSchema = z.object({
  violations: z.array(ViolationSchema),
  summary: z.object({
    total: z.number(),
    critical: z.number(),
    warning: z.number(),
    info: z.number(),
    passed: z.boolean(),
  }),
  checkedFiles: z.number(),
  checkDurationMs: z.number(),
  rulesApplied: z.array(z.string()),
});

export type Input = z.infer<typeof InputSchema>;
export type Violation = z.infer<typeof ViolationSchema>;
export type Output = z.infer<typeof OutputSchema>;
