@echo off
echo Checking Healing Agent Services...
echo.

echo [1] Checking if Python processes are running:
tasklist | findstr python.exe
echo.

echo [2] Checking port 7001 (Telemetry Stream):
netstat -ano | findstr :7001
echo.

echo [3] Checking port 7002 (Cognitive API):
netstat -ano | findstr :7002
echo.

echo [4] Checking port 7003 (UI Broker):
netstat -ano | findstr :7003
echo.

echo [5] Testing telemetry stream endpoint:
curl -s http://localhost:7001/metrics 2>nul
if %errorlevel% neq 0 (
    echo ✗ Telemetry stream not responding
) else (
    echo ✓ Telemetry stream is running
)
echo.

echo [6] Testing UI broker endpoint:
curl -s http://localhost:7003/docs 2>nul >nul
if %errorlevel% neq 0 (
    echo ✗ UI broker not responding
) else (
    echo ✓ UI broker is running
)
echo.

echo ========================================
echo EXPECTED: 4 Python processes running
echo EXPECTED: Ports 7001, 7002, 7003 in use
echo ========================================
echo.

echo To start all services:
echo   start_all_with_forwarder.bat
echo.

pause
