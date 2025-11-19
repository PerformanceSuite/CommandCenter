import * as fs from 'fs';
import * as path from 'path';
import { Input, Output, Finding } from './schemas';

export class SecurityScanner {
  async scan(input: Input): Promise<Output> {
    const startTime = Date.now();
    const findings: Finding[] = [];
    let scannedFiles = 0;

    const files = this.getFilesToScan(input.repositoryPath);

    for (const file of files) {
      scannedFiles++;
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');

      // Check for hardcoded secrets
      if (input.scanType === 'secrets' || input.scanType === 'all') {
        findings.push(...this.scanForSecrets(file, lines));
      }

      // Check for SQL injection
      if (input.scanType === 'sql-injection' || input.scanType === 'all') {
        findings.push(...this.scanForSQLInjection(file, lines));
      }

      // Check for XSS
      if (input.scanType === 'xss' || input.scanType === 'all') {
        findings.push(...this.scanForXSS(file, lines));
      }
    }

    // Filter by severity if specified
    const filteredFindings = input.severity
      ? findings.filter(f => f.severity === input.severity)
      : findings;

    const summary = this.generateSummary(filteredFindings);

    return {
      findings: filteredFindings,
      summary,
      scannedFiles,
      scanDurationMs: Date.now() - startTime,
    };
  }

  private getFilesToScan(repoPath: string): string[] {
    const files: string[] = [];
    const extensions = ['.ts', '.js', '.tsx', '.jsx', '.py', '.java'];

    const walk = (dir: string) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!entry.name.startsWith('.') && entry.name !== 'node_modules') {
            walk(fullPath);
          }
        } else if (extensions.some(ext => entry.name.endsWith(ext))) {
          files.push(fullPath);
        }
      }
    };

    walk(repoPath);
    return files;
  }

  private scanForSecrets(file: string, lines: string[]): Finding[] {
    const findings: Finding[] = [];
    const patterns = [
      { regex: /(api[_-]?key|apikey)\s*=\s*['"][^'"]+['"]/i, type: 'Hardcoded API Key' },
      { regex: /(password|passwd|pwd)\s*=\s*['"][^'"]+['"]/i, type: 'Hardcoded Password' },
      { regex: /(secret[_-]?key|secretkey)\s*=\s*['"][^'"]+['"]/i, type: 'Hardcoded Secret' },
      { regex: /sk-[a-zA-Z0-9]{48}/g, type: 'OpenAI API Key' },
      { regex: /ghp_[a-zA-Z0-9]{36}/g, type: 'GitHub Personal Access Token' },
    ];

    lines.forEach((line, index) => {
      for (const pattern of patterns) {
        if (pattern.regex.test(line)) {
          findings.push({
            type: pattern.type,
            severity: 'critical',
            file,
            line: index + 1,
            description: `Potential ${pattern.type.toLowerCase()} found in code`,
            code: line.trim(),
          });
        }
      }
    });

    return findings;
  }

  private scanForSQLInjection(file: string, lines: string[]): Finding[] {
    const findings: Finding[] = [];
    const patterns = [
      /execute\s*\(\s*['"]SELECT.*\$\{/i,
      /query\s*\(\s*['"]SELECT.*\+/i,
      /\.raw\s*\(\s*`SELECT.*\$\{/i,
    ];

    lines.forEach((line, index) => {
      for (const pattern of patterns) {
        if (pattern.test(line)) {
          findings.push({
            type: 'SQL Injection',
            severity: 'high',
            file,
            line: index + 1,
            description: 'Potential SQL injection vulnerability - string concatenation in query',
            code: line.trim(),
          });
        }
      }
    });

    return findings;
  }

  private scanForXSS(file: string, lines: string[]): Finding[] {
    const findings: Finding[] = [];
    const patterns = [
      /dangerouslySetInnerHTML/,
      /innerHTML\s*=/,
      /document\.write\(/,
    ];

    lines.forEach((line, index) => {
      for (const pattern of patterns) {
        if (pattern.test(line)) {
          findings.push({
            type: 'XSS Vulnerability',
            severity: 'medium',
            file,
            line: index + 1,
            description: 'Potential XSS vulnerability - unsafe HTML rendering',
            code: line.trim(),
          });
        }
      }
    });

    return findings;
  }

  private generateSummary(findings: Finding[]) {
    return {
      total: findings.length,
      critical: findings.filter(f => f.severity === 'critical').length,
      high: findings.filter(f => f.severity === 'high').length,
      medium: findings.filter(f => f.severity === 'medium').length,
      low: findings.filter(f => f.severity === 'low').length,
    };
  }
}
