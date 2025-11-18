import express from 'express';
import logger from '../utils/logger';
import config from '../config';
import healthRoutes from './routes/health';
import agentRoutes from './routes/agents';

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
  app.use('/api', agentRoutes);

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
