import { z } from 'zod';

export const InputSchema = z.object({
  target: z.string().default('/workspace').describe('Path to repository'),
  operation: z
    .enum([
      'update-deps',
      'dependency-update',
      'security-patch',
      'simple-refactor',
      'config-update',
    ])
    .default('update-deps')
    .describe('Type of patch operation'),
  file: z.string().optional().describe('Target file or pattern to patch'),
  changes: z
    .object({
      oldValue: z.string().optional(),
      newValue: z.string().optional(),
      version: z.string().optional(),
      content: z.string().optional(),
    })
    .optional()
    .describe('Changes to apply'),
  dryRun: z.boolean().default(true).describe('Preview changes without applying'),
});

export const FileChangeSchema = z.object({
  file: z.string(),
  action: z.enum(['modified', 'created', 'deleted']),
  linesChanged: z.number().optional(),
  diff: z.string().optional(),
});

export const OutputSchema = z.object({
  applied: z.boolean(),
  changes: z.array(FileChangeSchema),
  summary: z.object({
    filesModified: z.number(),
    filesCreated: z.number(),
    filesDeleted: z.number(),
    totalLinesChanged: z.number(),
  }),
  patchDurationMs: z.number(),
  rollbackScript: z.string().optional(),
});

export type Input = z.infer<typeof InputSchema>;
export type FileChange = z.infer<typeof FileChangeSchema>;
export type Output = z.infer<typeof OutputSchema>;
