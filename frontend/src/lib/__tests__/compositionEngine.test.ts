import { describe, it, expect } from 'vitest';
import { determineLayout, CompositionContext, buildContext, generateAffordances, generateSummary } from '../compositionEngine';
import { ComposedQuery, EMPTY_QUERY } from '../../types/query';
import { GraphNode, GraphEdge } from '../../types/graph';

describe('compositionEngine', () => {
  describe('determineLayout', () => {
    it('returns graph for few entities with relationships', () => {
      const context: CompositionContext = {
        nodeCount: 50,
        edgeCount: 75,
        hasRelationships: true,
        entityTypes: ['project', 'repo', 'file'],
      };
      const query: ComposedQuery = { ...EMPTY_QUERY, presentation: { layout: 'auto' } };
      expect(determineLayout(query, context)).toBe('graph');
    });

    it('returns list for many entities without relationships', () => {
      const context: CompositionContext = {
        nodeCount: 200,
        edgeCount: 0,
        hasRelationships: false,
        entityTypes: ['symbol'],
      };
      const query: ComposedQuery = { ...EMPTY_QUERY, presentation: { layout: 'auto' } };
      expect(determineLayout(query, context)).toBe('list');
    });

    it('returns detail for single entity', () => {
      const context: CompositionContext = {
        nodeCount: 1,
        edgeCount: 0,
        hasRelationships: false,
        entityTypes: ['symbol'],
      };
      const query: ComposedQuery = { ...EMPTY_QUERY, presentation: { layout: 'auto' } };
      expect(determineLayout(query, context)).toBe('detail');
    });

    it('respects explicit layout hint', () => {
      const context: CompositionContext = {
        nodeCount: 50,
        edgeCount: 75,
        hasRelationships: true,
        entityTypes: ['project'],
      };
      const query: ComposedQuery = { ...EMPTY_QUERY, presentation: { layout: 'list' } };
      expect(determineLayout(query, context)).toBe('list');
    });

    it('returns dashboard for heterogeneous entity types', () => {
      const context: CompositionContext = {
        nodeCount: 150,
        edgeCount: 50,
        hasRelationships: true,
        entityTypes: ['project', 'service', 'task', 'spec'],
      };
      const query: ComposedQuery = { ...EMPTY_QUERY, presentation: { layout: 'auto' } };
      expect(determineLayout(query, context)).toBe('dashboard');
    });

    it('returns list for many entities with relationships', () => {
      const context: CompositionContext = {
        nodeCount: 150,
        edgeCount: 200,
        hasRelationships: true,
        entityTypes: ['symbol', 'file'],
      };
      const query: ComposedQuery = { ...EMPTY_QUERY, presentation: { layout: 'auto' } };
      expect(determineLayout(query, context)).toBe('list');
    });
  });

  describe('buildContext', () => {
    it('builds context from nodes and edges', () => {
      const nodes: GraphNode[] = [
        { id: 'project:1', entity_type: 'project', entity_id: 1, label: 'Project', metadata: {} },
        { id: 'repo:1', entity_type: 'repo', entity_id: 1, label: 'Repo', metadata: {} },
      ];
      const edges: GraphEdge[] = [
        { from_node: 'project:1', to_node: 'repo:1', type: 'contains' },
      ];
      const context = buildContext(nodes, edges);
      expect(context.nodeCount).toBe(2);
      expect(context.edgeCount).toBe(1);
      expect(context.hasRelationships).toBe(true);
      expect(context.entityTypes).toEqual(['project', 'repo']);
    });

    it('deduplicates entity types', () => {
      const nodes: GraphNode[] = [
        { id: 'symbol:1', entity_type: 'symbol', entity_id: 1, label: 'Fn1', metadata: {} },
        { id: 'symbol:2', entity_type: 'symbol', entity_id: 2, label: 'Fn2', metadata: {} },
      ];
      const context = buildContext(nodes, []);
      expect(context.entityTypes).toEqual(['symbol']);
    });
  });

  describe('generateSummary', () => {
    it('generates summary for empty results', () => {
      const context: CompositionContext = {
        nodeCount: 0,
        edgeCount: 0,
        hasRelationships: false,
        entityTypes: [],
      };
      expect(generateSummary(context, 'list')).toBe('No entities match the query.');
    });

    it('generates summary for single entity', () => {
      const context: CompositionContext = {
        nodeCount: 1,
        edgeCount: 0,
        hasRelationships: false,
        entityTypes: ['symbol'],
      };
      expect(generateSummary(context, 'detail')).toBe('Showing details for 1 symbol.');
    });

    it('generates summary with relationships', () => {
      const context: CompositionContext = {
        nodeCount: 50,
        edgeCount: 75,
        hasRelationships: true,
        entityTypes: ['project', 'repo'],
      };
      const summary = generateSummary(context, 'graph');
      expect(summary).toContain('50 entities');
      expect(summary).toContain('75 relationships');
      expect(summary).toContain('graph view');
    });
  });

  describe('generateAffordances', () => {
    it('generates drill_down for container types', () => {
      const nodes: GraphNode[] = [
        { id: 'project:1', entity_type: 'project', entity_id: 1, label: 'MyProject', metadata: {} },
      ];
      const affordances = generateAffordances(nodes, 'graph');
      const drillDown = affordances.find(a => a.action === 'drill_down');
      expect(drillDown).toBeDefined();
      expect(drillDown?.target.type).toBe('project');
    });

    it('generates view_dependencies for symbols', () => {
      const nodes: GraphNode[] = [
        { id: 'symbol:1', entity_type: 'symbol', entity_id: 1, label: 'myFunction', metadata: {} },
      ];
      const affordances = generateAffordances(nodes, 'graph');
      const viewDeps = affordances.find(a => a.action === 'view_dependencies');
      expect(viewDeps).toBeDefined();
    });

    it('limits affordances to first 10 nodes', () => {
      const nodes: GraphNode[] = Array.from({ length: 20 }, (_, i) => ({
        id: `symbol:${i}`,
        entity_type: 'symbol' as const,
        entity_id: i,
        label: `fn${i}`,
        metadata: {},
      }));
      const affordances = generateAffordances(nodes, 'list');
      // Each symbol gets ~4 affordances (view_deps, view_dependents, trigger_audit, create_task)
      // 10 nodes * 4 = ~40 affordances max
      expect(affordances.length).toBeLessThanOrEqual(50);
    });
  });
});
