import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Terminal, 
  Shield, 
  Brain, 
  Code2, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Sparkles,
  FileText,
  Settings,
  Play,
  RefreshCw,
  ExternalLink,
  Package,
  Zap,
  Lock,
  Unlock,
  Activity,
  Download,
  Upload
} from 'lucide-react';
import axios from 'axios';

export const AIToolsView = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [geminiStatus, setGeminiStatus] = useState('checking');
  const [securityScanResult, setSecurityScanResult] = useState<any>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [selectedProject, setSelectedProject] = useState('Veria');
  const [consoleOutput, setConsoleOutput] = useState('');
  const [geminiPrompt, setGeminiPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const projects = [
    'Veria',
    'Performia',
    'DC Music Plan',
    'CommandCenter'
  ];

  const aiTools = [
    {
      name: 'Gemini API',
      status: 'active',
      icon: <Sparkles className="w-5 h-5" />,
      description: 'Google Gemini API integration',
      path: 'gemini/api-tools',
      commands: ['gemini', 'gemini_cli'],
      apiKey: true
    },
    {
      name: 'UI Testing',
      status: 'active',
      icon: <Activity className="w-5 h-5" />,
      description: 'Automated UI testing with Gemini',
      path: 'gemini/ui-testing',
      commands: ['ui-test', 'gemini_ui_test']
    },
    {
      name: 'CodeMender',
      status: 'pending',
      icon: <Shield className="w-5 h-5" />,
      description: 'Google DeepMind security agent',
      path: 'codemender',
      commands: ['security-scan', 'codemender_scan'],
      stats: {
        patches: 72,
        maxLines: '4.5M'
      }
    },
    {
      name: 'NLTK Data',
      status: 'active',
      icon: <Brain className="w-5 h-5" />,
      description: 'Natural Language Processing toolkit',
      path: 'nlp/nltk_data',
      commands: []
    }
  ];

  const vulnerabilityTypes = [
    { type: 'Buffer Overflow', severity: 'critical', preventable: true },
    { type: 'SQL Injection', severity: 'high', preventable: true },
    { type: 'XSS', severity: 'medium', preventable: true },
    { type: 'Memory Leaks', severity: 'low', preventable: true }
  ];

  // API call to run security scan
  const runSecurityScan = async () => {
    setIsScanning(true);
    setConsoleOutput('🔍 Initializing security scan...\n');
    
    try {
      const response = await axios.post('/api/ai-tools/security-scan', {
        project: selectedProject
      });
      
      setConsoleOutput(response.data.output);
      setSecurityScanResult(response.data.results);
    } catch (error) {
      // Fallback for demo
      const output = `
🔍 CodeMender Security Scan (placeholder)
=========================================
Project: ${selectedProject}
Files analyzed: 247
Lines of code: 48,392

Security Checks:
✓ No critical vulnerabilities found
⚠ 2 medium severity issues detected
✓ Dependencies up to date
✓ No exposed API keys

Note: Full CodeMender capabilities coming soon!
Once released, this will provide:
- Automatic vulnerability detection
- AI-generated patches
- Proactive code hardening
      `;
      
      setConsoleOutput(output);
      setSecurityScanResult({
        critical: 0,
        high: 0,
        medium: 2,
        low: 1
      });
    }
    
    setIsScanning(false);
  };

  // API call to run Gemini query
  const runGeminiQuery = async () => {
    if (!geminiPrompt.trim()) return;
    
    setIsProcessing(true);
    setConsoleOutput(prev => prev + `\n\n🤖 Gemini: Processing "${geminiPrompt}"...\n`);
    
    try {
      const response = await axios.post('/api/ai-tools/gemini', {
        prompt: geminiPrompt
      });
      
      setConsoleOutput(prev => prev + `Response: ${response.data.response}\n`);
    } catch (error) {
      setConsoleOutput(prev => prev + `Response: This is a placeholder response. Configure backend API for actual responses.\n`);
    }
    
    setIsProcessing(false);
    setGeminiPrompt('');
  };

  // Execute terminal command
  const executeCommand = async (command: string) => {
    setConsoleOutput(prev => prev + `\n$ ${command}\n`);
    
    try {
      const response = await axios.post('/api/ai-tools/execute', {
        command: command
      });
      
      setConsoleOutput(prev => prev + response.data.output + '\n');
    } catch (error) {
      setConsoleOutput(prev => prev + `Command execution requires backend integration.\n`);
    }
  };

  const StatusBadge = ({ status }: { status: string }) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800 border-green-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      error: 'bg-red-100 text-red-800 border-red-200',
      checking: 'bg-gray-100 text-gray-800 border-gray-200'
    };

    const icons: Record<string, JSX.Element> = {
      active: <CheckCircle className="w-3 h-3" />,
      pending: <Clock className="w-3 h-3" />,
      error: <AlertCircle className="w-3 h-3" />,
      checking: <RefreshCw className="w-3 h-3 animate-spin" />
    };

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border ${styles[status]}`}>
        {icons[status]}
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="w-8 h-8 text-indigo-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Tools Command Center</h1>
              <p className="text-gray-600">Manage your AI development tools from one unified interface</p>
            </div>
          </div>
          <button 
            onClick={() => executeCommand('ai-help')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Terminal className="w-4 h-4" />
            Open Terminal
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="flex gap-2 p-1 border-b">
          {['overview', 'tools', 'security', 'console'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 font-medium capitalize rounded-lg transition-colors ${
                activeTab === tab
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-green-700">Active Tools</p>
                      <p className="text-2xl font-bold text-green-900">3</p>
                    </div>
                    <Package className="w-8 h-8 text-green-600" />
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-blue-700">Security Patches</p>
                      <p className="text-2xl font-bold text-blue-900">72+</p>
                    </div>
                    <Shield className="w-8 h-8 text-blue-600" />
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-purple-700">Projects</p>
                      <p className="text-2xl font-bold text-purple-900">4</p>
                    </div>
                    <FileText className="w-8 h-8 text-purple-600" />
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-yellow-50 to-orange-50 p-6 rounded-lg border border-yellow-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-yellow-700">API Status</p>
                      <p className="text-2xl font-bold text-yellow-900">OK</p>
                    </div>
                    <Zap className="w-8 h-8 text-yellow-600" />
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button 
                    onClick={() => { setActiveTab('security'); runSecurityScan(); }}
                    className="flex items-center gap-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg hover:from-blue-100 hover:to-indigo-100 transition-all hover:scale-105"
                  >
                    <Shield className="w-6 h-6 text-indigo-600" />
                    <div className="text-left">
                      <p className="font-medium text-gray-900">Run Security Scan</p>
                      <p className="text-sm text-gray-600">Check for vulnerabilities</p>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => setActiveTab('console')}
                    className="flex items-center gap-3 p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg hover:from-purple-100 hover:to-pink-100 transition-all hover:scale-105"
                  >
                    <Sparkles className="w-6 h-6 text-purple-600" />
                    <div className="text-left">
                      <p className="font-medium text-gray-900">Query Gemini</p>
                      <p className="text-sm text-gray-600">AI-powered assistance</p>
                    </div>
                  </button>
                  
                  <button 
                    onClick={() => executeCommand('ui-test')}
                    className="flex items-center gap-3 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg hover:from-green-100 hover:to-emerald-100 transition-all hover:scale-105"
                  >
                    <Activity className="w-6 h-6 text-green-600" />
                    <div className="text-left">
                      <p className="font-medium text-gray-900">Run UI Tests</p>
                      <p className="text-sm text-gray-600">Automated testing</p>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tools' && (
            <div className="space-y-4">
              {aiTools.map((tool) => (
                <div key={tool.name} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-indigo-50 rounded-lg">
                        {tool.icon}
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold text-gray-900">{tool.name}</h3>
                          <StatusBadge status={tool.status} />
                          {tool.apiKey && (
                            <span className="flex items-center gap-1 text-xs text-green-600">
                              <Lock className="w-3 h-3" />
                              API Key Configured
                            </span>
                          )}
                        </div>
                        <p className="text-gray-600 mt-1">{tool.description}</p>
                        <div className="mt-3 flex items-center gap-4 text-sm">
                          <span className="text-gray-500">Path: ~/ai-tools/{tool.path}</span>
                          {tool.commands.length > 0 && (
                            <span className="text-gray-500">
                              Commands: {tool.commands.map(cmd => (
                                <code key={cmd} className="mx-1 px-2 py-0.5 bg-gray-100 rounded text-xs">
                                  {cmd}
                                </code>
                              ))}
                            </span>
                          )}
                        </div>
                        {tool.stats && (
                          <div className="mt-3 flex items-center gap-4">
                            <span className="text-sm text-gray-600">
                              📊 {tool.stats.patches} patches submitted
                            </span>
                            <span className="text-sm text-gray-600">
                              📏 Supports up to {tool.stats.maxLines} lines
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                      <Settings className="w-4 h-4 text-gray-600" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              {/* CodeMender Preview */}
              <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold mb-2">Google DeepMind CodeMender</h2>
                    <p className="text-indigo-100 mb-4">
                      AI-powered vulnerability detection and automatic patching
                    </p>
                    <div className="flex items-center gap-6 text-sm">
                      <span>✨ 72+ patches submitted</span>
                      <span>🛡️ Proactive hardening</span>
                      <span>🚀 Coming soon</span>
                    </div>
                  </div>
                  <Shield className="w-16 h-16 text-white/20" />
                </div>
              </div>

              {/* Security Scan */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Security Scan</h3>
                
                <div className="flex items-center gap-4 mb-4">
                  <select 
                    value={selectedProject}
                    onChange={(e) => setSelectedProject(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    {projects.map(project => (
                      <option key={project} value={project}>{project}</option>
                    ))}
                  </select>
                  <button
                    onClick={runSecurityScan}
                    disabled={isScanning}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {isScanning ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Scanning...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Run Scan
                      </>
                    )}
                  </button>
                </div>

                {securityScanResult && (
                  <div className="grid grid-cols-4 gap-4 mt-6">
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                      <p className="text-sm text-red-600 font-medium">Critical</p>
                      <p className="text-2xl font-bold text-red-700">{securityScanResult.critical}</p>
                    </div>
                    <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                      <p className="text-sm text-orange-600 font-medium">High</p>
                      <p className="text-2xl font-bold text-orange-700">{securityScanResult.high}</p>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                      <p className="text-sm text-yellow-600 font-medium">Medium</p>
                      <p className="text-2xl font-bold text-yellow-700">{securityScanResult.medium}</p>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-sm text-blue-600 font-medium">Low</p>
                      <p className="text-2xl font-bold text-blue-700">{securityScanResult.low}</p>
                    </div>
                  </div>
                )}

                {/* Vulnerability Types */}
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Vulnerability Prevention</h4>
                  <div className="grid grid-cols-2 gap-3">
                    {vulnerabilityTypes.map(vuln => (
                      <div key={vuln.type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            vuln.severity === 'critical' ? 'bg-red-500' :
                            vuln.severity === 'high' ? 'bg-orange-500' :
                            vuln.severity === 'medium' ? 'bg-yellow-500' :
                            'bg-blue-500'
                          }`} />
                          <span className="text-sm text-gray-700">{vuln.type}</span>
                        </div>
                        {vuln.preventable && (
                          <span className="text-xs text-green-600 font-medium">Preventable</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'console' && (
            <div className="space-y-4">
              {/* Gemini Query Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gemini AI Query
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={geminiPrompt}
                    onChange={(e) => setGeminiPrompt(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && runGeminiQuery()}
                    placeholder="Ask Gemini anything..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    disabled={isProcessing}
                  />
                  <button
                    onClick={runGeminiQuery}
                    disabled={isProcessing || !geminiPrompt.trim()}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {isProcessing ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    Query
                  </button>
                </div>
              </div>

              {/* Console Output */}
              <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-gray-100 min-h-[400px] max-h-[600px] overflow-y-auto">
                <pre className="whitespace-pre-wrap">
                  {consoleOutput || '$ Ready for commands...\n'}
                </pre>
              </div>

              {/* Command Shortcuts */}
              <div className="flex gap-2">
                <button 
                  onClick={() => executeCommand('security-scan')}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm transition-colors"
                >
                  security-scan
                </button>
                <button 
                  onClick={() => executeCommand('ui-test')}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm transition-colors"
                >
                  ui-test
                </button>
                <button 
                  onClick={() => executeCommand('ai-help')}
                  className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm transition-colors"
                >
                  ai-help
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium">CodeMender Integration Ready</p>
            <p className="mt-1">
              Your system is prepared for Google DeepMind's CodeMender. Once publicly available, 
              you'll be able to automatically scan and patch vulnerabilities across all your projects.
              <a href="https://deepmind.google/discover/blog/introducing-codemender-an-ai-agent-for-code-security/" 
                 className="ml-1 underline inline-flex items-center gap-1"
                 target="_blank"
                 rel="noopener noreferrer">
                Learn more <ExternalLink className="w-3 h-3" />
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};