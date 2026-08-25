@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo ChronoVision AI - One-Click Automated Setup for Windows
echo ========================================================
echo.

:: Navigate to repo root
cd /d "%~dp0\.."

:: 1. Check for Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo Please download and install Git from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)
echo [OK] Git is installed.

:: 2. Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not installed or not running!
    echo Please download Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo Once installed, open Docker Desktop and wait for the engine to start.
    echo.
    pause
    exit /b 1
)
echo [OK] Docker is installed.

:: 3. Setup Environment Variables
echo.
echo [1/3] Configuring environment (.env)...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [OK] Created .env from .env.example template.
    ) else (
        echo GEMINI_MODEL=gemini-3.5-flash-lite > .env
        echo QDRANT_COLLECTION=video_frames >> .env
        echo [OK] Created default .env file.
    )
) else (
    echo [OK] .env file already exists.
)

:: 4. Start Docker Containers
echo.
echo [2/3] Building and starting AI container cluster...
echo (Note: On the first run, downloading models and base images may take 5-10 minutes)
docker compose up -d --build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Docker compose failed to start. Please check the logs above.
    pause
    exit /b 1
)

:: 5. Success Banner
echo.
echo [3/3] Platform Launch Complete!
echo ========================================================
echo ChronoVision AI services are running:
echo.
echo   * Web Dashboard  : http://localhost:3001
echo   * FastAPI Docs   : http://localhost:8000/docs
echo   * Qdrant DB      : http://localhost:6333/dashboard
echo ========================================================
echo.
echo You can stop the stack at any time with: docker compose down
echo.
pause
