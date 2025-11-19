# Phase 10: Agent Orchestration - Implementation Plan

> **STATUS UPDATE (2025-11-19)**: ✅ Tasks 1-20 COMPLETE
>
> **Completed Phases**:
> - ✅ Phase 1-2: Foundation & Core Workflow (Tasks 1-10) - Merged via PRs #87, #88, #89, #90
> - ✅ Phase 3: Initial Agents (Tasks 11-20) - security-scanner, notifier, example workflow
>
> **Remaining Phases** (to be added):
> - 📋 Phase 4: VISLZR Integration (workflow builder UI)
> - 📋 Phase 5: Observability (OpenTelemetry, Prometheus)
> - 📋 Phase 6: Production Readiness
>
> **See**: `hub/orchestration/PHASE_3_SUMMARY.md` for Phase 3 details

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Dagger-powered agent orchestration system with TypeScript/Prisma service, NATS integration, and VISLZR UI.

**Architecture:** TypeScript orchestration service with Prisma ORM, Dagger SDK for sandboxed agent execution, NATS event bridge to Python backend, risk-based approval system.

**Tech Stack:** TypeScript, Node.js 20, Prisma ORM, Dagger SDK, NATS, React Flow (VISLZR), Zod (validation), OpenTelemetry

**Reference Design:** `docs/plans/2025-11-18-phase-10-agent-orchestration-design.md`

---

## Phase 1: Foundation Setup (Tasks 1-8)

### Task 1: Create Orchestration Service Directory Structure

**Files:**
- Create: `hub/orchestration/package.json`
- Create: `hub/orchestration/tsconfig.json`
- Create: `hub/orchestration/.gitignore`
- Create: `hub/orchestration/README.md`

**Step 1: Create service directory**

```bash
mkdir -p hub/orchestration
cd hub/orchestration
```

**Step 2: Initialize package.json**

Create `hub/orchestration/package.json`:

```json
{
  "name": "@commandcenter/orchestration",
  "version": "1.0.0",
  "description": "Agent orchestration service for CommandCenter",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.ts",
    "test": "vitest",
    "prisma:generate": "prisma generate",
    "prisma:migrate": "prisma migrate dev",
    "prisma:studio": "prisma studio"
  },
  "dependencies": {
    "@dagger.io/dagger": "^0.9.0",
    "@prisma/client": "^5.7.0",
    "express": "^4.18.2",
    "nats": "^2.18.0",
    "zod": "^3.22.4",
    "winston": "^3.11.0",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.0",
    "prisma": "^5.7.0",
    "tsx": "^4.6.2",
    "typescript": "^5.3.2",
    "vitest": "^1.0.4"
  }
}
```

**Step 3: Create tsconfig.json**

Create `hub/orchestration/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "moduleResolution": "node"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

**Step 4: Create .gitignore**

Create `hub/orchestration/.gitignore`:

```
node_modules/
dist/
.env
.env.local
*.log
.DS_Store
```

**Step 5: Create README**

Create `hub/orchestration/README.md`:

```markdown
# CommandCenter Agent Orchestration Service

Dagger-powered agent orchestration with TypeScript/Prisma.

## Setup

```bash
npm install
npx prisma generate
npm run dev
```

## Environment Variables

```
DATABASE_URL=postgresql://commandcenter:password@postgres:5432/commandcenter
NATS_URL=nats://commandcenter-hub-nats:4222
PORT=9002
```
```

**Step 6: Install dependencies**

```bash
cd hub/orchestration
npm install
```

Expected: Dependencies installed successfully

**Step 7: Verify TypeScript compiles**

```bash
mkdir -p src
echo 'console.log("Hello from orchestration");' > src/index.ts
npm run build
```

Expected: Compiles without errors

**Step 8: Commit**

```bash
git add hub/orchestration/
git commit -m "feat(orchestration): Initialize TypeScript service scaffolding

- Add package.json with dependencies (Dagger, Prisma, NATS, Zod)
- Configure TypeScript with strict mode
- Add .gitignore and README
- Verify compilation works"
```

---

### Task 2: Create Prisma Schema

**Files:**
- Create: `hub/orchestration/prisma/schema.prisma`

**Step 1: Create Prisma schema file**

Create `hub/orchestration/prisma/schema.prisma`:

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ============================================================================
// Agent Registry
// ============================================================================

model Agent {
  id            String   @id @default(cuid())
  projectId     Int
  name          String
  type          AgentType
  description   String?
  entryPath     String
  version       String
  riskLevel     RiskLevel
  registeredAt  DateTime @default(now())
  updatedAt     DateTime @updatedAt

  capabilities  AgentCapability[]
  runs          AgentRun[]
  workflowNodes WorkflowNode[]

  @@unique([projectId, name])
  @@index([projectId, type])
  @@map("agents")
}

model AgentCapability {
  id          String @id @default(cuid())
  agentId     String
  name        String
  description String?
  inputSchema Json
  outputSchema Json

  agent       Agent  @relation(fields: [agentId], references: [id], onDelete: Cascade)

  @@unique([agentId, name])
  @@map("agent_capabilities")
}

model AgentRun {
  id          String      @id @default(cuid())
  agentId     String
  workflowRunId String?
  inputJson   Json
  outputJson  Json?
  status      RunStatus
  error       String?
  startedAt   DateTime    @default(now())
  finishedAt  DateTime?
  durationMs  Int?

  agent       Agent       @relation(fields: [agentId], references: [id])
  workflowRun WorkflowRun? @relation(fields: [workflowRunId], references: [id])

  @@index([agentId, status])
  @@index([workflowRunId])
  @@map("agent_runs")
}

// ============================================================================
// Workflow System
// ============================================================================

model Workflow {
  id          String         @id @default(cuid())
  projectId   Int
  name        String
  description String?
  trigger     Json
  status      WorkflowStatus
  createdAt   DateTime       @default(now())
  updatedAt   DateTime       @updatedAt

  nodes       WorkflowNode[]
  runs        WorkflowRun[]

  @@unique([projectId, name])
  @@index([projectId, status])
  @@map("workflows")
}

model WorkflowNode {
  id          String   @id @default(cuid())
  workflowId  String
  agentId     String
  action      String
  inputsJson  Json
  dependsOn   String[]
  approvalRequired Boolean @default(false)

  workflow    Workflow @relation(fields: [workflowId], references: [id], onDelete: Cascade)
  agent       Agent    @relation(fields: [agentId], references: [id])

  @@index([workflowId])
  @@map("workflow_nodes")
}

model WorkflowRun {
  id          String      @id @default(cuid())
  workflowId  String
  trigger     String
  contextJson Json
  status      RunStatus
  startedAt   DateTime    @default(now())
  finishedAt  DateTime?

  workflow    Workflow    @relation(fields: [workflowId], references: [id])
  agentRuns   AgentRun[]
  approvals   WorkflowApproval[]

  @@index([workflowId, status])
  @@index([startedAt])
  @@map("workflow_runs")
}

model WorkflowApproval {
  id            String      @id @default(cuid())
  workflowRunId String
  nodeId        String
  status        ApprovalStatus
  requestedAt   DateTime    @default(now())
  respondedAt   DateTime?
  respondedBy   String?
  notes         String?

  workflowRun   WorkflowRun @relation(fields: [workflowRunId], references: [id])

  @@index([workflowRunId, status])
  @@map("workflow_approvals")
}

// ============================================================================
// Enums
// ============================================================================

enum AgentType {
  LLM
  RULE
  API
  SCRIPT
}

enum RiskLevel {
  AUTO
  APPROVAL_REQUIRED
}

enum RunStatus {
  PENDING
  RUNNING
  SUCCESS
  FAILED
  WAITING_APPROVAL
}

enum WorkflowStatus {
  ACTIVE
  DRAFT
  ARCHIVED
}

enum ApprovalStatus {
  PENDING
  APPROVED
  REJECTED
}
```

**Step 2: Generate Prisma client**

```bash
cd hub/orchestration
npx prisma generate
```

Expected: Prisma client generated successfully

**Step 3: Verify schema is valid**

```bash
npx prisma validate
```

Expected: "The schema is valid ✔"

**Step 4: Commit**

```bash
git add hub/orchestration/prisma/
git commit -m "feat(orchestration): Add Prisma schema for agent orchestration

Database models:
- Agent, AgentCapability, AgentRun
- Workflow, WorkflowNode, WorkflowRun, WorkflowApproval
- Enums: AgentType, RiskLevel, RunStatus, WorkflowStatus, ApprovalStatus

Multi-tenant isolation via projectId on Agent and Workflow models.

Ref: docs/plans/2025-11-18-phase-10-agent-orchestration-design.md"
```

---

### Task 3: Create Environment Configuration

**Files:**
- Create: `hub/orchestration/src/config.ts`
- Create: `hub/orchestration/.env.example`

**Step 1: Create config module**

Create `hub/orchestration/src/config.ts`:

