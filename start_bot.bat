@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === AI Abuse Monitor Bot ===
python -m pip install -r requirements.txt --quiet
python bot.py
pause
