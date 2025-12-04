import express from 'express';
import rateLimit from 'express-rate-limit';
import logger from '../utils/logger';
import config from '../config';
import healthRoutes from './routes/health';
import agentRoutes from './routes/agents';
import workflowRoutes from './routes/workflows';
import approvalRoutes from './routes/approvals';
import webhookRoutes from './routes/webhooks';

export function createServer() {
  const app = express();

  // Middleware
  app.use(express.json({ limit: '10mb' }));

  // Rate limiting - 100 requests per minute per IP
  const limiter = rateLimit({
    windowMs: 1 * 60 * 1000, // 1 minute
    max: 100, // Max 100 requests per window
    standardHeaders: true, // Return rate limit info in headers
    legacyHeaders: false,
    message: { error: 'Too many requests, please try again later' },
  });

  app.use('/api', limiter);

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
  app.use('/api', agentRoutes);
  app.use('/api', workflowRoutes);
  app.use('/api', approvalRoutes);
  app.use('/api/webhooks', webhookRoutes);

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
