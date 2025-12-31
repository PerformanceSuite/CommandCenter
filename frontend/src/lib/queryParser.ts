/**
 * Query Parser - Converts URL params to/from ComposedQuery
 *
 * URL format:
 *   ?entity=project:123&entity=repo:456
 *   &filter.language=python&filter.status=active
 *   &layout=graph&depth=2&direction=LR
 */

import {
  ComposedQuery,
  EntitySelector,
  Filter,
  RelationshipSpec,
  PresentationHint,
  LayoutType,
  DEFAULT_PRESENTATION,
  FilterOperator,
} from '../types/query';
import { EntityType, EdgeType } from '../types/graph';

// ============================================================================
// Parse URL Params -> ComposedQuery
// ============================================================================

export function parseQueryFromParams(params: URLSearchParams): ComposedQuery {
  const entities = parseEntities(params);
  const filters = parseFilters(params);
  const relationships = parseRelationships(params);
  const presentation = parsePresentation(params);
  const limit = params.get('limit') ? parseInt(params.get('limit')!, 10) : undefined;
  const offset = params.get('offset') ? parseInt(params.get('offset')!, 10) : undefined;

  return {
    entities,
    filters,
    relationships,
    presentation,
    limit,
    offset,
  };
}

function parseEntities(params: URLSearchParams): EntitySelector[] {
  const entityParams = params.getAll('entity');
  return entityParams.map(parseEntityString).filter(Boolean) as EntitySelector[];
}

function parseEntityString(str: string): EntitySelector | null {
  // Format: "type:id" or "type:id:projectId" or just "type"
  const parts = str.split(':');
  if (parts.length === 0) return null;

  const type = parts[0] as EntityType;
  const id = parts[1] ? parseInt(parts[1], 10) : undefined;
  const projectId = parts[2] ? parseInt(parts[2], 10) : undefined;

  return { type, id, projectId };
}

function parseFilters(params: URLSearchParams): Filter[] {
  const filters: Filter[] = [];

  for (const [key, value] of params.entries()) {
    if (key.startsWith('filter.')) {
      const field = key.replace('filter.', '');
      // Support operators: field=value (eq), field__in=a,b,c, field__gt=5
      const [fieldName, operator] = parseFieldOperator(field);
      filters.push({
        field: fieldName,
        operator,
        value: parseFilterValue(value, operator),
      });
    }
  }

  return filters;
}

function parseFieldOperator(field: string): [string, FilterOperator] {
  const operatorMap: Record<string, FilterOperator> = {
    '__in': 'in',
    '__neq': 'neq',
    '__gt': 'gt',
    '__lt': 'lt',
    '__contains': 'contains',
    '__between': 'between',
  };

  for (const [suffix, op] of Object.entries(operatorMap)) {
    if (field.endsWith(suffix)) {
      return [field.replace(suffix, ''), op];
    }
  }

  return [field, 'eq'];
}

function parseFilterValue(value: string, operator: FilterOperator): unknown {
  if (operator === 'in' || operator === 'between') {
    return value.split(',').map((v) => v.trim());
  }
  // Try to parse as number
  const num = parseFloat(value);
  if (!isNaN(num)) return num;
  // Try to parse as boolean
  if (value === 'true') return true;
  if (value === 'false') return false;
  return value;
}

function parseRelationships(params: URLSearchParams): RelationshipSpec[] {
  const depth = params.get('depth') ? parseInt(params.get('depth')!, 10) : 1;
  const direction = (params.get('rel_direction') || 'both') as 'inbound' | 'outbound' | 'both';
  const types = params.getAll('rel_type') as EdgeType[];

  // Only create relationships if depth > 0 or specific types are requested
  if (types.length === 0 && depth > 0) {
    // Default: include dependsOn relationship type
    return [{ type: 'dependsOn' as EdgeType, direction, depth }];
  }

  return types.map((type) => ({ type, direction, depth }));
}

function parsePresentation(params: URLSearchParams): PresentationHint {
  return {
    layout: (params.get('layout') as LayoutType) || DEFAULT_PRESENTATION.layout,
    graphDirection:
      (params.get('direction') as 'TB' | 'LR' | 'BT' | 'RL') || DEFAULT_PRESENTATION.graphDirection,
    sortBy: params.get('sortBy') || undefined,
    sortOrder: (params.get('sortOrder') as 'asc' | 'desc') || DEFAULT_PRESENTATION.sortOrder,
    groupBy: params.get('groupBy') || undefined,
    showMinimap: params.get('minimap') !== 'false',
    compact: params.get('compact') === 'true',
  };
}

// ============================================================================
// Serialize ComposedQuery -> URL Params
// ============================================================================

export function serializeQueryToParams(query: ComposedQuery): URLSearchParams {
  const params = new URLSearchParams();

  // Entities
  for (const entity of query.entities) {
    params.append('entity', serializeEntity(entity));
  }

  // Filters
  for (const filter of query.filters) {
    const key =
      filter.operator === 'eq'
        ? `filter.${filter.field}`
        : `filter.${filter.field}__${filter.operator}`;
    const value = Array.isArray(filter.value) ? filter.value.join(',') : String(filter.value);
    params.set(key, value);
  }

  // Relationships
  if (query.relationships.length > 0) {
    const rel = query.relationships[0];
    if (rel.depth && rel.depth !== 1) {
      params.set('depth', String(rel.depth));
    }
    if (rel.direction !== 'both') {
      params.set('rel_direction', rel.direction);
    }
    for (const r of query.relationships) {
      if (r.type !== 'dependsOn') {
        params.append('rel_type', r.type);
      }
    }
  }

  // Presentation
  if (query.presentation.layout !== 'auto') {
    params.set('layout', query.presentation.layout);
  }
  if (query.presentation.graphDirection && query.presentation.graphDirection !== 'TB') {
    params.set('direction', query.presentation.graphDirection);
  }
  if (query.presentation.sortBy) {
    params.set('sortBy', query.presentation.sortBy);
  }
  if (query.presentation.sortOrder && query.presentation.sortOrder !== 'desc') {
    params.set('sortOrder', query.presentation.sortOrder);
  }
  if (query.presentation.groupBy) {
    params.set('groupBy', query.presentation.groupBy);
  }
  if (query.presentation.showMinimap === false) {
    params.set('minimap', 'false');
  }
  if (query.presentation.compact) {
    params.set('compact', 'true');
  }

  // Pagination
  if (query.limit) {
    params.set('limit', String(query.limit));
  }
  if (query.offset) {
    params.set('offset', String(query.offset));
  }

  return params;
}

function serializeEntity(entity: EntitySelector): string {
  let str = entity.type;
  if (entity.id !== undefined) {
    str += `:${entity.id}`;
    if (entity.projectId !== undefined) {
      str += `:${entity.projectId}`;
    }
  }
  return str;
}
