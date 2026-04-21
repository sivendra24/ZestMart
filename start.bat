@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_BOOTSTRAP="
where py >nul 2>nul && set "PYTHON_BOOTSTRAP=py"
if not defined PYTHON_BOOTSTRAP (
    where python >nul 2>nul && set "PYTHON_BOOTSTRAP=python"
)

if not defined PYTHON_BOOTSTRAP (
    echo Python was not found on this machine.
    echo Install Python 3, then run this file again.
    pause
    exit /b 1
)

echo [1/5] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Creating local virtual environment...
    %PYTHON_BOOTSTRAP% -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

echo [2/5] Checking backend dependencies...
".venv\Scripts\python.exe" -c "import flask, flask_cors, flask_limiter, pymongo, bcrypt, jwt, dotenv, PIL, redis" >nul 2>nul
if errorlevel 1 (
    echo Installing backend dependencies...
    ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo Failed to install backend dependencies.
        pause
        exit /b 1
    )
)

echo [3/5] Checking MongoDB service...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$service = Get-Service -Name 'MongoDB' -ErrorAction SilentlyContinue; if (-not $service) { exit 2 }; if ($service.Status -ne 'Running') { try { Start-Service -Name 'MongoDB' -ErrorAction Stop; exit 0 } catch { exit 3 } } else { exit 0 }"
set "MONGO_STATUS=%ERRORLEVEL%"
if "%MONGO_STATUS%"=="2" (
    echo MongoDB Windows service was not found.
    echo If your database is remote, make sure MONGO_URI in .env points to it.
) else if not "%MONGO_STATUS%"=="0" (
    echo MongoDB could not be started automatically.
    echo If the app cannot connect, start MongoDB manually and run this file again.
)

echo [4/5] Seeding database...
".venv\Scripts\python.exe" backend\database\seed_data.py --only-if-empty
if errorlevel 1 (
    echo Failed to seed MongoDB.
    pause
    exit /b 1
)

echo [5/5] Starting ZestMart...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"
".venv\Scripts\python.exe" -m flask --app backend/wsgi.py run --host 0.0.0.0 --port 5000

endlocal
