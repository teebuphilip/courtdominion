#!/bin/bash
# CourtDominion Quick Start Script
# Sets up and runs backend + automation in Docker

set -e

echo "🏀 CourtDominion Docker Setup"
echo "=============================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if .env exists, create from example if not
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created (using default values)"
else
    echo "✅ .env already exists"
fi
echo ""

# Build services
echo "🔨 Building services..."
docker compose build --quiet
echo "✅ Services built"
echo ""

# Start backend and database
echo "🚀 Starting backend and database..."
docker compose up -d backend db
echo "✅ Services started"
echo ""

# Wait for backend to be healthy
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        echo "Check logs: docker compose logs backend"
        exit 1
    fi
    
    sleep 1
done
echo ""

# Run automation
echo "🤖 Running automation pipeline..."
docker compose run --rm automation
echo "✅ Automation completed"
echo ""

# Verify data generated
echo "📊 Verifying data..."
FILES=$(docker compose exec -T backend ls /data/outputs 2>/dev/null | wc -l)
if [ "$FILES" -gt 0 ]; then
    echo "✅ Data files generated: $FILES files"
else
    echo "⚠️  No data files found"
fi
echo ""

# Test endpoints
echo "🧪 Testing endpoints..."

# Health
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "  ✅ /health"
else
    echo "  ❌ /health"
fi

# Players
PLAYERS=$(curl -s http://localhost:8000/players | jq length 2>/dev/null || echo "0")
if [ "$PLAYERS" -gt 0 ]; then
    echo "  ✅ /players ($PLAYERS players)"
else
    echo "  ⚠️  /players (no data)"
fi

# Projections
PROJECTIONS=$(curl -s http://localhost:8000/projections | jq length 2>/dev/null || echo "0")
if [ "$PROJECTIONS" -gt 0 ]; then
    echo "  ✅ /projections ($PROJECTIONS projections)"
else
    echo "  ⚠️  /projections (no data)"
fi

echo ""
echo "=============================="
echo "🎉 Setup Complete!"
echo "=============================="
echo ""
echo "📍 Backend running at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs:        docker compose logs -f"
echo "  Stop services:    docker compose down"
echo "  Run automation:   docker compose run --rm automation"
echo "  Restart:          docker compose restart backend"
echo ""
