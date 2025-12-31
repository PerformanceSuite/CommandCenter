import { describe, it, expect } from 'vitest';
import { parseQueryFromParams, serializeQueryToParams } from '../queryParser';
import { ComposedQuery, EMPTY_QUERY } from '../../types/query';

describe('queryParser', () => {
  describe('parseQueryFromParams', () => {
    it('returns empty query for no params', () => {
      const params = new URLSearchParams();
      const query = parseQueryFromParams(params);
      expect(query.entities).toEqual([]);
      expect(query.filters).toEqual([]);
    });

    it('parses single entity selector', () => {
      const params = new URLSearchParams('entity=project:123');
      const query = parseQueryFromParams(params);
      expect(query.entities).toHaveLength(1);
      expect(query.entities[0]).toEqual({
        type: 'project',
        id: 123,
      });
    });

    it('parses multiple entity selectors', () => {
      const params = new URLSearchParams('entity=project:1&entity=repo:2');
      const query = parseQueryFromParams(params);
      expect(query.entities).toHaveLength(2);
    });

    it('parses layout presentation hint', () => {
      const params = new URLSearchParams('layout=list');
      const query = parseQueryFromParams(params);
      expect(query.presentation.layout).toBe('list');
    });

    it('parses depth parameter', () => {
      const params = new URLSearchParams('depth=3');
      const query = parseQueryFromParams(params);
      expect(query.relationships[0]?.depth).toBe(3);
    });

    it('parses filter parameters', () => {
      const params = new URLSearchParams('filter.language=python');
      const query = parseQueryFromParams(params);
      expect(query.filters).toHaveLength(1);
      expect(query.filters[0]).toEqual({
        field: 'language',
        operator: 'eq',
        value: 'python',
      });
    });

    it('parses filter with in operator', () => {
      const params = new URLSearchParams('filter.status__in=active,pending');
      const query = parseQueryFromParams(params);
      expect(query.filters).toHaveLength(1);
      expect(query.filters[0]).toEqual({
        field: 'status',
        operator: 'in',
        value: ['active', 'pending'],
      });
    });

    it('parses entity with projectId scope', () => {
      const params = new URLSearchParams('entity=file:42:1');
      const query = parseQueryFromParams(params);
      expect(query.entities[0]).toEqual({
        type: 'file',
        id: 42,
        projectId: 1,
      });
    });

    it('parses graphDirection parameter', () => {
      const params = new URLSearchParams('direction=LR');
      const query = parseQueryFromParams(params);
      expect(query.presentation.graphDirection).toBe('LR');
    });

    it('parses numeric filter values', () => {
      const params = new URLSearchParams('filter.count__gt=5');
      const query = parseQueryFromParams(params);
      expect(query.filters[0]).toEqual({
        field: 'count',
        operator: 'gt',
        value: 5,
      });
    });

    it('parses boolean filter values', () => {
      const params = new URLSearchParams('filter.active=true');
      const query = parseQueryFromParams(params);
      expect(query.filters[0]).toEqual({
        field: 'active',
        operator: 'eq',
        value: true,
      });
    });

    it('parses pagination parameters', () => {
      const params = new URLSearchParams('limit=50&offset=100');
      const query = parseQueryFromParams(params);
      expect(query.limit).toBe(50);
      expect(query.offset).toBe(100);
    });

    it('parses relationship direction', () => {
      const params = new URLSearchParams('rel_direction=outbound');
      const query = parseQueryFromParams(params);
      expect(query.relationships[0]?.direction).toBe('outbound');
    });
  });

  describe('serializeQueryToParams', () => {
    it('serializes empty query to empty params', () => {
      const params = serializeQueryToParams(EMPTY_QUERY);
      expect(params.toString()).toBe('');
    });

    it('serializes entity selector', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        entities: [{ type: 'project', id: 123 }],
      };
      const params = serializeQueryToParams(query);
      expect(params.get('entity')).toBe('project:123');
    });

    it('serializes multiple entities', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        entities: [
          { type: 'project', id: 1 },
          { type: 'repo', id: 2 },
        ],
      };
      const params = serializeQueryToParams(query);
      expect(params.getAll('entity')).toEqual(['project:1', 'repo:2']);
    });

    it('serializes entity with projectId', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        entities: [{ type: 'file', id: 42, projectId: 1 }],
      };
      const params = serializeQueryToParams(query);
      expect(params.get('entity')).toBe('file:42:1');
    });

    it('serializes filters with eq operator', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        filters: [{ field: 'language', operator: 'eq', value: 'python' }],
      };
      const params = serializeQueryToParams(query);
      expect(params.get('filter.language')).toBe('python');
    });

    it('serializes filters with in operator', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        filters: [{ field: 'status', operator: 'in', value: ['active', 'pending'] }],
      };
      const params = serializeQueryToParams(query);
      expect(params.get('filter.status__in')).toBe('active,pending');
    });

    it('serializes layout presentation', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        presentation: { ...EMPTY_QUERY.presentation, layout: 'graph' },
      };
      const params = serializeQueryToParams(query);
      expect(params.get('layout')).toBe('graph');
    });

    it('serializes pagination', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        limit: 25,
        offset: 50,
      };
      const params = serializeQueryToParams(query);
      expect(params.get('limit')).toBe('25');
      expect(params.get('offset')).toBe('50');
    });

    it('roundtrips complex query', () => {
      const original: ComposedQuery = {
        entities: [{ type: 'project', id: 1 }],
        filters: [{ field: 'language', operator: 'eq', value: 'python' }],
        relationships: [{ type: 'dependsOn', direction: 'outbound', depth: 2 }],
        presentation: { layout: 'graph', graphDirection: 'LR', sortOrder: 'asc' },
      };
      const params = serializeQueryToParams(original);
      const parsed = parseQueryFromParams(params);
      expect(parsed.entities).toEqual(original.entities);
      expect(parsed.presentation.layout).toBe('graph');
    });

    it('omits default values from params', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        presentation: { ...EMPTY_QUERY.presentation, layout: 'auto', graphDirection: 'TB' },
      };
      const params = serializeQueryToParams(query);
      expect(params.has('layout')).toBe(false);
      expect(params.has('direction')).toBe(false);
    });

    it('serializes relationship depth', () => {
      const query: ComposedQuery = {
        ...EMPTY_QUERY,
        relationships: [{ type: 'dependsOn', direction: 'both', depth: 3 }],
      };
      const params = serializeQueryToParams(query);
      expect(params.get('depth')).toBe('3');
    });
  });
});
