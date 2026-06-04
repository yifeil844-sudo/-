@echo off
chcp 65001 >nul
title 校园跑GPS自动模拟

echo.
echo ================================================
echo   校园跑 GPS 自动模拟
echo   配合爱思助手虚拟定位使用
echo ================================================
echo.

powershell -STA -ExecutionPolicy Bypass -File "%~dp0auto_gps.ps1"

pause
