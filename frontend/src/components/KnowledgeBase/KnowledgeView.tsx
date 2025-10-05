import React, { useState } from 'react';
import { Search, Database } from 'lucide-react';

export const KnowledgeView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
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
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search knowledge base..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        {results.length > 0 ? (
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="border-b pb-4 last:border-b-0">
                <p className="text-gray-800">{result}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto text-gray-300 mb-4" />
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
