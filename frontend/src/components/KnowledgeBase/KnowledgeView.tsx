import React, { useState, useCallback, KeyboardEvent } from 'react';
import { Search, Database } from 'lucide-react';

interface KnowledgeSearchResult {
  id: string;
  content: string;
  source: string;
  relevance: number;
  timestamp: string;
}

export const KnowledgeView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      // API call will be implemented when backend is ready
      // const data = await api.queryKnowledge(query);
      // setResults(data);
      console.log('Searching for:', query);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const handleKeyPress = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  }, [handleSearch]);

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg shadow p-6" aria-labelledby="search-heading">
        <h2 id="search-heading" className="sr-only">Search Knowledge Base</h2>
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
              placeholder="Search knowledge base..."
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
      </section>

      <div className="bg-white rounded-lg shadow p-6">
        {results.length > 0 ? (
          <div className="space-y-4" role="region" aria-label="Search results">
            {results.map((result) => (
              <div
                key={result.id}
                className="border-b pb-4 last:border-b-0"
                role="article"
                aria-label={`Search result from ${result.source}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <p className="text-sm text-gray-500">{result.source}</p>
                  <span className="text-xs text-gray-400">
                    Relevance: {(result.relevance * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-gray-800">{result.content}</p>
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(result.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto text-gray-300 mb-4" aria-hidden="true" />
            <p className="text-gray-500 text-lg">Knowledge base search</p>
            <p className="text-gray-400 text-sm mt-2">
              Enter a query to search through your knowledge base
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
