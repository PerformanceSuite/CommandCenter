import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
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
        <div className="flex h-screen bg-slate-900">
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

      {/* Global toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937', // Slightly lighter for better contrast
            color: '#f9fafb',
            fontSize: '14px',
            padding: '12px 16px',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
          success: {
            duration: 3000,
            style: {
              background: '#065f46',
              color: '#f0fdf4',
            },
            iconTheme: {
              primary: '#10b981',
              secondary: '#f0fdf4',
            },
          },
          error: {
            duration: 5000,
            style: {
              background: '#7f1d1d',
              color: '#fef2f2',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fef2f2',
            },
          },
          loading: {
            style: {
              background: '#1e40af',
              color: '#eff6ff',
            },
          },
        }}
      />
    </ErrorBoundary>
  );
}

export default App;
