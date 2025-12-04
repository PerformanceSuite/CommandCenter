import { defineFlow, generate } from 'genkit';
import { googleGenai } from '@genkit-ai/google-genai';
import { z } from 'zod';

export const postGeneratorFlow = defineFlow(
  {
    name: 'postGeneratorFlow',
    inputSchema: z.object({ topic: z.string() }),
    outputSchema: z.string(),
  },
  async ({ topic }) => {
    const llmResponse = await generate({
      model: googleGenai('gemini-pro'),
      prompt: `Generate a short, engaging social media post about: ${topic}`,
      output: {
        format: 'text',
      },
    });

    return llmResponse.text();
  }
);
