import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type {
  Document,
  DocumentWithEntities,
  DocumentDeleteResponse,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  CreateSimpleConceptRequest,
  CreateSimpleRequirementRequest,
  UpdateConceptRequest,
  UpdateRequirementRequest,
  DocumentType,
  DocumentStatus,
} from '../types/documents';
import type {
  Concept,
  Requirement,
  ApprovalResponse,
  RejectionResponse,
  ConceptStatus,
  RequirementStatus,
} from '../types/review';

const DOCUMENTS_QUERY_KEY = ['documents'];
const DOCUMENT_QUERY_KEY = ['document'];

export interface UseDocumentsOptions {
  limit?: number;
  offset?: number;
  doc_types?: DocumentType[];
  statuses?: DocumentStatus[];
  search?: string;
}

export interface UseDocumentsResult {
  // Document list
  documents: Document[];
  total: number;
  hasMore: boolean;
  documentsLoading: boolean;
  documentsError: Error | null;

  // Selected document
  selectedDocument: DocumentWithEntities | null;
  selectedDocumentLoading: boolean;
  selectedDocumentError: Error | null;
  selectDocument: (id: number | null) => void;

  // Document mutations
  createDocument: (data: CreateDocumentRequest) => Promise<Document>;
  updateDocument: (id: number, data: UpdateDocumentRequest) => Promise<Document>;
  deleteDocument: (id: number, cascade?: boolean) => Promise<DocumentDeleteResponse>;
  isCreatingDocument: boolean;
  isUpdatingDocument: boolean;
  isDeletingDocument: boolean;

  // Concept mutations
  createConcept: (data: CreateSimpleConceptRequest) => Promise<Concept>;
  updateConcept: (id: number, data: UpdateConceptRequest) => Promise<Concept>;
  approveConcepts: (ids: number[], status?: ConceptStatus, indexToKb?: boolean) => Promise<ApprovalResponse>;
  rejectConcepts: (ids: number[]) => Promise<RejectionResponse>;
  isCreatingConcept: boolean;
  isUpdatingConcept: boolean;

  // Requirement mutations
  createRequirement: (data: CreateSimpleRequirementRequest) => Promise<Requirement>;
  updateRequirement: (id: number, data: UpdateRequirementRequest) => Promise<Requirement>;
  approveRequirements: (ids: number[], status?: RequirementStatus, indexToKb?: boolean) => Promise<ApprovalResponse>;
  rejectRequirements: (ids: number[]) => Promise<RejectionResponse>;
  isCreatingRequirement: boolean;
  isUpdatingRequirement: boolean;

  // Refetch
  refetchDocuments: () => void;
  refetchSelectedDocument: () => void;
}