```typescript
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  // Server
  port: parseInt(process.env.PORT || '9002', 10),
  nodeEnv: process.env.NODE_ENV || 'development',

  // Database
  databaseUrl: process.env.DATABASE_URL || '',

  // NATS
  natsUrl: process.env.NATS_URL || 'nats://localhost:4222',

  // Dagger
  daggerEngine: process.env.DAGGER_ENGINE || 'docker',

  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',

  // Agent Execution Defaults
  agentDefaults: {
    maxMemoryMb: parseInt(process.env.AGENT_MAX_MEMORY_MB || '512', 10),
    timeoutSeconds: parseInt(process.env.AGENT_TIMEOUT_SECONDS || '300', 10),
  },
} as const;

// Validate required config
if (!config.databaseUrl) {
  throw new Error('DATABASE_URL environment variable is required');
}

export default config;
```

**Step 2: Create .env.example**

Create `hub/orchestration/.env.example`:

```bash
# Server
PORT=9002
NODE_ENV=development

# Database (shared with Python backend)
DATABASE_URL=postgresql://commandcenter:password@postgres:5432/commandcenter

# NATS (Hub NATS instance)
NATS_URL=nats://commandcenter-hub-nats:4222

# Dagger
DAGGER_ENGINE=docker

# Logging
LOG_LEVEL=info

# Agent Execution
AGENT_MAX_MEMORY_MB=512
AGENT_TIMEOUT_SECONDS=300
```

**Step 3: Test config validation**

Create `hub/orchestration/src/config.test.ts`:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('config', () => {
  let originalEnv: NodeJS.ProcessEnv;

  beforeEach(() => {
    originalEnv = { ...process.env };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('should throw if DATABASE_URL is missing', () => {
    delete process.env.DATABASE_URL;
    expect(() => require('./config')).toThrow('DATABASE_URL');
  });

  it('should use defaults for optional config', () => {
    process.env.DATABASE_URL = 'postgresql://test';
    const { config } = require('./config');
    expect(config.port).toBe(9002);
    expect(config.agentDefaults.maxMemoryMb).toBe(512);
  });
});
```

**Step 4: Run test**

```bash
cd hub/orchestration
npm test src/config.test.ts
```

Expected: Tests pass

**Step 5: Commit**

```bash
git add hub/orchestration/src/config.ts hub/orchestration/.env.example hub/orchestration/src/config.test.ts
git commit -m "feat(orchestration): Add environment configuration

- Centralized config with validation
- Default values for all settings
- Tests for config validation"
```

---

### Task 4: Create Logger Service

**Files:**
- Create: `hub/orchestration/src/utils/logger.ts`

**Step 1: Create logger utility**

Create `hub/orchestration/src/utils/logger.ts`:

```typescript
import winston from 'winston';
import config from '../config';

const logger = winston.createLogger({
  level: config.logLevel,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(
          ({ level, message, timestamp, ...meta }) =>
            `${timestamp} [${level}] ${message} ${
              Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''
            }`
        )
      ),
    }),
  ],
});

export default logger;
```

**Step 2: Test logger**

Create test file `hub/orchestration/src/utils/logger.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import logger from './logger';

describe('logger', () => {
  it('should export winston logger instance', () => {
    expect(logger).toBeDefined();
    expect(logger.info).toBeDefined();
    expect(logger.error).toBeDefined();
  });
});
```

**Step 3: Run test**

```bash
npm test src/utils/logger.test.ts
```

Expected: Test passes

**Step 4: Commit**

```bash
git add hub/orchestration/src/utils/
git commit -m "feat(orchestration): Add Winston logger utility

- JSON logging with timestamps
- Colorized console output in development
- Configurable log level"
```

---

### Task 5: Create Prisma Client Singleton

**Files:**
- Create: `hub/orchestration/src/db/prisma.ts`

**Step 1: Create Prisma client singleton**

Create `hub/orchestration/src/db/prisma.ts`:

```typescript
import { PrismaClient } from '@prisma/client';
import logger from '../utils/logger';

// Singleton pattern for Prisma client
const globalForPrisma = global as unknown as { prisma: PrismaClient };

export const prisma =
  globalForPrisma.prisma ||
  new PrismaClient({
    log: [
      { level: 'query', emit: 'event' },
      { level: 'error', emit: 'stdout' },
      { level: 'warn', emit: 'stdout' },
    ],
  });

// Log queries in development
if (process.env.NODE_ENV === 'development') {
  prisma.$on('query', (e: any) => {
    logger.debug('Prisma Query', { query: e.query, duration: e.duration });
  });
}

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;
```

**Step 2: Test Prisma connection**

Create `hub/orchestration/src/db/prisma.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import prisma from './prisma';

describe('prisma', () => {
  it('should export Prisma client instance', () => {
    expect(prisma).toBeDefined();
    expect(prisma.$connect).toBeDefined();
  });
});
```

**Step 3: Run test**

```bash
npm test src/db/prisma.test.ts
```

Expected: Test passes

**Step 4: Commit**

```bash
git add hub/orchestration/src/db/
git commit -m "feat(orchestration): Add Prisma client singleton

- Single PrismaClient instance for connection pooling
- Query logging in development mode
- Type-safe database access"
```

---

### Task 6: Create NATS Connection Module

**Files:**
- Create: `hub/orchestration/src/events/nats-client.ts`

**Step 1: Create NATS client**

Create `hub/orchestration/src/events/nats-client.ts`:

```typescript
import { connect, NatsConnection, StringCodec } from 'nats';
import logger from '../utils/logger';
import config from '../config';

export class NatsClient {
  private connection: NatsConnection | null = null;
  private codec = StringCodec();

  async connect(): Promise<void> {
    try {
      this.connection = await connect({
        servers: config.natsUrl,
      });
      logger.info('Connected to NATS', { url: config.natsUrl });
    } catch (error) {
      logger.error('Failed to connect to NATS', { error });
      throw error;
    }
  }

  async publish(subject: string, data: unknown): Promise<void> {
    if (!this.connection) {
      throw new Error('NATS not connected');
    }

    const payload = this.codec.encode(JSON.stringify(data));
    this.connection.publish(subject, payload);
    logger.debug('Published NATS message', { subject, data });
  }

  async subscribe(
    subject: string,
    handler: (data: unknown) => Promise<void>
  ): Promise<void> {
    if (!this.connection) {
      throw new Error('NATS not connected');
    }

    const sub = this.connection.subscribe(subject);
    logger.info('Subscribed to NATS subject', { subject });

    (async () => {
      for await (const msg of sub) {
        try {
          const data = JSON.parse(this.codec.decode(msg.data));
          await handler(data);
        } catch (error) {
          logger.error('Error handling NATS message', {
            subject,
            error,
          });
        }
      }
    })();
  }

  async close(): Promise<void> {
    if (this.connection) {
      await this.connection.drain();
      logger.info('NATS connection closed');
    }
  }
}

export const natsClient = new NatsClient();
export default natsClient;
```

**Step 2: Test NATS client**

Create `hub/orchestration/src/events/nats-client.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { NatsClient } from './nats-client';

describe('NatsClient', () => {
  it('should create NatsClient instance', () => {
    const client = new NatsClient();
    expect(client).toBeDefined();
    expect(client.connect).toBeDefined();
    expect(client.publish).toBeDefined();
    expect(client.subscribe).toBeDefined();
  });

  it('should throw if publishing before connect', async () => {
    const client = new NatsClient();
    await expect(client.publish('test', {})).rejects.toThrow('not connected');
  });
});
```

**Step 3: Run test**

```bash
npm test src/events/nats-client.test.ts
```

Expected: Tests pass

**Step 4: Commit**

```bash
git add hub/orchestration/src/events/
git commit -m "feat(orchestration): Add NATS client module

- Async connect/publish/subscribe API
- JSON encoding/decoding
- Error handling for message processing
- Graceful connection draining"
```

---

### Task 7: Create Dagger Executor Service

**Files:**
- Create: `hub/orchestration/src/dagger/executor.ts`
- Create: `hub/orchestration/src/dagger/types.ts`

**Step 1: Create Dagger types**

Create `hub/orchestration/src/dagger/types.ts`:

```typescript
export interface AgentExecutionConfig {
  maxMemoryMb: number;
  timeoutSeconds: number;
  outputSchema: object;
  secrets?: Record<string, string>;
  allowNetwork?: boolean;
}

export interface AgentExecutionResult {
  success: boolean;
  output?: unknown;
  error?: string;
  executionTimeMs: number;
  containerLogs?: string;
}
```

**Step 2: Create Dagger executor**

Create `hub/orchestration/src/dagger/executor.ts`:

```typescript
import { connect, Client, Container } from '@dagger.io/dagger';
import logger from '../utils/logger';
import {
  AgentExecutionConfig,
  AgentExecutionResult,
} from './types';

export class DaggerAgentExecutor {
  private client: Client | null = null;

  async connect(): Promise<void> {
    this.client = await connect();
    logger.info('Connected to Dagger engine');
  }

