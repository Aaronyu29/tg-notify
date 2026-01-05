@echo off
chcp 65001 >nul
echo ============================================================
echo   币种价格监控器
echo ============================================================
echo.
echo 正在启动监控程序...
echo.

cd /d "%~dp0"
python realtime_monitor_v2.py

pause
