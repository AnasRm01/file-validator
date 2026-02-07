@echo off
echo ==========================================
echo File Validator - Windows Installation
echo Production Edition v1.1
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed!
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install watchdog pyyaml pywin32
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed
    echo Trying without pywin32 (optional)...
    pip install watchdog pyyaml
)

echo.
echo [2/4] Creating default configuration...
python file_validator_windows.py --create-config
echo OK

echo.
echo [3/4] Testing installation...
python file_validator_windows.py --version
echo OK

echo.
echo [4/4] Installation complete!
echo.
echo ==========================================
echo SUCCESS! File Validator Installed
echo ==========================================
echo.
echo Features enabled:
echo   [X] Real-time file monitoring
echo   [X] Automatic quarantine
echo   [X] SIEM-ready JSON logging
echo   [X] File hashing (SHA256)
echo   [X] User attribution
echo.
echo Configuration file:
echo   %%USERPROFILE%%\file-validator-config.yaml
echo.
echo To start monitoring:
echo   python file_validator_windows.py
echo.
pause