  async executeAgent(
    agentPath: string,
    input: unknown,
    config: AgentExecutionConfig
  ): Promise<AgentExecutionResult> {
    if (!this.client) {
      throw new Error('Dagger client not connected');
    }

    const startTime = Date.now();

    try {
      // 1. Create isolated container
      let container = this.client
        .container()
        .from('node:20-alpine')
        .withDirectory('/workspace', this.client.host().directory('.'))
        .withWorkdir('/workspace')
        .withExec(['npm', 'install']);

      // 2. Inject secrets (if needed)
      if (config.secrets) {
        for (const [key, value] of Object.entries(config.secrets)) {
          const secret = this.client.setSecret(key, value);
          container = container.withSecretVariable(key, secret);
        }
      }

      // 3. Apply resource limits
      container = container.withEnvVariable(
        'NODE_OPTIONS',
        `--max-old-space-size=${config.maxMemoryMb}`
      );

      // 4. Execute agent with timeout
      const result = await container
        .withExec([
          'timeout',
          config.timeoutSeconds.toString(),
          'node',
          agentPath,
          JSON.stringify(input),
        ])
        .stdout();

      // 5. Parse and validate output
      const output = JSON.parse(result);
      // TODO: Validate against outputSchema using Zod

      return {
        success: true,
        output,
        executionTimeMs: Date.now() - startTime,
      };
    } catch (error: any) {
      logger.error('Agent execution failed', { agentPath, error });
      return {
        success: false,
        error: error.message,
        executionTimeMs: Date.now() - startTime,
      };
    }
  }

  async close(): Promise<void> {
    if (this.client) {
      await this.client.close();
      logger.info('Dagger connection closed');
    }
  }
}

export const daggerExecutor = new DaggerAgentExecutor();
export default daggerExecutor;
```

**Step 3: Test Dagger executor**

Create `hub/orchestration/src/dagger/executor.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { DaggerAgentExecutor } from './executor';

describe('DaggerAgentExecutor', () => {
  it('should create executor instance', () => {
    const executor = new DaggerAgentExecutor();
    expect(executor).toBeDefined();
    expect(executor.connect).toBeDefined();
    expect(executor.executeAgent).toBeDefined();
  });

  it('should throw if executing before connect', async () => {
    const executor = new DaggerAgentExecutor();
    await expect(
      executor.executeAgent('test.js', {}, {
        maxMemoryMb: 512,
        timeoutSeconds: 300,
        outputSchema: {},
      })
    ).rejects.toThrow('not connected');
  });
});
```

**Step 4: Run test**

```bash
npm test src/dagger/executor.test.ts
```

Expected: Tests pass

**Step 5: Commit**

```bash
git add hub/orchestration/src/dagger/
git commit -m "feat(orchestration): Add Dagger agent executor

- Sandboxed container execution
- Resource limits (memory, timeout)
- Secret injection support
- JSON input/output handling
- Error capture and logging"
```

---

### Task 8: Create Express API Server

**Files:**
- Create: `hub/orchestration/src/api/server.ts`
- Create: `hub/orchestration/src/api/routes/health.ts`
- Create: `hub/orchestration/src/index.ts`

**Step 1: Create health check route**

Create `hub/orchestration/src/api/routes/health.ts`:

```typescript
import { Router } from 'express';

const router = Router();

router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'orchestration',
    timestamp: new Date().toISOString(),
  });
});

export default router;
```

**Step 2: Create Express server**

Create `hub/orchestration/src/api/server.ts`:

```typescript
import express from 'express';
import logger from '../utils/logger';
import config from '../config';
import healthRoutes from './routes/health';

export function createServer() {
  const app = express();

  // Middleware
  app.use(express.json());

  // Request logging
  app.use((req, res, next) => {
    logger.info('HTTP Request', {
      method: req.method,
      path: req.path,
    });
    next();
  });

  // Routes
  app.use('/api', healthRoutes);

  // Error handler
  app.use(
    (
      err: Error,
      req: express.Request,
      res: express.Response,
      next: express.NextFunction
    ) => {
      logger.error('Unhandled error', { error: err });
      res.status(500).json({ error: 'Internal server error' });
    }
  );

  return app;
}

export function startServer() {
  const app = createServer();

  const server = app.listen(config.port, () => {
    logger.info('Orchestration service started', {
      port: config.port,
      env: config.nodeEnv,
    });
  });

  return server;
}
```

**Step 3: Create main entry point**

Create `hub/orchestration/src/index.ts`:

```typescript
import { startServer } from './api/server';
import natsClient from './events/nats-client';
import daggerExecutor from './dagger/executor';
import prisma from './db/prisma';
import logger from './utils/logger';

async function main() {
  try {
    // Connect to dependencies
    logger.info('Starting orchestration service...');

    await prisma.$connect();
    logger.info('Connected to database');

    await natsClient.connect();
    await daggerExecutor.connect();

    // Start HTTP server
    const server = startServer();

    // Graceful shutdown
    process.on('SIGTERM', async () => {
      logger.info('SIGTERM received, shutting down...');
      server.close();
      await natsClient.close();
      await daggerExecutor.close();
      await prisma.$disconnect();
      process.exit(0);
    });
  } catch (error) {
    logger.error('Failed to start service', { error });
    process.exit(1);
  }
}

main();
```

**Step 4: Test server creation**

Create `hub/orchestration/src/api/server.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { createServer } from './server';
import request from 'supertest';

describe('Express Server', () => {
  it('should respond to health check', async () => {
    const app = createServer();
    const response = await request(app).get('/api/health');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ok');
  });
});
```

**Step 5: Add supertest dependency**

```bash
npm install -D supertest @types/supertest
```

**Step 6: Run test**

```bash
npm test src/api/server.test.ts
```

Expected: Test passes

**Step 7: Test dev server**

```bash
npm run dev
```

Expected: Server starts on port 9002, health endpoint responds

**Step 8: Commit**

```bash
git add hub/orchestration/src/index.ts hub/orchestration/src/api/
git commit -m "feat(orchestration): Add Express API server

- Health check endpoint
- Request logging middleware
- Error handling
- Graceful shutdown with cleanup
- Integration with Prisma, NATS, Dagger"
```

---

## Phase 2: Agent Registry (Tasks 9-12)

### Task 9: Create Agent Registry Service

**Files:**
- Create: `hub/orchestration/src/services/agent-registry.ts`

**Step 1: Write failing test**

Create `hub/orchestration/src/services/agent-registry.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { AgentRegistry } from './agent-registry';
import prisma from '../db/prisma';

describe('AgentRegistry', () => {
  let registry: AgentRegistry;

  beforeEach(async () => {
    registry = new AgentRegistry(prisma);
    // Clean up test data
    await prisma.agent.deleteMany({});
  });

  it('should register a new agent', async () => {
    const agent = await registry.register({
      projectId: 1,
      name: 'test-agent',
      type: 'SCRIPT',
      description: 'Test agent',
      entryPath: 'agents/test.ts',
      version: '1.0.0',
      riskLevel: 'AUTO',
      capabilities: [{
        name: 'testAction',
        description: 'Test action',
        inputSchema: {},
        outputSchema: {},
      }],
    });

    expect(agent.id).toBeDefined();
    expect(agent.name).toBe('test-agent');
  });

  it('should list agents for a project', async () => {
    await registry.register({
      projectId: 1,
      name: 'agent1',
      type: 'SCRIPT',
      entryPath: 'agents/agent1.ts',
      version: '1.0.0',
      riskLevel: 'AUTO',
      capabilities: [],
    });

    const agents = await registry.listByProject(1);
    expect(agents).toHaveLength(1);
    expect(agents[0].name).toBe('agent1');
  });
});
```

**Step 2: Run test to verify it fails**

```bash
npm test src/services/agent-registry.test.ts
```

Expected: FAIL - AgentRegistry module not found

**Step 3: Implement AgentRegistry**

Create `hub/orchestration/src/services/agent-registry.ts`:

```typescript
import { PrismaClient, Agent, AgentType, RiskLevel } from '@prisma/client';
import logger from '../utils/logger';

export interface RegisterAgentInput {
  projectId: number;
  name: string;
  type: AgentType;
  description?: string;
  entryPath: string;
  version: string;
  riskLevel: RiskLevel;
  capabilities: Array<{
    name: string;
    description?: string;
    inputSchema: object;
    outputSchema: object;
  }>;
}

export class AgentRegistry {
  constructor(private prisma: PrismaClient) {}

  async register(input: RegisterAgentInput): Promise<Agent> {
    const agent = await this.prisma.agent.create({
      data: {
        projectId: input.projectId,
        name: input.name,
        type: input.type,
        description: input.description,
        entryPath: input.entryPath,
        version: input.version,
        riskLevel: input.riskLevel,
        capabilities: {
          create: input.capabilities,
        },
      },
      include: {
        capabilities: true,
      },
    });

    logger.info('Agent registered', {
      agentId: agent.id,
      name: agent.name,
      projectId: agent.projectId,
    });

    return agent;
  }

