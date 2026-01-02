import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type {
  Concept,
  Requirement,
  ConceptStatus,
  RequirementStatus,
  ApprovalResponse,
  RejectionResponse,
} from '../types/review';

const CONCEPTS_QUERY_KEY = ['review', 'concepts'];
const REQUIREMENTS_QUERY_KEY = ['review', 'requirements'];

export interface UseReviewQueueOptions {
  conceptLimit?: number;
  requirementLimit?: number;
}

export interface UseReviewQueueResult {
  // Data
  concepts: Concept[];
  requirements: Requirement[];
  totalPendingConcepts: number;
  totalPendingRequirements: number;
  totalPending: number;
  hasMoreConcepts: boolean;
  hasMoreRequirements: boolean;

  // Loading states
  loading: boolean;
  conceptsLoading: boolean;
  requirementsLoading: boolean;

  // Errors
  conceptsError: Error | null;
  requirementsError: Error | null;

  // Mutations
  approveConcepts: (ids: number[], status?: ConceptStatus, indexToKb?: boolean) => Promise<ApprovalResponse>;
  approveRequirements: (ids: number[], status?: RequirementStatus, indexToKb?: boolean) => Promise<ApprovalResponse>;
  rejectConcepts: (ids: number[]) => Promise<RejectionResponse>;
  rejectRequirements: (ids: number[]) => Promise<RejectionResponse>;

  // Mutation states
  isApprovingConcepts: boolean;
  isApprovingRequirements: boolean;
  isRejectingConcepts: boolean;
  isRejectingRequirements: boolean;

  // Refetch
  refetch: () => void;
}

export function useReviewQueue(options: UseReviewQueueOptions = {}): UseReviewQueueResult {
  const { conceptLimit = 50, requirementLimit = 50 } = options;
  const queryClient = useQueryClient();

  // Fetch pending concepts
  const conceptsQuery = useQuery({
    queryKey: [...CONCEPTS_QUERY_KEY, { limit: conceptLimit }],
    queryFn: async () => {
      return api.getConceptsForReview({ limit: conceptLimit });
    },
  });

  // Fetch pending requirements
  const requirementsQuery = useQuery({
    queryKey: [...REQUIREMENTS_QUERY_KEY, { limit: requirementLimit }],
    queryFn: async () => {
      return api.getRequirementsForReview({ limit: requirementLimit });
    },
  });

  // Approve concepts mutation
  const approveConceptsMutation = useMutation<ApprovalResponse, Error, { ids: number[]; status?: ConceptStatus; indexToKb?: boolean }>({
    mutationFn: ({ ids, status, indexToKb }) =>
      api.approveConcepts({
        ids,
        status: status ?? ('active' as ConceptStatus),
        index_to_kb: indexToKb ?? true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONCEPTS_QUERY_KEY });
    },
  });

  // Approve requirements mutation
  const approveRequirementsMutation = useMutation<ApprovalResponse, Error, { ids: number[]; status?: RequirementStatus; indexToKb?: boolean }>({
    mutationFn: ({ ids, status, indexToKb }) =>
      api.approveRequirements({
        ids,
        status: status ?? ('accepted' as RequirementStatus),
        index_to_kb: indexToKb ?? true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REQUIREMENTS_QUERY_KEY });
    },
  });

  // Reject concepts mutation
  const rejectConceptsMutation = useMutation<RejectionResponse, Error, number[]>({
    mutationFn: (ids) => api.rejectConcepts(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONCEPTS_QUERY_KEY });
    },
  });

  // Reject requirements mutation
  const rejectRequirementsMutation = useMutation<RejectionResponse, Error, number[]>({
    mutationFn: (ids) => api.rejectRequirements(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REQUIREMENTS_QUERY_KEY });
    },
  });

  // Wrapper functions
  const approveConcepts = async (ids: number[], status?: ConceptStatus, indexToKb?: boolean): Promise<ApprovalResponse> => {
    return approveConceptsMutation.mutateAsync({ ids, status, indexToKb });
  };

  const approveRequirements = async (ids: number[], status?: RequirementStatus, indexToKb?: boolean): Promise<ApprovalResponse> => {
    return approveRequirementsMutation.mutateAsync({ ids, status, indexToKb });
  };

  const rejectConcepts = async (ids: number[]): Promise<RejectionResponse> => {
    return rejectConceptsMutation.mutateAsync(ids);
  };

  const rejectRequirements = async (ids: number[]): Promise<RejectionResponse> => {
    return rejectRequirementsMutation.mutateAsync(ids);
  };

  const refetch = () => {
    conceptsQuery.refetch();
    requirementsQuery.refetch();
  };

  return {
    // Data
    concepts: conceptsQuery.data?.items ?? [],
    requirements: requirementsQuery.data?.items ?? [],
    totalPendingConcepts: conceptsQuery.data?.total_pending ?? 0,
    totalPendingRequirements: requirementsQuery.data?.total_pending ?? 0,
    totalPending: (conceptsQuery.data?.total_pending ?? 0) + (requirementsQuery.data?.total_pending ?? 0),
    hasMoreConcepts: conceptsQuery.data?.has_more ?? false,
    hasMoreRequirements: requirementsQuery.data?.has_more ?? false,

    // Loading states
    loading: conceptsQuery.isLoading || requirementsQuery.isLoading,
    conceptsLoading: conceptsQuery.isLoading,
    requirementsLoading: requirementsQuery.isLoading,

    // Errors
    conceptsError: conceptsQuery.error,
    requirementsError: requirementsQuery.error,

    // Mutations
    approveConcepts,
    approveRequirements,
    rejectConcepts,
    rejectRequirements,

    // Mutation states
    isApprovingConcepts: approveConceptsMutation.isPending,
    isApprovingRequirements: approveRequirementsMutation.isPending,
    isRejectingConcepts: rejectConceptsMutation.isPending,
    isRejectingRequirements: rejectRequirementsMutation.isPending,

    // Refetch
    refetch,
  };
}
