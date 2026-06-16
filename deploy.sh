#!/bin/bash
echo "========================================"
echo "  Shopee Video Generator - VPS Deploy"
echo "========================================"
echo

if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and fill in your values:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo "[1/4] Pulling latest code..."
git pull

echo "[2/4] Building Docker images..."
docker compose build

echo "[3/4] Starting services..."
docker compose up -d

echo "[4/4] Checking services..."
sleep 5

echo
echo "Services:"
docker compose ps

echo
echo "========================================"
echo "  Deployment Complete!"
echo "========================================"
echo
echo "Backend:     http://localhost:8000"
echo "Swagger:     http://localhost:8000/docs"
echo "Shopo API:   http://localhost:3000/api/health"
echo
echo "Bot status:  docker compose logs telegram-bot"
echo "Backend:     docker compose logs backend"
echo
echo "Stop:        docker compose down"
echo "Restart:     docker compose restart"
echo "Logs:        docker compose logs -f"
