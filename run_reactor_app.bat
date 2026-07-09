@echo off
setlocal
title Reactor Platform Launcher
chcp 65001 >nul

set "URL=https://github.com/mungn0603-code/chemical_reactor_parameter_optimization_platform/archive/refs/heads/main.zip"
set "DEST=%USERPROFILE%\reactor-platform"
set "APPDIR=%DEST%\chemical_reactor_parameter_optimization_platform-main"

echo ==================================================
echo   Chemical Reactor Platform - one-click launcher
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.10+ from https://www.python.org/downloads/ ^(check "Add to PATH"^).
  pause
  exit /b 1
)
where curl >nul 2>nul
if errorlevel 1 (
  echo [ERROR] curl not found. Windows 10/11 is required.
  pause
  exit /b 1
)

if not exist "%DEST%" mkdir "%DEST%"
cd /d "%DEST%"

echo [1/4] Downloading source...
curl -L -o main.zip "%URL%"
if errorlevel 1 ( echo Download failed. & pause & exit /b 1 )

echo [2/4] Extracting...
if exist "%APPDIR%" rmdir /s /q "%APPDIR%"
tar -xf main.zip
if errorlevel 1 ( echo Extract failed. & pause & exit /b 1 )

cd /d "%APPDIR%"

echo [3/4] Installing dependencies...
python -m pip install --upgrade pip >nul 2>nul
python -m pip install -r requirements.txt

echo [4/4] Launching the app in your browser...
python -m streamlit run chemical_reactor_app.py

echo.
echo App stopped. Press any key to close.
pause >nul
