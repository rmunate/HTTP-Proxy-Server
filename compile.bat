@echo off
chcp 65001 >nul
title HTTP Proxy Server - Installer and Compiler

echo.
echo ==========================================
echo   HTTP PROXY SERVER - COMPILER
echo   Automated Installation and Compilation
echo ==========================================
echo.

echo 📋 This script will perform:
echo    1. Creation and activation of the virtual environment
echo    2. Installation of dependencies
echo    3. Compilation to executable
echo    4. Windows configuration
echo.

pause

echo.
echo 🔍 Checking Python...
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo.
echo 🛠️  Creating virtual environment...
if not exist venv (
    python -m venv venv
)

echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate

echo.
echo 📦 Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo 🚀 Starting compilation...
python build_exe.py

echo.
echo ✅ Process completed.
echo    The executable will be in the 'dist' folder
echo.
pause