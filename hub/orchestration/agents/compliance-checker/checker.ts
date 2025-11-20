import * as fs from 'fs';
import * as path from 'path';
import { Input, Output, Violation } from './schemas';

export class ComplianceChecker {
  async check(input: Input): Promise<Output> {
    const startTime = Date.now();
    const violations: Violation[] = [];
    const rulesApplied: string[] = [];
    let checkedFiles = 0;

    // Determine which rules to apply
    const rules = input.rules.includes('all')
      ? ['licenses', 'security-headers', 'secrets']
      : input.rules;

    for (const rule of rules) {
      if (rule !== 'all') {
        rulesApplied.push(rule);
      }
    }

    // Check licenses
    if (rules.includes('licenses') || rules.includes('all')) {
      const licenseViolations = await this.checkLicenses(input.repositoryPath);
      violations.push(...licenseViolations);
      checkedFiles += 1; // package.json or similar
    }

    // Check security headers (in config files)
    if (rules.includes('security-headers') || rules.includes('all')) {
      const headerViolations = await this.checkSecurityHeaders(input.repositoryPath);
      violations.push(...headerViolations);
      checkedFiles += headerViolations.length;
    }

    // Check for secrets (environment variables in code)
    if (rules.includes('secrets') || rules.includes('all')) {
      const secretViolations = await this.checkSecrets(input.repositoryPath);
      violations.push(...secretViolations);
      checkedFiles += this.countCodeFiles(input.repositoryPath);
    }

    const summary = this.generateSummary(violations, input.strictMode);

    return {
      violations,
      summary,
      checkedFiles,
      checkDurationMs: Date.now() - startTime,
      rulesApplied,
    };
  }

  private async checkLicenses(repoPath: string): Promise<Violation[]> {
    const violations: Violation[] = [];
    const allowedLicenses = ['MIT', 'Apache-2.0', 'BSD-3-Clause', 'ISC'];

    // Check package.json for Node.js projects
    const packageJsonPath = path.join(repoPath, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));

      if (!packageJson.license) {
        violations.push({
          rule: 'licenses',
          severity: 'warning',
          file: packageJsonPath,
          message: 'No license specified in package.json',
          remediation: 'Add a "license" field with an OSS-approved license (MIT, Apache-2.0, etc.)',
        });
      } else if (!allowedLicenses.includes(packageJson.license)) {
        violations.push({
          rule: 'licenses',
          severity: 'critical',
          file: packageJsonPath,
          message: `Non-compliant license: ${packageJson.license}`,
          remediation: `Use an approved license: ${allowedLicenses.join(', ')}`,
        });
      }

      // Check dependencies for license compliance
      if (packageJson.dependencies) {
        const nodeModulesPath = path.join(repoPath, 'node_modules');
        if (fs.existsSync(nodeModulesPath)) {
          for (const dep of Object.keys(packageJson.dependencies)) {
            const depPackageJsonPath = path.join(nodeModulesPath, dep, 'package.json');
            if (fs.existsSync(depPackageJsonPath)) {
              const depPackageJson = JSON.parse(fs.readFileSync(depPackageJsonPath, 'utf-8'));
              if (
                depPackageJson.license &&
                !allowedLicenses.includes(depPackageJson.license) &&
                !depPackageJson.license.includes('MIT') &&
                !depPackageJson.license.includes('Apache')
              ) {
                violations.push({
                  rule: 'licenses',
                  severity: 'warning',
                  file: depPackageJsonPath,
                  message: `Dependency "${dep}" has license: ${depPackageJson.license}`,
                  remediation: 'Review dependency license compatibility',
                });
              }
            }
          }
        }
      }
    }

    // Check for LICENSE file
    const licenseFiles = ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING'];
    const hasLicenseFile = licenseFiles.some((file) =>
      fs.existsSync(path.join(repoPath, file))
    );

    if (!hasLicenseFile) {
      violations.push({
        rule: 'licenses',
        severity: 'warning',
        file: repoPath,
        message: 'No LICENSE file found in repository root',
        remediation: 'Add a LICENSE file with your chosen open-source license',
      });
    }

    return violations;
  }

  private async checkSecurityHeaders(repoPath: string): Promise<Violation[]> {
    const violations: Violation[] = [];
    const requiredHeaders = [
      'Content-Security-Policy',
      'X-Frame-Options',
      'X-Content-Type-Options',
      'Strict-Transport-Security',
    ];

    // Check common config files for security headers
    const configFiles = [
      'nginx.conf',
      'apache2.conf',
      'middleware.ts',
      'middleware.js',
      'server.ts',
      'server.js',
    ];

    for (const configFile of configFiles) {
      const fullPath = this.findFile(repoPath, configFile);
      if (fullPath) {
        const content = fs.readFileSync(fullPath, 'utf-8');
        const lines = content.split('\n');

        for (const header of requiredHeaders) {
          const headerFound = content.includes(header);
          if (!headerFound) {
            violations.push({
              rule: 'security-headers',
              severity: 'warning',
              file: fullPath,
              message: `Missing security header: ${header}`,
              remediation: `Add ${header} header to your HTTP response configuration`,
            });
          }
        }
      }
    }

    return violations;
  }

  private async checkSecrets(repoPath: string): Promise<Violation[]> {
    const violations: Violation[] = [];
    const files = this.getCodeFiles(repoPath);

    const secretPatterns = [
      {
        regex: /process\.env\.[A-Z_]+\s*\|\|\s*['"][^'"]+['"]/g,
        message: 'Hardcoded default value for environment variable',
        severity: 'warning' as const,
      },
      {
        regex: /(password|secret|token|key)\s*=\s*['"][^'"]{10,}['"]/gi,
        message: 'Potential hardcoded secret',
        severity: 'critical' as const,
      },
      {
        regex: /\.env\s*=\s*{[^}]+}/g,
        message: 'Hardcoded environment variables in code',
        severity: 'warning' as const,
      },
    ];

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');

      lines.forEach((line, index) => {
        for (const pattern of secretPatterns) {
          if (pattern.regex.test(line)) {
            violations.push({
              rule: 'secrets',
              severity: pattern.severity,
              file,
              line: index + 1,
              message: pattern.message,
              remediation: 'Use environment variables without hardcoded defaults',
            });
          }
        }
      });
    }

    return violations;
  }

  private findFile(repoPath: string, filename: string): string | null {
    const walk = (dir: string): string | null => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isFile() && entry.name === filename) {
          return fullPath;
        } else if (
          entry.isDirectory() &&
          !entry.name.startsWith('.') &&
          entry.name !== 'node_modules'
        ) {
          const found = walk(fullPath);
          if (found) return found;
        }
      }
      return null;
    };

    return walk(repoPath);
  }

  private getCodeFiles(repoPath: string): string[] {
    const files: string[] = [];
    const extensions = ['.ts', '.js', '.tsx', '.jsx', '.py', '.java', '.go'];
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
          files.push(fullPath);
        }
      }
    };

    walk(repoPath);
    return files;
  }

  private countCodeFiles(repoPath: string): number {
    return this.getCodeFiles(repoPath).length;
  }

  private generateSummary(
    violations: Violation[],
    strictMode: boolean
  ): Output['summary'] {
    const summary = {
      total: violations.length,
      critical: violations.filter((v) => v.severity === 'critical').length,
      warning: violations.filter((v) => v.severity === 'warning').length,
      info: violations.filter((v) => v.severity === 'info').length,
      passed: false,
    };

    // In strict mode, fail on any violation
    // In normal mode, only fail on critical violations
    summary.passed = strictMode
      ? summary.total === 0
      : summary.critical === 0;

    return summary;
  }
}
