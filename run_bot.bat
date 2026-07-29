@echo off
cd /d c:\switzerbot
echo Installing dependencies...
python -m pip install -r requirements-core.txt
echo.
echo Installation complete!
echo.
echo Starting bot...
python -m bot.main
pause