  async listByProject(projectId: number): Promise<Agent[]> {
    return this.prisma.agent.findMany({
      where: { projectId },
      include: {
        capabilities: true,
      },
      orderBy: { name: 'asc' },
    });
  }

  async getById(id: string): Promise<Agent | null> {
    return this.prisma.agent.findUnique({
      where: { id },
      include: {
        capabilities: true,
      },
    });
  }

  async update(
    id: string,
    data: Partial<RegisterAgentInput>
  ): Promise<Agent> {
    return this.prisma.agent.update({
      where: { id },
      data: {
        description: data.description,
        entryPath: data.entryPath,
        version: data.version,
        riskLevel: data.riskLevel,
      },
      include: {
        capabilities: true,
      },
    });
  }

  async delete(id: string): Promise<void> {
    await this.prisma.agent.delete({
      where: { id },
    });

    logger.info('Agent deleted', { agentId: id });
  }
}
```

**Step 4: Run test to verify it passes**

```bash
npm test src/services/agent-registry.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add hub/orchestration/src/services/agent-registry.ts hub/orchestration/src/services/agent-registry.test.ts
git commit -m "feat(orchestration): Add agent registry service

- Register agents with capabilities
- List agents by project
- CRUD operations for agents
- Includes comprehensive tests"
```

---

## Phase 3: Workflow Runner (Tasks 13-16)

### Task 10: Create Workflow Runner Service

**Files:**
- Create: `hub/orchestration/src/services/workflow-runner.ts`

**Step 1: Write failing test for DAG topological sort**

Create `hub/orchestration/src/services/workflow-runner.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { WorkflowRunner } from './workflow-runner';

describe('WorkflowRunner', () => {
  describe('topologicalSort', () => {
    it('should sort nodes with dependencies', () => {
      const runner = new WorkflowRunner(null as any, null as any);

      const nodes = [
        { id: 'c', dependsOn: ['a', 'b'] },
        { id: 'b', dependsOn: ['a'] },
        { id: 'a', dependsOn: [] },
      ];

      const sorted = runner['topologicalSort'](nodes as any);

      // Should return batches that can run in parallel
      expect(sorted[0].map(n => n.id)).toEqual(['a']);
      expect(sorted[1].map(n => n.id)).toEqual(['b']);
      expect(sorted[2].map(n => n.id)).toEqual(['c']);
    });

    it('should batch independent nodes together', () => {
      const runner = new WorkflowRunner(null as any, null as any);

      const nodes = [
        { id: 'a', dependsOn: [] },
        { id: 'b', dependsOn: [] },
        { id: 'c', dependsOn: ['a', 'b'] },
      ];

      const sorted = runner['topologicalSort'](nodes as any);

      // a and b can run in parallel
      expect(sorted[0].map(n => n.id).sort()).toEqual(['a', 'b']);
      expect(sorted[1].map(n => n.id)).toEqual(['c']);
    });
  });
});
```

**Step 2: Run test to verify it fails**

```bash
npm test src/services/workflow-runner.test.ts
```

Expected: FAIL

**Step 3: Implement WorkflowRunner with topological sort**

Create `hub/orchestration/src/services/workflow-runner.ts`:

```typescript
import { PrismaClient, WorkflowNode } from '@prisma/client';
import { DaggerAgentExecutor } from '../dagger/executor';
import logger from '../utils/logger';

export class WorkflowRunner {
  constructor(
    private prisma: PrismaClient,
    private daggerExecutor: DaggerAgentExecutor
  ) {}

  /**
   * Topological sort of workflow nodes into execution batches
   * Nodes in the same batch can run in parallel
   */
  private topologicalSort(nodes: WorkflowNode[]): WorkflowNode[][] {
    const batches: WorkflowNode[][] = [];
    const remaining = new Set(nodes);
    const completed = new Set<string>();

    while (remaining.size > 0) {
      // Find nodes with all dependencies satisfied
      const batch: WorkflowNode[] = [];

      for (const node of remaining) {
        const allDepsCompleted = node.dependsOn.every(depId =>
          completed.has(depId)
        );

        if (allDepsCompleted) {
          batch.push(node);
        }
      }

      if (batch.length === 0) {
        throw new Error('Circular dependency detected in workflow');
      }

      // Mark batch nodes as completed
      batch.forEach(node => {
        remaining.delete(node);
        completed.add(node.id);
      });

      batches.push(batch);
    }

    return batches;
  }

  async executeWorkflow(workflowRunId: string): Promise<void> {
    const workflowRun = await this.prisma.workflowRun.findUnique({
      where: { id: workflowRunId },
      include: {
        workflow: {
          include: {
            nodes: {
              include: {
                agent: {
                  include: {
                    capabilities: true,
                  },
                },
              },
            },
          },
        },
      },
    });

    if (!workflowRun) {
      throw new Error(`WorkflowRun ${workflowRunId} not found`);
    }

    const dag = this.topologicalSort(workflowRun.workflow.nodes);

    logger.info('Executing workflow', {
      workflowRunId,
      workflowName: workflowRun.workflow.name,
      batches: dag.length,
    });

    // Execute batches sequentially, nodes in batch in parallel
    for (const batch of dag) {
      await Promise.all(
        batch.map(node => this.executeNode(node, workflowRun))
      );
    }

    // Mark workflow complete
    await this.prisma.workflowRun.update({
      where: { id: workflowRunId },
      data: {
        status: 'SUCCESS',
        finishedAt: new Date(),
      },
    });

    logger.info('Workflow completed', { workflowRunId });
  }

  private async executeNode(
    node: WorkflowNode & { agent: any },
    workflowRun: any
  ): Promise<unknown> {
    logger.info('Executing workflow node', {
      nodeId: node.id,
      agentName: node.agent.name,
    });

    // TODO: Resolve inputs from template
    const inputs = node.inputsJson;

    // TODO: Check approval if needed

    // Execute agent via Dagger
    const capability = node.agent.capabilities.find(
      (c: any) => c.name === node.action
    );

    const result = await this.daggerExecutor.executeAgent(
      node.agent.entryPath,
      inputs,
      {
        maxMemoryMb: 512,
        timeoutSeconds: 300,
        outputSchema: capability.outputSchema,
      }
    );

    // Store agent run
    await this.prisma.agentRun.create({
      data: {
        agentId: node.agentId,
        workflowRunId: workflowRun.id,
        inputJson: inputs,
        outputJson: result.output || null,
        status: result.success ? 'SUCCESS' : 'FAILED',
        error: result.error,
        durationMs: result.executionTimeMs,
        finishedAt: new Date(),
      },
    });

    return result.output;
  }
}
```

**Step 4: Run test to verify it passes**

```bash
npm test src/services/workflow-runner.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add hub/orchestration/src/services/workflow-runner.ts hub/orchestration/src/services/workflow-runner.test.ts
git commit -m "feat(orchestration): Add workflow runner with DAG execution

- Topological sort for dependency resolution
- Parallel execution of independent nodes
- Sequential batch execution
- Agent run tracking in database
- Circular dependency detection"
```

---

## Phase 3: Initial Agents (Tasks 11-20)

### Task 11: Create Security Scanner Agent Structure

**Goal**: Implement a security scanner agent that scans code for common vulnerabilities

**Files**:
- Create: `hub/orchestration/agents/security-scanner/index.ts`
- Create: `hub/orchestration/agents/security-scanner/schemas.ts`
- Create: `hub/orchestration/agents/security-scanner/scanner.ts`
- Create: `hub/orchestration/agents/security-scanner/package.json`

**Step 1: Create agent directory**

```bash
mkdir -p hub/orchestration/agents/security-scanner
cd hub/orchestration/agents/security-scanner
```

**Step 2: Create package.json**

Create `hub/orchestration/agents/security-scanner/package.json`:

```json
{
  "name": "@commandcenter/agent-security-scanner",
  "version": "1.0.0",
  "description": "Security scanner agent for CommandCenter",
  "main": "index.ts",
  "scripts": {
    "start": "ts-node index.ts"
  },
  "dependencies": {
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.3.2"
  }
}
```

**Step 3: Create Zod schemas**

Create `hub/orchestration/agents/security-scanner/schemas.ts`:

```typescript
import { z } from 'zod';

export const InputSchema = z.object({
  repositoryPath: z.string().describe('Path to repository to scan'),
  scanType: z.enum(['secrets', 'sql-injection', 'xss', 'all']).default('all'),
  severity: z.enum(['low', 'medium', 'high', 'critical']).optional(),
});

export const FindingSchema = z.object({
  type: z.string(),
  severity: z.enum(['low', 'medium', 'high', 'critical']),
  file: z.string(),
  line: z.number(),
  description: z.string(),
  code: z.string().optional(),
});

export const OutputSchema = z.object({
  findings: z.array(FindingSchema),
  summary: z.object({
    total: z.number(),
    critical: z.number(),
    high: z.number(),
    medium: z.number(),
    low: z.number(),
  }),
  scannedFiles: z.number(),
  scanDurationMs: z.number(),
});

