import axios from 'axios';

const API_BASE = process.env.ORCHESTRATION_API || 'http://localhost:9002';

async function registerSecurityScanner() {
  const agent = {
    projectId: 1,
    name: 'security-scanner',
    type: 'SCRIPT',
    description: 'Scans code for security vulnerabilities (secrets, SQL injection, XSS)',
    entryPath: 'agents/security-scanner/index.ts',
    version: '1.0.0',
    riskLevel: 'AUTO',
    capabilities: [
      {
        name: 'scan',
        description: 'Scan repository for security issues',
        inputSchema: {
          type: 'object',
          properties: {
            repositoryPath: { type: 'string' },
            scanType: { type: 'string', enum: ['secrets', 'sql-injection', 'xss', 'all'] },
            severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          },
          required: ['repositoryPath'],
        },
        outputSchema: {
          type: 'object',
          properties: {
            findings: { type: 'array' },
            summary: { type: 'object' },
            scannedFiles: { type: 'number' },
            scanDurationMs: { type: 'number' },
          },
          required: ['findings', 'summary', 'scannedFiles', 'scanDurationMs'],
        },
      },
    ],
  };

  const response = await axios.post(`${API_BASE}/api/agents`, agent);
  console.log('Security scanner registered:', response.data);
  return response.data;
}

async function main() {
  try {
    await registerSecurityScanner();
    process.exit(0);
  } catch (error: any) {
    console.error('Registration failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

main();
