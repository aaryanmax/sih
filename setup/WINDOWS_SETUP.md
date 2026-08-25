# 🪟 Windows Setup Guide for Beginners

This guide is designed for Windows users of all technical levels to get **ChronoVision AI** up and running in minutes using our automated script or manual steps.

---

## 📋 Prerequisites (Software to Install)

You only need two programs to run the complete platform:

### 1. Git for Windows
- **Download Link**: [Download Git for Windows (64-bit)](https://git-scm.com/download/win)
- **Installation**: Run the downloaded installer. You can click **Next** on all prompts to accept default settings.

### 2. Docker Desktop
- **Download Link**: [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- **Installation**: Run the installer and ensure the **Use WSL 2 instead of Hyper-V** option is checked.
- **Restart**: Restart your computer when prompted by the installer.
- **Launch**: Open **Docker Desktop** from your Start menu and wait until the whale icon in the taskbar turns solid green (Engine running).

---

## 🚀 Option A: Automated 1-Click Setup (Recommended)

1. Open **Command Prompt** or **PowerShell** and clone the repository:
   ```cmd
   git clone https://github.com/aaryanmax/sih.git
   cd sih
   ```

2. Run the automated setup script:
   - Double-click `setup_windows.bat` in the root folder, or
   - Run `setup\setup_windows.bat` from your terminal.

3. The script will automatically:
   - Verify that Git and Docker are installed and running.
   - Generate your `.env` configuration file.
   - Build and start all containers (Qdrant, vLLM, FastAPI, Next.js).

---

## 🛠️ Option B: Manual Local Setup (Bare Metal / Python)

If you prefer running Python and Node directly on your host machine without Docker:

### 1. Install Runtimes
- **Python 3.14+**: [Download Python for Windows](https://www.python.org/downloads/) *(Ensure "Add python.exe to PATH" is checked during installation)*.
- **Node.js 24+**: [Download Node.js for Windows](https://nodejs.org/en/download/).

### 2. Setup Virtual Environment & Dependencies
```powershell
# Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
pip install -r apps/api/requirements.txt

# Install frontend dependencies
cd apps\web
npm install
cd ..\..
```

### 3. Start Backend & Frontend
```powershell
# In Terminal 1: Start FastAPI Backend
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

# In Terminal 2: Start Next.js Frontend
npm --prefix apps/web run dev
```

---

## 🔑 Configure API Keys (Gemini Explainability)

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Open the `.env` file in Notepad:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```
3. Save the file. The backend will automatically reload with Gemini explainability enabled.

---

## 🌐 Access the Application

- **Frontend Search Dashboard**: [http://localhost:3001](http://localhost:3001) (or `http://localhost:3000` for bare metal)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Qdrant Vector Database**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 🛑 How to Stop the App

When you're finished using ChronoVision:
```cmd
docker compose down
```
