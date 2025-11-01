@echo off
echo Starting Healing Agent System...
echo.

echo [1/3] Starting Telemetry Stream on port 7001...
start "Telemetry Stream" cmd /k "cd /d %~dp0 && python phase1_data/telemetry_stream.py"
timeout /t 3

echo [2/3] Starting Cognitive API on port 7002...
start "Cognitive API" cmd /k "cd /d %~dp0 && python phase2_cognitive/reasoning_api.py"
timeout /t 3

echo [3/3] Starting UI Broker on port 7003...
start "UI Broker" cmd /k "cd /d %~dp0 && python phase4_interface/ui_broker.py"
timeout /t 3

echo.
echo All services started!
echo Opening dashboard in browser...
timeout /t 2
start http://localhost:7003

echo.
echo Dashboard: http://localhost:7003
echo Cognitive API Docs: http://localhost:7002/docs
echo Metrics: http://localhost:7002/metrics
echo.
echo Press any key to exit this window (services will keep running)...
pause
