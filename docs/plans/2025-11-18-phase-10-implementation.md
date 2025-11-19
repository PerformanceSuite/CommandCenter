# Phase 10: Agent Orchestration - Implementation Plan

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

## Summary

This implementation plan covers the foundation (Tasks 1-8) and begins Phase 2 (Agent Registry) and Phase 3 (Workflow Runner).

**What's Implemented**:
- ✅ TypeScript service scaffolding
- ✅ Prisma database schema
- ✅ Configuration and logging
- ✅ NATS client
- ✅ Dagger executor
- ✅ Express API server
- ✅ Agent registry service
- ✅ Workflow runner with DAG execution

**Remaining Work** (to be added in subsequent tasks):
- Agent registry API endpoints
- Workflow API endpoints (create, list, trigger)
- NATS event bridge (workflow triggers)
- Approval system
- Sample agents (security-scanner, notifier)
- VISLZR UI integration
- OpenTelemetry tracing
- Prometheus metrics
- Docker Compose integration

**Estimated Total Tasks**: ~40-50 tasks for complete Phase 10 implementation

**Current Progress**: 10/~45 tasks complete (Foundation + Core Services)
