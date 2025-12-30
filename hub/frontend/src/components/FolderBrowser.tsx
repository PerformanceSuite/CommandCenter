import { useState, useEffect } from 'react';
import { filesystemApi } from '../services/api';
import type { FilesystemBrowseResponse } from '../types';

interface FolderBrowserProps {
  onSelect: (path: string) => void;
  onClose: () => void;
}

export default function FolderBrowser({ onSelect, onClose }: FolderBrowserProps) {
  const [currentPath, setCurrentPath] = useState('');
  const [parent, setParent] = useState<string | null>(null);
  const [directories, setDirectories] = useState<FilesystemBrowseResponse['directories']>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const browsePath = async (path?: string) => {
    setLoading(true);
    setError('');

    try {
      let targetPath = path;

      // If no path provided, start at home (which is PROJECTS_ROOT in Docker)
      if (!targetPath) {
        const homeData = await filesystemApi.getHome();
        targetPath = homeData.path;
      }

      const data = await filesystemApi.browse(targetPath);

      setCurrentPath(data.currentPath);
      setParent(data.parent);
      setDirectories(data.directories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to browse directory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    browsePath();
  }, []);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">Select Project Folder</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Current Path */}
        <div className="p-4 border-b border-slate-700 bg-slate-900">
          <div className="text-sm text-slate-400">Current folder:</div>
          <div className="font-mono text-sm mt-1 text-white">{currentPath || 'Loading...'}</div>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Directory List */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="text-center text-slate-400 py-8">Loading...</div>
          ) : (
            <div className="space-y-1">
              {/* Parent directory */}
              {parent && (
                <button
                  onClick={() => browsePath(parent)}
                  className="w-full text-left px-4 py-2 rounded hover:bg-slate-700 transition-colors flex items-center gap-2 text-white"
                >
                  <span>📁</span>
                  <span>..</span>
                </button>
              )}

              {/* Directories */}
              {directories.map(dir => (
                <button
                  key={dir.path}
                  onClick={() => browsePath(dir.path)}
                  onDoubleClick={() => onSelect(dir.path)}
                  className="w-full text-left px-4 py-2 rounded hover:bg-slate-700 transition-colors flex items-center gap-2 text-white"
                >
                  <span>📁</span>
                  <span>{dir.name}</span>
                </button>
              ))}

              {directories.length === 0 && !parent && (
                <div className="text-center text-slate-400 py-8">No subdirectories found</div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-700 flex justify-between items-center gap-3">
          <div className="text-sm text-slate-400">Double-click a folder to select it</div>
          <div className="flex gap-3">
            <button onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={() => onSelect(currentPath)}
              disabled={!currentPath}
              className="btn-primary"
            >
              Select Current Folder
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
