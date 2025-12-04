#!/usr/bin/env ts-node

import { CodeReviewer } from './reviewer';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    const inputJson = process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided');
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
