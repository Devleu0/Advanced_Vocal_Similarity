@echo off
setlocal
chcp 65001 >nul

echo ==============================================
echo  Vocal Similarity Pipeline Launcher
echo ==============================================

REM Check for python
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH. Please install Python 3.11+.
    goto :error_exit
)

if exist "venv" goto :run_main

:setup_env
echo [*] First-time setup. Creating virtual environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo [!] Failed to create virtual environment.
    goto :error_exit
)

echo [*] Installing required libraries...
echo [*] Upgrading pip...
call .\venv\Scripts\python.exe -m pip install --upgrade pip >nul

echo [*] Installing production requirements...
call .\venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] An error occurred during 'pip install -r requirements.txt'.
    goto :error_exit
)

if exist "requirements-dev.txt" (
    echo [*] Installing development requirements...
    call .\venv\Scripts\pip.exe install -r requirements-dev.txt
    if %errorlevel% neq 0 (
        echo [!] An error occurred during 'pip install -r requirements-dev.txt'.
        goto :error_exit
    )
)
goto :run_main

:run_main
echo.
echo ==============================================
echo [*] Starting the pipeline (main.py)...
echo ==============================================
call .\venv\Scripts\python main.py
if %errorlevel% neq 0 (
    echo [!] An error occurred while running 'python main.py'.
    goto :error_exit
)

echo.
echo ==============================================
echo [*] Pipeline finished successfully.
echo ==============================================
pause
exit /b 0

:error_exit
echo [!] The script encountered an error. Please review the message above.
pause
exit /b 1
