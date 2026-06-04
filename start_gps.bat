@echo off
chcp 65001 >nul
title 校园跑GPS模拟器

echo.
echo ================================================
echo   校园跑 GPS 模拟器
echo ================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo 请先安装 Python: https://www.python.org/downloads/
    echo 安装时必须勾选 "Add Python to PATH"
    echo.
    pause
    exit /b
)

echo [1/2] 检查并安装依赖，首次约需2-3分钟...
pip show pymobiledevice3 >nul 2>&1
if errorlevel 1 (
    pip install pymobiledevice3 --disable-pip-version-check -q
    if errorlevel 1 (
        echo [错误] 安装失败，请右键以管理员身份运行
        pause
        exit /b
    )
)
echo [1/2] 依赖就绪

echo [2/2] 启动GPS模拟器...
echo.
python campus_run_gps.py

echo.
pause
