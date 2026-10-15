@echo off
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python not found. Install Python 3.10+ from python.org and tick "Add to PATH".
    pause
    exit /b 1
)
python launcher.py
if errorlevel 1 (
    echo.
    echo Something went wrong, see messages above.
    pause
)
