#!/bin/bash

# LIDA Service Startup Script

# Load environment variables
export OPENAI_API_KEY="${OPENAI_API_KEY}"

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "Set it with: export OPENAI_API_KEY=your-key"
fi

echo "🚀 Starting LIDA Service..."
echo "   Host: 0.0.0.0"
echo "   Port: 8080"
echo ""

# Run the server
python3 main.py

