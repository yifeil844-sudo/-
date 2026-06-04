@echo off
chcp 65001 >nul
title 校园跑 GPS 模拟器

echo ================================================
echo   校园跑 GPS 模拟器 - 安装与启动
echo ================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python
    echo    请安装 Python 3.8+：https://www.python.org/downloads/
    echo    安装时勾选 Add Python to PATH
    pause & exit /b
)

:: 检查并安装依赖
echo 📦 检查依赖（首次需要 2~3 分钟）...
pip show pymobiledevice3 >nul 2>&1
if errorlevel 1 (
    echo    正在安装 pymobiledevice3...
    pip install pymobiledevice3 --disable-pip-version-check
    if errorlevel 1 (
        echo.
        echo ❌ 安装 pymobiledevice3 失败
        echo    请尝试以管理员身份运行此文件
        echo    右键 start_gps.bat → 以管理员身份运行
        pause & exit /b
    )
    echo    ✅ 安装完成
) else (
    echo    ✅ 依赖已就绪
)

echo.

:: 运行 GPS 模拟器
python campus_run_gps.py

echo.
pause
