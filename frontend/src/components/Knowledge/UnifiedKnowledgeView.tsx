import { useState } from 'react';
import {
  FileText,
  FolderOpen,
  Plus,
  Search,
  CheckCircle,
  XCircle,
  Trash2,
  ChevronDown,
  ChevronRight,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useDocuments } from '../../hooks/useDocuments';
import type {
  DocumentType,
  DocumentStatus,
  CreateSimpleConceptRequest,
  CreateSimpleRequirementRequest,
} from '../../types/documents';
import type { Concept, Requirement, ConceptType, RequirementType, RequirementPriority } from '../../types/review';

// Document type colors
const docTypeColors: Record<DocumentType, string> = {
  plan: 'bg-blue-500/20 text-blue-400',
  concept: 'bg-purple-500/20 text-purple-400',
  guide: 'bg-green-500/20 text-green-400',
  reference: 'bg-yellow-500/20 text-yellow-400',
  report: 'bg-orange-500/20 text-orange-400',
  session: 'bg-pink-500/20 text-pink-400',
  archive: 'bg-gray-500/20 text-gray-400',
};

// Status colors
const statusColors: Record<DocumentStatus, string> = {
  active: 'bg-green-500/20 text-green-400',
  completed: 'bg-blue-500/20 text-blue-400',
  superseded: 'bg-yellow-500/20 text-yellow-400',
  abandoned: 'bg-red-500/20 text-red-400',
  stale: 'bg-gray-500/20 text-gray-400',
};

// Concept type colors
const conceptTypeColors: Record<string, string> = {
  product: 'bg-blue-500/20 text-blue-400',
  feature: 'bg-green-500/20 text-green-400',
  module: 'bg-purple-500/20 text-purple-400',
  process: 'bg-yellow-500/20 text-yellow-400',
  technology: 'bg-cyan-500/20 text-cyan-400',
  framework: 'bg-orange-500/20 text-orange-400',
  methodology: 'bg-pink-500/20 text-pink-400',
  other: 'bg-gray-500/20 text-gray-400',
};

// Requirement type colors
const reqTypeColors: Record<string, string> = {
  functional: 'bg-blue-500/20 text-blue-400',
  nonFunctional: 'bg-purple-500/20 text-purple-400',
  constraint: 'bg-yellow-500/20 text-yellow-400',
  dependency: 'bg-orange-500/20 text-orange-400',
  outcome: 'bg-green-500/20 text-green-400',
};

// Priority colors
const priorityColors: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400',
  high: 'bg-orange-500/20 text-orange-400',
  medium: 'bg-yellow-500/20 text-yellow-400',
  low: 'bg-gray-500/20 text-gray-400',
  unknown: 'bg-gray-500/20 text-gray-400',
};

interface AddEntityModalProps {
  type: 'concept' | 'requirement';
  documentId?: number;
  onClose: () => void;
  onSubmit: (data: CreateSimpleConceptRequest | CreateSimpleRequirementRequest) => void;
  isLoading: boolean;
}

