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
