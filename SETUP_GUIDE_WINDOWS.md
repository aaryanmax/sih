# ChronoVision AI - Windows Setup Guide for Beginners

Welcome to ChronoVision AI! This guide is designed for users with little to no technical background. We have provided an automated script to make the process as easy as possible.

## Step 1: Install Required Software

You only need two programs to run this entire AI platform on your Windows machine:

1. **Git** (Downloads the code)
   - **Download Link**: [Click here to download Git for Windows](https://git-scm.com/download/win) (Download the "64-bit Git for Windows Setup").
   - **Installation**: Run the downloaded file and keep clicking "Next" to accept all default settings until it finishes.

2. **Docker Desktop** (Runs the AI in isolated containers)
   - **Download Link**: [Click here to download Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - **Installation**: Run the installer and accept the defaults. **Important**: After installation, your computer may need to restart.
   - **Post-Install**: Open the "Docker Desktop" app from your Start Menu. Leave it running in the background (you should see a whale icon in your taskbar).

## Step 2: Download ChronoVision AI

1. Open your Windows Start Menu, search for **Command Prompt**, and open it.
2. Type the following command and press **Enter**:
   ```cmd
   git clone https://github.com/aaryanmax/sih.git
   ```
3. Type the following command to go into the downloaded folder:
   ```cmd
   cd sih
   ```

## Step 3: Run the One-Click Setup Script

We have created an automated script that configures everything for you!

1. Open the `sih` folder in your File Explorer (it is usually located at `C:\Users\YourName\sih`).
2. Double-click the file named **`setup_windows.bat`**.
3. A black window will appear and automatically:
   - Check if you installed Git and Docker correctly.
   - Set up your configuration files.
   - Download the AI models and start the servers (This will take 10-15 minutes the very first time).

## Step 4: Add Your AI API Keys (Optional but Recommended)

For the AI to explain search results, it needs a Gemini AI Key:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create a free API Key.
2. In your `sih` folder, find the file named `.env` (it might just look like a blank file called `env`). Right-click it and open it with **Notepad**.
3. Find the line that says `GEMINI_API_KEY=` and paste your key after the equals sign. Save the file.

## Step 5: Start Using the App!

Once the script finishes, you can open your web browser and go to:
- **ChronoVision Dashboard**: [http://localhost:3001](http://localhost:3001)

### Stopping the App
When you are done using the app, you can stop it from running in the background to save computer memory:
1. Open **Command Prompt**.
2. Type `cd sih`
3. Type `docker compose down`

---

### Troubleshooting Walkthrough
- **Error: "Docker Desktop is not running"**: Make sure you opened the Docker Desktop app from your Start menu and waited for the green "Engine Running" icon.
- **Error: "Port is already allocated"**: You might have another program using port 3001, 8000, or 6333. Restart your computer and try running the script again.
