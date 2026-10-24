@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 --version >nul 2>&1
  if errorlevel 1 (
    echo Python 3.12 with the Windows launcher is required. Install it, then try again.
    goto fail
  )
  py -3.12 -m venv .venv
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -c "import sys; assert sys.version_info[:2] == (3,12), 'This project uses Python 3.12; create its venv with py -3.12.'"
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist "instance\tracker.sqlite3" (
  .venv\Scripts\python.exe -m flask --app app init-db --demo
  if errorlevel 1 goto fail
) else (
  echo Existing database retained. Setup does not reset or replace it.
)
.venv\Scripts\python.exe scripts\local_check.py
if errorlevel 1 goto fail
echo Setup complete. Use START_WINDOWS.bat to run the application.
if /i not "%~1"=="--no-pause" pause
exit /b 0
:fail
echo Setup did not complete. Review the error above; existing data has been preserved.
if /i not "%~1"=="--no-pause" pause
exit /b 1