export function useDocuments(options: UseDocumentsOptions = {}): UseDocumentsResult {
  const {
    limit = 50,
    offset = 0,
    doc_types,
    statuses,
    search,
  } = options;

  const queryClient = useQueryClient();

  // Track selected document ID
  const selectedDocumentId = queryClient.getQueryData<number | null>(['selectedDocumentId']) ?? null;

  // Fetch documents list
  const documentsQuery = useQuery({
    queryKey: [...DOCUMENTS_QUERY_KEY, { limit, offset, doc_types, statuses, search }],
    queryFn: async () => {
      return api.getDocuments({
        limit,
        offset,
        doc_types: doc_types?.join(','),
        statuses: statuses?.join(','),
        search,
      });
    },
  });

  // Fetch selected document with entities
  const selectedDocumentQuery = useQuery({
    queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId],
    queryFn: async () => {
      if (!selectedDocumentId) return null;
      return api.getDocument(selectedDocumentId);
    },
    enabled: selectedDocumentId !== null,
  });

  // Select document function
  const selectDocument = (id: number | null) => {
    queryClient.setQueryData(['selectedDocumentId'], id);
    if (id !== null) {
      queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, id] });
    }
  };

  // Document mutations
  const createDocumentMutation = useMutation({
    mutationFn: (data: CreateDocumentRequest) => api.createDocument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY });
    },
  });

  const updateDocumentMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateDocumentRequest }) =>
      api.updateDocument(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, id] });
    },
  });

  const deleteDocumentMutation = useMutation({
    mutationFn: ({ id, cascade }: { id: number; cascade?: boolean }) =>
      api.deleteDocument(id, cascade),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY });
      selectDocument(null);
    },
  });

  // Concept mutations
  const createConceptMutation = useMutation({
    mutationFn: (data: CreateSimpleConceptRequest) => api.createSimpleConcept(data),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  const updateConceptMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateConceptRequest }) =>
      api.updateConcept(id, data),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  const approveConceptsMutation = useMutation({
    mutationFn: ({ ids, status, indexToKb }: { ids: number[]; status?: ConceptStatus; indexToKb?: boolean }) =>
      api.approveConcepts({
        ids,
        status: status ?? ('active' as ConceptStatus),
        index_to_kb: indexToKb ?? true,
      }),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  const rejectConceptsMutation = useMutation({
    mutationFn: (ids: number[]) => api.rejectConcepts(ids),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  // Requirement mutations
  const createRequirementMutation = useMutation({
    mutationFn: (data: CreateSimpleRequirementRequest) => api.createSimpleRequirement(data),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  const updateRequirementMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateRequirementRequest }) =>
      api.updateRequirement(id, data),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  const approveRequirementsMutation = useMutation({
    mutationFn: ({ ids, status, indexToKb }: { ids: number[]; status?: RequirementStatus; indexToKb?: boolean }) =>
      api.approveRequirements({
        ids,
        status: status ?? ('accepted' as RequirementStatus),
        index_to_kb: indexToKb ?? true,
      }),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  const rejectRequirementsMutation = useMutation({
    mutationFn: (ids: number[]) => api.rejectRequirements(ids),
    onSuccess: () => {
      if (selectedDocumentId) {
        queryClient.invalidateQueries({ queryKey: [...DOCUMENT_QUERY_KEY, selectedDocumentId] });
      }
    },
  });

  // Wrapper functions
  const createDocument = async (data: CreateDocumentRequest) => {
    return createDocumentMutation.mutateAsync(data);
  };

  const updateDocument = async (id: number, data: UpdateDocumentRequest) => {
    return updateDocumentMutation.mutateAsync({ id, data });
  };

  const deleteDocument = async (id: number, cascade?: boolean) => {
    return deleteDocumentMutation.mutateAsync({ id, cascade });
  };

  const createConcept = async (data: CreateSimpleConceptRequest) => {
    return createConceptMutation.mutateAsync(data);
  };

  const updateConcept = async (id: number, data: UpdateConceptRequest) => {
    return updateConceptMutation.mutateAsync({ id, data });
  };

  const approveConcepts = async (ids: number[], status?: ConceptStatus, indexToKb?: boolean) => {
    return approveConceptsMutation.mutateAsync({ ids, status, indexToKb });
  };

  const rejectConcepts = async (ids: number[]) => {
    return rejectConceptsMutation.mutateAsync(ids);
  };

  const createRequirement = async (data: CreateSimpleRequirementRequest) => {
    return createRequirementMutation.mutateAsync(data);
  };

  const updateRequirement = async (id: number, data: UpdateRequirementRequest) => {
    return updateRequirementMutation.mutateAsync({ id, data });
  };

  const approveRequirements = async (ids: number[], status?: RequirementStatus, indexToKb?: boolean) => {
    return approveRequirementsMutation.mutateAsync({ ids, status, indexToKb });
  };

  const rejectRequirements = async (ids: number[]) => {
    return rejectRequirementsMutation.mutateAsync(ids);
  };

  return {
    // Document list
    documents: documentsQuery.data?.items ?? [],
    total: documentsQuery.data?.total ?? 0,
    hasMore: documentsQuery.data?.has_more ?? false,
    documentsLoading: documentsQuery.isLoading,
    documentsError: documentsQuery.error,

    // Selected document
    selectedDocument: selectedDocumentQuery.data ?? null,
    selectedDocumentLoading: selectedDocumentQuery.isLoading,
    selectedDocumentError: selectedDocumentQuery.error,
    selectDocument,

    // Document mutations
    createDocument,
    updateDocument,
    deleteDocument,
    isCreatingDocument: createDocumentMutation.isPending,
    isUpdatingDocument: updateDocumentMutation.isPending,
    isDeletingDocument: deleteDocumentMutation.isPending,

    // Concept mutations
    createConcept,
    updateConcept,
    approveConcepts,
    rejectConcepts,
    isCreatingConcept: createConceptMutation.isPending,
    isUpdatingConcept: updateConceptMutation.isPending,

    // Requirement mutations
    createRequirement,
    updateRequirement,
    approveRequirements,
    rejectRequirements,
    isCreatingRequirement: createRequirementMutation.isPending,
    isUpdatingRequirement: updateRequirementMutation.isPending,

    // Refetch
    refetchDocuments: () => documentsQuery.refetch(),
    refetchSelectedDocument: () => selectedDocumentQuery.refetch(),
  };
}
