import * as fs from 'fs';
import * as path from 'path';
import { Input, Output, Issue } from './schemas';

export class CodeReviewer {
  async review(input: Input): Promise<Output> {
    const startTime = Date.now();
    const issues: Issue[] = [];
    const files = this.getCodeFiles(input.target, input.filePattern);

    let totalLines = 0;
    let totalComplexity = 0;
    let maxComplexity = 0;

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      totalLines += lines.length;

      // Calculate cyclomatic complexity
      const complexity = this.calculateComplexity(content);
      totalComplexity += complexity;
      if (complexity > maxComplexity) maxComplexity = complexity;

      // Quality checks
      if (input.type === 'quality' || input.type === 'all') {
        issues.push(...this.checkQuality(file, lines, complexity));
      }

      // Security checks
      if (input.type === 'security' || input.type === 'all') {
        issues.push(...this.checkSecurity(file, lines));
      }

      // Performance checks
      if (input.type === 'performance' || input.type === 'all') {
        issues.push(...this.checkPerformance(file, lines));
      }
    }

    const summary = {
      total: issues.length,
      errors: issues.filter((i) => i.severity === 'error').length,
      warnings: issues.filter((i) => i.severity === 'warning').length,
      info: issues.filter((i) => i.severity === 'info').length,
      filesReviewed: files.length,
    };

    const metrics = {
      avgComplexity: files.length > 0 ? totalComplexity / files.length : 0,
      maxComplexity,
      totalLines,
    };

    // Limit issues to avoid JSON overflow in stdout capture (8KB buffer limit)
    const limitedIssues = issues.slice(0, 20).map(issue => ({
      type: issue.type,
      severity: issue.severity,
      file: issue.file.replace(/^\/workspace\//, '').slice(0, 50),
      line: issue.line,
      description: issue.description.slice(0, 100),
    }));

    return {
      issues: limitedIssues,
      summary,
      metrics,
      reviewDurationMs: Date.now() - startTime,
    };
  }

  private checkQuality(file: string, lines: string[], complexity: number): Issue[] {
    const issues: Issue[] = [];

    // High complexity
    if (complexity > 15) {
      issues.push({
        type: 'quality',
        severity: 'warning',
        file,
        line: 1,
        description: `High cyclomatic complexity: ${complexity}`,
        suggestion: 'Refactor into smaller functions (target: complexity < 10)',
      });
    }

    // Long functions
    lines.forEach((line, index) => {
      if (/(function|const \w+ = \(.*\) =>|class \w+)/.test(line)) {
        const funcLines = this.countFunctionLines(lines, index);
        if (funcLines > 50) {
          issues.push({
            type: 'quality',
            severity: 'warning',
            file,
            line: index + 1,
            description: `Function too long: ${funcLines} lines`,
            suggestion: 'Break down into smaller functions (target: < 50 lines)',
          });
        }
      }

      // TODO/FIXME comments
      if (line.includes('TODO') || line.includes('FIXME')) {
        issues.push({
          type: 'quality',
          severity: 'info',
          file,
          line: index + 1,
          description: 'Unresolved TODO/FIXME comment',
          suggestion: 'Address technical debt or create a task',
        });
      }

      // Console.log in production
      if (line.includes('console.log') && !file.includes('test')) {
        issues.push({
          type: 'best-practice',
          severity: 'warning',
          file,
          line: index + 1,
          description: 'console.log found in production code',
          suggestion: 'Use a logging library or remove debug statements',
        });
      }
    });

    return issues;
  }

  private checkSecurity(file: string, lines: string[]): Issue[] {
    const issues: Issue[] = [];

    lines.forEach((line, index) => {
      // eval() usage
      if (/eval\(/.test(line)) {
        issues.push({
          type: 'security',
          severity: 'error',
          file,
          line: index + 1,
          description: 'Use of eval() is dangerous',
          suggestion: 'Avoid eval(), use safer alternatives like JSON.parse()',
        });
      }

      // innerHTML/outerHTML
      if (/innerHTML|outerHTML/.test(line) && !line.includes('textContent')) {
        issues.push({
          type: 'security',
          severity: 'warning',
          file,
          line: index + 1,
          description: 'Potential XSS vulnerability with innerHTML',
          suggestion: 'Use textContent or sanitize HTML with DOMPurify',
        });
      }

      // SQL string concatenation
      if (/SELECT.*\+|INSERT.*\+|UPDATE.*\+|DELETE.*\+/.test(line)) {
        issues.push({
          type: 'security',
          severity: 'error',
          file,
          line: index + 1,
          description: 'Potential SQL injection with string concatenation',
          suggestion: 'Use parameterized queries or an ORM',
        });
      }
    });

    return issues;
  }

  private checkPerformance(file: string, lines: string[]): Issue[] {
    const issues: Issue[] = [];

    lines.forEach((line, index) => {
      // Nested loops
      if (/for|while|forEach/.test(line)) {
        const nextLines = lines.slice(index, index + 10).join('\n');
        if ((nextLines.match(/for|while|forEach/g) || []).length > 1) {
          issues.push({
            type: 'performance',
            severity: 'warning',
            file,
            line: index + 1,
            description: 'Nested loops detected',
            suggestion: 'Consider optimizing with Map/Set or refactoring algorithm',
          });
        }
      }

      // Synchronous fs operations
      if (/fs\.readFileSync|fs\.writeFileSync/.test(line)) {
        issues.push({
          type: 'performance',
          severity: 'info',
          file,
          line: index + 1,
          description: 'Synchronous file system operation',
          suggestion: 'Use async fs.promises for better performance',
        });
      }
    });

    return issues;
  }

  private calculateComplexity(content: string): number {
    const patterns = [
      /\bif\b/g,
      /\belse\b/g,
      /\bfor\b/g,
      /\bwhile\b/g,
      /\bcase\b/g,
      /\bcatch\b/g,
      /\b\?\b/g, // Ternary
      /&&/g,
      /\|\|/g,
    ];

    let complexity = 1; // Base complexity
    for (const pattern of patterns) {
      const matches = content.match(pattern);
      if (matches) complexity += matches.length;
    }

    return complexity;
  }

  private countFunctionLines(lines: string[], startIndex: number): number {
    let openBraces = 0;
    let count = 0;

    for (let i = startIndex; i < lines.length; i++) {
      const line = lines[i];
      openBraces += (line.match(/{/g) || []).length;
      openBraces -= (line.match(/}/g) || []).length;
      count++;

      if (openBraces === 0 && count > 1) break;
    }

    return count;
  }

  private getCodeFiles(repoPath: string, pattern?: string): string[] {
    const files: string[] = [];
    const extensions = ['.ts', '.js', '.tsx', '.jsx'];
    const excludeDirs = ['node_modules', 'venv', '.venv', 'dist', '.git', 'build'];

    const walk = (dir: string) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          if (!entry.name.startsWith('.') && !excludeDirs.includes(entry.name)) {
            walk(fullPath);
          }
        } else if (extensions.some((ext) => entry.name.endsWith(ext))) {
          if (!pattern || fullPath.includes(pattern)) {
            files.push(fullPath);
          }
        }
      }
    };

    walk(repoPath);
    return files;
  }
}
