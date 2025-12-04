import { z } from 'zod';

export const InputSchema = z.object({
  repositoryPath: z.string().describe('Path to repository'),
  patchType: z
    .enum([
      'dependency-update',
      'security-patch',
      'simple-refactor',
      'config-update',
    ])
    .describe('Type of patch to apply'),
  target: z.string().describe('Target file, package, or pattern to patch'),
  changes: z
    .object({
      oldValue: z.string().optional(),
      newValue: z.string().optional(),
      version: z.string().optional(),
      content: z.string().optional(),
    })
    .describe('Changes to apply'),
  dryRun: z.boolean().default(false).describe('Preview changes without applying'),
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
