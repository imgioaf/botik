@echo off
cd /d "%~dp0"
call stop_bot.bat
venv\Scripts\python.exe -m bot.main
pause
