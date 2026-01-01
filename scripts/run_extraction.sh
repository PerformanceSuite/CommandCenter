#!/bin/bash
# Run document intelligence extraction with API key from config

# Load API key from config
source ~/.config/api-keys/.env.api-keys

cd /Users/danielconnolly/Projects/CommandCenter

# Run extraction with any passed arguments
python3 scripts/extract_document_intelligence.py "$@"
