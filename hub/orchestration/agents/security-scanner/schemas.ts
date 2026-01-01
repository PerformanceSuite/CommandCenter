import { z } from 'zod';

export const InputSchema = z.object({
  target: z.string().describe('Path to repository to scan'),
  scanType: z.enum(['secrets', 'sql-injection', 'xss', 'all']).default('all'),
  severity: z.enum(['low', 'medium', 'high', 'critical']).optional(),
});

export const FindingSchema = z.object({
  type: z.string(),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  file: z.string(),
  line: z.number(),
  description: z.string(),
  code: z.string().optional(),
});

export const OutputSchema = z.object({
  findings: z.array(FindingSchema),
  summary: z.object({
    total: z.number(),
    critical: z.number(),
    high: z.number(),
    medium: z.number(),
    low: z.number(),
  }),
  scannedFiles: z.number(),
  scanDurationMs: z.number(),
});

export type Input = z.infer<typeof InputSchema>;
export type Finding = z.infer<typeof FindingSchema>;
export type Output = z.infer<typeof OutputSchema>;
