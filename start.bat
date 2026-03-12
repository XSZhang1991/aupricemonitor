@echo off
chcp 65001 >nul
echo ============================================
echo   黄金价格监控系统 - 启动脚本
echo ============================================
echo.

REM Start MySQL service if not running
echo [1/3] 检查 MySQL 服务...
sc query MySQL84 | findstr "RUNNING" >nul 2>&1
if errorlevel 1 (
    echo     正在启动 MySQL84 服务...
    powershell -Command "Start-Process sc -ArgumentList 'start MySQL84' -Verb RunAs -Wait -WindowStyle Hidden"
    timeout /t 3 /nobreak >nul
)
echo     MySQL 已就绪

REM Start backend
echo [2/3] 启动后端服务 (端口 8000)...
start "Gold Monitor Backend" /min cmd /c ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
echo     后端已启动

REM Start frontend
echo [3/3] 启动前端服务 (端口 5173)...
start "Gold Monitor Frontend" /min cmd /c "cd frontend && npm run dev"
timeout /t 5 /nobreak >nul

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*10\." ^| head -1') do set LOCALIP=%%a
for /f "tokens=* delims= " %%a in ("%LOCALIP%") do set LOCALIP=%%a
if "%LOCALIP%"=="" (
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do set LOCALIP=%%a
    for /f "tokens=* delims= " %%a in ("%LOCALIP%") do set LOCALIP=%%a
)

echo.
echo ============================================
echo   本机访问:  http://localhost:5173
echo   局域网:    http://%LOCALIP%:5173
echo   API接口:   http://%LOCALIP%:8000/docs
echo ============================================
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost:5173
