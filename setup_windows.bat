@echo off
echo ========================================================
echo ChronoVision AI - One-Click Setup for Windows
echo ========================================================
echo.

:: Check for Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo Please download and install Git from: https://git-scm.com/download/win
    pause
    exit /b
)

:: Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not installed or not running!
    echo Please download Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo Install it, start it from your Start Menu, and run this script again.
    pause
    exit /b
)

:: Setup Environment Variables
echo [1/3] Setting up environment variables...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo Created .env file. Please edit it later to add your API keys.
    ) else (
        echo Creating a blank .env file...
        echo GEMINI_API_KEY=your_key_here > .env
    )
) else (
    echo .env file already exists.
)

:: Start Docker Containers
echo.
echo [2/3] Downloading and starting AI services...
echo (Note: This may take 10-15 minutes on the very first run as it downloads the AI models)
docker compose up -d

echo.
echo [3/3] Setup Complete!
echo ========================================================
echo ChronoVision AI is now starting in the background.
echo.
echo Please wait 1-2 minutes for the servers to fully boot up, then open your browser:
echo.
echo Frontend Dashboard : http://localhost:3001
echo FastAPI Backend    : http://localhost:8000/docs
echo Qdrant Database    : http://localhost:6333/dashboard
echo ========================================================
echo.
pause
