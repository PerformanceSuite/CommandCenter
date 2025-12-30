import { useState } from 'react';
import { HypothesisDashboard } from '../components/HypothesisDashboard';
import { EvidenceExplorer } from '../components/EvidenceExplorer';
import { SettingsDashboard } from '../components/SettingsDashboard';

type TabType = 'hypotheses' | 'evidence' | 'settings';

export function HypothesesPage() {
  const [activeTab, setActiveTab] = useState<TabType>('hypotheses');

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-white">AI Arena</h2>
        <p className="text-slate-400 mt-1">
          Validate business hypotheses using multi-model AI debates
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 mb-6 border-b border-slate-700">
        <TabButton
          active={activeTab === 'hypotheses'}
          onClick={() => setActiveTab('hypotheses')}
        >
          <HypothesesIcon className="w-4 h-4" />
          Hypotheses
        </TabButton>
        <TabButton
          active={activeTab === 'evidence'}
          onClick={() => setActiveTab('evidence')}
        >
          <EvidenceIcon className="w-4 h-4" />
          Evidence Explorer
        </TabButton>
        <TabButton
          active={activeTab === 'settings'}
          onClick={() => setActiveTab('settings')}
        >
          <SettingsIcon className="w-4 h-4" />
          Settings
        </TabButton>
      </div>

      {/* Content */}
      {activeTab === 'hypotheses' && <HypothesisDashboard />}
      {activeTab === 'evidence' && <EvidenceExplorer />}
      {activeTab === 'settings' && <SettingsDashboard />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
        active
          ? 'text-white border-blue-500'
          : 'text-slate-400 border-transparent hover:text-white hover:border-slate-600'
      }`}
    >
      {children}
    </button>
  );
}

function HypothesesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
      />
    </svg>
  );
}

function EvidenceIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}

function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );
}

export default HypothesesPage;
