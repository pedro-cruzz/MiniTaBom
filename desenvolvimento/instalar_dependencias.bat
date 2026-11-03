@echo off
cd /d "%~dp0.."
python -m pip install --target .deps --upgrade --no-warn-script-location -r requirements.txt
if errorlevel 1 pause
