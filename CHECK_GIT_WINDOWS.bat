@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe scripts\git_preflight.py
set "check_result=%ERRORLEVEL%"
pause
exit /b %check_result%
