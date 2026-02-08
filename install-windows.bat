@echo off
REM ============================================================================
REM File Validator - Windows Auto-Installer
REM Downloads and installs File Validator automatically
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================================================
echo.
echo          File Validator - Windows Installation
echo          Auto-download and setup
echo.
echo ========================================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as Administrator!
    echo.
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Step 1: Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python installed: %PYTHON_VERSION%
echo.

REM Step 2: Download File Validator
echo [2/6] Downloading File Validator from GitHub...

REM Create temp directory
set TEMP_DIR=%TEMP%\file-validator-install
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM Download using PowerShell
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/AnasRm01/file-validator/main/file_validator_windows.py' -OutFile '%TEMP_DIR%\file_validator_windows.py'}" >nul 2>&1

if not exist "%TEMP_DIR%\file_validator_windows.py" (
    REM Try alternative download method
    echo [WARN] Primary download failed, trying alternative method...
    
    powershell -Command "& {(New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/AnasRm01/file-validator/main/file_validator_windows.py', '%TEMP_DIR%\file_validator_windows.py')}" >nul 2>&1
)

if not exist "%TEMP_DIR%\file_validator_windows.py" (
    echo [ERROR] Failed to download File Validator
    echo Please check your internet connection
    echo.
    pause
    exit /b 1
)

echo [OK] Downloaded successfully
echo.

REM Step 3: Install dependencies
echo [3/6] Installing Python dependencies...
pip install --quiet watchdog pyyaml pywin32 2>nul
if errorlevel 1 (
    echo [WARN] Some dependencies may have failed
    echo Trying without pywin32...
    pip install --quiet watchdog pyyaml 2>nul
)
echo [OK] Dependencies installed
echo.

REM Step 4: Install File Validator
echo [4/6] Installing File Validator...

REM Determine installation directory
set INSTALL_DIR=%USERPROFILE%\FileValidator
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy program
copy /Y "%TEMP_DIR%\file_validator_windows.py" "%INSTALL_DIR%\file-validator.py" >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy file
    pause
    exit /b 1
)

echo [OK] Installed to: %INSTALL_DIR%
echo.

REM Step 5: Create default config
echo [5/6] Creating configuration...

REM Create basic config file
(
echo monitoring:
echo   auto_detect_paths: true
echo   custom_paths:
echo     - C:\Temp
echo   excluded_paths:
echo     - C:\Windows
echo     - C:\Program Files
echo.
echo quarantine:
echo   enabled: true
echo   path: %USERPROFILE%\file-validator-quarantine
echo   keep_original: false
echo.
echo logging:
echo   log_file: %USERPROFILE%\file-validator.log
echo   log_level: INFO
echo   siem_format: true
echo   console_output: true
echo.
echo detection:
echo   calculate_hash: true
echo   get_file_owner: true
echo   max_file_size_mb: 100
) > "%USERPROFILE%\file-validator-config.yaml"

echo [OK] Configuration created
echo.

REM Step 6: Create startup script
echo [6/6] Creating startup script...

(
echo @echo off
echo python "%INSTALL_DIR%\file-validator.py"
) > "%INSTALL_DIR%\start-file-validator.bat"

echo [OK] Startup script created
echo.

REM Cleanup
rd /s /q "%TEMP_DIR%" 2>nul

REM Success message
echo ========================================================================
echo.
echo                  Installation Complete!
echo.
echo ========================================================================
echo.
echo Installation location: %INSTALL_DIR%
echo Configuration file:    %USERPROFILE%\file-validator-config.yaml
echo Log file:              %USERPROFILE%\file-validator.log
echo Quarantine folder:     %USERPROFILE%\file-validator-quarantine
echo.
echo ========================================================================
echo  Next Steps:
echo ========================================================================
echo.
echo 1. Start File Validator:
echo    %INSTALL_DIR%\start-file-validator.bat
echo.
echo 2. Test detection:
echo    echo %%PDF-1.4 fake ^> %%USERPROFILE%%\Downloads\test.jpg
echo.
echo 3. View logs:
echo    notepad %%USERPROFILE%%\file-validator.log
echo.
echo 4. Configure settings:
echo    notepad %%USERPROFILE%%\file-validator-config.yaml
echo.
echo ========================================================================
echo.
echo Press any key to start File Validator now...
pause >nul

REM Start File Validator
start "File Validator" cmd /k "%INSTALL_DIR%\start-file-validator.bat"

echo.
echo File Validator is now running in a new window!
echo.
pause