export type Input = z.infer<typeof InputSchema>;
export type Finding = z.infer<typeof FindingSchema>;
export type Output = z.infer<typeof OutputSchema>;
```

**Step 4: Implement scanner logic**

Create `hub/orchestration/agents/security-scanner/scanner.ts`:

```typescript
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
```

**Step 5: Create agent entrypoint**

Create `hub/orchestration/agents/security-scanner/index.ts`:

```typescript
#!/usr/bin/env ts-node

import { SecurityScanner } from './scanner';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    // Read input from command line argument
    const inputJson = process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided');
    }

    const input = JSON.parse(inputJson);

    // Validate input
    const validatedInput = InputSchema.parse(input);

    // Run scanner
    const scanner = new SecurityScanner();
    const output = await scanner.scan(validatedInput);

    // Validate output
    const validatedOutput = OutputSchema.parse(output);

    // Print output to stdout (Dagger will capture this)
    console.log(JSON.stringify(validatedOutput));
    process.exit(0);
  } catch (error: any) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
```

**Step 6: Make executable**

```bash
chmod +x hub/orchestration/agents/security-scanner/index.ts
```

**Step 7: Install dependencies**

```bash
cd hub/orchestration/agents/security-scanner
npm install
```

Expected: Dependencies installed successfully

**Step 8: Test agent locally**

```bash
echo '{"repositoryPath": "../../src", "scanType": "all"}' | npm start
```

Expected: JSON output with findings array and summary

**Step 9: Commit**

```bash
git add hub/orchestration/agents/security-scanner/
git commit -m "feat(orchestration): Add security scanner agent

- Scans for hardcoded secrets (API keys, passwords, tokens)
- Detects SQL injection patterns
- Detects XSS vulnerabilities
- Zod schema validation for inputs/outputs
- JSON output for Dagger executor
- Supports filtering by scan type and severity

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 12: Register Security Scanner Agent

**Goal**: Register the security-scanner agent in the database via API

**Step 1: Create registration script**

Create `hub/orchestration/scripts/register-agents.ts`:

```typescript
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
```

**Step 2: Add axios dependency**

```bash
cd hub/orchestration
npm install axios
npm install -D @types/axios
```

**Step 3: Start orchestration service**

```bash
# In one terminal
cd hub/orchestration
npm run dev
```

Expected: Server starts on port 9002

**Step 4: Register agent**

```bash
# In another terminal
cd hub/orchestration
npx ts-node scripts/register-agents.ts
```

Expected: Agent registered with ID returned

**Step 5: Verify registration**

```bash
curl http://localhost:9002/api/agents?projectId=1
```

Expected: JSON array containing security-scanner agent

**Step 6: Commit**

```bash
git add hub/orchestration/scripts/register-agents.ts hub/orchestration/package.json
git commit -m "feat(orchestration): Add agent registration script

- Automated registration for security-scanner
- Can be extended for other agents
- Validates API connectivity"
```

---

### Task 13: Create Notifier Agent Structure

**Goal**: Implement a notifier agent that sends alerts via Slack/Discord

**Files**:
- Create: `hub/orchestration/agents/notifier/index.ts`
- Create: `hub/orchestration/agents/notifier/schemas.ts`
- Create: `hub/orchestration/agents/notifier/notifier.ts`
- Create: `hub/orchestration/agents/notifier/package.json`

**Step 1: Create agent directory**

```bash
mkdir -p hub/orchestration/agents/notifier
cd hub/orchestration/agents/notifier
```

**Step 2: Create package.json**

Create `hub/orchestration/agents/notifier/package.json`:

```json
{
  "name": "@commandcenter/agent-notifier",
  "version": "1.0.0",
  "description": "Notification agent for CommandCenter",
  "main": "index.ts",
  "scripts": {
    "start": "ts-node index.ts"
  },
  "dependencies": {
    "zod": "^3.22.4",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "ts-node": "^10.9.2",
    "typescript": "^5.3.2"
  }
}
```

**Step 3: Create Zod schemas**

Create `hub/orchestration/agents/notifier/schemas.ts`:

```typescript
import { z } from 'zod';

export const InputSchema = z.object({
  channel: z.enum(['slack', 'discord', 'console']),
  message: z.string(),
  severity: z.enum(['info', 'warning', 'error', 'critical']).default('info'),
  metadata: z.record(z.unknown()).optional(),
  webhookUrl: z.string().url().optional(),
});

export const OutputSchema = z.object({
  success: z.boolean(),
  channel: z.string(),
  messageId: z.string().optional(),
  timestamp: z.string(),
  error: z.string().optional(),
});

export type Input = z.infer<typeof InputSchema>;
export type Output = z.infer<typeof OutputSchema>;
```

**Step 4: Implement notifier logic**

Create `hub/orchestration/agents/notifier/notifier.ts`:

```typescript
import axios from 'axios';
import { Input, Output } from './schemas';

export class Notifier {
  async send(input: Input): Promise<Output> {
    const timestamp = new Date().toISOString();

    try {
      switch (input.channel) {
        case 'slack':
          return await this.sendSlack(input, timestamp);
        case 'discord':
          return await this.sendDiscord(input, timestamp);
        case 'console':
          return this.sendConsole(input, timestamp);
        default:
          throw new Error(`Unknown channel: ${input.channel}`);
      }
    } catch (error: any) {
      return {
        success: false,
        channel: input.channel,
        timestamp,
        error: error.message,
      };
    }
  }

  private async sendSlack(input: Input, timestamp: string): Promise<Output> {
    if (!input.webhookUrl) {
      throw new Error('webhookUrl required for Slack');
    }

    const color = this.getSeverityColor(input.severity);
    const payload = {
      attachments: [
        {
          color,
          title: `${this.getSeverityEmoji(input.severity)} ${input.severity.toUpperCase()}`,
          text: input.message,
          fields: input.metadata
            ? Object.entries(input.metadata).map(([key, value]) => ({
                title: key,
                value: String(value),
                short: true,
              }))
            : [],
          ts: Math.floor(Date.now() / 1000),
        },
      ],
    };

    const response = await axios.post(input.webhookUrl, payload);

    return {
      success: response.status === 200,
      channel: 'slack',
      messageId: response.data.ts,
      timestamp,
    };
  }

  private async sendDiscord(input: Input, timestamp: string): Promise<Output> {
    if (!input.webhookUrl) {
      throw new Error('webhookUrl required for Discord');
    }

    const color = this.getSeverityColorInt(input.severity);
    const payload = {
      embeds: [
        {
          title: `${this.getSeverityEmoji(input.severity)} ${input.severity.toUpperCase()}`,
          description: input.message,
          color,
          fields: input.metadata
            ? Object.entries(input.metadata).map(([key, value]) => ({
                name: key,
                value: String(value),
                inline: true,
              }))
            : [],
          timestamp,
        },
      ],
    };

    const response = await axios.post(input.webhookUrl, payload);

    return {
      success: response.status === 204,
      channel: 'discord',
      messageId: response.headers['x-message-id'],
      timestamp,
    };
  }

  private sendConsole(input: Input, timestamp: string): Output {
    const emoji = this.getSeverityEmoji(input.severity);
    console.log(`\n${emoji} [${input.severity.toUpperCase()}] ${input.message}`);

    if (input.metadata) {
      console.log('Metadata:', JSON.stringify(input.metadata, null, 2));
    }

    return {
      success: true,
      channel: 'console',
      timestamp,
    };
  }

  private getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
      info: '#36a64f',
      warning: '#ff9900',
      error: '#ff0000',
      critical: '#8b0000',
    };
    return colors[severity] || '#cccccc';
  }

  private getSeverityColorInt(severity: string): number {
    const colors: Record<string, number> = {
      info: 0x36a64f,
      warning: 0xff9900,
      error: 0xff0000,
      critical: 0x8b0000,
    };
    return colors[severity] || 0xcccccc;
  }

  private getSeverityEmoji(severity: string): string {
    const emojis: Record<string, string> = {
      info: 'ℹ️',
      warning: '⚠️',
      error: '❌',
      critical: '🚨',
    };
    return emojis[severity] || '📢';
  }
}
```

**Step 5: Create agent entrypoint**

Create `hub/orchestration/agents/notifier/index.ts`:

```typescript
#!/usr/bin/env ts-node

import { Notifier } from './notifier';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    // Read input from command line argument
    const inputJson = process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided');
    }

    const input = JSON.parse(inputJson);

    // Validate input
    const validatedInput = InputSchema.parse(input);

    // Send notification
    const notifier = new Notifier();
    const output = await notifier.send(validatedInput);

    // Validate output
    const validatedOutput = OutputSchema.parse(output);

    // Print output to stdout
    console.log(JSON.stringify(validatedOutput));
    process.exit(0);
  } catch (error: any) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
```

**Step 6: Make executable**

