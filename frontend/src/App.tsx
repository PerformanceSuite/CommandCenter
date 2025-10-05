import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { DashboardView } from './components/Dashboard/DashboardView';
import { RadarView } from './components/TechnologyRadar/RadarView';
import { ResearchView } from './components/ResearchHub/ResearchView';
import { KnowledgeView } from './components/KnowledgeBase/KnowledgeView';
import { SettingsView } from './components/Settings/SettingsView';

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />

        <div className="flex-1 ml-64 flex flex-col overflow-hidden">
          <Header />

          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<DashboardView />} />
              <Route path="/radar" element={<RadarView />} />
              <Route path="/research" element={<ResearchView />} />
              <Route path="/knowledge" element={<KnowledgeView />} />
              <Route path="/settings" element={<SettingsView />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
