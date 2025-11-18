/**
 * GraphQL Mutations for VISLZR
 *
 * Mutations for triggering audits, creating tasks, and managing graph entities.
 */

import { gql } from '@apollo/client'

export const TRIGGER_AUDIT = gql`
  mutation TriggerAudit(
    $targetEntity: String!
    $targetId: Int!
    $kind: String!
    $projectId: Int!
  ) {
    triggerAudit(
      targetEntity: $targetEntity
      targetId: $targetId
      kind: $kind
      projectId: $projectId
    ) {
      id
      targetEntity
      targetId
      kind
      status
      summary
      reportPath
      score
      createdAt
    }
  }
`

export const CREATE_TASK = gql`
  mutation CreateTask(
    $projectId: Int!
    $title: String!
    $kind: String!
    $specItemId: Int
    $labels: [String!]
  ) {
    createTask(
      projectId: $projectId
      title: $title
      kind: $kind
      specItemId: $specItemId
      labels: $labels
    ) {
      id
      title
      kind
      status
      createdAt
    }
  }
`

export const CREATE_LINK = gql`
  mutation CreateLink(
    $fromEntity: String!
    $fromId: Int!
    $toEntity: String!
    $toId: Int!
    $type: String!
  ) {
    link(
      fromEntity: $fromEntity
      fromId: $fromId
      toEntity: $toEntity
      toId: $toId
      type: $type
    ) {
      id
      fromEntity
      fromId
      toEntity
      toId
      type
    }
  }
`

export const REFRESH_PROJECT = gql`
  mutation RefreshProject($projectId: Int!, $modes: [String!]!) {
    refreshProject(projectId: $projectId, modes: $modes) {
      success
      message
    }
  }
`
