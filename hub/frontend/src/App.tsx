import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Dashboard from './pages/Dashboard';
import { WorkflowBuilder } from './components/WorkflowBuilder/WorkflowBuilder';
import { ApprovalQueue } from './components/ApprovalQueue/ApprovalQueue';
import { ApprovalBadge } from './components/ApprovalBadge/ApprovalBadge';

function Navigation() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const linkClass = (path: string) => `
    px-4 py-2 rounded-lg transition-colors
    ${isActive(path)
      ? 'bg-slate-800 text-white'
      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}
  `;

  return (
    <nav className="flex items-center gap-4">
      <Link to="/" className={linkClass('/')}>
        Projects
      </Link>
      <Link to="/workflows" className={linkClass('/workflows')}>
        Workflows
      </Link>
      <Link to="/approvals" className={linkClass('/approvals')}>
        Approvals
      </Link>
      <ApprovalBadge />
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950">
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid #334155',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#f1f5f9',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#f1f5f9',
              },
            },
          }}
        />

        <header className="bg-slate-900 border-b border-slate-800">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gradient">
                  CommandCenter Hub
                </h1>
                <p className="text-slate-400 text-sm mt-1">
                  Manage multiple CommandCenter instances across projects
                </p>
              </div>
              <Navigation />
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/workflows" element={<WorkflowBuilder />} />
            <Route path="/approvals" element={<ApprovalQueue />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
