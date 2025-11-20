# Patcher Agent

Applies code patches automatically including dependency updates, security fixes, simple refactoring, and configuration changes.

## Overview

- **Type**: MUTATION
- **Risk Level**: APPROVAL_REQUIRED (modifies code)
- **Capabilities**: Dependency updates, security patches, code refactoring, config updates

## Input Schema

```typescript
{
  repositoryPath: string;                        // Path to repository
  patchType: "dependency-update" | "security-patch" | "simple-refactor" | "config-update";
  target: string;                                // Target file, package, or pattern
  changes: {
    oldValue?: string;                           // Old value to replace
    newValue?: string;                           // New value to use
    version?: string;                            // Version for dependency updates
    content?: string;                            // Full content for config files
  };
  dryRun: boolean;                               // Preview without applying (default: false)
}
```

## Output Schema

```typescript
{
  applied: boolean;                              // True if changes were applied
  changes: Array<{
    file: string;                                // File path
    action: "modified" | "created" | "deleted";
    linesChanged?: number;
    diff?: string;                               // Unified diff format
  }>;
  summary: {
    filesModified: number;
    filesCreated: number;
    filesDeleted: number;
    totalLinesChanged: number;
  };
  patchDurationMs: number;
  rollbackScript?: string;                       // Bash script to rollback changes
}
```

## Patch Types

### 1. Dependency Update (`dependency-update`)

Update package dependency versions in `package.json`.

**Required Fields**:
- `target`: Package name (e.g., "express")
- `changes.version`: New version (e.g., "^4.18.2")

**Example**:
```json
{
  "repositoryPath": "/workspace",
  "patchType": "dependency-update",
  "target": "zod",
  "changes": {
    "version": "^3.23.0"
  },
  "dryRun": false
}
```

**Output**:
```json
{
  "applied": true,
  "changes": [{
    "file": "/workspace/package.json",
    "action": "modified",
    "linesChanged": 2,
    "diff": "- \"zod\": \"^3.22.4\"\n+ \"zod\": \"^3.23.0\""
  }],
  "summary": {
    "filesModified": 1,
    "filesCreated": 0,
    "filesDeleted": 0,
    "totalLinesChanged": 2
  },
  "patchDurationMs": 45,
  "rollbackScript": "#!/bin/bash\ngit checkout -- \"/workspace/package.json\""
}
```

### 2. Security Patch (`security-patch`)

Replace vulnerable code patterns with secure alternatives.

**Required Fields**:
- `target`: Filename to patch
- `changes.oldValue`: Vulnerable pattern (regex)
- `changes.newValue`: Secure replacement

**Example** (Fix SQL injection):
```json
{
  "repositoryPath": "/workspace",
  "patchType": "security-patch",
  "target": "database.ts",
  "changes": {
    "oldValue": "SELECT \\* FROM users WHERE id = '\\$\\{userId\\}'",
    "newValue": "SELECT * FROM users WHERE id = $1"
  },
  "dryRun": false
}
```

### 3. Simple Refactor (`simple-refactor`)

Find and replace across multiple files (rename variables, update imports).

**Required Fields**:
- `target`: File pattern to match (optional, processes all if empty)
- `changes.oldValue`: Pattern to find (regex)
- `changes.newValue`: Replacement value

**Example** (Rename function):
```json
{
  "repositoryPath": "/workspace",
  "patchType": "simple-refactor",
  "target": "src/",
  "changes": {
    "oldValue": "getUserData\\(",
    "newValue": "fetchUserProfile("
  },
  "dryRun": false
}
```

### 4. Config Update (`config-update`)

Create or replace configuration files.

**Required Fields**:
- `target`: Config file path (relative to repo root)
- `changes.content`: Full file content

**Example** (Add security middleware):
```json
{
  "repositoryPath": "/workspace",
  "patchType": "config-update",
  "target": "src/middleware/security.ts",
  "changes": {
    "content": "import { Request, Response, NextFunction } from 'express';\n\nexport function securityHeaders(req: Request, res: Response, next: NextFunction) {\n  res.setHeader('X-Frame-Options', 'DENY');\n  next();\n}"
  },
  "dryRun": false
}
```

## Dry Run Mode

Always test patches with `dryRun: true` first:

