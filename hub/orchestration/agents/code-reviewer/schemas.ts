import { z } from 'zod';

export const InputSchema = z.object({
  repositoryPath: z.string(),
  reviewType: z.enum(['quality', 'security', 'performance', 'all']).default('all'),
  filePattern: z.string().optional(),
});

export const IssueSchema = z.object({
  type: z.enum(['quality', 'security', 'performance', 'best-practice']),
  severity: z.enum(['info', 'warning', 'error']),
  file: z.string(),
  line: z.number(),
  description: z.string(),
  suggestion: z.string().optional(),
});

export const OutputSchema = z.object({
  issues: z.array(IssueSchema),
  summary: z.object({
    total: z.number(),
    errors: z.number(),
    warnings: z.number(),
    info: z.number(),
    filesReviewed: z.number(),
  }),
  metrics: z.object({
    avgComplexity: z.number(),
    maxComplexity: z.number(),
    totalLines: z.number(),
  }),
  reviewDurationMs: z.number(),
});

export type Input = z.infer<typeof InputSchema>;
export type Issue = z.infer<typeof IssueSchema>;
export type Output = z.infer<typeof OutputSchema>;
