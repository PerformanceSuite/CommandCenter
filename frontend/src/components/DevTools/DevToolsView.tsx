import React, { useState, useEffect } from 'react';
import { 
  Bot, Terminal, Shield, Brain, Code2, AlertCircle, CheckCircle, Clock,
  Sparkles, FileText, Settings, Play, RefreshCw, ExternalLink, Package,
  Zap, Lock, Activity, Github, Server, Cpu, Database, Globe, 
  Layers, GitBranch, GitPullRequest, GitCommit, Cloud, Monitor,
  Command, Wrench, Boxes, Users, BookOpen, MessageCircle, Search,
  Eye, Rocket, ChevronRight, Download, Upload, Copy, Check
} from 'lucide-react';
import axios from 'axios';

export const DevToolsView = () => {
  const [activeCategory, setActiveCategory] = useState('overview');
  const [activeTab, setActiveTab] = useState('status');
  const [selectedModel, setSelectedModel] = useState('claude');
  const [consoleOutput, setConsoleOutput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [mcpStatus, setMcpStatus] = useState({});
  const [githubStats, setGithubStats] = useState(null);

  // Categories of tools
  const categories = [
    { id: 'overview', name: 'Overview', icon: <Monitor className="w-4 h-4" /> },
    { id: 'models', name: 'AI Models', icon: <Brain className="w-4 h-4" /> },
    { id: 'mcp', name: 'MCP Servers', icon: <Server className="w-4 h-4" /> },
    { id: 'assistants', name: 'Code Assistants', icon: <Bot className="w-4 h-4" /> },
    { id: 'github', name: 'GitHub', icon: <Github className="w-4 h-4" /> },
    { id: 'security', name: 'Security', icon: <Shield className="w-4 h-4" /> },
    { id: 'workflows', name: 'Workflows', icon: <GitBranch className="w-4 h-4" /> },
    { id: 'console', name: 'Console', icon: <Terminal className="w-4 h-4" /> }
  ];

  // Model Providers Configuration
  const modelProviders = [
    {
      id: 'claude',
      name: 'Claude (Anthropic)',
      status: 'active',
      models: ['Claude 3 Opus', 'Claude 3 Sonnet', 'Claude 3 Haiku'],
      features: ['Claude Agent SDK', 'MCP Support', 'Projects', 'Artifacts'],
      apiKey: true,
      icon: <MessageCircle className="w-5 h-5" />
    },
    {
      id: 'openai',
      name: 'OpenAI',
      status: 'active',
      models: ['GPT-4', 'GPT-4 Turbo', 'GPT-3.5'],
      features: ['Chat', 'Completions', 'Embeddings', 'DALL-E'],
      apiKey: true,
      icon: <Sparkles className="w-5 h-5" />
    },
    {
      id: 'gemini',
      name: 'Google Gemini',
      status: 'active',
      models: ['Gemini Pro', 'Gemini Pro Vision'],
      features: ['Multimodal', 'Long Context', 'Function Calling'],
      apiKey: true,
      icon: <Sparkles className="w-5 h-5" />
    },
    {
      id: 'ollama',
      name: 'Ollama (Local)',
      status: 'active',
      models: ['Llama 2', 'Mistral', 'CodeLlama', 'Phi-2'],
      features: ['Local Models', 'No API Key', 'Privacy'],
      apiKey: false,
      icon: <Cpu className="w-5 h-5" />
    },
    {
      id: 'lmstudio',
      name: 'LM Studio',
      status: 'active',
      models: ['Any GGUF Model'],
      features: ['Local Server', 'GPU Acceleration', 'Model Management'],
      apiKey: false,
      icon: <Server className="w-5 h-5" />
    }
  ];

  // MCP Servers Configuration
  const mcpServers = [
    {
      id: 'filesystem',
      name: 'Filesystem',
      status: 'active',
      description: 'Read/write files, navigate directories',
      path: '/Users/danielconnolly',
      icon: <FileText className="w-5 h-5" />
    },
    {
      id: 'github',
      name: 'GitHub',
      status: 'active',
      description: 'Manage repos, PRs, issues, actions',
      features: ['Create/fork repos', 'Manage PRs', 'Issues', 'Actions'],
      icon: <Github className="w-5 h-5" />
    },
    {
      id: 'brave-search',
      name: 'Brave Search',
      status: 'active',
      description: 'Web search with privacy',
      icon: <Search className="w-5 h-5" />
    },
    {
      id: 'puppeteer',
      name: 'Puppeteer',
      status: 'active',
      description: 'Browser automation and testing',
      icon: <Globe className="w-5 h-5" />
    },
    {
      id: 'desktop-commander',
      name: 'Desktop Commander',
      status: 'active',
      description: 'Control desktop applications',
      icon: <Command className="w-5 h-5" />
    },
    {
      id: 'git',
      name: 'Git',
      status: 'active',
      description: 'Version control operations',
      icon: <GitCommit className="w-5 h-5" />
    }
  ];

  // Code Assistants - Claude Agent SDK replaces most others
  const codeAssistants = [
    {
      id: 'claude-agent',
      name: 'Claude Agent SDK',
      status: 'active',
      description: 'Complete agentic development platform - replaces Goose, Copilot, and most other assistants',
      commands: ['claude-code', 'cc', 'claude'],
      features: [
        'Multi-file editing',
        'Full project context',
        'Automated testing',
        'Code review & refactoring',
        'Session management',
        'Debugging assistance',
        'Documentation generation',
        'Architecture planning',
        'Performance optimization',
        'Security analysis'
      ],
      icon: <Code2 className="w-5 h-5" />
    },
    {
      id: 'codex',
      name: 'Codex',
      status: 'legacy',
      description: 'Basic code completion (mostly replaced by Claude)',
      commands: ['codex', 'cdx'],
      features: ['Auto-complete', 'Simple generation'],
      icon: <Wrench className="w-5 h-5" />
    },
    {
      id: 'jules',
      name: 'Jules Helper',
      status: 'active',
      description: 'Task management and workflow automation',
      commands: ['jules_task', 'jules_list', 'jules_repos'],
      features: ['Task tracking', 'GitHub issues', 'TODO processing'],
      icon: <Boxes className="w-5 h-5" />
    },
    {
      id: 'codemender',
      name: 'CodeMender',
      status: 'pending',
      description: 'Google DeepMind security agent',
      features: ['Auto-patching', 'Vulnerability detection', 'Code hardening'],
      stats: { patches: 72, maxLines: '4.5M' },
      icon: <Shield className="w-5 h-5" />
    }
  ];

  // GitHub Features (from existing CommandCenter)
  const githubFeatures = [
    { name: 'Repositories', count: 42, trend: '+3' },
    { name: 'Pull Requests', count: 8, status: 'open' },
    { name: 'Issues', count: 15, status: 'open' },
    { name: 'Actions', count: 5, status: 'running' },
    { name: 'Forks', count: 127 },
    { name: 'Stars', count: 352 }
  ];

  // Workflows - Powered by Claude Agent SDK
  const workflows = [
    {
      name: 'Development Flow',
      steps: ['Code', 'Test', 'Review', 'Deploy'],
      tools: ['Claude Agent SDK', 'GitHub Actions', 'Vercel'],
      status: 'active'
    },
    {
      name: 'Security Scan',
      steps: ['Scan', 'Analyze', 'Patch', 'Verify'],
      tools: ['CodeMender', 'Claude Agent', 'GitHub Security'],
      status: 'scheduled'
    },
    {
      name: 'Documentation',
      steps: ['Generate', 'Review', 'Publish'],
      tools: ['Claude Agent SDK', 'Markdown', 'GitHub Pages'],
      status: 'active'
    }
  ];

  const StatusBadge = ({ status }: { status: string }) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800 border-green-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      error: 'bg-red-100 text-red-800 border-red-200',
      scheduled: 'bg-blue-100 text-blue-800 border-blue-200',
      legacy: 'bg-gray-100 text-gray-800 border-gray-200'
    };

    const icons: Record<string, JSX.Element> = {
      active: <CheckCircle className="w-3 h-3" />,
      pending: <Clock className="w-3 h-3" />,
      error: <AlertCircle className="w-3 h-3" />,
      scheduled: <RefreshCw className="w-3 h-3" />,
      legacy: <AlertCircle className="w-3 h-3" />
    };

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border ${styles[status] || styles.pending}`}>
        {icons[status] || icons.pending}
        {status}
      </span>
    );
  };

  const executeCommand = async (command: string) => {
    setIsProcessing(true);
    setConsoleOutput(prev => prev + `\n$ ${command}\n`);
    
    // Simulate command execution
    setTimeout(() => {
      setConsoleOutput(prev => prev + `Command '${command}' executed successfully.\n`);
      setIsProcessing(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Layers className="w-8 h-8 text-indigo-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Developer Tools Hub</h1>
              <p className="text-sm text-gray-600">Unified control center for all development tools</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
              <Settings className="w-4 h-4" />
              Configure
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
              <Terminal className="w-4 h-4" />
              Terminal
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-5rem)]">
        {/* Sidebar Navigation */}
        <div className="w-56 bg-white border-r overflow-y-auto">
          <div className="p-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Categories</h3>
            <nav className="space-y-1">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    activeCategory === category.id
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {category.icon}
                  <span className="text-sm font-medium">{category.name}</span>
                  <ChevronRight className={`w-4 h-4 ml-auto transition-transform ${
                    activeCategory === category.id ? 'rotate-90' : ''
                  }`} />
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeCategory === 'overview' && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-6 rounded-xl shadow-sm border">
                  <div className="flex items-center justify-between mb-2">
                    <Brain className="w-8 h-8 text-purple-600" />
                    <StatusBadge status="active" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">5</p>
                  <p className="text-sm text-gray-600">AI Models</p>
                </div>
                
                <div className="bg-white p-6 rounded-xl shadow-sm border">
                  <div className="flex items-center justify-between mb-2">
                    <Server className="w-8 h-8 text-blue-600" />
                    <StatusBadge status="active" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">6</p>
                  <p className="text-sm text-gray-600">MCP Servers</p>
                </div>
                
                <div className="bg-white p-6 rounded-xl shadow-sm border">
                  <div className="flex items-center justify-between mb-2">
                    <Github className="w-8 h-8 text-gray-900" />
                    <span className="text-xs text-green-600">Connected</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">42</p>
                  <p className="text-sm text-gray-600">Repositories</p>
                </div>
                
                <div className="bg-white p-6 rounded-xl shadow-sm border">
                  <div className="flex items-center justify-between mb-2">
                    <Bot className="w-8 h-8 text-indigo-600" />
                    <StatusBadge status="active" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">3</p>
                  <p className="text-sm text-gray-600">Code Assistants</p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <button 
                    onClick={() => setActiveCategory('models')}
                    className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg hover:from-purple-100 hover:to-pink-100 transition-all hover:scale-105"
                  >
                    <Brain className="w-6 h-6 text-purple-600 mb-2" />
                    <p className="text-sm font-medium text-gray-900">Switch Model</p>
                  </button>
                  
                  <button 
                    onClick={() => setActiveCategory('github')}
                    className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg hover:from-gray-100 hover:to-gray-200 transition-all hover:scale-105"
                  >
                    <GitPullRequest className="w-6 h-6 text-gray-700 mb-2" />
                    <p className="text-sm font-medium text-gray-900">Create PR</p>
                  </button>
                  
                  <button 
                    onClick={() => setActiveCategory('security')}
                    className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg hover:from-blue-100 hover:to-indigo-100 transition-all hover:scale-105"
                  >
                    <Shield className="w-6 h-6 text-blue-600 mb-2" />
                    <p className="text-sm font-medium text-gray-900">Security Scan</p>
                  </button>
                  
                  <button 
                    onClick={() => setActiveCategory('console')}
                    className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg hover:from-green-100 hover:to-emerald-100 transition-all hover:scale-105"
                  >
                    <Terminal className="w-6 h-6 text-green-600 mb-2" />
                    <p className="text-sm font-medium text-gray-900">Open Console</p>
                  </button>
                </div>
              </div>

              {/* Active Workflows */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Workflows</h2>
                <div className="space-y-3">
                  {workflows.map(workflow => (
                    <div key={workflow.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          workflow.status === 'active' ? 'bg-green-500' : 'bg-blue-500'
                        }`} />
                        <div>
                          <p className="font-medium text-gray-900">{workflow.name}</p>
                          <p className="text-xs text-gray-500">
                            {workflow.steps.join(' → ')}
                          </p>
                        </div>
                      </div>
                      <StatusBadge status={workflow.status} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeCategory === 'models' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">AI Model Providers</h2>
              
              <div className="grid gap-4">
                {modelProviders.map(provider => (
                  <div key={provider.id} className="bg-white rounded-xl shadow-sm border p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="p-2 bg-indigo-50 rounded-lg">
                          {provider.icon}
                        </div>
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900">{provider.name}</h3>
                            <StatusBadge status={provider.status} />
                            {provider.apiKey && (
                              <span className="flex items-center gap-1 text-xs text-green-600">
                                <Lock className="w-3 h-3" />
                                API Configured
                              </span>
                            )}
                          </div>
                          
                          <div className="mb-3">
                            <p className="text-sm text-gray-600 mb-1">Available Models:</p>
                            <div className="flex flex-wrap gap-1">
                              {provider.models.map(model => (
                                <span key={model} className="px-2 py-1 bg-gray-100 text-xs rounded">
                                  {model}
                                </span>
                              ))}
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-2">
                            {provider.features.map(feature => (
                              <span key={feature} className="text-xs text-gray-500">
                                ✓ {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <button 
                        onClick={() => setSelectedModel(provider.id)}
                        className={`px-4 py-2 rounded-lg transition-colors ${
                          selectedModel === provider.id
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {selectedModel === provider.id ? 'Active' : 'Select'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Additional category content continues... */}
        </div>
      </div>
    </div>
  );
};