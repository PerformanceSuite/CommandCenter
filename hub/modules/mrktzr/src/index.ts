import express from 'express';
import { createLogger, format, transports } from 'winston';
import authRouter from './api/auth';
import contentRouter from './api/content';

// Logger configuration (CommandCenter pattern)
const logger = createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: format.combine(
    format.timestamp(),
    format.errors({ stack: true }),
    format.json()
  ),
  defaultMeta: { service: 'mrktzr' },
  transports: [
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.simple()
      )
    })
  ]
});

const app = express();
const port = parseInt(process.env.MRKTZR_PORT || '3003', 10);

// Middleware
app.use(express.json({ limit: '10mb' }));

// Health check endpoint (CommandCenter pattern)
app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    service: 'mrktzr',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// API routes
app.use('/api/auth', authRouter);
app.use('/api/content', contentRouter);

// Error handler
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  logger.error('Unhandled error', { error: err.message, stack: err.stack });
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(port, () => {
  logger.info(`MRKTZR service running on http://localhost:${port}`);
  logger.info('Health check available at /health');
});

export { app, logger };
