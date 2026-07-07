@echo off
title J.A.R.V.I.S. 2.0 - Core Mainframe Setup Wizard
echo =======================================================
echo          PROJECT J.A.R.V.I.S. 2.0 SETUP WIZARD         
echo =======================================================
echo.

:: 1. Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌ ERROR]: Python is not installed or not added to your system PATH.
    echo Please install Python 3.10 or newer from python.org and try again.
    pause
    exit /b
)

echo [✓] Python detected successfully.

:: 2. Create Virtual Environment if it doesn't exist
if not exist ".venv" (
    echo [⚙️] Creating Python Virtual Environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [❌ ERROR]: Failed to create virtual environment.
        pause
        exit /b
    )
    echo [✓] Virtual environment created.
) else (
    echo [✓] Virtual environment (.venv) already exists.
)

:: 3. Upgrade Pip and Install dependencies
echo [⚙️] Upgrading package manager (pip)...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul

if exist "requirements.txt" (
    echo [⚙️] Installing required neural and system dependencies...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [❌ ERROR]: Dependency installation failed.
        pause
        exit /b
    )
    echo [✓] All dependencies installed successfully.
) else (
    echo [⚠️ WARNING]: requirements.txt not found. Skipping dependency install.
)

:: 4. Setup Environment Variables (.env)
if not exist ".env" (
    echo.
    echo =======================================================
    echo          NEURAL CORE CONFIGURATION (API KEY)
    echo =======================================================
    echo To allow J.A.R.V.I.S. to connect to the Gemini Neural Network,
    echo please enter your Gemini API Key.
    echo.
    set /p API_KEY="Enter Gemini API Key: "
    
    echo GEMINI_API_KEY=%API_KEY%> .env
    echo JARVIS_CITY=Guntur>> .env
    echo [✓] Secure .env configuration created.
) else (
    echo [✓] Configuration file (.env) already exists.
)

echo.
echo =======================================================
echo         J.A.R.V.I.S. 2.0 INITIALIZATION COMPLETE       
echo =======================================================
echo.
echo You can now launch the command center by double-clicking:
echo   - run_jarvis.bat
echo.
pause
