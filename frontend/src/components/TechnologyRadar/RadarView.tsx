import React, { useMemo, useState } from 'react';
import { useTechnologies } from '../../hooks/useTechnologies';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { TechnologyCard } from './TechnologyCard';
import { TechnologyForm } from './TechnologyForm';
import { Plus, Search, Filter, AlertCircle } from 'lucide-react';
import { TechnologyDomain, TechnologyStatus, Technology, TechnologyCreate, TechnologyUpdate } from '../../types/technology';

export const RadarView: React.FC = () => {
  const {
    technologies,
    loading,
    error,
    createTechnology,
    updateTechnology,
    deleteTechnology,
    isCreating,
    isUpdating,
  } = useTechnologies();

  // UI State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTechnology, setEditingTechnology] = useState<Technology | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomains, setSelectedDomains] = useState<Set<TechnologyDomain>>(new Set());
  const [selectedStatuses, setSelectedStatuses] = useState<Set<TechnologyStatus>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  // Filter technologies
  const filteredTechnologies = useMemo(() => {
    return technologies.filter((tech) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          tech.title.toLowerCase().includes(query) ||
          tech.vendor?.toLowerCase().includes(query) ||
          tech.description?.toLowerCase().includes(query) ||
          tech.tags?.toLowerCase().includes(query);
        if (!matchesSearch) return false;
      }

      // Domain filter
      if (selectedDomains.size > 0 && !selectedDomains.has(tech.domain)) {
        return false;
      }

      // Status filter
      if (selectedStatuses.size > 0 && !selectedStatuses.has(tech.status)) {
        return false;
      }

      return true;
    });
  }, [technologies, searchQuery, selectedDomains, selectedStatuses]);

  // Group by domain
  const groupedByDomain = useMemo(
    () => filteredTechnologies.reduce((acc, tech) => {
      if (!acc[tech.domain]) {
        acc[tech.domain] = [];
      }
      acc[tech.domain].push(tech);
      return acc;
    }, {} as Record<string, typeof filteredTechnologies>),
    [filteredTechnologies]
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

  const toggleDomain = (domain: TechnologyDomain) => {
    setSelectedDomains(prev => {
      const newSet = new Set(prev);
      if (newSet.has(domain)) {
        newSet.delete(domain);
      } else {
        newSet.add(domain);
      }
      return newSet;
    });
  };

  const toggleStatus = (status: TechnologyStatus) => {
    setSelectedStatuses(prev => {
      const newSet = new Set(prev);
      if (newSet.has(status)) {
        newSet.delete(status);
      } else {
        newSet.add(status);
      }
      return newSet;
    });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedDomains(new Set());
    setSelectedStatuses(new Set());
  };

  const hasActiveFilters = searchQuery || selectedDomains.size > 0 || selectedStatuses.size > 0;

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
      {/* Header with Create Button */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Technology Radar</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors flex items-center gap-2"
        >
          <Plus size={20} />
          Add Technology
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search technologies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 border rounded-md transition-colors flex items-center gap-2 ${
              showFilters || hasActiveFilters
                ? 'bg-primary-50 border-primary-300 text-primary-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Filter size={20} />
            Filters
            {hasActiveFilters && (
              <span className="bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">
                {(selectedDomains.size + selectedStatuses.size) || ''}
              </span>
            )}
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="border-t border-gray-200 pt-4 space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-700">Domain</h3>
                {selectedDomains.size > 0 && (
                  <button
                    onClick={() => setSelectedDomains(new Set())}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.values(TechnologyDomain).map((domain) => (
                  <button
                    key={domain}
                    onClick={() => toggleDomain(domain)}
                    className={`px-3 py-1 text-sm rounded-full transition-colors ${
                      selectedDomains.has(domain)
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {domain.replace(/-/g, ' ').toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-700">Status</h3>
                {selectedStatuses.size > 0 && (
                  <button
                    onClick={() => setSelectedStatuses(new Set())}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.values(TechnologyStatus).map((status) => (
                  <button
                    key={status}
                    onClick={() => toggleStatus(status)}
                    className={`px-3 py-1 text-sm rounded-full transition-colors ${
                      selectedStatuses.has(status)
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {hasActiveFilters && (
              <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  Showing {filteredTechnologies.length} of {technologies.length} technologies
                </p>
                <button
                  onClick={clearFilters}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Technologies Grid */}
      {domainEntries.length > 0 ? (
        domainEntries.map(([domain, techs]) => (
          <section
            key={domain}
            className="bg-white rounded-lg shadow p-6"
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
        ))
      ) : (
        <div
          className="bg-white rounded-lg shadow p-12 text-center"
          role="status"
          aria-live="polite"
        >
          {hasActiveFilters ? (
            <>
              <p className="text-gray-500 text-lg">No technologies match your filters</p>
              <button
                onClick={clearFilters}
                className="mt-4 text-primary-600 hover:text-primary-700 font-medium"
              >
                Clear filters
              </button>
            </>
          ) : (
            <>
              <p className="text-gray-500 text-lg">No technologies tracked yet</p>
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
