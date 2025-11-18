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
