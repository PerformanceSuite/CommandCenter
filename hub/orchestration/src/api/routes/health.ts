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
