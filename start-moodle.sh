#!/bin/bash
set -e

echo "🚀 Starting Moodle Docker Environment"
echo "===================================="

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

# Create .env if needed
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Start containers
echo "🐳 Starting containers..."
docker compose up -d

# Wait for Moodle
echo "⏳ Waiting for Moodle to start..."
for i in {1..30}; do
    if docker exec moodle-app curl -sf http://localhost:80 > /dev/null 2>&1; then
        echo ""
        echo "✅ Moodle is ready!"
        echo ""
        echo "📍 http://localhost:8080"
        echo "🔐 admin / Admin123!"
        echo ""
        echo "📖 See DOCKER.md for Web Services setup"
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "⚠️  Moodle is taking longer than expected"
echo "Check logs: docker logs moodle-app -f"
exit 1
