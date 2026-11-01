@echo off
setlocal
pushd "%~dp0" || exit /b 1
chcp 65001 >nul

echo ==============================================
echo  Vocal Similarity Web UI Launcher
echo ==============================================

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python is not installed or not in PATH. Please install Python 3.11+.
    goto :error_exit
)

where node >nul 2>nul
if errorlevel 1 (
    echo [!] Node.js 22+ is required for YouTube extraction. Install Node.js and add it to PATH.
    goto :error_exit
)

if not exist "venv\Scripts\python.exe" (
    echo [*] First-time setup. Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :error_exit

    call ".\venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :error_exit

    call ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error_exit
)

echo [*] Installing web UI requirements...
call ".\venv\Scripts\python.exe" -m pip install -q -r requirements-web.txt
if errorlevel 1 goto :error_exit

echo [*] Updating YouTube downloader and JavaScript challenge support...
call ".\venv\Scripts\python.exe" -m pip install -q "yt-dlp[default]>=2026.10.26"
if errorlevel 1 goto :error_exit

echo [*] Checking the web server...
curl.exe --fail --silent --max-time 2 http://127.0.0.1:8000/api/health >nul 2>nul
if not errorlevel 1 goto :server_ready

echo [*] Starting the web server...
start "" /min "%CD%\venv\Scripts\python.exe" "%CD%\web.py" --port 8000

echo [*] Waiting for the web server to become ready...
set /a WAIT_COUNT=0

:wait_for_server
curl.exe --fail --silent --max-time 1 http://127.0.0.1:8000/api/health >nul 2>nul
if not errorlevel 1 goto :server_ready
set /a WAIT_COUNT+=1
if %WAIT_COUNT% geq 60 goto :server_timeout
ping -n 2 127.0.0.1 >nul
goto :wait_for_server

:server_timeout
echo [!] The web server did not become ready within 60 seconds.
goto :error_exit

:server_ready
echo [*] Opening http://localhost:8000 ...
start "" "http://localhost:8000"

popd
exit /b 0

:error_exit
echo [!] The script encountered an error. Please review the message above.
popd
pause
exit /b 1
