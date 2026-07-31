@echo off
chcp 65001 >nul
echo ==============================================
echo  Vocal Similarity Pipeline Launcher
echo ==============================================

REM Check for python
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH. Please install Python 3.11+.
    pause
    exit /b 1
)


if not exist "venv" (
    echo [*] First-time setup. Creating virtual environment (venv)...
    python -m venv venv
    
    echo [*] Installing required libraries (this may take some time as PyTorch is large)...
    echo [*] Upgrading pip...
    .\venv\Scripts\python.exe -m pip install --upgrade pip >nul
    
    echo [*] Installing production requirements...
    .\venv\Scripts\pip.exe install -r requirements.txt
    
    if exist "requirements-dev.txt" (
        echo [*] Installing development requirements...
        .\venv\Scripts\pip.exe install -r requirements-dev.txt
    )

) else (
    echo [*] Virtual environment found. Activating...
)

echo.
echo ==============================================
echo [*] Starting the pipeline (main.py)...
echo ==============================================
.\venv\Scripts\python.exe main.py

echo.
echo ==============================================
echo [*] Pipeline finished.
echo ==============================================
pause
