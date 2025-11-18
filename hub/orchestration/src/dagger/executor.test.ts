import { describe, it, expect } from 'vitest';
import { DaggerAgentExecutor } from './executor';

describe('DaggerAgentExecutor', () => {
  it('should create executor instance', () => {
    const executor = new DaggerAgentExecutor();
    expect(executor).toBeDefined();
    expect(executor.connect).toBeDefined();
    expect(executor.executeAgent).toBeDefined();
  });

  it('should throw if executing before connect', async () => {
    const executor = new DaggerAgentExecutor();
    await expect(
      executor.executeAgent('test.js', {}, {
        maxMemoryMb: 512,
        timeoutSeconds: 300,
        outputSchema: {},
      })
    ).rejects.toThrow('not connected');
  });
});
