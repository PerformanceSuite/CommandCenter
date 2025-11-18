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
