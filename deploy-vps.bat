@echo off
echo ========================================
echo  Shopee Video Generator - Deploy to VPS
echo ========================================
echo.

set VPS_IP=54.179.142.26
set VPS_USER=admin

echo [1/3] Creating deployment package...
tar -czf gen-video-deploy.tar.gz --exclude=__pycache__ --exclude=temp --exclude=output --exclude=uploads --exclude=.env --exclude=*.mp4 --exclude=*.mp3 .

echo [2/3] Uploading to VPS...
scp gen-video-deploy.tar.gz %VPS_USER%@%VPS_IP%:/tmp/

echo [3/3] Running setup on VPS...
ssh %VPS_USER%@%VPS_IP% "mkdir -p /opt/gen-video && cd /opt/gen-video && tar -xzf /tmp/gen-video-deploy.tar.gz && rm /tmp/gen-video-deploy.tar.gz && chmod +x vps-setup.sh"

echo.
echo ========================================
echo  Upload Complete!
echo ========================================
echo.
echo Now SSH into VPS and run:
echo.
echo   ssh %VPS_USER%@%VPS_IP%
echo   cd /opt/gen-video
echo   bash vps-setup.sh
echo.
echo Then edit .env and deploy:
echo   nano .env
echo   docker compose up -d --build
echo.

del gen-video-deploy.tar.gz
