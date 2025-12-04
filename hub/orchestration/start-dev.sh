#!/bin/bash
# Load environment variables
export $(cat .env | grep -v '^#' | xargs)
# Start the service
exec npx tsx watch src/index.ts
