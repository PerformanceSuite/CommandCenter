import { Router } from 'express';
import { runFlow } from 'genkit';
import { postGeneratorFlow } from '../core/contentGenerator';

const router = Router();

router.post('/generate-post', async (req, res) => {
  const { topic } = req.body;

  if (!topic) {
    return res.status(400).send('Topic is required');
  }

  try {
    const generatedPost = await runFlow(postGeneratorFlow, { topic });
    res.json({ post: generatedPost });
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to generate post');
  }
});

export default router;
