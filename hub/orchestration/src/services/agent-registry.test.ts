import { describe, it, expect } from 'vitest';
import { AgentRegistry } from './agent-registry';

describe('AgentRegistry', () => {
  it('should create AgentRegistry instance', () => {
    const mockPrisma = {} as any;
    const registry = new AgentRegistry(mockPrisma);

    expect(registry).toBeDefined();
    expect(registry.register).toBeDefined();
    expect(registry.listByProject).toBeDefined();
    expect(registry.getById).toBeDefined();
    expect(registry.update).toBeDefined();
    expect(registry.delete).toBeDefined();
  });
});