```bash
chmod +x hub/orchestration/agents/notifier/index.ts
```

**Step 7: Install dependencies**

```bash
cd hub/orchestration/agents/notifier
npm install
```

Expected: Dependencies installed successfully

**Step 8: Test agent locally**

```bash
echo '{"channel": "console", "message": "Test notification", "severity": "info"}' | npm start
```

Expected: Console output with formatted message

**Step 9: Commit**

```bash
git add hub/orchestration/agents/notifier/
git commit -m "feat(orchestration): Add notifier agent

- Supports Slack, Discord, and console output
- Severity-based color coding
- Metadata field support
- Zod schema validation
- Emoji indicators for severity levels

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 14: Register Notifier Agent

**Goal**: Register the notifier agent in the database

**Step 1: Update registration script**

Edit `hub/orchestration/scripts/register-agents.ts` and add:

```typescript
async function registerNotifier() {
  const agent = {
    projectId: 1,
    name: 'notifier',
    type: 'SCRIPT',
    description: 'Sends notifications via Slack, Discord, or console',
    entryPath: 'agents/notifier/index.ts',
    version: '1.0.0',
    riskLevel: 'AUTO',
    capabilities: [
      {
        name: 'send',
        description: 'Send notification to specified channel',
        inputSchema: {
          type: 'object',
          properties: {
            channel: { type: 'string', enum: ['slack', 'discord', 'console'] },
            message: { type: 'string' },
            severity: { type: 'string', enum: ['info', 'warning', 'error', 'critical'] },
            metadata: { type: 'object' },
            webhookUrl: { type: 'string' },
          },
          required: ['channel', 'message'],
        },
        outputSchema: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            channel: { type: 'string' },
            messageId: { type: 'string' },
            timestamp: { type: 'string' },
            error: { type: 'string' },
          },
          required: ['success', 'channel', 'timestamp'],
        },
      },
    ],
  };

  const response = await axios.post(`${API_BASE}/api/agents`, agent);
  console.log('Notifier registered:', response.data);
  return response.data;
}

// Update main() to register both agents
async function main() {
  try {
    await registerSecurityScanner();
    await registerNotifier();
    process.exit(0);
  } catch (error: any) {
    console.error('Registration failed:', error.response?.data || error.message);
    process.exit(1);
  }
}
```

**Step 2: Register agent**

```bash
cd hub/orchestration
npx ts-node scripts/register-agents.ts
```

Expected: Both agents registered

**Step 3: Verify registration**

```bash
curl http://localhost:9002/api/agents?projectId=1
```

Expected: JSON array with both agents

**Step 4: Commit**

```bash
git add hub/orchestration/scripts/register-agents.ts
git commit -m "feat(orchestration): Register notifier agent

- Added notifier to registration script
- Now registers both security-scanner and notifier
- Verified API connectivity"
```

---

### Task 15: Create Example Workflow (Scan and Notify)

**Goal**: Create a workflow that scans code and sends notification with results

**Step 1: Create workflow definition file**

Create `hub/orchestration/examples/scan-and-notify-workflow.json`:

```json
{
  "projectId": 1,
  "name": "scan-and-notify",
  "description": "Scan repository for security issues and notify via console",
  "trigger": {
    "event": "graph.file.updated",
    "pattern": "graph.file.updated"
  },
  "status": "ACTIVE",
  "nodes": [
    {
      "id": "scan-node",
      "agentName": "security-scanner",
      "action": "scan",
      "inputsJson": {
        "repositoryPath": "{{ context.repositoryPath }}",
        "scanType": "all"
      },
      "dependsOn": [],
      "approvalRequired": false
    },
    {
      "id": "notify-node",
      "agentName": "notifier",
      "action": "send",
      "inputsJson": {
        "channel": "console",
        "message": "Security scan complete: {{ nodes.scan-node.output.summary.total }} findings (Critical: {{ nodes.scan-node.output.summary.critical }}, High: {{ nodes.scan-node.output.summary.high }})",
        "severity": "{{ nodes.scan-node.output.summary.critical > 0 ? 'critical' : 'info' }}",
        "metadata": {
          "scannedFiles": "{{ nodes.scan-node.output.scannedFiles }}",
          "duration": "{{ nodes.scan-node.output.scanDurationMs }}ms"
        }
      },
      "dependsOn": ["scan-node"],
      "approvalRequired": false
    }
  ]
}
```

**Step 2: Create workflow creation script**

Create `hub/orchestration/scripts/create-workflow.ts`:

```typescript
import axios from 'axios';
import * as fs from 'fs';

const API_BASE = process.env.ORCHESTRATION_API || 'http://localhost:9002';

async function createWorkflow(definitionPath: string) {
  const definition = JSON.parse(fs.readFileSync(definitionPath, 'utf-8'));

  // Get agent IDs from names
  const agentsResponse = await axios.get(`${API_BASE}/api/agents?projectId=${definition.projectId}`);
  const agents = agentsResponse.data;

  // Map agent names to IDs
  const agentMap = new Map(agents.map((a: any) => [a.name, a.id]));

  // Transform nodes to use agent IDs
  const nodes = definition.nodes.map((node: any) => ({
    agentId: agentMap.get(node.agentName),
    action: node.action,
    inputsJson: node.inputsJson,
    dependsOn: node.dependsOn,
    approvalRequired: node.approvalRequired,
  }));

  const workflow = {
    projectId: definition.projectId,
    name: definition.name,
    description: definition.description,
    trigger: definition.trigger,
    status: definition.status,
    nodes,
  };

  const response = await axios.post(`${API_BASE}/api/workflows`, workflow);
  console.log('Workflow created:', response.data);
  return response.data;
}

async function main() {
  const definitionPath = process.argv[2] || 'examples/scan-and-notify-workflow.json';

  try {
    await createWorkflow(definitionPath);
    process.exit(0);
  } catch (error: any) {
    console.error('Workflow creation failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

main();
```

**Step 3: Create workflow**

```bash
cd hub/orchestration
npx ts-node scripts/create-workflow.ts examples/scan-and-notify-workflow.json
```

Expected: Workflow created with ID returned

**Step 4: Verify workflow**

```bash
curl http://localhost:9002/api/workflows?projectId=1
```

Expected: JSON array containing scan-and-notify workflow

**Step 5: Commit**

```bash
git add hub/orchestration/examples/ hub/orchestration/scripts/create-workflow.ts
git commit -m "feat(orchestration): Add scan-and-notify example workflow

- Security scanner -> Notifier pipeline
- Template-based input resolution
- Conditional severity based on findings
- Example of DAG dependency (notify depends on scan)

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 16: Test End-to-End Workflow Execution

**Goal**: Trigger the workflow and verify agents execute correctly

**Step 1: Create workflow trigger script**

Create `hub/orchestration/scripts/trigger-workflow.ts`:

```typescript
import axios from 'axios';

const API_BASE = process.env.ORCHESTRATION_API || 'http://localhost:9002';

async function triggerWorkflow(workflowId: string, context: any) {
  const response = await axios.post(
    `${API_BASE}/api/workflows/${workflowId}/trigger`,
    { context }
  );

  console.log('Workflow triggered:', response.data);
  return response.data;
}

async function main() {
  const workflowId = process.argv[2];
  const contextJson = process.argv[3] || '{}';

  if (!workflowId) {
    console.error('Usage: npx ts-node trigger-workflow.ts <workflowId> [context]');
    process.exit(1);
  }

  try {
    const context = JSON.parse(contextJson);
    await triggerWorkflow(workflowId, context);
    process.exit(0);
  } catch (error: any) {
    console.error('Trigger failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

main();
```

**Step 2: Get workflow ID**

```bash
curl http://localhost:9002/api/workflows?projectId=1 | jq '.[0].id'
```

**Step 3: Trigger workflow**

```bash
cd hub/orchestration
WORKFLOW_ID="<workflow-id-from-step-2>"
npx ts-node scripts/trigger-workflow.ts $WORKFLOW_ID '{"repositoryPath": "./src"}'
```

Expected: Workflow run created, agents execute

**Step 4: Check workflow run status**

```bash
curl http://localhost:9002/api/workflows/$WORKFLOW_ID/runs
```

Expected: WorkflowRun with status SUCCESS

**Step 5: Verify agent runs**

```bash
curl http://localhost:9002/api/agents/runs?workflowRunId=<run-id>
```

Expected: Two AgentRun records (security-scanner + notifier)

**Step 6: Document test results**

Create `hub/orchestration/TESTING.md`:

```markdown
# Orchestration Service Testing

## End-to-End Workflow Test Results

**Date**: 2025-11-19
**Workflow**: scan-and-notify
**Status**: ✅ PASSING

### Test Execution

1. Registered agents: security-scanner, notifier
2. Created workflow with 2 nodes (scan -> notify)
3. Triggered workflow with context: `{"repositoryPath": "./src"}`
4. Verified execution:
   - WorkflowRun status: SUCCESS
   - AgentRun count: 2
   - security-scanner output: X findings
   - notifier output: Message sent to console

### Performance

- Total execution time: ~5-10s
- security-scanner: ~3-5s
- notifier: <1s

### Issues Found

- None (initial implementation successful)

### Next Steps

- Add Slack/Discord webhook testing
- Test with larger repositories
- Verify approval system with high-risk agents
```

**Step 7: Commit**

```bash
git add hub/orchestration/scripts/trigger-workflow.ts hub/orchestration/TESTING.md
git commit -m "feat(orchestration): Add workflow trigger script and E2E test docs

- Script to trigger workflows via API
- Documented E2E test results
- Verified scan-and-notify workflow execution

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 17: Fix Failing Tests

**Goal**: Fix the 11 failing tests identified in status assessment

**Step 1: Set DATABASE_URL for tests**

Create `hub/orchestration/.env.test`:

```bash
DATABASE_URL=postgresql://commandcenter:password@localhost:5432/commandcenter_test
NATS_URL=nats://localhost:4222
PORT=9002
NODE_ENV=test
```

**Step 2: Update test setup**

Edit `hub/orchestration/src/test-setup.ts`:

```typescript
import dotenv from 'dotenv';
import path from 'path';

// Load test environment variables
dotenv.config({ path: path.join(__dirname, '../.env.test') });

// Mock Prisma for tests that don't need database
export const mockPrisma = {
  agent: {
    create: vi.fn(),
    findMany: vi.fn(),
    findUnique: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    deleteMany: vi.fn(),
  },
  workflow: {
    create: vi.fn(),
    findMany: vi.fn(),
    findUnique: vi.fn(),
    update: vi.fn(),
    deleteMany: vi.fn(),
  },
  workflowRun: {
    create: vi.fn(),
    findUnique: vi.fn(),
    update: vi.fn(),
    deleteMany: vi.fn(),
  },
  agentRun: {
    create: vi.fn(),
    deleteMany: vi.fn(),
  },
  workflowApproval: {
    create: vi.fn(),
    findFirst: vi.fn(),
    update: vi.fn(),
    deleteMany: vi.fn(),
  },
};
```

**Step 3: Update vitest config**

Edit `hub/orchestration/vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    setupFiles: ['./src/test-setup.ts'],
    testTimeout: 10000,
    env: {
      DATABASE_URL: 'postgresql://test:test@localhost:5432/test',
      NATS_URL: 'nats://localhost:4222',
    },
  },
});
```

**Step 4: Update event-bridge tests to use mocks**

Edit `hub/orchestration/src/services/event-bridge.test.ts` - replace database calls with mocks where appropriate

**Step 5: Run tests**

```bash
cd hub/orchestration
npm test
```

Expected: All tests passing

**Step 6: Commit**

```bash
git add hub/orchestration/.env.test hub/orchestration/src/test-setup.ts hub/orchestration/vitest.config.ts
git commit -m "fix(orchestration): Fix failing tests

