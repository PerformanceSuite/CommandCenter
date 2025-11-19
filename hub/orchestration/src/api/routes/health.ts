import { Router } from 'express';
import prisma from '../../db/prisma';
import { natsClient } from '../../events/nats-client';
import logger from '../../utils/logger';

const router = Router();

async function checkDatabase(): Promise<boolean> {
  try {
    await prisma.$queryRaw`SELECT 1`;
    return true;
  } catch (error) {
    logger.error('Database health check failed', { error });
    return false;
  }
}

async function checkNATS(): Promise<boolean> {
  try {
    return natsClient.isConnected();
  } catch (error) {
    logger.error('NATS health check failed', { error });
    return false;
  }
}

router.get('/health', async (req, res) => {
  try {
    const checks = {
      database: await checkDatabase(),
      nats: await checkNATS(),
      timestamp: new Date().toISOString(),
    };

    const healthy = checks.database && checks.nats;
    res.status(healthy ? 200 : 503).json({
      status: healthy ? 'ok' : 'degraded',
      service: 'orchestration',
      ...checks,
    });
  } catch (error: any) {
    logger.error('Health check failed', { error });
    res.status(503).json({
      status: 'error',
      error: 'Health check failed',
      message: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

export default router;
