import React, { useState, useCallback, useEffect, KeyboardEvent } from 'react';
import { Search, Upload, Database, Filter, AlertCircle } from 'lucide-react';
import { useKnowledge } from '../../hooks/useKnowledge';
import { useTechnologies } from '../../hooks/useTechnologies';
import { KnowledgeSearchResult } from './KnowledgeSearchResult';
import { DocumentUploadModal } from './DocumentUploadModal';
import { KnowledgeStats } from './KnowledgeStats';
import type { KnowledgeSearchRequest } from '../../types/knowledge';

export const KnowledgeView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showStats, setShowStats] = useState(false);

  const {
    searchResults,
    statistics,
    collections,
    categories,
    loading,
    error,
    currentCollection,
    query: performQuery,
    uploadDocument,
    fetchStatistics,
    fetchCollections,
    fetchCategories,
    clearSearchResults,
    switchCollection,
  } = useKnowledge();

  const { technologies } = useTechnologies();

  // Load initial data
  useEffect(() => {
    fetchCollections();
    fetchCategories();
    fetchStatistics();
  }, [fetchCollections, fetchCategories, fetchStatistics]);

  // Reload categories when collection changes
  useEffect(() => {
    fetchCategories(currentCollection);
  }, [currentCollection, fetchCategories]);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) {
      clearSearchResults();
      return;
    }

    const searchRequest: KnowledgeSearchRequest = {
      query,
      category: selectedCategory || undefined,
      limit: 10,
    };

    try {
      await performQuery(searchRequest);
    } catch (err) {
      console.error('Search failed:', err);
    }
  }, [query, selectedCategory, performQuery, clearSearchResults]);

  const handleKeyPress = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        handleSearch();
      }
    },
    [handleSearch]
  );

  const handleCollectionChange = useCallback(
    (collection: string) => {
      switchCollection(collection);
      clearSearchResults();
      setSelectedCategory('');
    },
    [switchCollection, clearSearchResults]
  );

  const handleUpload = useCallback(
    async (file: File, category: string, technologyId?: number, collection?: string) => {
      const result = await uploadDocument({
        file,
        category,
        technology_id: technologyId,
        collection,
      });

      // Refresh categories and stats after successful upload
      await fetchCategories(collection || currentCollection);
      await fetchStatistics(collection || currentCollection);

      return result;
    },
    [uploadDocument, fetchCategories, fetchStatistics, currentCollection]
  );

  const handleCategoryFilter = useCallback(
    (category: string) => {
      setSelectedCategory(category === selectedCategory ? '' : category);
    },
    [selectedCategory]
  );

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Database className="text-primary-600" size={28} />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
              <p className="text-sm text-gray-600">
                Semantic search powered by RAG (Retrieval-Augmented Generation)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowStats(!showStats)}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
            >
              <Database size={18} />
              <span>{showStats ? 'Hide' : 'Show'} Statistics</span>
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
            >
              <Upload size={18} />
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Collection Selector */}
        <div className="mb-4">
          <label htmlFor="collection" className="block text-sm font-medium text-gray-700 mb-2">
            Collection
          </label>
          <select
            id="collection"
            value={currentCollection}
            onChange={(e) => handleCollectionChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {collections.map((coll) => (
              <option key={coll} value={coll}>
                {coll}
              </option>
            ))}
          </select>
        </div>

        {/* Search Bar */}
        <div className="flex items-center gap-4" role="search">
          <div className="flex-1 relative">
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              size={20}
              aria-hidden="true"
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Search knowledge base using natural language..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent focus:outline-none"
              aria-label="Search query"
              aria-describedby="search-hint"
            />
            <span id="search-hint" className="sr-only">
              Press Enter to search or click the search button
            </span>
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            aria-label={loading ? 'Searching...' : 'Search'}
            type="button"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Category Filters */}
        {categories.length > 0 && (
          <div className="mt-4">
            <div className="flex items-center gap-2 mb-2">
              <Filter size={16} className="text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Filter by category:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => handleCategoryFilter(category)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    selectedCategory === category
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </button>
              ))}
              {selectedCategory && (
                <button
                  onClick={() => setSelectedCategory('')}
                  className="px-3 py-1.5 rounded-full text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                >
                  Clear Filter
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Statistics Panel */}
      {showStats && <KnowledgeStats statistics={statistics} loading={loading} />}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle size={20} />
            <p className="font-medium">Error: {error.message}</p>
          </div>
        </div>
      )}

      {/* Search Results */}
      <div className="bg-white rounded-lg shadow p-6">
        {searchResults.length > 0 ? (
          <div role="region" aria-label="Search results">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">
                Search Results ({searchResults.length})
              </h2>
              {selectedCategory && (
                <span className="text-sm text-gray-600">
                  Filtered by: <span className="font-medium">{selectedCategory}</span>
                </span>
              )}
            </div>
            <div className="space-y-4">
              {searchResults.map((result, index) => (
                <KnowledgeSearchResult
                  key={`${result.source_file}-${index}`}
                  result={result}
                  searchQuery={query}
                  onTechnologyClick={(techId) => {
                    console.log('Navigate to technology:', techId);
                    // TODO: Implement navigation to technology detail
                  }}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto text-gray-300 mb-4" aria-hidden="true" />
            <p className="text-gray-500 text-lg">Knowledge base search</p>
            <p className="text-gray-400 text-sm mt-2">
              {query
                ? 'No results found. Try different search terms or filters.'
                : 'Enter a query to search through your knowledge base'}
            </p>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
        technologies={technologies}
        categories={categories}
        collections={collections}
        currentCollection={currentCollection}
      />
    </div>
  );
};
