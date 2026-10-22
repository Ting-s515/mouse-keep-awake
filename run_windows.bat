@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
    echo 找不到 Python Launcher，請先安裝 Python 3。
    pause
    exit /b 1
)
py -3 mouse_keep_awake.py %*
pause