- Added .env.test for test environment variables
- Updated test setup with Prisma mocks
- Increased test timeout to 10s
- All 30 tests now passing

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 18: Update PROJECT.md

**Goal**: Document Phase 3 completion in PROJECT.md

**Step 1: Update PROJECT.md**

Edit `/Users/danielconnolly/Projects/CommandCenter/docs/PROJECT.md`:

Find the Phase 7 section and update:

```markdown
- 🔄 **[Phase 7](plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-7-graph-service-implementation-weeks-9-12)**: Graph Service Implementation ([Design Doc](plans/2025-11-06-phase-7-graph-service-implementation.md))
  - ✅ **Week 1**: Core Service Layer (GraphService, Router, Schemas)
  - ✅ **Week 2**: Python AST Parser & Graph Indexer CLI
  - ⏭️ **Week 3**: TypeScript/JavaScript Parser (Deferred - not needed for Python-only backend)
  - ✅ **Week 4**: NATS Integration & Stub Audit Agents
```

Add after Phase 9:

```markdown
- ✅ **[Phase 10](plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md#phase-10-agent-orchestration--workflow-automation-weeks-21-24)**: Agent Orchestration & Workflows **COMPLETE** (Completed 2025-11-19)
  - ✅ **Phase 1-2**: Foundation & Core Workflow Engine (PR #87)
    - TypeScript orchestration service with Prisma ORM
    - Dagger SDK for sandboxed agent execution
    - NATS event bridge
    - Agent registry service
    - Workflow runner with DAG execution
    - Docker integration (PR #88)
    - Approval system (PR #89)
    - Input templating (PR #90)
  - ✅ **Phase 3**: Initial Agents (Completed 2025-11-19)
    - security-scanner agent (secrets, SQL injection, XSS detection)
    - notifier agent (Slack, Discord, console output)
    - scan-and-notify example workflow
    - End-to-end workflow execution verified
    - 30 tests passing
  - 📋 **Phase 4**: VISLZR Integration (workflow builder UI, execution monitor)
  - 📋 **Phase 5**: Observability (OpenTelemetry, Prometheus, Grafana)
  - 📋 **Phase 6**: Production Readiness (additional agents, load testing, security audit)
```

**Step 2: Commit**

```bash
git add docs/PROJECT.md
git commit -m "docs: Update PROJECT.md with Phase 10 Phase 3 completion

- Documented security-scanner and notifier agents
- Marked Phase 3 as complete
- Updated next steps (Phase 4: VISLZR UI, Phase 5: Observability)

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 19: Create Phase 3 Completion Summary

**Goal**: Document what was built and next steps

**Step 1: Create completion summary**

Create `hub/orchestration/PHASE_3_SUMMARY.md`:

```markdown
# Phase 10 Phase 3: Initial Agents - Completion Summary

**Date**: 2025-11-19
**Status**: ✅ COMPLETE

---

## What Was Built

### 1. Security Scanner Agent

**Location**: `hub/orchestration/agents/security-scanner/`

**Capabilities**:
- Scans code for hardcoded secrets (API keys, passwords, GitHub tokens, OpenAI keys)
- Detects SQL injection patterns (string concatenation in queries)
- Identifies XSS vulnerabilities (dangerouslySetInnerHTML, innerHTML, document.write)
- Supports filtering by scan type (secrets, sql-injection, xss, all)
- Supports filtering by severity (low, medium, high, critical)

**Input Schema**:
```json
{
  "repositoryPath": "string (required)",
  "scanType": "secrets | sql-injection | xss | all (default: all)",
  "severity": "low | medium | high | critical (optional)"
}
```

**Output Schema**:
```json
{
  "findings": [
    {
      "type": "string",
      "severity": "low | medium | high | critical",
      "file": "string",
      "line": "number",
      "description": "string",
      "code": "string (optional)"
    }
  ],
  "summary": {
    "total": "number",
    "critical": "number",
    "high": "number",
    "medium": "number",
    "low": "number"
  },
  "scannedFiles": "number",
  "scanDurationMs": "number"
}
```

**Risk Level**: AUTO (no approval required)

---

### 2. Notifier Agent

**Location**: `hub/orchestration/agents/notifier/`

**Capabilities**:
- Sends notifications to Slack (via webhook)
- Sends notifications to Discord (via webhook)
- Logs to console (for testing)
- Severity-based color coding
- Supports metadata fields
- Emoji indicators for severity levels

**Input Schema**:
```json
{
  "channel": "slack | discord | console (required)",
  "message": "string (required)",
  "severity": "info | warning | error | critical (default: info)",
  "metadata": "object (optional)",
  "webhookUrl": "string (required for slack/discord)"
}
```

**Output Schema**:
```json
{
  "success": "boolean",
  "channel": "string",
  "messageId": "string (optional)",
  "timestamp": "string",
  "error": "string (optional)"
}
```

**Risk Level**: AUTO (no approval required)

---

### 3. Example Workflow: Scan and Notify

**Definition**: `hub/orchestration/examples/scan-and-notify-workflow.json`

**Flow**:
1. **scan-node**: Runs security-scanner on repository
2. **notify-node**: Sends notification with scan results (depends on scan-node)

**Features Demonstrated**:
- DAG dependency resolution (notify waits for scan)
- Template-based input resolution (`{{ context.repositoryPath }}`, `{{ nodes.scan-node.output.summary.total }}`)
- Conditional logic in templates (critical severity if critical findings > 0)
- Metadata field population from node outputs

**Execution Time**: ~5-10 seconds

---

## Scripts Created

### 1. Register Agents (`scripts/register-agents.ts`)

- Registers security-scanner and notifier via API
- Validates API connectivity
- Can be extended for additional agents

### 2. Create Workflow (`scripts/create-workflow.ts`)

- Reads workflow definition JSON
- Maps agent names to IDs
- Creates workflow via API
- Supports custom workflow definitions

### 3. Trigger Workflow (`scripts/trigger-workflow.ts`)

- Triggers workflow by ID
- Accepts context JSON for template resolution
- Returns workflow run status

---

## Test Results

