@echo off
cd /d "%~dp0.."
python -m pip install --target .build-tools --upgrade -r requirements-build.txt
if errorlevel 1 goto falha
python tools\build_windows.py
if errorlevel 1 goto falha
echo.
echo Pronto! O ZIP esta na pasta dist.
pause
exit /b 0
:falha
echo.
echo Nao foi possivel gerar o pacote. Confira a mensagem acima.
pause
exit /b 1
