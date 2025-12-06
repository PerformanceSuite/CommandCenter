import { Router, Request, Response } from 'express';
import { runFlow } from 'genkit';
import { postGeneratorFlow } from '../core/contentGenerator';
import { logger } from '../index';

const router = Router();

interface GeneratePostRequest {
  topic: string;
}

router.post('/generate-post', async (req: Request<{}, {}, GeneratePostRequest>, res: Response) => {
  const { topic } = req.body;

  if (!topic || typeof topic !== 'string') {
    return res.status(400).json({ error: 'Topic is required and must be a string' });
  }

  try {
    const generatedPost = await runFlow(postGeneratorFlow, { topic });
    res.json({ post: generatedPost });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Failed to generate post', { error: errorMessage, topic: topic.slice(0, 50) });
    res.status(500).json({ error: 'Failed to generate post' });
  }
});

export default router;
