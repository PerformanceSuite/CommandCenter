#!/usr/bin/env ts-node

import { CodeReviewer } from './reviewer';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    // Read input from environment variable (preferred) or command line argument (fallback)
    const inputJson = process.env.AGENT_INPUT || process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided. Set AGENT_INPUT env var or pass as CLI argument.');
    }

    const input = JSON.parse(inputJson);
    const validatedInput = InputSchema.parse(input);

    const reviewer = new CodeReviewer();
    const output = await reviewer.review(validatedInput);

    const validatedOutput = OutputSchema.parse(output);

    console.log(JSON.stringify(validatedOutput));
    process.exit(0);
  } catch (error: any) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
