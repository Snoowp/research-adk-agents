#!/bin/bash

# Test health endpoint
echo "Testing health endpoint..."
curl http://localhost:8000/health
echo -e "\n"

# Test research with a simple query
echo "Testing research endpoint with a simple query..."
curl -N -X POST http://localhost:8000/api/adk-research-stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the latest developments in quantum computing?",
    "effort_level": "low",
    "reasoning_model": "gemini-2.0-flash-thinking-exp"
  }'