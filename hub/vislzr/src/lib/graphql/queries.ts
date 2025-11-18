/**
 * GraphQL Queries for VISLZR
 *
 * Queries the CommandCenter GraphService for project graph data.
 */

import { gql } from '@apollo/client'

export const GET_PROJECT_GRAPH = gql`
  query GetProjectGraph($projectId: Int!, $depth: Int, $filters: GraphFilters) {
    projectGraph(projectId: $projectId, depth: $depth, filters: $filters) {
      nodes {
        id
        entity
        label
        metadata
      }
      edges {
        fromId
        toId
        type
      }
    }
  }
`

export const GET_DEPENDENCIES = gql`
  query GetDependencies($symbolId: Int!, $direction: String!, $depth: Int!) {
    dependencies(symbolId: $symbolId, direction: $direction, depth: $depth) {
      nodes {
        id
        entity
        label
        metadata
      }
      edges {
        fromId
        toId
        type
      }
    }
  }
`

export const GET_GHOST_NODES = gql`
  query GetGhostNodes($projectId: Int!, $filters: GhostNodeFilters) {
    ghostNodes(projectId: $projectId, filters: $filters) {
      id
      title
      description
      source
      status
    }
  }
`

export const SEARCH_GRAPH = gql`
  query SearchGraph($query: String!, $scope: String!) {
    search(query: $query, scope: $scope) {
      results {
        id
        entity
        label
        snippet
        score
      }
    }
  }
`
