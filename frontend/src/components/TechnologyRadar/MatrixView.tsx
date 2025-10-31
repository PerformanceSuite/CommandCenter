import React, { useMemo, useState } from 'react';
import type { Technology } from '../../types/technology';
import {
  ArrowUpDown,
  ExternalLink,
  Star,
  GitBranch,
  DollarSign,
  Edit2,
  Trash2
} from 'lucide-react';

interface MatrixViewProps {
  technologies: Technology[];
  onEdit?: (technology: Technology) => void;
  onDelete?: (technology: Technology) => void;
}

type SortField =
  | 'title'
  | 'vendor'
  | 'domain'
  | 'status'
  | 'relevance_score'
  | 'priority'
  | 'maturity_level'
  | 'stability_score'
  | 'cost_tier'
  | 'github_stars'
  | 'integration_difficulty';

type SortDirection = 'asc' | 'desc';

export const MatrixView: React.FC<MatrixViewProps> = ({ technologies, onEdit, onDelete }) => {
  const [sortField, setSortField] = useState<SortField>('relevance_score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());

  // Sort technologies
  const sortedTechnologies = useMemo(() => {
    return [...technologies].sort((a, b) => {
      let aVal: unknown = a[sortField];
      let bVal: unknown = b[sortField];

      // Handle null/undefined values
      if (aVal === null && bVal === null) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      // String comparison for text fields
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        const aLower = aVal.toLowerCase();
        const bLower = bVal.toLowerCase();
        const comparison = aLower < bLower ? -1 : aLower > bLower ? 1 : 0;
        return sortDirection === 'asc' ? comparison : -comparison;
      }

      // Numeric comparison
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [technologies, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const toggleRowSelection = (id: number) => {
    setSelectedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleAllRows = () => {
    if (selectedRows.size === technologies.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(technologies.map(t => t.id)));
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => (
    <ArrowUpDown
      size={14}
      className={`inline ml-1 ${sortField === field ? 'text-primary-600' : 'text-gray-400'}`}
    />
  );

  const formatCostTier = (tier: string | null) => {
    if (!tier) return '-';
    return tier.charAt(0).toUpperCase() + tier.slice(1);
  };

  const formatMaturityLevel = (level: string | null) => {
    if (!level) return '-';
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  const formatIntegrationDifficulty = (difficulty: string | null) => {
    if (!difficulty) return '-';
    return difficulty.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  const maturityLevelColors: Record<string, string> = {
    alpha: 'text-red-700 bg-red-100',
    beta: 'text-orange-700 bg-orange-100',
    stable: 'text-green-700 bg-green-100',
    mature: 'text-blue-700 bg-blue-100',
    legacy: 'text-slate-300 bg-slate-800',
  };

  const costTierColors: Record<string, string> = {
    free: 'text-green-700 bg-green-100',
    freemium: 'text-emerald-700 bg-emerald-100',
    affordable: 'text-blue-700 bg-blue-100',
    moderate: 'text-yellow-700 bg-yellow-100',
    expensive: 'text-orange-700 bg-orange-100',
    enterprise: 'text-red-700 bg-red-100',
  };

  const statusColors: Record<string, string> = {
    discovery: 'text-purple-700 bg-purple-100',
    research: 'text-blue-700 bg-blue-100',
    evaluation: 'text-yellow-700 bg-yellow-100',
    implementation: 'text-orange-700 bg-orange-100',
    integrated: 'text-green-700 bg-green-100',
    archived: 'text-slate-300 bg-slate-800',
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg shadow overflow-hidden">
      {/* Table Controls */}
      <div className="px-4 py-3 border-b border-gray-200 bg-slate-900 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={selectedRows.size === technologies.length && technologies.length > 0}
              onChange={toggleAllRows}
              className="rounded border-gray-300"
            />
            <span>{selectedRows.size > 0 ? `${selectedRows.size} selected` : 'Select all'}</span>
          </label>
        </div>
        <div className="text-sm text-slate-400">
          {technologies.length} {technologies.length === 1 ? 'technology' : 'technologies'}
        </div>
      </div>

      {/* Scrollable Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 border-b border-gray-200 sticky top-0 z-10">
            <tr>
              <th className="w-10 px-3 py-3"></th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('title')}
              >
                Technology <SortIcon field="title" />
              </th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('vendor')}
              >
                Vendor <SortIcon field="vendor" />
              </th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('domain')}
              >
                Domain <SortIcon field="domain" />
              </th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('status')}
              >
                Status <SortIcon field="status" />
              </th>
              <th
                className="px-4 py-3 text-center font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('priority')}
              >
                Priority <SortIcon field="priority" />
              </th>
              <th
                className="px-4 py-3 text-center font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('relevance_score')}
              >
                Relevance <SortIcon field="relevance_score" />
              </th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('maturity_level')}
              >
                Maturity <SortIcon field="maturity_level" />
              </th>
              <th
                className="px-4 py-3 text-center font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('stability_score')}
              >
                Stability <SortIcon field="stability_score" />
              </th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('cost_tier')}
              >
                Cost <SortIcon field="cost_tier" />
              </th>
              <th
                className="px-4 py-3 text-center font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('github_stars')}
              >
                GitHub Stars <SortIcon field="github_stars" />
              </th>
              <th
                className="px-4 py-3 text-left font-semibold text-slate-300 cursor-pointer hover:bg-slate-700 transition-colors"
                onClick={() => handleSort('integration_difficulty')}
              >
                Integration <SortIcon field="integration_difficulty" />
              </th>
              <th className="px-4 py-3 text-left font-semibold text-slate-300">
                Links
              </th>
              <th className="px-4 py-3 text-right font-semibold text-slate-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedTechnologies.map((tech) => (
              <tr
                key={tech.id}
                className={`hover:bg-slate-900 transition-colors ${
                  selectedRows.has(tech.id) ? 'bg-primary-50' : ''
                }`}
              >
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.has(tech.id)}
                    onChange={() => toggleRowSelection(tech.id)}
                    className="rounded border-gray-300"
                  />
                </td>
                <td className="px-4 py-3 font-medium text-white">
                  {tech.title}
                </td>
                <td className="px-4 py-3 text-slate-400">
                  {tech.vendor || '-'}
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 text-xs font-medium rounded bg-slate-800 text-slate-300">
                    {tech.domain.replace(/-/g, ' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs font-medium rounded ${statusColors[tech.status] || 'bg-slate-800 text-slate-300'}`}>
                    {tech.status.charAt(0).toUpperCase() + tech.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span
                        key={star}
                        className={`text-sm ${
                          star <= tech.priority ? 'text-yellow-500' : 'text-gray-300'
                        }`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col items-center gap-1">
                    <span className="font-medium text-white">{tech.relevance_score}</span>
                    <div className="w-16 bg-slate-700 rounded-full h-1.5">
                      <div
                        className="bg-primary-600 h-1.5 rounded-full"
                        style={{ width: `${tech.relevance_score}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {tech.maturity_level ? (
                    <span className={`px-2 py-1 text-xs font-medium rounded ${maturityLevelColors[tech.maturity_level] || 'bg-slate-800 text-slate-300'}`}>
                      {formatMaturityLevel(tech.maturity_level)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {tech.stability_score !== null ? (
                    <div className="flex flex-col items-center gap-1">
                      <span className="font-medium text-white">{tech.stability_score}</span>
                      <div className="w-12 bg-slate-700 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full"
                          style={{ width: `${tech.stability_score}%` }}
                        />
                      </div>
                    </div>
                  ) : (
                    <span className="text-gray-400 text-center block">-</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {tech.cost_tier ? (
                    <span className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1 ${costTierColors[tech.cost_tier] || 'bg-slate-800 text-slate-300'}`}>
                      <DollarSign size={10} />
                      {formatCostTier(tech.cost_tier)}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  {tech.github_stars !== null ? (
                    <div className="flex items-center justify-center gap-1">
                      <Star size={12} className="text-yellow-500" />
                      <span className="font-medium text-white">
                        {tech.github_stars.toLocaleString()}
                      </span>
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-slate-400 text-xs">
                  {formatIntegrationDifficulty(tech.integration_difficulty)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    {tech.website_url && (
                      <a
                        href={tech.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700"
                        title="Website"
                      >
                        <ExternalLink size={14} />
                      </a>
                    )}
                    {tech.repository_url && (
                      <a
                        href={tech.repository_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700"
                        title="Repository"
                      >
                        <GitBranch size={14} />
                      </a>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(tech)}
                        className="text-slate-400 hover:text-primary-600 transition-colors"
                        title="Edit"
                      >
                        <Edit2 size={16} />
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => onDelete(tech)}
                        className="text-slate-400 hover:text-red-600 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {technologies.length === 0 && (
        <div className="px-4 py-12 text-center text-slate-500">
          <p>No technologies to display</p>
        </div>
      )}
    </div>
  );
};
