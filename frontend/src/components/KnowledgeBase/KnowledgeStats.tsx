import React from 'react';
import { Database, FileText, Tag, Cpu, Layers } from 'lucide-react';
import type { KnowledgeStatistics } from '../../types/knowledge';

interface KnowledgeStatsProps {
  statistics: KnowledgeStatistics | null;
  loading: boolean;
}

export const KnowledgeStats: React.FC<KnowledgeStatsProps> = ({ statistics, loading }) => {
  if (loading) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-700 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-20 bg-slate-700 rounded"></div>
            <div className="h-20 bg-slate-700 rounded"></div>
            <div className="h-20 bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!statistics) {
    return null;
  }

  const totalCategories = Object.keys(statistics.vector_db.categories).length;
  const categoryBreakdown = Object.entries(statistics.vector_db.categories).sort(
    ([, a], [, b]) => b - a
  );

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-1">
          <Database className="text-primary-600" size={24} />
          <h2 className="text-xl font-semibold text-white">Knowledge Base Statistics</h2>
        </div>
        <p className="text-sm text-slate-400">Collection: {statistics.collection}</p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {/* Total Chunks */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Layers className="text-blue-600" size={24} />
              <span className="text-3xl font-bold text-blue-900">
                {statistics.vector_db.total_chunks.toLocaleString()}
              </span>
            </div>
            <p className="text-sm font-medium text-blue-800">Total Chunks</p>
            <p className="text-xs text-blue-600 mt-1">Vector embeddings stored</p>
          </div>

          {/* Total Documents */}
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <FileText className="text-green-600" size={24} />
              <span className="text-3xl font-bold text-green-900">
                {statistics.database.total_entries.toLocaleString()}
              </span>
            </div>
            <p className="text-sm font-medium text-green-800">Documents</p>
            <p className="text-xs text-green-600 mt-1">Processed and indexed</p>
          </div>

          {/* Categories */}
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <Tag className="text-purple-600" size={24} />
              <span className="text-3xl font-bold text-purple-900">{totalCategories}</span>
            </div>
            <p className="text-sm font-medium text-purple-800">Categories</p>
            <p className="text-xs text-purple-600 mt-1">Topic classifications</p>
          </div>
        </div>

        {/* Category Breakdown */}
        {categoryBreakdown.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Tag size={16} />
              Category Breakdown
            </h3>
            <div className="space-y-2">
              {categoryBreakdown.map(([category, count]) => {
                const percentage = (count / statistics.vector_db.total_chunks) * 100;
                return (
                  <div key={category}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-medium text-slate-300">{category}</span>
                      <span className="text-slate-400">
                        {count} chunks ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Embedding Model Info */}
        <div className="bg-slate-900 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="text-slate-400" size={18} />
            <h3 className="text-sm font-semibold text-slate-300">Embedding Model</h3>
          </div>
          <p className="text-sm text-gray-800 font-mono">{statistics.embedding_model}</p>
          <p className="text-xs text-slate-400 mt-1">
            Local model for semantic search (no API costs)
          </p>
        </div>
      </div>
    </div>
  );
};
