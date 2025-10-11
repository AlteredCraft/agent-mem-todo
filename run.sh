#!/bin/bash
# Quick start script for Agent Memory Todo App

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo ""
    echo "Please create .env file from template:"
    echo "  cp dist.env .env"
    echo ""
    echo "Then edit .env and add your Anthropic API key"
    echo "Get your key at: https://console.anthropic.com/"
    exit 1
fi

# Run the todo agent (python-dotenv will load .env)
uv run python todo_agent.py
