# Agent Development Guide

Complete guide to creating custom agents for the CommandCenter orchestration system.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Agent Architecture](#agent-architecture)
3. [Creating an Agent](#creating-an-agent)
4. [Agent Templates](#agent-templates)
5. [Best Practices](#best-practices)
6. [Testing](#testing)
7. [Deployment](#deployment)

---

## Quick Start

### 5-Minute Agent

```bash
# 1. Create agent directory
mkdir -p orchestration/agents/my-agent
cd orchestration/agents/my-agent

# 2. Create package.json
cat > package.json <<EOF
{
  "name": "@commandcenter/agent-my-agent",
  "version": "1.0.0",
  "scripts": { "start": "ts-node index.ts" },
  "dependencies": { "zod": "^3.22.4" },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.3.2"
  }
}
EOF

# 3. Create schemas (input/output validation)
# 4. Create agent logic
# 5. Create index.ts (entry point)
# 6. Test locally
npm install
npm start '{"input": "value"}'

# 7. Register with orchestration service
curl -X POST http://localhost:9002/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent", "type": "TASK", "riskLevel": "AUTO", "dockerImage": "my-agent:latest"}'
```

---

## Agent Architecture

### File Structure

```
orchestration/agents/my-agent/
├── schemas.ts          # Zod schemas (input/output validation)
├── agent.ts            # Main agent logic
├── index.ts            # CLI entry point
├── package.json        # Dependencies
├── README.md           # Agent documentation
└── tsconfig.json       # TypeScript config (optional)
```

### Data Flow

```
Orchestration Service
  │
  ├─> Dagger Executor
  │     │
  │     ├─> Build Docker Container
  │     │     │
  │     │     └─> Install Dependencies (npm install)
  │     │
  │     └─> Run Agent
  │           │
  │           ├─> Parse CLI Args (JSON input)
  │           ├─> Validate Input (Zod schema)
  │           ├─> Execute Agent Logic
  │           ├─> Validate Output (Zod schema)
  │           └─> Print JSON to stdout
  │
  └─> Capture Output & Parse JSON
```

---

## Creating an Agent

### Step 1: Define Schemas

**File**: `schemas.ts`

```typescript
import { z } from 'zod';

// Input schema (what the agent receives)
export const InputSchema = z.object({
  target: z.string().describe('Target to process'),
  options: z.object({
    verbose: z.boolean().default(false),
    timeout: z.number().default(30000),
  }).optional(),
});

// Output schema (what the agent returns)
export const OutputSchema = z.object({
  success: z.boolean(),
  result: z.any(),
  metadata: z.object({
    processedAt: z.string(),
    duration: z.number(),
  }),
});

// TypeScript types (inferred from schemas)
export type Input = z.infer<typeof InputSchema>;
export type Output = z.infer<typeof OutputSchema>;
```

**Why Zod?**
- Runtime validation (catches bad inputs)
- TypeScript types (compile-time safety)
- Auto-generated error messages
- Schema documentation via `.describe()`

---

### Step 2: Implement Agent Logic

**File**: `agent.ts`

```typescript
import { Input, Output } from './schemas';

export class MyAgent {
  async execute(input: Input): Promise<Output> {
    const startTime = Date.now();

    try {
      // Your agent logic here
      const result = await this.processTarget(input.target);

      return {
        success: true,
        result,
        metadata: {
          processedAt: new Date().toISOString(),
          duration: Date.now() - startTime,
        },
      };
    } catch (error: any) {
      return {
        success: false,
        result: null,
        metadata: {
          processedAt: new Date().toISOString(),
          duration: Date.now() - startTime,
        },
      };
    }
  }

  private async processTarget(target: string): Promise<any> {
    // Implementation
    return { processed: target };
  }
}
```

**Best Practices**:
- Keep logic in separate methods (testable)
- Use try-catch for error handling
- Return structured output
- Include metadata (timestamps, duration)

---

### Step 3: Create CLI Entry Point

**File**: `index.ts`

```typescript
#!/usr/bin/env ts-node

import { MyAgent } from './agent';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    // 1. Read input from CLI argument
    const inputJson = process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided');
    }

    const input = JSON.parse(inputJson);

    // 2. Validate input
    const validatedInput = InputSchema.parse(input);

    // 3. Execute agent
    const agent = new MyAgent();
    const output = await agent.execute(validatedInput);

    // 4. Validate output
    const validatedOutput = OutputSchema.parse(output);

    // 5. Print to stdout (orchestration service captures this)
    console.log(JSON.stringify(validatedOutput));
    process.exit(0);
  } catch (error: any) {
    // Print error to stderr (not captured as output)
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
```

**Important**:
- **stdout**: Agent output (JSON only)
- **stderr**: Logs, errors (won't be parsed)
- Exit code 0 = success, 1 = failure

---

### Step 4: Test Locally

```bash
# Install dependencies
npm install

# Make index.ts executable
chmod +x index.ts

# Test with valid input
npm start '{"target": "test", "options": {"verbose": true}}'

# Test with invalid input (should fail validation)
npm start '{}'

# Test error handling
npm start '{"target": "error-trigger"}'
```

---

## Agent Templates

### Template 1: Analysis Agent (Read-Only)

**Use Case**: Scan code, analyze data, generate reports

**Risk Level**: AUTO (safe to run automatically)

**Example**: `security-scanner`, `compliance-checker`, `code-reviewer`

```typescript
export class AnalysisAgent {
  async analyze(input: Input): Promise<Output> {
    const findings: Finding[] = [];

    // Read files
    const files = this.getFiles(input.path);

    for (const file of files) {
      const content = fs.readFileSync(file, 'utf-8');
      // Analyze content
      findings.push(...this.analyzeContent(content));
    }

    return {
      findings,
      summary: this.summarize(findings),
    };
  }

  private analyzeContent(content: string): Finding[] {
    // Analysis logic
    return [];
  }
}
```

---

### Template 2: Mutation Agent (Modifies Code)

**Use Case**: Apply patches, update files, refactor code

**Risk Level**: APPROVAL_REQUIRED (requires human approval)

**Example**: `patcher`

```typescript
export class MutationAgent {
  async mutate(input: Input): Promise<Output> {
    const changes: Change[] = [];

    if (input.dryRun) {
      // Preview changes without applying
      return { applied: false, changes: this.previewChanges(input) };
    }

    // Apply changes
    for (const target of input.targets) {
      const change = await this.applyChange(target);
      changes.push(change);
    }

    return {
      applied: true,
      changes,
      rollbackScript: this.generateRollback(changes),
    };
  }

  private generateRollback(changes: Change[]): string {
    // Generate bash script to undo changes
    return changes.map(c => `git checkout -- "${c.file}"`).join('\n');
  }
}
```

**Safety Features**:
- `dryRun` mode (preview changes)
- Rollback scripts
- Diff generation

---

### Template 3: Notification Agent

**Use Case**: Send alerts, update external systems

**Risk Level**: AUTO (safe side effects)

**Example**: `notifier`

```typescript
export class NotificationAgent {
  async notify(input: Input): Promise<Output> {
    const { channel, message, severity } = input;

    switch (channel) {
      case 'slack':
        return await this.sendSlack(message, severity);
      case 'email':
        return await this.sendEmail(message, severity);
      default:
        throw new Error(`Unknown channel: ${channel}`);
    }
  }

  private async sendSlack(message: string, severity: string): Promise<Output> {
    // Slack integration
    return { success: true, messageId: 'slack-123' };
  }
}
```

---

## Best Practices

### 1. Input Validation

✅ **DO**:
```typescript
const InputSchema = z.object({
  path: z.string().min(1),
  type: z.enum(['file', 'directory']),
  maxSize: z.number().positive().max(1000000),
});
```

❌ **DON'T**:
```typescript
// No validation - dangerous!
function execute(input: any) {
  fs.readFileSync(input.path); // Path traversal risk
}
```

---

### 2. Error Handling

✅ **DO**:
```typescript
try {
  const result = await riskyOperation();
  return { success: true, result };
} catch (error: any) {
  console.error(`Error: ${error.message}`); // Log to stderr
  return { success: false, error: error.message };
}
```

❌ **DON'T**:
```typescript
// Unhandled errors crash agent
const result = await riskyOperation(); // No try-catch
```

---

### 3. Output Format

✅ **DO**:
```typescript
// Structured output
console.log(JSON.stringify({
  success: true,
  data: result,
  metadata: { timestamp: new Date().toISOString() }
}));
```

❌ **DON'T**:
```typescript
// Mixed output (corrupts JSON)
console.log('Processing...');
console.log(JSON.stringify(result));
```

---

### 4. Logging

✅ **DO**:
```typescript
// Logs go to stderr
console.error('[INFO] Processing file:', filename);
console.error('[ERROR] Failed:', error.message);

// Output goes to stdout
console.log(JSON.stringify(output));
```

❌ **DON'T**:
```typescript
// Logs go to stdout (corrupts output)
console.log('Processing...'); // Wrong!
console.log(JSON.stringify(output));
```

---

### 5. File System Access

✅ **DO**:
```typescript
// Safe: Validate paths
const safePath = path.resolve(input.repositoryPath, input.file);
if (!safePath.startsWith(input.repositoryPath)) {
  throw new Error('Path traversal attempt');
}
```

❌ **DON'T**:
```typescript
// Unsafe: Direct path usage
fs.readFileSync(input.file); // Path traversal risk
```

---

## Testing

### Unit Tests

```typescript
import { MyAgent } from './agent';

describe('MyAgent', () => {
  let agent: MyAgent;

  beforeEach(() => {
    agent = new MyAgent();
  });

  it('should process valid input', async () => {
    const input = { target: 'test' };
    const output = await agent.execute(input);

    expect(output.success).toBe(true);
    expect(output.result).toBeDefined();
  });

  it('should handle errors gracefully', async () => {
    const input = { target: 'invalid' };
    const output = await agent.execute(input);

    expect(output.success).toBe(false);
  });
});
```

### Integration Tests

```bash
# Test agent CLI
npm start '{"target": "test"}' > output.json
cat output.json | jq '.success'
# Expected: true
```

---

## Deployment

### 1. Register Agent

```bash
curl -X POST http://localhost:9002/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "type": "TASK",
    "riskLevel": "AUTO",
    "dockerImage": "commandcenter-agent-my-agent",
    "capabilities": ["analysis", "reporting"]
  }'
```

### 2. Use in Workflow

```typescript
const workflow = {
  name: "my-workflow",
  trigger: "MANUAL",
  nodes: [
    {
      id: "step1",
      agentName: "my-agent",
      input: {
        target: "/workspace",
        options: { verbose: true }
      }
    }
  ],
  edges: []
};
```

---

## Examples

See existing agents for reference:
- `security-scanner/` - Analysis agent with pattern matching
- `patcher/` - Mutation agent with dry-run and rollback
- `notifier/` - Notification agent with multiple channels
- `compliance-checker/` - Complex analysis with multiple rule types
- `code-reviewer/` - Static analysis with metrics

---

*Last updated: 2025-11-20*
