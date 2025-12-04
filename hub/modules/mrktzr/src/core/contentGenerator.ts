import { defineFlow, generate } from 'genkit';
import { googleGenai } from '@genkit-ai/google-genai';
import { z } from 'zod';

// Input validation schema with constraints to mitigate prompt injection
const topicSchema = z.object({
  topic: z
    .string()
    .min(1, 'Topic is required')
    .max(500, 'Topic must be under 500 characters')
    .refine(
      (val) => !val.includes('ignore previous') && !val.includes('system:'),
      'Invalid topic content'
    ),
});

export const postGeneratorFlow = defineFlow(
  {
    name: 'postGeneratorFlow',
    inputSchema: topicSchema,
    outputSchema: z.string(),
  },
  async ({ topic }) => {
    // Sanitize topic: escape special characters, limit length
    const sanitizedTopic = topic
      .replace(/[<>]/g, '') // Remove potential HTML/XML
      .slice(0, 200); // Enforce reasonable length for prompt

    const llmResponse = await generate({
      model: googleGenai('gemini-pro'),
      prompt: `You are a social media content assistant. Generate a short, engaging social media post about the following topic. Only generate content appropriate for professional social media.

Topic: "${sanitizedTopic}"

Generate a concise post (under 280 characters):`,
      output: {
        format: 'text',
      },
    });

    return llmResponse.text();
  }
);
