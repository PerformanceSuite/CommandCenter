import React from 'react';
import { useTechnologies } from '../../hooks/useTechnologies';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { TechnologyCard } from './TechnologyCard';

export const RadarView: React.FC = () => {
  const { technologies, loading } = useTechnologies();

  if (loading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  const groupedByDomain = technologies.reduce((acc, tech) => {
    if (!acc[tech.domain]) {
      acc[tech.domain] = [];
    }
    acc[tech.domain].push(tech);
    return acc;
  }, {} as Record<string, typeof technologies>);

  return (
    <div className="space-y-8">
      {Object.entries(groupedByDomain).map(([domain, techs]) => (
        <div key={domain} className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold mb-4 capitalize">{domain}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {techs.map((tech) => (
              <TechnologyCard key={tech.id} technology={tech} />
            ))}
          </div>
        </div>
      ))}

      {technologies.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">No technologies tracked yet</p>
          <p className="text-gray-400 text-sm mt-2">Add technologies to see them on the radar</p>
        </div>
      )}
    </div>
  );
};
