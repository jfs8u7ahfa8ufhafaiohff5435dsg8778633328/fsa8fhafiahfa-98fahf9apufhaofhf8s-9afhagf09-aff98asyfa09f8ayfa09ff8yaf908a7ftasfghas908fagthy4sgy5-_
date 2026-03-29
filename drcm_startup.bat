@echo off
title DRCM Setup
echo ========================================
echo         DRCM - Roblox Manager
echo ========================================
echo.
echo         Created by: Dev_Z / ipad_halobuck
echo.
echo ========================================
echo.

:: Set paths
set "DRCM_DIR=%USERPROFILE%\Downloads\Drcm"
set "DRCM_SCRIPT=%DRCM_DIR%\drcm.py"
set "VERSION_FILE=%DRCM_DIR%\version.txt"

:: GitHub API URL (no caching)
set "GITHUB_API_URL=https://api.github.com/repos/jfs8u7ahfa8ufhafaiohff5435dsg8778633328/fsa8fhafiahfa-98fahf9apufhaofhf8s-9afhagf09-aff98asyfa09f8ayfa09ff8yaf908a7ftasfghas908fagthy4sgy5-_/contents/version.txt"
set "GITHUB_RAW_BASE=https://raw.githubusercontent.com/jfs8u7ahfa8ufhafaiohff5435dsg8778633328/fsa8fhafiahfa-98fahf9apufhaofhf8s-9afhagf09-aff98asyfa09f8ayfa09ff8yaf908a7ftasfghas908fagthy4sgy5-_/refs/heads/main"
set "GITHUB_SCRIPT_URL=%GITHUB_RAW_BASE%/drcm.py"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [1/5] Python is not installed...
    echo.
    echo Downloading Python 3.14...
    echo.
    
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.14.0/python-3.14.0-amd64.exe' -OutFile '%temp%\python_installer.exe'"
    
    echo Installing Python 3.14...
    echo Please follow the installer prompts.
    echo IMPORTANT: Make sure to check "Add Python to PATH"
    echo.
    start /wait %temp%\python_installer.exe
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python installation failed!
        pause
        exit /b 1
    )
    echo Python installed successfully!
) else (
    echo [1/5] Python is ready
)

for /f "tokens=2" %%I in ('python --version 2^>^&1') do set pyver=%%I
echo        Version: %pyver%
echo.

:: Create directory if it doesn't exist
if not exist "%DRCM_DIR%" (
    echo [2/5] Creating DRCM folder...
    mkdir "%DRCM_DIR%"
) else (
    echo [2/5] DRCM folder ready
)
echo.

:: Get remote version using GitHub API (no cache)
echo [3/5] Checking for updates...
echo.

:: Use PowerShell to get version from GitHub API
powershell -Command "$url = '%GITHUB_API_URL%'; try { $response = Invoke-WebRequest -Uri $url -UseBasicParsing; $content = ($response.Content | ConvertFrom-Json).content; $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($content)); $decoded.Trim() } catch { '0' }" > "%temp%\remote_version.txt" 2>nul

set REMOTE_VERSION=
if exist "%temp%\remote_version.txt" (
    set /p REMOTE_VERSION=<"%temp%\remote_version.txt"
)

:: If remote version is empty, use default
if "%REMOTE_VERSION%"=="" set "REMOTE_VERSION=1.0.2"

echo        Remote version: %REMOTE_VERSION%

:: Check local version
set LOCAL_VERSION=
if exist "%VERSION_FILE%" (
    set /p LOCAL_VERSION=<"%VERSION_FILE%"
    echo        Local version: %LOCAL_VERSION%
) else (
    echo        No local version found
)

echo.

:: ALWAYS REMOVE OLD SCRIPT AND REINSTALL
echo        Removing old version...
if exist "%DRCM_SCRIPT%" (
    del /f /q "%DRCM_SCRIPT%"
    echo        Old script removed.
) else (
    echo        No existing script found.
)

echo.
echo        Downloading latest version %REMOTE_VERSION%...
powershell -Command "try { Invoke-WebRequest -Uri '%GITHUB_SCRIPT_URL%' -OutFile '%DRCM_SCRIPT%' -UseBasicParsing -ErrorAction Stop } catch { exit 1 }" >nul 2>&1

if exist "%DRCM_SCRIPT%" (
    echo %REMOTE_VERSION% > "%VERSION_FILE%"
    echo        Download successful! Version %REMOTE_VERSION% installed.
) else (
    echo        Download failed! Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo [4/5] Installing required packages...
echo.

:: Install packages (quiet mode)
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo        Installing PySide6...
    python -m pip install PySide6 -q 2>nul
) else (
    echo        PySide6 ready
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo        Installing requests...
    python -m pip install requests -q 2>nul
) else (
    echo        Requests ready
)

python -c "import wmi" >nul 2>&1
if errorlevel 1 (
    echo        Installing wmi...
    python -m pip install wmi -q 2>nul
) else (
    echo        WMI ready
)

python -c "import win32api" >nul 2>&1
if errorlevel 1 (
    echo        Installing pywin32...
    python -m pip install pywin32 -q 2>nul
) else (
    echo        pywin32 ready
)

echo.
echo [5/5] Preparing folders...
echo.

:: Create necessary folders
mkdir "%DRCM_DIR%\RbxV" 2>nul
mkdir "%DRCM_DIR%\dt\dt" 2>nul
mkdir "%DRCM_DIR%\nt\nt" 2>nul
mkdir "%DRCM_DIR%\ct" 2>nul
mkdir "%DRCM_DIR%\Settings" 2>nul
mkdir "%DRCM_DIR%\Sounds" 2>nul

echo        All folders ready.
echo.
echo ========================================
echo    Setup Complete!
echo ========================================
echo.

:: Display current version
if exist "%VERSION_FILE%" (
    set /p CURRENT_VERSION=<"%VERSION_FILE%"
    echo DRCM Version: %CURRENT_VERSION%
) else (
    echo DRCM Version: 1.0.2
)
echo.
echo Starting DRCM...
echo.

if exist "%DRCM_SCRIPT%" (
    start /b python "%DRCM_SCRIPT%"
) else (
    echo ERROR: DRCM not found at: %DRCM_SCRIPT%
    pause
    exit /b 1
)

:check
timeout /t 1 /nobreak >nul
tasklist /fi "imagename eq python.exe" 2>nul | find /i "python.exe" >nul
if not errorlevel 1 goto check

echo.
echo DRCM closed.
exit
