@echo off
setlocal

:: Default Configuration
if "%ACESTEP_API_HOST%"=="" set ACESTEP_API_HOST=0.0.0.0
if "%ACESTEP_API_PORT%"=="" set ACESTEP_API_PORT=8001
if "%ACESTEP_API_LOG_LEVEL%"=="" set ACESTEP_API_LOG_LEVEL=info

echo Starting ACE-Step API Server...
echo Host: %ACESTEP_API_HOST%
echo Port: %ACESTEP_API_PORT%
echo Log Level: %ACESTEP_API_LOG_LEVEL%

:: Run server with Python
python -m uvicorn acestep.api_server:app ^
    --host %ACESTEP_API_HOST% ^
    --port %ACESTEP_API_PORT% ^
    --workers 1 ^
    --log-level %ACESTEP_API_LOG_LEVEL%

if errorlevel 1 (
    echo Server crashed or failed to start.
    pause
)

endlocal
