@echo off
echo Stopping any running servers...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul

timeout /t 2 /nobreak >nul

echo Starting server...
cd backend
start "GeoGLI API Server" .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo Server started in new window
echo API: http://localhost:8000
echo Docs: http://localhost:8000/docs
echo Health: http://localhost:8000/api/dify/health
