@echo off
chcp 65001 >nul
title 步频模拟器

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8 或更高版本
    echo.
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b
)

echo 正在检查依赖...
pip install qrcode pillow --quiet --disable-pip-version-check 2>nul

echo 启动步频模拟器...
python step_simulator.py

pause
