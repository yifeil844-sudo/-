@echo off
chcp 65001 >nul
title 校园跑 GPS 模拟器

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时务必勾选 Add Python to PATH
    pause & exit /b
)

echo 正在安装依赖（首次约需 1~2 分钟）...
pip install flask pymobiledevice3 --quiet --disable-pip-version-check

echo.
echo 启动校园跑 GPS 模拟器，浏览器会自动打开...
python campus_run_sim.py

pause
