@echo off
chcp 65001 >nul
cd /d "%~dp0"
python nosrati_ide.py
if errorlevel 1 pause
