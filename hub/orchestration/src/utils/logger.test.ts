import { describe, it, expect } from 'vitest';
import logger from './logger';

describe('logger', () => {
  it('should export winston logger instance', () => {
    expect(logger).toBeDefined();
    expect(logger.info).toBeDefined();
    expect(logger.error).toBeDefined();
  });
});
