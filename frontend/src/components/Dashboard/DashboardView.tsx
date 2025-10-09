import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GitBranch, Database, ClipboardList, FileText, Plus, Activity, Users, Shield, Bot } from 'lucide-react';

export const DashboardView: React.FC = () => {
  const navigate = useNavigate();

  // Mock data for display
  const stats = {
    repositoryCount: 42,
    technologyCount: 15,
    researchTaskCount: 8,
    knowledgeEntryCount: 234
  };

  const recentActivity = [
    { id: 1, type: 'repo', message: 'Repository CommandCenter updated', time: '2 hours ago' },
    { id: 2, type: 'tech', message: 'Added React 18 to tech stack', time: '5 hours ago' },
    { id: 3, type: 'research', message: 'Completed AI integration research', time: '1 day ago' },
    { id: 4, type: 'knowledge', message: 'Added 5 new documentation entries', time: '2 days ago' }
  ];

  const quickActions = [
    { label: 'AI Tools', path: '/ai-tools', icon: <Bot className="w-6 h-6" />, color: 'from-purple-500 to-pink-500' },
    { label: 'Dev Tools Hub', path: '/dev-tools', icon: <Shield className="w-6 h-6" />, color: 'from-blue-500 to-indigo-500' },
    { label: 'Tech Radar', path: '/radar', icon: <Activity className="w-6 h-6" />, color: 'from-green-500 to-emerald-500' },
    { label: 'Research Hub', path: '/research', icon: <ClipboardList className="w-6 h-6" />, color: 'from-orange-500 to-red-500' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Command Center Dashboard</h1>
            <p className="text-gray-600 mt-1">Welcome to your unified development hub</p>
          </div>
          <button
            onClick={() => navigate('/dev-tools')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Open Dev Tools
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {quickActions.map((action) => (
          <button
            key={action.path}
            onClick={() => navigate(action.path)}
            className={`bg-gradient-to-br ${action.color} text-white rounded-lg p-6 hover:scale-105 transition-transform shadow-lg`}
          >
            <div className="flex flex-col items-center">
              {action.icon}
              <span className="mt-2 font-semibold">{action.label}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Repositories</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.repositoryCount}</p>
            </div>
            <GitBranch className="w-8 h-8 text-indigo-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Technologies</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.technologyCount}</p>
            </div>
            <Database className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Research Tasks</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.researchTaskCount}</p>
            </div>
            <ClipboardList className="w-8 h-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Knowledge Entries</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.knowledgeEntryCount}</p>
            </div>
            <FileText className="w-8 h-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {recentActivity.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-700">{item.message}</span>
                </div>
                <span className="text-xs text-gray-500">{item.time}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <span className="text-sm text-gray-700">Backend API</span>
              <span className="text-sm font-medium text-green-600">Online</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <span className="text-sm text-gray-700">MCP Servers</span>
              <span className="text-sm font-medium text-green-600">6 Connected</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <span className="text-sm text-gray-700">AI Models</span>
              <span className="text-sm font-medium text-green-600">5 Available</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <span className="text-sm text-gray-700">CodeMender</span>
              <span className="text-sm font-medium text-yellow-600">Pending Release</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-6 text-white">
        <h2 className="text-xl font-bold mb-3">🚀 New Features Available</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="font-semibold mb-1">Claude Agent SDK</h3>
            <p className="text-sm text-indigo-100">Complete agentic development platform replacing Goose and others</p>
          </div>
          <div>
            <h3 className="font-semibold mb-1">MCP Integration</h3>
            <p className="text-sm text-indigo-100">6 protocol servers connected for enhanced capabilities</p>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Multi-Model Support</h3>
            <p className="text-sm text-indigo-100">Claude, GPT-4, Gemini, and local models all in one place</p>
          </div>
        </div>
      </div>
    </div>
  );
};