function AddEntityModal({ type, documentId, onClose, onSubmit, isLoading }: AddEntityModalProps) {
  const [name, setName] = useState('');
  const [text, setText] = useState('');
  const [entityType, setEntityType] = useState<string>(type === 'concept' ? 'feature' : 'functional');
  const [priority, setPriority] = useState<RequirementPriority>('medium' as RequirementPriority);
  const [definition, setDefinition] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (type === 'concept') {
      onSubmit({
        name,
        concept_type: entityType as ConceptType,
        definition: definition || undefined,
        source_document_id: documentId,
      });
    } else {
      onSubmit({
        text,
        req_type: entityType as RequirementType,
        priority,
        source_document_id: documentId,
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-white mb-4">
          Add {type === 'concept' ? 'Concept' : 'Requirement'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          {type === 'concept' ? (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-700 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Type *</label>
                <select
                  value={entityType}
                  onChange={(e) => setEntityType(e.target.value)}
                  className="w-full bg-gray-700 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="product">Product</option>
                  <option value="feature">Feature</option>
                  <option value="module">Module</option>
                  <option value="process">Process</option>
                  <option value="technology">Technology</option>
                  <option value="framework">Framework</option>
                  <option value="methodology">Methodology</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Definition</label>
                <textarea
                  value={definition}
                  onChange={(e) => setDefinition(e.target.value)}
                  className="w-full bg-gray-700 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Requirement Text *</label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full bg-gray-700 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Type *</label>
                <select
                  value={entityType}
                  onChange={(e) => setEntityType(e.target.value)}
                  className="w-full bg-gray-700 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="functional">Functional</option>
                  <option value="nonFunctional">Non-Functional</option>
                  <option value="constraint">Constraint</option>
                  <option value="dependency">Dependency</option>
                  <option value="outcome">Outcome</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as RequirementPriority)}
                  className="w-full bg-gray-700 text-white rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function UnifiedKnowledgeView() {
  const [searchTerm, setSearchTerm] = useState('');
  const [addEntityModal, setAddEntityModal] = useState<{ type: 'concept' | 'requirement' } | null>(null);
  const [expandedSections, setExpandedSections] = useState({ concepts: true, requirements: true });

  const {
    documents,
    total,
    documentsLoading,
    documentsError,
    selectedDocument,
    selectedDocumentLoading,
    selectDocument,
    createConcept,
    createRequirement,
    approveConcepts,
    rejectConcepts,
    approveRequirements,
    rejectRequirements,
    isCreatingConcept,
    isCreatingRequirement,
    deleteDocument,
  } = useDocuments({ search: searchTerm || undefined });

  const toggleSection = (section: 'concepts' | 'requirements') => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleAddEntity = async (data: CreateSimpleConceptRequest | CreateSimpleRequirementRequest) => {
    if (addEntityModal?.type === 'concept') {
      await createConcept(data as CreateSimpleConceptRequest);
    } else {
      await createRequirement(data as CreateSimpleRequirementRequest);
    }
    setAddEntityModal(null);
  };

  const pendingConceptCount = selectedDocument?.pending_concept_count ?? 0;
  const pendingRequirementCount = selectedDocument?.pending_requirement_count ?? 0;
  const totalPending = pendingConceptCount + pendingRequirementCount;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <FolderOpen className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
            <p className="text-gray-400 text-sm">
              Manage documents, concepts, and requirements
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {totalPending > 0 && (
            <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm">
              {totalPending} pending review
            </span>
          )}
          <span className="text-gray-400">{total} documents</span>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Document list panel */}
        <div className="w-80 border-r border-gray-700 flex flex-col">
          {/* Search */}
          <div className="p-4 border-b border-gray-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-800 text-white rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Document list */}
          <div className="flex-1 overflow-y-auto p-2">
            {documentsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
              </div>
            ) : documentsError ? (
              <div className="flex items-center justify-center py-8 text-red-400">
                <AlertCircle className="w-5 h-5 mr-2" />
                Failed to load documents
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>No documents found</p>
              </div>
            ) : (
              <div className="space-y-1">
                {documents.map((doc) => (
                  <button
                    key={doc.id}
                    onClick={() => selectDocument(doc.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedDocument?.document.id === doc.id
                        ? 'bg-blue-600/20 border border-blue-500'
                        : 'hover:bg-gray-800'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <FileText className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-white text-sm font-medium truncate">
                          {doc.title || doc.path.split('/').pop()}
                        </p>
                        <p className="text-gray-500 text-xs truncate">{doc.path}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`px-1.5 py-0.5 rounded text-xs ${docTypeColors[doc.doc_type]}`}>
                            {doc.doc_type}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded text-xs ${statusColors[doc.status]}`}>
                            {doc.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Document detail panel */}
        <div className="flex-1 overflow-y-auto p-6">
          {selectedDocumentLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : selectedDocument ? (
            <div className="space-y-6">
              {/* Document header */}
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">
                      {selectedDocument.document.title || selectedDocument.document.path.split('/').pop()}
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">{selectedDocument.document.path}</p>
                    <div className="flex items-center gap-2 mt-3">
                      <span className={`px-2 py-1 rounded text-sm ${docTypeColors[selectedDocument.document.doc_type]}`}>
                        {selectedDocument.document.doc_type}
                      </span>
                      <span className={`px-2 py-1 rounded text-sm ${statusColors[selectedDocument.document.status]}`}>
                        {selectedDocument.document.status}
                      </span>
                      {selectedDocument.document.word_count > 0 && (
                        <span className="text-gray-400 text-sm">
                          {selectedDocument.document.word_count.toLocaleString()} words
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      if (confirm('Delete this document?')) {
                        deleteDocument(selectedDocument.document.id, true);
                      }
                    }}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Concepts section */}
              <div className="bg-gray-800 rounded-lg">
                <button
                  onClick={() => toggleSection('concepts')}
                  className="w-full flex items-center justify-between p-4 text-left"
                >
                  <div className="flex items-center gap-2">
                    {expandedSections.concepts ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                    <span className="text-white font-medium">
                      Concepts ({selectedDocument.concepts.length})
                    </span>
                    {pendingConceptCount > 0 && (
                      <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">
                        {pendingConceptCount} pending
                      </span>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setAddEntityModal({ type: 'concept' });
                    }}
                    className="p-1 text-gray-400 hover:text-blue-400 hover:bg-gray-700 rounded"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                </button>
                {expandedSections.concepts && (
                  <div className="border-t border-gray-700 p-4 space-y-2">
                    {selectedDocument.concepts.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">No concepts extracted</p>
                    ) : (
                      selectedDocument.concepts.map((concept) => (
                        <ConceptItem
                          key={concept.id}
                          concept={concept}
                          onApprove={() => approveConcepts([concept.id])}
                          onReject={() => rejectConcepts([concept.id])}
                        />
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Requirements section */}
              <div className="bg-gray-800 rounded-lg">
                <button
                  onClick={() => toggleSection('requirements')}
                  className="w-full flex items-center justify-between p-4 text-left"
                >
                  <div className="flex items-center gap-2">
                    {expandedSections.requirements ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                    <span className="text-white font-medium">
                      Requirements ({selectedDocument.requirements.length})
                    </span>
                    {pendingRequirementCount > 0 && (
                      <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">
                        {pendingRequirementCount} pending
                      </span>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setAddEntityModal({ type: 'requirement' });
                    }}
                    className="p-1 text-gray-400 hover:text-blue-400 hover:bg-gray-700 rounded"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                </button>
                {expandedSections.requirements && (
                  <div className="border-t border-gray-700 p-4 space-y-2">
                    {selectedDocument.requirements.length === 0 ? (
                      <p className="text-gray-500 text-center py-4">No requirements extracted</p>
                    ) : (
                      selectedDocument.requirements.map((req) => (
                        <RequirementItem
                          key={req.id}
                          requirement={req}
                          onApprove={() => approveRequirements([req.id])}
                          onReject={() => rejectRequirements([req.id])}
                        />
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <FileText className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg">Select a document to view details</p>
              <p className="text-sm mt-2">
                Or use the search to find documents
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Add entity modal */}
      {addEntityModal && (
        <AddEntityModal
          type={addEntityModal.type}
          documentId={selectedDocument?.document.id}
          onClose={() => setAddEntityModal(null)}
          onSubmit={handleAddEntity}
          isLoading={addEntityModal.type === 'concept' ? isCreatingConcept : isCreatingRequirement}
        />
      )}
    </div>
  );
}

// Concept item component
interface ConceptItemProps {
  concept: Concept;
  onApprove: () => void;
  onReject: () => void;
}

function ConceptItem({ concept, onApprove, onReject }: ConceptItemProps) {
  const isPending = concept.status === 'unknown';

  return (
    <div className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white font-medium">{concept.name}</span>
          <span className={`px-1.5 py-0.5 rounded text-xs ${conceptTypeColors[concept.concept_type] || conceptTypeColors.other}`}>
            {concept.concept_type}
          </span>
          {isPending && (
            <span className="px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">
              pending
            </span>
          )}
        </div>
        {concept.definition && (
          <p className="text-gray-400 text-sm mt-1 line-clamp-2">{concept.definition}</p>
        )}
      </div>
      {isPending && (
        <div className="flex items-center gap-1">
          <button
            onClick={onApprove}
            className="p-1.5 text-green-400 hover:bg-green-500/20 rounded"
            title="Approve"
          >
            <CheckCircle className="w-4 h-4" />
          </button>
          <button
            onClick={onReject}
            className="p-1.5 text-red-400 hover:bg-red-500/20 rounded"
            title="Reject"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

// Requirement item component
interface RequirementItemProps {
  requirement: Requirement;
  onApprove: () => void;
  onReject: () => void;
}

function RequirementItem({ requirement, onApprove, onReject }: RequirementItemProps) {
  const isPending = requirement.status === 'proposed';

  return (
    <div className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-white font-mono text-sm">{requirement.req_id}</span>
          <span className={`px-1.5 py-0.5 rounded text-xs ${reqTypeColors[requirement.req_type] || reqTypeColors.functional}`}>
            {requirement.req_type}
          </span>
          <span className={`px-1.5 py-0.5 rounded text-xs ${priorityColors[requirement.priority] || priorityColors.medium}`}>
            {requirement.priority}
          </span>
          {isPending && (
            <span className="px-1.5 py-0.5 bg-orange-500/20 text-orange-400 rounded text-xs">
              pending
            </span>
          )}
        </div>
        <p className="text-gray-300 text-sm mt-1">{requirement.text}</p>
      </div>
      {isPending && (
        <div className="flex items-center gap-1">
          <button
            onClick={onApprove}
            className="p-1.5 text-green-400 hover:bg-green-500/20 rounded"
            title="Approve"
          >
            <CheckCircle className="w-4 h-4" />
          </button>
          <button
            onClick={onReject}
            className="p-1.5 text-red-400 hover:bg-red-500/20 rounded"
            title="Reject"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

export default UnifiedKnowledgeView;
