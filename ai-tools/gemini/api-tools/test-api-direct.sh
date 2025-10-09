#!/bin/bash

# Direct test of Gemini API using curl
API_KEY="AIzaSyBL1RerykYca17CcHLrmvjxVc0HRAyUm6A"

echo "🔍 Testing Gemini API key directly..."
echo "API Key: ${API_KEY:0:10}..."

# Test the API with a simple request
response=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Say hello in exactly 3 words"
      }]
    }]
  }')

# Check if response contains an error
if echo "$response" | grep -q '"error"'; then
  echo "❌ API Error:"
  echo "$response" | grep -o '"message":"[^"]*"' | sed 's/"message":"//;s/"$//'
else
  # Extract the text from the response
  text=$(echo "$response" | grep -o '"text":"[^"]*"' | head -1 | sed 's/"text":"//;s/"$//')
  if [ -n "$text" ]; then
    echo "✅ API Key is working!"
    echo "🎉 Gemini says: $text"
  else
    echo "❌ Unexpected response format"
    echo "$response"
  fi
fi
