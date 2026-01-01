#!/usr/bin/env ts-node

import { Patcher } from './patcher';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    // Read input from environment variable (preferred) or command line argument (fallback)
    const inputJson = process.env.AGENT_INPUT || process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided. Set AGENT_INPUT env var or pass as CLI argument.');
    }

    const input = JSON.parse(inputJson);

    // Validate input
    const validatedInput = InputSchema.parse(input);

    // Run patcher
    const patcher = new Patcher();
    const output = await patcher.patch(validatedInput);

    // Validate output
    const validatedOutput = OutputSchema.parse(output);

    // Print output to stdout (Dagger will capture this)
    console.log(JSON.stringify(validatedOutput));
    process.exit(0);
  } catch (error: any) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
