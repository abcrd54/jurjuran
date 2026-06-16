# Shopee Video Generator

Generate promotional videos from Shopee product links automatically.

## Features

- 🎬 Auto-generate video from Shopee URL
- 🎤 AI dubbing (Indonesian voice)
- 📝 Auto captions (synced to voice)
- 🎵 Background music
- 📱 Multiple aspect ratios (9:16, 1:1, 16:9)
- 🎨 Video templates (promo, review, unboxing, minimal)
- 🤖 Telegram bot

## Quick Start (Local)

```bash
cp .env.example .env
# Edit .env with your settings

pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal:
python start.py
```

## VPS Deployment

### 1. Upload to VPS

```bash
# Windows
deploy-vps.bat

# Or manually:
scp -r . admin@54.179.142.26:/opt/gen-video/
```

### 2. Setup VPS

```bash
ssh admin@54.179.142.26
cd /opt/gen-video
bash vps-setup.sh
```

### 3. Configure

```bash
nano .env
```

Fill in:
- `TELEGRAM_BOT_TOKEN` - Get from @BotFather
- `AI_BASE_URL` - Tailscale IP of AI service
- `AI_API_KEY` - Your AI API key

### 4. Deploy

```bash
docker compose up -d --build
```

### 5. Check Status

```bash
docker compose ps
docker compose logs -f telegram-bot
docker compose logs -f backend
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/generate` | Generate video |
| GET | `/api/progress/{id}` | Check progress |
| POST | `/api/batch` | Batch generate |
| GET | `/api/templates` | List templates |
| GET | `/api/aspect-ratios` | List aspect ratios |
| GET | `/api/voices` | List TTS voices |
| GET | `/api/health` | Health check |
| GET | `/docs` | Swagger UI |

## Telegram Bot Commands

- `/start` - Main menu
- `/help` - Help
- `/status` - Check status
- `/cancel` - Cancel process

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SCRAPER_URL` | Shopee scraper API URL |
| `AI_BASE_URL` | AI service URL |
| `AI_MODEL` | AI model name |
| `AI_API_KEY` | AI API key |
| `TTS_VOICE` | TTS voice (id-ID-ArdiNeural/id-ID-GadisNeural) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `BACKEND_URL` | Backend URL for bot |
