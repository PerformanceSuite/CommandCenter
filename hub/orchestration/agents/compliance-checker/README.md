# Compliance Checker Agent

Validates code and configuration against compliance rules including license scanning, security headers, and secret detection.

## Overview

- **Type**: ANALYSIS
- **Risk Level**: AUTO (read-only, no mutations)
- **Capabilities**: License scanning, security header validation, secret detection

## Input Schema

```typescript
{
  repositoryPath: string;       // Path to repository to check
  rules: string[];              // ["licenses", "security-headers", "secrets", "all"]
  strictMode: boolean;          // Fail on any violation (default: false)
}
```

## Output Schema

```typescript
{
  violations: Array<{
    rule: string;               // Rule that was violated
    severity: "info" | "warning" | "critical";
    file: string;               // File with violation
    line?: number;              // Line number (optional)
    message: string;            // Description of violation
    remediation?: string;       // How to fix (optional)
  }>;
  summary: {
    total: number;              // Total violations
    critical: number;           // Critical severity count
    warning: number;            // Warning severity count
    info: number;               // Info severity count
    passed: boolean;            // True if check passed
  };
  checkedFiles: number;         // Number of files checked
  checkDurationMs: number;      // Duration in milliseconds
  rulesApplied: string[];       // Rules that were applied
}
```

## Rules

### 1. License Compliance (`licenses`)

**Checks**:
- `package.json` has a license field
- License is OSS-approved (MIT, Apache-2.0, BSD-3-Clause, ISC)
- Dependencies use compatible licenses
- LICENSE file exists in repository root

**Violations**:
- **Critical**: Non-compliant license (e.g., proprietary, GPL in commercial code)
- **Warning**: Missing license field or LICENSE file
- **Warning**: Dependency with incompatible license

**Remediation**:
```json
// package.json
{
  "license": "MIT"
}
```

Add a LICENSE file to repository root with full license text.

### 2. Security Headers (`security-headers`)

**Checks**:
- Configuration files (nginx, apache, middleware) include security headers
- Required headers: CSP, X-Frame-Options, X-Content-Type-Options, HSTS

**Violations**:
- **Warning**: Missing required security header

**Remediation** (Express middleware):
```typescript
app.use((req, res, next) => {
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  next();
});
```

### 3. Secret Detection (`secrets`)

**Checks**:
- No hardcoded defaults for environment variables
- No hardcoded passwords, tokens, or API keys in code
- No inline environment variable objects

**Violations**:
- **Critical**: Hardcoded secret/token/password
- **Warning**: Hardcoded default for environment variable

**Remediation**:
```typescript
// ❌ Bad
const apiKey = process.env.API_KEY || 'default-key-123';

// ✅ Good
const apiKey = process.env.API_KEY;
if (!apiKey) {
  throw new Error('API_KEY environment variable required');
}
```

## Usage

### Via Agent Registry

```bash
# Register agent
curl -X POST http://localhost:9002/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "compliance-checker",
    "type": "ANALYSIS",
    "riskLevel": "AUTO",
    "dockerImage": "commandcenter-agent-compliance-checker",
    "capabilities": ["license-scanning", "security-headers", "secret-detection"]
  }'
```

### Via Workflow

```typescript
const workflow = {
  name: "compliance-check",
  nodes: [
    {
      id: "check",
      agentName: "compliance-checker",
      input: {
        repositoryPath: "/workspace",
        rules: ["all"],
        strictMode: false
      }
    }
  ],
  edges: []
};
```

### Direct Execution

```bash
cd orchestration/agents/compliance-checker
npm install
npm start '{"repositoryPath": "/path/to/repo", "rules": ["all"]}'
```

## Example Output

```json
{
  "violations": [
    {
      "rule": "licenses",
      "severity": "warning",
      "file": "/repo/package.json",
      "message": "No license specified in package.json",
      "remediation": "Add a \"license\" field with an OSS-approved license (MIT, Apache-2.0, etc.)"
    },
    {
      "rule": "secrets",
      "severity": "critical",
      "file": "/repo/src/config.ts",
      "line": 12,
      "message": "Potential hardcoded secret",
      "remediation": "Use environment variables without hardcoded defaults"
    }
  ],
  "summary": {
    "total": 2,
    "critical": 1,
    "warning": 1,
    "info": 0,
    "passed": false
  },
  "checkedFiles": 45,
  "checkDurationMs": 1250,
  "rulesApplied": ["licenses", "security-headers", "secrets"]
}
```

## Testing

```bash
# Test on CommandCenter codebase
npm start '{"repositoryPath": "../../..", "rules": ["licenses", "secrets"]}'

# Strict mode (fail on any violation)
npm start '{"repositoryPath": "../../..", "rules": ["all"], "strictMode": true}'

# Single rule
npm start '{"repositoryPath": "../../..", "rules": ["licenses"]}'
```

## Integration with Workflows

The compliance-checker agent can be used in various workflows:

1. **Pre-commit Check**: Run before commits to ensure compliance
2. **Pull Request Validation**: Automated checks on PR creation
3. **Security Audit**: Scheduled compliance scans
4. **Dependency Updates**: Check license compatibility when updating deps

## Exit Codes

- **0**: Check passed (no critical violations, or no violations in strict mode)
- **1**: Check failed (has critical violations, or any violation in strict mode)
- **1**: Execution error (invalid input, file system error, etc.)

## Notes

- Agent is read-only and safe to run automatically (AUTO risk level)
- Supports Node.js projects (package.json) - Python/Java support can be added
- License checking requires node_modules to be installed for dependency scanning
- Security header checks look for common config file patterns
- Secret detection uses regex patterns (not comprehensive, but catches common issues)
