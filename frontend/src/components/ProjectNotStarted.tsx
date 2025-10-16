/**
 * Component shown when backend is not available
 * Provides instructions to start the project
 */

interface ProjectNotStartedProps {
  projectName?: string;
  backendPort?: number;
}

function ProjectNotStarted({ projectName = "Command Center", backendPort = 8000 }: ProjectNotStartedProps) {
  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-8 shadow-2xl">
          {/* Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-slate-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 12h14M12 5l7 7-7 7"
                />
              </svg>
            </div>
          </div>

          {/* Title */}
          <h1 className="text-3xl font-bold text-white text-center mb-4">
            {projectName}
          </h1>

          <h2 className="text-xl text-slate-400 text-center mb-8">
            Project Not Started
          </h2>

          {/* Instructions */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">To start this project:</h3>
            <ol className="space-y-3 text-slate-300">
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  1
                </span>
                <div>
                  <p className="font-medium">Open a terminal in the project directory</p>
                  <code className="text-sm text-slate-400 font-mono block mt-1">
                    cd {window.location.hostname === 'localhost' ? 'commandcenter' : 'your-project/commandcenter'}
                  </code>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  2
                </span>
                <div>
                  <p className="font-medium">Start the containers</p>
                  <code className="text-sm text-slate-400 font-mono block mt-1">
                    docker-compose up -d
                  </code>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  3
                </span>
                <div>
                  <p className="font-medium">Wait for services to start (~30 seconds)</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  4
                </span>
                <div>
                  <p className="font-medium">Refresh this page</p>
                </div>
              </li>
            </ol>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Refresh Page
          </button>

          {/* Debug Info */}
          <div className="mt-6 p-4 bg-slate-800/30 border border-slate-700/50 rounded text-sm text-slate-400">
            <p className="mb-1">
              <span className="font-medium text-slate-300">Frontend:</span> {window.location.origin}
            </p>
            <p>
              <span className="font-medium text-slate-300">Backend:</span> http://localhost:{backendPort}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProjectNotStarted;
