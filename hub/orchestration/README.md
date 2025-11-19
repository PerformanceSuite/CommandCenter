# CommandCenter Agent Orchestration Service

Dagger-powered agent orchestration with TypeScript/Prisma.

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Required variables:
```env
DATABASE_URL=postgresql://commandcenter:password@localhost:5432/commandcenter
NATS_URL=nats://localhost:4222
PORT=9002
```

### 3. Run Database Migrations

```bash
npx prisma generate
npx prisma migrate deploy
```

### 4. Start Service

```bash
npm run dev
```

## Testing

### Running Tests

Tests require a PostgreSQL database. Set `DATABASE_URL` before running:

```bash
export DATABASE_URL="postgresql://commandcenter:password@localhost:5432/commandcenter_test"
npm test
```

### Test Database Setup

Create a test database:

```sql
CREATE DATABASE commandcenter_test;
```

Apply migrations:

```bash
DATABASE_URL="postgresql://commandcenter:password@localhost:5432/commandcenter_test" npx prisma migrate deploy
```

### CI/CD Testing

For automated testing, use docker-compose to spin up a test database:

```bash
docker-compose -f docker-compose.test.yml up -d postgres
npm test
```
