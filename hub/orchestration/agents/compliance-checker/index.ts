#!/usr/bin/env ts-node

import { ComplianceChecker } from './checker';
import { InputSchema, OutputSchema } from './schemas';

async function main() {
  try {
    // Read input from command line argument
    const inputJson = process.argv[2];
    if (!inputJson) {
      throw new Error('No input provided');
    }

    const input = JSON.parse(inputJson);

    // Validate input
    const validatedInput = InputSchema.parse(input);

    // Run checker
    const checker = new ComplianceChecker();
    const output = await checker.check(validatedInput);

    // Validate output
    const validatedOutput = OutputSchema.parse(output);

    // Print output to stdout (Dagger will capture this)
    console.log(JSON.stringify(validatedOutput));
    process.exit(output.summary.passed ? 0 : 1);
  } catch (error: any) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
  }
}

main();