```bash
# Preview changes
npm start '{"repositoryPath": "/workspace", "patchType": "security-patch", "target": "config.ts", "changes": {"oldValue": "old", "newValue": "new"}, "dryRun": true}'

# Review diff output, then apply
npm start '{"repositoryPath": "/workspace", "patchType": "security-patch", "target": "config.ts", "changes": {"oldValue": "old", "newValue": "new"}, "dryRun": false}'
```

## Safety Features

1. **Rollback Scripts**: Every non-dry-run patch generates a rollback script
2. **Validation**: Zod schema validation for all inputs
3. **Error Handling**: Fails fast with clear error messages
4. **Excluded Directories**: Won't modify `node_modules`, `venv`, `.git`, `dist`, `build`
5. **Diff Generation**: Shows exactly what changed

## Rollback Example

The agent returns a rollback script in the output:

```bash
#!/bin/bash
# Rollback script

git checkout -- "/workspace/src/config.ts"
git checkout -- "/workspace/package.json"
```

Save this to a file and execute to undo changes:

```bash
chmod +x rollback.sh
./rollback.sh
```

## Integration with Workflows

The patcher agent requires **human approval** before execution:

```typescript
const workflow = {
  name: "apply-security-patch",
  nodes: [
    {
      id: "patch",
      agentName: "patcher",
      input: {
        repositoryPath: "/workspace",
        patchType: "security-patch",
        target: "api/routes.ts",
        changes: {
          oldValue: "eval\\(userInput\\)",
          newValue: "// REMOVED: eval is dangerous"
        },
        dryRun: false
      },
      riskLevel: "APPROVAL_REQUIRED"  // Workflow will pause for approval
    }
  ],
  edges: []
};
```

Workflow execution flow:
1. User triggers workflow
2. System shows patch preview (diff)
3. User approves or rejects
4. If approved, patch is applied
5. Rollback script stored for recovery

## Usage Examples

### Update Dependency

```bash
cd orchestration/agents/patcher
npm install
npm start '{"repositoryPath": "../../..", "patchType": "dependency-update", "target": "typescript", "changes": {"version": "^5.4.0"}, "dryRun": true}'
```

### Apply Security Fix

```bash
npm start '{"repositoryPath": "../../..", "patchType": "security-patch", "target": "server.ts", "changes": {"oldValue": "process\\.env\\.SECRET \\|\\| \"default\"", "newValue": "process.env.SECRET"}, "dryRun": true}'
```

### Refactor Code

```bash
npm start '{"repositoryPath": "../../..", "patchType": "simple-refactor", "target": "src/", "changes": {"oldValue": "oldFunctionName", "newValue": "newFunctionName"}, "dryRun": true}'
```

### Add Config File

```bash
npm start '{"repositoryPath": "../../..", "patchType": "config-update", "target": ".prettierrc", "changes": {"content": "{\"semi\": true, \"singleQuote\": true}"}, "dryRun": false}'
```

## Exit Codes

- **0**: Patch applied successfully
- **1**: Patch failed (invalid input, file not found, pattern not matched, etc.)

## Limitations

- **No Syntax Validation**: Agent doesn't validate TypeScript/JavaScript syntax after patching
- **Simple Regex**: Uses basic regex, not AST-based refactoring
- **No Git Integration**: Doesn't create commits automatically (workflow handles this)
- **Single File for Security Patches**: Can only patch one file at a time for security fixes

## Best Practices

1. **Always dry-run first**: Preview changes before applying
2. **Use version control**: Commit before running patcher
3. **Test after patching**: Run tests to ensure no breakage
4. **Save rollback scripts**: Store rollback scripts for recovery
5. **Small patches**: Apply one logical change per patch for easier rollback

## Common Errors

**Error**: `Dependency "X" not found in package.json`
- **Cause**: Package name doesn't exist in dependencies or devDependencies
- **Fix**: Check spelling, ensure package is installed

**Error**: `File not found: X`
- **Cause**: Target file doesn't exist
- **Fix**: Verify file path, check for typos

**Error**: `Pattern not found in file`
- **Cause**: oldValue regex didn't match anything
- **Fix**: Check regex pattern, view file contents

**Error**: `oldValue and newValue required`
- **Cause**: Missing required fields for patch type
- **Fix**: Provide all required fields in changes object
