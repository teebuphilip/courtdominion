#!/bin/bash

# CourtDominion Quick Start Script

echo "========================================"
echo "CourtDominion Desktop Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Creating .env from template..."
    cp .env.template .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo ""
    echo "Run this command to edit:"
    echo "  nano .env"
    echo ""
    read -p "Press Enter once you've added your API key..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if OPENAI_API_KEY is set in .env
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OPENAI_API_KEY not found in .env"
    echo ""
    echo "Please edit .env and add your OpenAI API key:"
    echo "  nano .env"
    echo ""
    exit 1
fi

echo "✅ OpenAI API key found in .env"
echo ""

# Build and start services
echo "🚀 Building and starting services..."
echo ""

docker-compose up --build

# Note: Script will run until user presses Ctrl+C
