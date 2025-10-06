import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Lazy load route components for code splitting
const DashboardView = lazy(() => import('./components/Dashboard/DashboardView').then(m => ({ default: m.DashboardView })));
const RadarView = lazy(() => import('./components/TechnologyRadar/RadarView').then(m => ({ default: m.RadarView })));
const ResearchView = lazy(() => import('./components/ResearchHub/ResearchView').then(m => ({ default: m.ResearchView })));
const KnowledgeView = lazy(() => import('./components/KnowledgeBase/KnowledgeView').then(m => ({ default: m.KnowledgeView })));
const SettingsView = lazy(() => import('./components/Settings/SettingsView').then(m => ({ default: m.SettingsView })));

// Loading fallback component
const PageLoadingFallback = () => (
  <div className="flex items-center justify-center h-full">
    <LoadingSpinner size="lg" />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="flex h-screen bg-gray-50">
          <Sidebar />

          <div className="flex-1 ml-64 flex flex-col overflow-hidden">
            <Header />

            <main className="flex-1 overflow-y-auto p-6" role="main">
              <Suspense fallback={<PageLoadingFallback />}>
                <Routes>
                  <Route path="/" element={<DashboardView />} />
                  <Route path="/radar" element={<RadarView />} />
                  <Route path="/research" element={<ResearchView />} />
                  <Route path="/knowledge" element={<KnowledgeView />} />
                  <Route path="/settings" element={<SettingsView />} />
                </Routes>
              </Suspense>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
