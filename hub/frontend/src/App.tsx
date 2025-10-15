import Dashboard from './pages/Dashboard';

function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold text-gradient">
            CommandCenter Hub
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage multiple CommandCenter instances across projects
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
