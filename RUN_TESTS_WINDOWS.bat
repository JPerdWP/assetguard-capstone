@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP_WINDOWS.bat first.
  goto fail
)
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
if not exist "local-results" mkdir "local-results"
.venv\Scripts\python.exe -m pytest -q --junitxml=local-results\test-results.xml > local-results\test-output.txt 2>&1
set "test_result=%ERRORLEVEL%"
type local-results\test-output.txt
echo Results are in local-results. Tests use temporary databases.
pause
exit /b %test_result%
:fail
pause
exit /b 1
