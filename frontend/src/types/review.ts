/**
 * Review Queue types for Document Intelligence approval workflow
 *
 * These types support the review UI for approving/rejecting
 * AI-extracted concepts and requirements before they're indexed
 * to KnowledgeBeast.
 */

// ============================================================================
// Status Enums
// ============================================================================

export enum ConceptStatus {
  UNKNOWN = 'unknown',
  PROPOSED = 'proposed',
  ACTIVE = 'active',
  IMPLEMENTED = 'implemented',
  DEPRECATED = 'deprecated',
}

export enum RequirementStatus {
  PROPOSED = 'proposed',
  ACCEPTED = 'accepted',
  IMPLEMENTED = 'implemented',
  VERIFIED = 'verified',
  UNKNOWN = 'unknown',
}

export enum ConceptType {
  PRODUCT = 'product',
  FEATURE = 'feature',
  MODULE = 'module',
  PROCESS = 'process',
  TECHNOLOGY = 'technology',
  FRAMEWORK = 'framework',
  METHODOLOGY = 'methodology',
  OTHER = 'other',
}

export enum RequirementType {
  FUNCTIONAL = 'functional',
  NON_FUNCTIONAL = 'nonFunctional',
  CONSTRAINT = 'constraint',
  DEPENDENCY = 'dependency',
  OUTCOME = 'outcome',
}

export enum RequirementPriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  UNKNOWN = 'unknown',
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';

// ============================================================================
// Review Item Types
// ============================================================================

export interface Concept {
  id: number;
  project_id: number;
  source_document_id: number | null;
  source_document_path: string | null;
  name: string;
  concept_type: ConceptType;
  definition: string | null;
  status: ConceptStatus;
  domain: string | null;
  source_quote: string | null;
  confidence: ConfidenceLevel;
  related_entities: string[] | null;
  created_at: string;
}

export interface Requirement {
  id: number;
  project_id: number;
  source_document_id: number | null;
  source_document_path: string | null;
  req_id: string;
  text: string;
  req_type: RequirementType;
  priority: RequirementPriority;
  status: RequirementStatus;
  source_concept: string | null;
  source_quote: string | null;
  created_at: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ReviewQueueConceptsResponse {
  items: Concept[];
  total_pending: number;
  has_more: boolean;
}

export interface ReviewQueueRequirementsResponse {
  items: Requirement[];
  total_pending: number;
  has_more: boolean;
}

export interface ApprovalResponse {
  approved: number;
  indexed_to_kb: number;
}

export interface RejectionResponse {
  deleted: number;
}

// ============================================================================
// Request Types
// ============================================================================

export interface ApproveConceptsRequest {
  ids: number[];
  status?: ConceptStatus;
  index_to_kb?: boolean;
}

export interface ApproveRequirementsRequest {
  ids: number[];
  status?: RequirementStatus;
  index_to_kb?: boolean;
}

export interface RejectEntitiesRequest {
  ids: number[];
}

// ============================================================================
// UI Helper Types
// ============================================================================

export type ReviewTab = 'concepts' | 'requirements';

export interface ReviewSelection {
  concepts: Set<number>;
  requirements: Set<number>;
}
