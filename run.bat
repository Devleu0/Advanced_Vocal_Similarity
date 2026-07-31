@echo off
chcp 65001 >nul
echo ==============================================
echo  Vocal Similarity Pipeline Launcher
echo ==============================================

if not exist "venv" (
    echo [*] 최초 실행을 감지했습니다. 가상환경(venv)을 생성합니다...
    python -m venv venv
    call venv\Scripts\activate
    
    echo [*] 필수 라이브러리를 설치합니다 (PyTorch 등 용량이 커 다소 시간이 소요됩니다)...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo [*] 기존 가상환경을 활성화합니다...
    call venv\Scripts\activate
)

echo [*] 파이프라인(main.py) 구동을 시작합니다...
echo ==============================================
python main.py

echo.
pause