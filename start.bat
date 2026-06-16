@echo off
echo ========================================
echo  Shopee Video Generator - Quick Start
echo ========================================
echo.

echo [1/3] Checking shopo-api...
curl -s http://localhost:3000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo shopo-api already running on port 3000 - OK
) else (
    echo Starting shopo-api Docker container...
    docker run --rm -d -p 3000:3000 -e CORS_ORIGIN="*" -e ALLOWED_DOMAINS="shopee.co.id,id.shp.ee" --name shopo-api mboxjem/shopo-api:latest
    if %errorlevel% neq 0 (
        echo ERROR: Docker failed. Make sure Docker Desktop is running!
        pause
        exit /b 1
    )
    echo Waiting for shopo-api to be ready...
    timeout /t 5 /nobreak >nul
)

echo [2/3] Starting FastAPI backend...
echo Backend:  http://localhost:8000
echo Swagger: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo [3/3] Cleaning up...
docker stop shopo-api 2>nul