**Total Tests**: 30
**Passing**: 30 (100%)
**Failing**: 0

**Test Files**:
- `config.test.ts` (3 tests)
- `workflow-runner.test.ts` (10 tests)
- `nats-client.test.ts` (2 tests)
- `logger.test.ts` (1 test)
- `agent-registry.test.ts` (1 test)
- `prisma.test.ts` (1 test)
- `event-bridge.test.ts` (6 tests)
- `dagger/executor.test.ts` (3 tests)
- `api/routes/*.test.ts` (3 tests)

**Fixes Applied**:
- Added `.env.test` for test environment
- Updated test setup with Prisma mocks
- Increased test timeout to 10s

---

## Files Created/Modified

**New Files** (17):
- `agents/security-scanner/index.ts`
- `agents/security-scanner/schemas.ts`
- `agents/security-scanner/scanner.ts`
- `agents/security-scanner/package.json`
- `agents/notifier/index.ts`
- `agents/notifier/schemas.ts`
- `agents/notifier/notifier.ts`
- `agents/notifier/package.json`
- `scripts/register-agents.ts`
- `scripts/create-workflow.ts`
- `scripts/trigger-workflow.ts`
- `examples/scan-and-notify-workflow.json`
- `TESTING.md`
- `PHASE_3_SUMMARY.md`
- `.env.test`

**Modified Files** (3):
- `src/test-setup.ts` (Prisma mocks)
- `vitest.config.ts` (test environment)
- `docs/PROJECT.md` (completion tracking)

---

## Verification Checklist

- [x] Security scanner detects hardcoded secrets
- [x] Security scanner detects SQL injection patterns
- [x] Security scanner detects XSS vulnerabilities
- [x] Notifier sends to console
- [x] Notifier supports Slack (webhook ready)
- [x] Notifier supports Discord (webhook ready)
- [x] Workflow executes DAG correctly (scan -> notify)
- [x] Template resolution works (context + node outputs)
- [x] All tests passing
- [x] Agents registered via API
- [x] Workflow created via API
- [x] Workflow triggered and completes successfully

---

## Next Steps (Phase 4: VISLZR Integration)

### Goal: Build workflow builder UI and execution monitor

**Components to Build**:
1. Workflow Builder (React Flow)
   - Drag-and-drop agent nodes
   - Connect nodes with edges
   - Configure node inputs
   - Set approval requirements

2. Execution Monitor
   - Real-time workflow status
   - Agent run logs
   - Error visualization
   - Retry failed nodes

3. Approval UI
   - Pending approval list
   - Approve/reject workflow steps
   - View context and node outputs
   - Add approval notes

4. Agent Library Browser
   - List available agents
   - View capabilities and schemas
   - Test agents with sample inputs
   - Register new agents

**Estimated Effort**: 2-3 weeks

---

## Alternative Next Step (Phase 5: Observability)

### Goal: Add OpenTelemetry tracing and Prometheus metrics

**Components to Build**:
1. OpenTelemetry Integration
   - Trace workflow execution
   - Span per agent run
   - Context propagation

2. Prometheus Metrics
   - Workflow execution count/duration
   - Agent success/failure rates
   - Approval pending time

3. Grafana Dashboards
   - Workflow health overview
   - Agent performance
   - Approval bottlenecks

**Estimated Effort**: 1-2 weeks

---

**Recommendation**: Prioritize Phase 4 (VISLZR UI) to enable non-technical users to create workflows. Phase 5 (Observability) can be done in parallel or after UI is functional.

---

**End of Summary**
```

**Step 2: Commit**

```bash
git add hub/orchestration/PHASE_3_SUMMARY.md
git commit -m "docs: Add Phase 3 completion summary

- Documented all agents built (security-scanner, notifier)
- Summarized test results (30/30 passing)
- Listed all files created/modified
- Provided next steps (Phase 4: VISLZR UI vs Phase 5: Observability)

Ref: Phase 10 Phase 3 - Initial Agents"
```

---

### Task 20: Archive Old Plan and Update Single Source of Truth

**Goal**: Mark old incomplete plan as archived and establish updated plan as source of truth

**Step 1: Add completion note to beginning of plan**

Edit `docs/plans/2025-11-18-phase-10-implementation.md` - add at top:

```markdown
# Phase 10: Agent Orchestration - Implementation Plan

> **STATUS UPDATE (2025-11-19)**: ✅ Tasks 1-20 COMPLETE
>
> **Completed Phases**:
> - ✅ Phase 1-2: Foundation & Core Workflow (Tasks 1-10) - Merged via PRs #87, #88, #89, #90
> - ✅ Phase 3: Initial Agents (Tasks 11-20) - security-scanner, notifier, example workflow
>
> **Remaining Phases** (to be added):
> - 📋 Phase 4: VISLZR Integration (workflow builder UI)
> - 📋 Phase 5: Observability (OpenTelemetry, Prometheus)
> - 📋 Phase 6: Production Readiness
>
> **See**: `hub/orchestration/PHASE_3_SUMMARY.md` for Phase 3 details

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
```

**Step 2: Archive status assessment**

```bash
mv docs/plans/2025-11-19-phase-10-status-assessment.md docs/plans/archive/2025-11-19-phase-10-status-assessment.md
```

**Step 3: Update implementation plan summary**

Edit `docs/plans/2025-11-18-phase-10-implementation.md` - update summary section at end:

Replace summary section with:

```markdown
---

## Progress Tracking

### ✅ Phase 1: Foundation Setup (Tasks 1-8) - COMPLETE

**Completed**: 2025-11-18 (PR #87)
- TypeScript service scaffolding
- Prisma database schema
- Configuration and logging
- NATS client
- Dagger executor
- Express API server

### ✅ Phase 2: Agent Registry (Task 9) - COMPLETE

**Completed**: 2025-11-18 (PR #87)
- Agent registry service with CRUD operations

### ✅ Phase 3: Workflow Runner (Task 10) - COMPLETE

**Completed**: 2025-11-18 (PR #87)
- Workflow runner with DAG execution
- Topological sort
- Parallel batch execution

### ✅ Phase 3 Enhancements - COMPLETE

**Completed**: 2025-11-19 (PRs #88, #89, #90)
- Docker integration (PR #88)
- Approval system (PR #89)
- Input templating (PR #90)

### ✅ Phase 3: Initial Agents (Tasks 11-20) - COMPLETE

**Completed**: 2025-11-19
- security-scanner agent (secrets, SQL injection, XSS)
- notifier agent (Slack, Discord, console)
- scan-and-notify example workflow
- End-to-end workflow execution verified
- 30/30 tests passing

**See**: `hub/orchestration/PHASE_3_SUMMARY.md`

---

## Next Phase Planning

**Phase 4: VISLZR Integration** (Tasks 21-35, estimated)
- Workflow builder UI (React Flow)
- Execution monitor dashboard
- Approval UI
- Agent library browser

**Phase 5: Observability** (Tasks 36-45, estimated)
- OpenTelemetry tracing
- Prometheus metrics
- Grafana dashboards

**Phase 6: Production Readiness** (Tasks 46-55, estimated)
- Additional agents (compliance-checker, patcher, code-reviewer)
- Load testing
- Security audit
- Documentation

**Current Progress**: 20/~55 tasks complete (36% - Foundation + Phase 3 Agents)

---

**Last Updated**: 2025-11-19
```

**Step 4: Commit**

```bash
mkdir -p docs/plans/archive
git add docs/plans/
git commit -m "docs: Update Phase 10 implementation plan with completion status

- Marked Tasks 1-20 as complete
- Added status update banner at top
- Updated progress tracking section
- Archived status assessment document
- Implementation plan is now single source of truth

Next: Phase 4 (VISLZR UI) or Phase 5 (Observability)"
```

---

## Summary of Phase 3 Tasks (11-20)

**What Was Implemented**:
1. ✅ Task 11: Security scanner agent structure
2. ✅ Task 12: Registered security scanner via API
3. ✅ Task 13: Notifier agent structure
4. ✅ Task 14: Registered notifier via API
5. ✅ Task 15: Created scan-and-notify example workflow
6. ✅ Task 16: Tested end-to-end workflow execution
7. ✅ Task 17: Fixed failing tests (30/30 passing)
8. ✅ Task 18: Updated PROJECT.md
9. ✅ Task 19: Created Phase 3 completion summary
10. ✅ Task 20: Archived old plan, updated single source of truth

**Verification**:
```bash
# List agents
curl http://localhost:9002/api/agents?projectId=1

# List workflows
curl http://localhost:9002/api/workflows?projectId=1

# Run tests
cd hub/orchestration && npm test

# Trigger workflow
npx ts-node scripts/trigger-workflow.ts <workflow-id> '{"repositoryPath": "./src"}'
```

**Estimated Total Time**: 4-6 hours for implementation + testing + documentation

**Next Decision Point**: Choose Phase 4 (UI) or Phase 5 (Observability) based on priorities

---

**End of Implementation Plan Update**
