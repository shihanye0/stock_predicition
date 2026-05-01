@echo off
chcp 65001 >nul
title Stock Sentiment System

echo ========================================
echo   Stock Sentiment System v2.0
echo ========================================
echo.

REM Kill existing processes
echo [INFO] Killing existing processes on ports 8000 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

timeout /t 2 /nobreak >nul

REM Verify conda environment
set "CONDA_PYTHON=C:\Users\Lenovo\anaconda3\envs\finance\python.exe"

if not exist "%CONDA_PYTHON%" (
    echo [ERROR] Conda environment not found: finance
    echo Please ensure conda environment 'finance' exists
    echo Run: conda create -n finance python=3.10
    pause
    exit /b 1
)

echo [OK] Using conda environment: finance
echo.

REM Start backend
echo ========================================
echo   [1/2] Starting Backend on http://localhost:8000
echo   Check for "Application startup complete" message
echo ========================================
echo.
start "Backend" cmd /k "cd /d E:\stock_predicition\backend && \"%CONDA_PYTHON%\" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

REM Wait for backend to start
echo [INFO] Waiting for backend to initialize...
timeout /t 15 /nobreak >nul

REM Start frontend
echo.
echo ========================================
echo   [2/2] Starting Frontend on http://localhost:3000
echo ========================================
start "Frontend" cmd /k "cd /d E:\stock_predicition\frontend && npm run dev"

echo.
echo ========================================
echo   Services Started Successfully!
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo   Admin API (测试数据):
echo   GET http://localhost:8000/api/v1/admin/data-status
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
