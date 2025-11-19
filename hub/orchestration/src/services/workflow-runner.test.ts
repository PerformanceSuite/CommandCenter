import { describe, it, expect } from 'vitest';
import { WorkflowRunner } from './workflow-runner';

describe('WorkflowRunner', () => {
  describe('topologicalSort', () => {
    it('should sort nodes with dependencies', () => {
      const runner = new WorkflowRunner(null as any, null as any);

      const nodes = [
        { id: 'c', dependsOn: ['a', 'b'] },
        { id: 'b', dependsOn: ['a'] },
        { id: 'a', dependsOn: [] },
      ];

      const sorted = runner['topologicalSort'](nodes as any);

      // Should return batches that can run in parallel
      expect(sorted[0].map(n => n.id)).toEqual(['a']);
      expect(sorted[1].map(n => n.id)).toEqual(['b']);
      expect(sorted[2].map(n => n.id)).toEqual(['c']);
    });

    it('should batch independent nodes together', () => {
      const runner = new WorkflowRunner(null as any, null as any);

      const nodes = [
        { id: 'a', dependsOn: [] },
        { id: 'b', dependsOn: [] },
        { id: 'c', dependsOn: ['a', 'b'] },
      ];

      const sorted = runner['topologicalSort'](nodes as any);

      // a and b can run in parallel
      expect(sorted[0].map(n => n.id).sort()).toEqual(['a', 'b']);
      expect(sorted[1].map(n => n.id)).toEqual(['c']);
    });
  });
});
