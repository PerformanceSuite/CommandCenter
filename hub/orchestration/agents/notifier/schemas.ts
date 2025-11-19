import { z } from 'zod';

export const InputSchema = z.object({
  channel: z.enum(['slack', 'discord', 'console']),
  message: z.string(),
  severity: z.enum(['info', 'warning', 'error', 'critical']).default('info'),
  metadata: z.record(z.unknown()).optional(),
  webhookUrl: z.string().url().optional(),
});

export const OutputSchema = z.object({
  success: z.boolean(),
  channel: z.string(),
  messageId: z.string().optional(),
  timestamp: z.string(),
  error: z.string().optional(),
});

export type Input = z.infer<typeof InputSchema>;
export type Output = z.infer<typeof OutputSchema>;
