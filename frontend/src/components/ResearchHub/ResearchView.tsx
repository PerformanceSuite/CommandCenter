import React from 'react';
import { FileText, Calendar, Tag } from 'lucide-react';

export const ResearchView: React.FC = () => {
  // Placeholder data - will be connected to API later
  const researchEntries = [
    {
      id: '1',
      title: 'JUCE Framework Research',
      source: 'Documentation',
      summary: 'Audio plugin development framework with C++',
      tags: ['audio', 'c++', 'framework'],
      created_at: '2025-10-01',
    },
    {
      id: '2',
      title: 'LangChain Integration Patterns',
      source: 'GitHub',
      summary: 'Best practices for RAG systems',
      tags: ['ai', 'rag', 'python'],
      created_at: '2025-10-03',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Research Entries</h2>
          <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            Add Entry
          </button>
        </div>

        <div className="space-y-4">
          {researchEntries.map((entry) => (
            <div
              key={entry.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-start gap-3">
                  <FileText size={20} className="text-primary-600 mt-1" />
                  <div>
                    <h3 className="font-semibold text-lg">{entry.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{entry.summary}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Calendar size={14} />
                  {new Date(entry.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-1">
                  <Tag size={14} />
                  {entry.source}
                </div>
              </div>

              <div className="flex gap-2 mt-3">
                {entry.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
