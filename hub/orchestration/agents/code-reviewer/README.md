# Code Reviewer Agent

Automated code review with static analysis for quality, security, and performance issues.

## Overview

- **Type**: ANALYSIS
- **Risk Level**: AUTO (read-only)
- **Capabilities**: Static analysis, complexity metrics, best practice validation

## Input

```typescript
{
  repositoryPath: string;
  reviewType: "quality" | "security" | "performance" | "all";
  filePattern?: string;  // Optional filter (e.g., "src/api")
}
```

## Output

```typescript
{
  issues: Array<{
    type: "quality" | "security" | "performance" | "best-practice";
    severity: "info" | "warning" | "error";
    file: string;
    line: number;
    description: string;
    suggestion?: string;
  }>;
  summary: {
    total: number;
    errors: number;
    warnings: number;
    info: number;
    filesReviewed: number;
  };
  metrics: {
    avgComplexity: number;
    maxComplexity: number;
    totalLines: number;
  };
  reviewDurationMs: number;
}
```

## Checks

### Quality
- High cyclomatic complexity (> 15)
- Long functions (> 50 lines)
- TODO/FIXME comments
- console.log in production code

### Security
- Use of `eval()`
- Potential XSS with `innerHTML/outerHTML`
- SQL injection via string concatenation

### Performance
- Nested loops
- Synchronous fs operations

## Usage

```bash
npm install
npm start '{"repositoryPath": "../../..", "reviewType": "all"}'
```
