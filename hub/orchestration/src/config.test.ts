import { describe, it, expect } from 'vitest';
import { config } from './config';

describe('config', () => {
  it('should have required configuration', () => {
    expect(config.databaseUrl).toBeDefined();
    expect(config.databaseUrl).not.toBe('');
  });

  it('should use defaults for optional config', () => {
    expect(config.port).toBe(9002);
    expect(config.agentDefaults.maxMemoryMb).toBe(512);
    expect(config.agentDefaults.timeoutSeconds).toBe(300);
  });

  it('should have NATS configuration', () => {
    expect(config.natsUrl).toBeDefined();
  });
});
