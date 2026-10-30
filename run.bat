@echo off
setlocal
cd /d "%~dp0" || exit /b 1
if not exist "%~dp0.venv\Scripts\pythonw.exe" (
    echo No se encuentra el entorno virtual de Mouse Virtual.
    pause
    exit /b 1
)
start "" /D "%~dp0" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
exit /b %errorlevel%
