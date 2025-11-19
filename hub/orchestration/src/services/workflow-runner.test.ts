import { describe, it, expect, beforeEach } from 'vitest';
import { WorkflowRunner } from './workflow-runner';
import { PrismaClient } from '@prisma/client';
import { DaggerAgentExecutor } from '../dagger/executor';
import { NatsClient } from '../events/nats-client';

describe('WorkflowRunner - Template Resolution', () => {
  let workflowRunner: WorkflowRunner;
  let mockPrisma: any;
  let mockDaggerExecutor: any;
  let mockNatsClient: any;

  beforeEach(() => {
    mockPrisma = {} as PrismaClient;
    mockDaggerExecutor = {} as DaggerAgentExecutor;
    mockNatsClient = {} as NatsClient;

    workflowRunner = new WorkflowRunner(
      mockPrisma,
      mockDaggerExecutor,
      mockNatsClient
    );
  });

  describe('resolveInputs', () => {
    it('should resolve simple context variables', () => {
      const node = {
        id: 'node-1',
        inputsJson: {
          filePath: '{{ context.filePath }}',
          repository: '{{ context.repository }}',
        },
      } as any;

      const context = {
        filePath: '/src/auth/login.ts',
        repository: 'CommandCenter',
      };

      const previousOutputs = new Map();

      const result = (workflowRunner as any).resolveInputs(
        node,
        context,
        previousOutputs
      );

      expect(result).toEqual({
        filePath: '/src/auth/login.ts',
        repository: 'CommandCenter',
      });
    });

    it('should resolve nested context variables', () => {
      const node = {
        id: 'node-1',
        inputsJson: {
          threshold: '{{ context.config.security.threshold }}',
          level: '{{ context.config.level }}',
        },
      } as any;

      const context = {
        config: {
          security: {
            threshold: 75,
          },
          level: 'high',
        },
      };

      const previousOutputs = new Map();

      const result = (workflowRunner as any).resolveInputs(
        node,
        context,
        previousOutputs
      );

      expect(result).toEqual({
        threshold: 75,
        level: 'high',
      });
    });

    it('should resolve node output variables', () => {
      const node = {
        id: 'notify-node',
        inputsJson: {
          severity: '{{ nodes.scan-node.output.severity }}',
          count: '{{ nodes.scan-node.output.vulnerabilityCount }}',
        },
      } as any;

      const context = {};
      const previousOutputs = new Map([
        [
          'scan-node',
          {
            severity: 'HIGH',
            vulnerabilityCount: 3,
            findings: [],
          },
        ],
      ]);

      const result = (workflowRunner as any).resolveInputs(
        node,
        context,
        previousOutputs
      );

      expect(result).toEqual({
        severity: 'HIGH',
        count: 3,
      });
    });

    it('should mix context and node output variables', () => {
      const node = {
        id: 'notify-node',
        inputsJson: {
          message:
            'Found {{ nodes.scan-node.output.count }} issues in {{ context.filePath }}',
          severity: '{{ nodes.scan-node.output.severity }}',
          repository: '{{ context.repository }}',
        },
      } as any;

      const context = {
        filePath: '/src/auth/login.ts',
        repository: 'CommandCenter',
      };

      const previousOutputs = new Map([
        [
          'scan-node',
          {
            count: 5,
            severity: 'HIGH',
          },
        ],
      ]);

      const result = (workflowRunner as any).resolveInputs(
        node,
        context,
        previousOutputs
      );

      expect(result).toEqual({
        message: 'Found 5 issues in /src/auth/login.ts',
        severity: 'HIGH',
        repository: 'CommandCenter',
      });
    });

    it('should preserve types (numbers, booleans)', () => {
      const node = {
        id: 'node-1',
        inputsJson: {
          threshold: '{{ context.threshold }}',
          enabled: '{{ context.enabled }}',
          count: '{{ nodes.counter.output.count }}',
        },
      } as any;

      const context = {
        threshold: 100,
        enabled: true,
      };

      const previousOutputs = new Map([
        ['counter', { count: 42 }],
      ]);

      const result = (workflowRunner as any).resolveInputs(
        node,
        context,
        previousOutputs
      );

      expect(result).toEqual({
        threshold: 100,
        enabled: true,
        count: 42,
      });

      expect(typeof result.threshold).toBe('number');
      expect(typeof result.enabled).toBe('boolean');
      expect(typeof result.count).toBe('number');
    });

    it('should keep original template if value not found', () => {
      const node = {
        id: 'node-1',
        inputsJson: {
          value: '{{ context.nonExistent }}',
        },
      } as any;

      const context = {};
      const previousOutputs = new Map();

      const result = (workflowRunner as any).resolveInputs(
        node,
        context,
        previousOutputs
      );

      expect(result).toEqual({
        value: '{{ context.nonExistent }}',
      });
    });
  });

  describe('getNestedValue', () => {
    it('should get simple property', () => {
      const obj = { name: 'John' };
      const result = (workflowRunner as any).getNestedValue(obj, 'name');
      expect(result).toBe('John');
    });

    it('should get nested property', () => {
      const obj = { user: { profile: { name: 'John' } } };
      const result = (workflowRunner as any).getNestedValue(
        obj,
        'user.profile.name'
      );
      expect(result).toBe('John');
    });

    it('should return undefined for non-existent path', () => {
      const obj = { user: { name: 'John' } };
      const result = (workflowRunner as any).getNestedValue(
        obj,
        'user.age'
      );
      expect(result).toBeUndefined();
    });

    it('should handle array access', () => {
      const obj = { items: ['a', 'b', 'c'] };
      const result = (workflowRunner as any).getNestedValue(obj, 'items.0');
      expect(result).toBe('a');
    });
  });
});
