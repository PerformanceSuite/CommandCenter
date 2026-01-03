/**
 * Document types for the unified Knowledge Base view
 *
 * These types support the document-centric UI for managing documents,
 * concepts, and requirements.
 */

import type {
  Concept,
  Requirement,
  ConceptStatus,
  RequirementStatus,
  ConceptType,
  RequirementType,
  RequirementPriority,
  ConfidenceLevel,
} from './review';

// Re-export review types for convenience
export type {
  Concept,
  Requirement,
  ConceptStatus,
  RequirementStatus,
  ConceptType,
  RequirementType,
  RequirementPriority,
  ConfidenceLevel,
};

// ============================================================================
// Document Enums
// ============================================================================

export enum DocumentType {
  PLAN = 'plan',
  CONCEPT = 'concept',
  GUIDE = 'guide',
  REFERENCE = 'reference',
  REPORT = 'report',
  SESSION = 'session',
  ARCHIVE = 'archive',
}

export enum DocumentStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  SUPERSEDED = 'superseded',
  ABANDONED = 'abandoned',
  STALE = 'stale',
}

// ============================================================================
// Document Types
// ============================================================================

export interface Document {
  id: number;
  project_id: number;
  path: string;
  title: string | null;
  doc_type: DocumentType;
  subtype: string | null;
  status: DocumentStatus;
  audience: string | null;
  value_assessment: string | null;
  word_count: number;
  content_hash: string | null;
  staleness_score: number | null;
  last_meaningful_date: string | null;
  recommended_action: string | null;
  target_location: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  last_analyzed_at: string | null;
}

export interface DocumentWithEntities {
  document: Document;
  concepts: Concept[];
  requirements: Requirement[];
  pending_concept_count: number;
  pending_requirement_count: number;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface DocumentListResponse {
  items: Document[];
  total: number;
  has_more: boolean;
}

export interface DocumentDeleteResponse {
  deleted: boolean;
  cascaded_concepts: number;
  cascaded_requirements: number;
}

// ============================================================================
// Request Types
// ============================================================================

export interface CreateDocumentRequest {
  path: string;
  title?: string;
  doc_type: DocumentType;
  subtype?: string;
  status?: DocumentStatus;
  audience?: string;
  value_assessment?: string;
  word_count?: number;
  staleness_score?: number;
  last_meaningful_date?: string;
  recommended_action?: string;
  target_location?: string;
  metadata?: Record<string, unknown>;
}

export interface UpdateDocumentRequest {
  title?: string;
  doc_type?: DocumentType;
  subtype?: string;
  status?: DocumentStatus;
  audience?: string;
  value_assessment?: string;
  recommended_action?: string;
  target_location?: string;
  metadata?: Record<string, unknown>;
}

export interface CreateSimpleConceptRequest {
  name: string;
  concept_type: ConceptType;
  definition?: string;
  source_document_id?: number;
}

export interface CreateSimpleRequirementRequest {
  text: string;
  req_type: RequirementType;
  priority?: RequirementPriority;
  source_document_id?: number;
}

export interface UpdateConceptRequest {
  name?: string;
  concept_type?: ConceptType;
  definition?: string;
  status?: ConceptStatus;
  domain?: string;
  source_quote?: string;
  confidence?: ConfidenceLevel;
  related_entities?: string[];
  metadata?: Record<string, unknown>;
}

export interface UpdateRequirementRequest {
  text?: string;
  req_type?: RequirementType;
  priority?: RequirementPriority;
  status?: RequirementStatus;
  source_concept?: string;
  source_quote?: string;
  verification?: string;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Filter Types
// ============================================================================

export interface DocumentFilters {
  doc_types?: DocumentType[];
  statuses?: DocumentStatus[];
  search?: string;
}

// ============================================================================
// UI Helper Types
// ============================================================================

export type EntityType = 'concept' | 'requirement';

export interface EntitySelection {
  concepts: Set<number>;
  requirements: Set<number>;
}
