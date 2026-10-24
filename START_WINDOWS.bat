@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  call SETUP_WINDOWS.bat --no-pause
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe scripts\local_check.py
if errorlevel 1 goto fail
echo Open http://127.0.0.1:5000 in your browser.
echo Keep this window open. Press Ctrl+C to stop the server.
.venv\Scripts\python.exe app.py
pause
exit /b 0
:fail
echo Run SETUP_WINDOWS.bat and review any reported problem before starting.
pause
exit /b 1
