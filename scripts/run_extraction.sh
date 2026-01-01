#!/bin/bash
# Quick launcher for document extraction
# Runs in background, logs to /tmp/extraction.log

# Source API key from config
source ~/.config/api-keys/.env.api-keys

cd ~/Projects/CommandCenter

echo "Starting extraction at $(date)" > /tmp/extraction.log
/usr/bin/python3 scripts/extract_document_intelligence.py "$@" >> /tmp/extraction.log 2>&1
echo "Finished at $(date)" >> /tmp/extraction.log
echo "Results in docs/cleanup/extraction-results.yaml"
