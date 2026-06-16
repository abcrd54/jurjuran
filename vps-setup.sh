#!/bin/bash
set -e

echo "========================================"
echo "  Shopee Video Generator - VPS Setup"
echo "========================================"

echo "[1/6] Updating system..."
apt-get update -y
apt-get upgrade -y

echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
fi

echo "[3/6] Installing Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi

echo "[4/6] Installing git..."
apt-get install -y git curl

echo "[5/6] Cloning project..."
cd /opt
if [ -d "gen-video" ]; then
    cd gen-video
    git pull
else
    git clone https://github.com/YOUR_USERNAME/gen-video.git
    cd gen-video
fi

echo "[6/6] Setup complete!"
echo
echo "========================================"
echo "  Next Steps:"
echo "========================================"
echo
echo "1. Edit .env file:"
echo "   nano /opt/gen-video/.env"
echo
echo "2. Fill in:"
echo "   - TELEGRAM_BOT_TOKEN (from @BotFather)"
echo "   - AI_BASE_URL (Tailscale IP of AI service)"
echo "   - AI_API_KEY"
echo
echo "3. Deploy:"
echo "   cd /opt/gen-video"
echo "   docker compose up -d --build"
echo
echo "4. Check status:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo
