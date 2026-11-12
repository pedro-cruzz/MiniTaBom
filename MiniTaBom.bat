@echo off
cd /d "%~dp0"
if exist "%~dp0Aplicativo\Abrir.bat" (
    call "%~dp0Aplicativo\Abrir.bat"
    exit /b 0
)
if exist "%~dp0Aplicativo\MiniTaBom.exe" (
    start "" "%~dp0Aplicativo\MiniTaBom.exe"
    exit /b 0
)
python src\app.py
if errorlevel 1 pause
