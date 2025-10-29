import { Suspense, lazy, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { Sidebar } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import ProjectNotStarted from './components/ProjectNotStarted';

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
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);
  // Read project name from runtime config (injected by docker-entrypoint.sh) or fall back to build-time env
  const [projectName] = useState(
    (window as Window & { RUNTIME_CONFIG?: { PROJECT_NAME?: string } }).RUNTIME_CONFIG?.PROJECT_NAME ||
    import.meta.env.VITE_PROJECT_NAME ||
    'Command Center'
  );

  useEffect(() => {
    // Check if backend is available
    const checkBackend = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/health`, {
          method: 'GET',
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        setBackendAvailable(response.ok);
      } catch (error) {
        clearTimeout(timeoutId);
        setBackendAvailable(false);
      }
    };

    checkBackend();
  }, []);

  // Show loading while checking backend
  if (backendAvailable === null) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Show "Project Not Started" if backend is unavailable
  if (!backendAvailable) {
    return <ProjectNotStarted projectName={projectName} backendPort={8000} />;
  }

  // Backend is available, show normal app
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
