@echo off
setlocal
pushd "%~dp0"
chcp 65001 >nul

echo ==============================================
echo  Vocal Similarity Web UI Launcher
echo ==============================================

python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH. Please install Python 3.9+.
    goto :error_exit
)

if not exist "venv" (
    echo [*] First-time setup. Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 goto :error_exit
    call .\venv\Scripts\python.exe -m pip install --upgrade pip >nul
    call .\venv\Scripts\pip.exe install -r requirements.txt
    if %errorlevel% neq 0 goto :error_exit
)

echo [*] Installing web UI requirements...
call .\venv\Scripts\pip.exe install -q -r requirements-web.txt
if %errorlevel% neq 0 goto :error_exit

echo [*] Opening http://localhost:8000 ...
start "" "http://localhost:8000"
call .\venv\Scripts\python.exe web.py --port 8000
if %errorlevel% neq 0 goto :error_exit

popd
exit /b 0

:error_exit
echo [!] The script encountered an error. Please review the message above.
popd
pause
exit /b 1
