import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTechnologies, TechnologyFilters } from '../../hooks/useTechnologies';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { Pagination } from '../common/Pagination';
import { TechnologyCard } from './TechnologyCard';
import { MatrixView } from './MatrixView';
import { TechnologyForm } from './TechnologyForm';
import { Plus, Search, Filter, AlertCircle, Grid, List } from 'lucide-react';
import { TechnologyDomain, TechnologyStatus, Technology, TechnologyCreate, TechnologyUpdate } from '../../types/technology';

export const RadarView: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse and validate URL params for filters
  // Page validation: must be positive integer, default to 1 if invalid
  const pageFromUrl = (() => {
    const page = parseInt(searchParams.get('page') || '1', 10);
    return !isNaN(page) && page > 0 ? page : 1;
  })();

  // Limit validation: must be between 1 and 100, default to 20 if invalid
  const limitFromUrl = (() => {
    const limit = parseInt(searchParams.get('limit') || '20', 10);
    return !isNaN(limit) && limit >= 1 && limit <= 100 ? limit : 20;
  })();

  // Domain validation: must be valid TechnologyDomain enum value, undefined if invalid
  const domainFromUrl = (() => {
    const domain = searchParams.get('domain');
    return domain && Object.values(TechnologyDomain).includes(domain as TechnologyDomain)
      ? domain
      : undefined;
  })();

  // Status validation: must be valid TechnologyStatus enum value, undefined if invalid
  const statusFromUrl = (() => {
    const status = searchParams.get('status');
    return status && Object.values(TechnologyStatus).includes(status as TechnologyStatus)
      ? status
      : undefined;
  })();

  const searchFromUrl = searchParams.get('search') || '';

  // View mode validation: must be 'card' or 'matrix', default to 'card'
  const viewModeFromUrl = (() => {
    const view = searchParams.get('view');
    return view === 'matrix' ? 'matrix' : 'card';
  })();

  // Initialize filters from URL
  const [filters, setFilters] = useState<TechnologyFilters>({
    page: pageFromUrl,
    limit: limitFromUrl,
    domain: domainFromUrl,
    status: statusFromUrl,
    search: searchFromUrl || undefined,
  });

  const {
    technologies,
    loading,
    error,
    total,
    page,
    totalPages,
    createTechnology,
    updateTechnology,
    deleteTechnology,
    isCreating,
    isUpdating,
  } = useTechnologies(filters);

  // UI State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTechnology, setEditingTechnology] = useState<Technology | null>(null);
  const [searchQuery, setSearchQuery] = useState(searchFromUrl);
  const [selectedDomain, setSelectedDomain] = useState<string>(domainFromUrl || '');
  const [selectedStatus, setSelectedStatus] = useState<string>(statusFromUrl || '');
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'card' | 'matrix'>(viewModeFromUrl);

  // Update URL when filters change
  const updateUrlParams = useCallback(
    (newFilters: Partial<TechnologyFilters>) => {
      const params = new URLSearchParams(searchParams);

      // Update or remove parameters
      if (newFilters.page && newFilters.page !== 1) {
        params.set('page', newFilters.page.toString());
      } else {
        params.delete('page');
      }

      if (newFilters.limit && newFilters.limit !== 20) {
        params.set('limit', newFilters.limit.toString());
      } else {
        params.delete('limit');
      }

      if (newFilters.domain) {
        params.set('domain', newFilters.domain);
      } else {
        params.delete('domain');
      }

      if (newFilters.status) {
        params.set('status', newFilters.status);
      } else {
        params.delete('status');
      }

      if (newFilters.search) {
        params.set('search', newFilters.search);
      } else {
        params.delete('search');
      }

      if (viewMode !== 'card') {
        params.set('view', viewMode);
      } else {
        params.delete('view');
      }

      setSearchParams(params, { replace: true });
    },
    [searchParams, setSearchParams, viewMode]
  );

  // Update filters and URL
  const handleFilterChange = useCallback(
    (newFilters: Partial<TechnologyFilters>) => {
      const updatedFilters = {
        ...filters,
        ...newFilters,
        // Reset to page 1 when changing filters (except when changing page itself)
        page: newFilters.page !== undefined ? newFilters.page : 1,
      };

      setFilters(updatedFilters);
      updateUrlParams(updatedFilters);
    },
    [filters, updateUrlParams]
  );

  // Debounced search handler with proper cleanup to prevent race conditions
  // Use useRef to persist timer across renders and properly clear it
  const searchTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Clear any pending timer before setting a new one
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }

    searchTimerRef.current = setTimeout(() => {
      if (searchQuery !== filters.search) {
        handleFilterChange({ search: searchQuery || undefined });
      }
    }, 500);

    // Cleanup function to clear timer when component unmounts or searchQuery changes
    return () => {
      if (searchTimerRef.current) {
        clearTimeout(searchTimerRef.current);
        searchTimerRef.current = null;
      }
    };
  }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  // Update view mode in URL
  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    if (viewMode !== 'card') {
      params.set('view', viewMode);
    } else {
      params.delete('view');
    }
    setSearchParams(params, { replace: true });
  }, [viewMode]); // eslint-disable-line react-hooks/exhaustive-deps

  // Group by domain for card view
  const groupedByDomain = useMemo(
    () => technologies.reduce((acc, tech) => {
      if (!acc[tech.domain]) {
        acc[tech.domain] = [];
      }
      acc[tech.domain].push(tech);
      return acc;
    }, {} as Record<string, typeof technologies>),
    [technologies]
  );

  const domainEntries = useMemo(
    () => Object.entries(groupedByDomain),
    [groupedByDomain]
  );

  // Handlers
  const handleCreate = async (data: TechnologyCreate) => {
    try {
      await createTechnology(data);
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create technology:', error);
      alert('Failed to create technology. Please try again.');
    }
  };

  const handleUpdate = async (data: TechnologyUpdate) => {
    if (!editingTechnology) return;
    try {
      await updateTechnology(editingTechnology.id, data);
      setEditingTechnology(null);
    } catch (error) {
      console.error('Failed to update technology:', error);
      alert('Failed to update technology. Please try again.');
    }
  };

  const handleDelete = async (tech: Technology) => {
    if (!window.confirm(`Are you sure you want to delete "${tech.title}"?`)) {
      return;
    }
    try {
      await deleteTechnology(tech.id);
    } catch (error) {
      console.error('Failed to delete technology:', error);
      alert('Failed to delete technology. Please try again.');
    }
  };

  const handleDomainChange = (domain: string) => {
    setSelectedDomain(domain);
    handleFilterChange({ domain: domain || undefined });
  };

  const handleStatusChange = (status: string) => {
    setSelectedStatus(status);
    handleFilterChange({ status: status || undefined });
  };

  const handlePageChange = (newPage: number) => {
    handleFilterChange({ page: newPage });
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedDomain('');
    setSelectedStatus('');
    handleFilterChange({ search: undefined, domain: undefined, status: undefined, page: 1 });
  };

  const hasActiveFilters = searchQuery || selectedDomain || selectedStatus;

  if (loading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-center gap-3">
        <AlertCircle className="text-red-600" size={24} />
        <div>
          <h3 className="text-red-800 font-semibold">Error loading technologies</h3>
          <p className="text-red-600 text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with View Toggle and Create Button */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Technology Radar</h1>
        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-800 rounded-md p-1">
            <button
              onClick={() => setViewMode('card')}
              className={`px-3 py-1.5 rounded flex items-center gap-2 transition-colors ${
                viewMode === 'card'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Card View"
            >
              <Grid size={18} />
              Cards
            </button>
            <button
              onClick={() => setViewMode('matrix')}
              className={`px-3 py-1.5 rounded flex items-center gap-2 transition-colors ${
                viewMode === 'matrix'
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
              title="Matrix View"
            >
              <List size={18} />
              Matrix
            </button>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors flex items-center gap-2"
          >
            <Plus size={20} />
            Add Technology
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-4 space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              placeholder="Search technologies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900 text-white placeholder-slate-400 border border-slate-600 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 border rounded-md transition-colors flex items-center gap-2 ${
              showFilters || hasActiveFilters
                ? 'bg-primary-600 border-primary-600 text-white'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Filter size={20} />
            Filters
            {hasActiveFilters && (
              <span className="bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">
                {(selectedDomain ? 1 : 0) + (selectedStatus ? 1 : 0)}
              </span>
            )}
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="border-t border-slate-600 pt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Domain Filter */}
              <div>
                <label htmlFor="domain-filter" className="block text-sm font-medium text-slate-300 mb-2">
                  Domain
                </label>
                <select
                  id="domain-filter"
                  value={selectedDomain}
                  onChange={(e) => handleDomainChange(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 text-white border border-slate-600 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  aria-label="Filter by domain"
                >
                  <option value="">All Domains</option>
                  {Object.values(TechnologyDomain).map((domain) => (
                    <option key={domain} value={domain}>
                      {domain.replace(/-/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label htmlFor="status-filter" className="block text-sm font-medium text-slate-300 mb-2">
                  Status
                </label>
                <select
                  id="status-filter"
                  value={selectedStatus}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 text-white border border-slate-600 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  aria-label="Filter by status"
                >
                  <option value="">All Statuses</option>
                  {Object.values(TechnologyStatus).map((status) => (
                    <option key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {hasActiveFilters && (
              <div className="flex items-center justify-between pt-2 border-t border-slate-600">
                <p className="text-sm text-slate-400">
                  Showing {technologies.length} of {total} technologies
                </p>
                <button
                  onClick={clearFilters}
                  className="text-sm text-primary-400 hover:text-primary-300 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Technologies View */}
      {viewMode === 'matrix' ? (
        /* Matrix View */
        <>
          {technologies.length > 0 ? (
            <>
              <MatrixView
                technologies={technologies}
                onEdit={setEditingTechnology}
                onDelete={handleDelete}
              />
              {/* Pagination for Matrix View */}
              {totalPages > 1 && (
                <div className="bg-slate-800 border border-slate-700 rounded-lg shadow">
                  <Pagination
                    currentPage={page}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                    totalItems={total}
                    pageSize={filters.limit || 20}
                    showPageInfo={true}
                  />
                </div>
              )}
            </>
          ) : (
            <div
              className="bg-slate-800 border border-slate-700 rounded-lg shadow p-12 text-center"
              role="status"
              aria-live="polite"
            >
              {hasActiveFilters ? (
                <>
                  <p className="text-slate-500 text-lg">No technologies match your filters</p>
                  <button
                    onClick={clearFilters}
                    className="mt-4 text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Clear filters
                  </button>
                </>
              ) : (
                <>
                  <p className="text-slate-500 text-lg">No technologies tracked yet</p>
                  <p className="text-gray-400 text-sm mt-2">Add technologies to see them on the radar</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors inline-flex items-center gap-2"
                  >
                    <Plus size={20} />
                    Add Your First Technology
                  </button>
                </>
              )}
            </div>
          )}
        </>
      ) : (
        /* Card Grid View */
        <>
          {domainEntries.length > 0 ? (
            <>
              {domainEntries.map(([domain, techs]) => (
                <section
                  key={domain}
                  className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6"
                  aria-labelledby={`domain-${domain}-heading`}
                >
                  <h2 id={`domain-${domain}-heading`} className="text-2xl font-bold mb-4 capitalize">
                    {domain.replace(/-/g, ' ')} ({techs.length})
                  </h2>
                  <div
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                    role="list"
                    aria-label={`Technologies in ${domain} domain`}
                  >
                    {techs.map((tech) => (
                      <TechnologyCard
                        key={tech.id}
                        technology={tech}
                        onEdit={setEditingTechnology}
                        onDelete={handleDelete}
                      />
                    ))}
                  </div>
                </section>
              ))}
              {/* Pagination for Card View */}
              {totalPages > 1 && (
                <div className="bg-slate-800 border border-slate-700 rounded-lg shadow">
                  <Pagination
                    currentPage={page}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                    totalItems={total}
                    pageSize={filters.limit || 20}
                    showPageInfo={true}
                  />
                </div>
              )}
            </>
          ) : (
            <div
              className="bg-slate-800 border border-slate-700 rounded-lg shadow p-12 text-center"
              role="status"
              aria-live="polite"
            >
              {hasActiveFilters ? (
                <>
                  <p className="text-slate-500 text-lg">No technologies match your filters</p>
                  <button
                    onClick={clearFilters}
                    className="mt-4 text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Clear filters
                  </button>
                </>
              ) : (
                <>
                  <p className="text-slate-500 text-lg">No technologies tracked yet</p>
                  <p className="text-gray-400 text-sm mt-2">Add technologies to see them on the radar</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors inline-flex items-center gap-2"
                  >
                    <Plus size={20} />
                    Add Your First Technology
                  </button>
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <TechnologyForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isLoading={isCreating}
        />
      )}

      {/* Edit Modal */}
      {editingTechnology && (
        <TechnologyForm
          technology={editingTechnology}
          onSubmit={handleUpdate}
          onCancel={() => setEditingTechnology(null)}
          isLoading={isUpdating}
        />
      )}
    </div>
  );
};
