@echo off
setlocal

taskkill /F /IM python.exe >nul 2>&1

REM Set PYTHONPATH to your project root
set PYTHONPATH=C:\Temp\Bluecard_v2

python C:\Temp\Bluecard_v2\src\main.py
