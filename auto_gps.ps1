# auto_gps.ps1 - 校园跑GPS自动模拟
# 自动操作爱思助手虚拟定位，按路线循环换坐标

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Threading;

public class Win32Auto {
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();

    [DllImport("user32.dll")]
    public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, IntPtr dwExtraInfo);

    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);

    public const int MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const int MOUSEEVENTF_LEFTUP = 0x0004;
    public const uint ES_CONTINUOUS = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED = 0x00000002;

    public static void LeftClick() {
        mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, IntPtr.Zero);
        Thread.Sleep(60);
        mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, IntPtr.Zero);
    }

    public static void PreventSleep() {
        SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
    }

    public static void AllowSleep() {
        SetThreadExecutionState(ES_CONTINUOUS);
    }
}
"@

[Win32Auto]::SetProcessDPIAware() | Out-Null

function Click-At {
    param([int]$X, [int]$Y)
    [System.Windows.Forms.Cursor]::Position = [System.Drawing.Point]::new($X, $Y)
    Start-Sleep -Milliseconds 150
    [Win32Auto]::LeftClick()
    Start-Sleep -Milliseconds 300
}

function Input-Value {
    param([int]$X, [int]$Y, [string]$Value)
    # Click the field
    [System.Windows.Forms.Cursor]::Position = [System.Drawing.Point]::new($X, $Y)
    Start-Sleep -Milliseconds 100
    [Win32Auto]::LeftClick()
    Start-Sleep -Milliseconds 150

    # Triple click to select all
    [Win32Auto]::LeftClick()
    Start-Sleep -Milliseconds 60
    [Win32Auto]::LeftClick()
    Start-Sleep -Milliseconds 100

    # Ctrl+A as backup
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    Start-Sleep -Milliseconds 80

    # Paste value via clipboard
    [System.Windows.Forms.Clipboard]::SetText($Value)
    Start-Sleep -Milliseconds 50
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 150
}

# =============================================
Clear-Host
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "    校园跑 GPS 自动模拟" -ForegroundColor Cyan
Write-Host "    自动操作爱思助手，按路线换坐标" -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""

# Find route file
$routeFile = $null
$searchPaths = @(
    (Join-Path $PSScriptRoot "route.json"),
    (Join-Path $PSScriptRoot "campus_route.json"),
    (Join-Path ([Environment]::GetFolderPath("UserProfile")) "Downloads\route.json"),
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "route.json")
)
foreach ($p in $searchPaths) {
    if (Test-Path $p) { $routeFile = $p; break }
}

if (-not $routeFile) {
    Write-Host "  [X] 找不到路线文件 route.json" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先用 campus_run_map.html 生成路线:" -ForegroundColor Yellow
    Write-Host "    1. 双击打开 campus_run_map.html"
    Write-Host "    2. 在地图上画操场路线"
    Write-Host "    3. 点 [生成跑步路线] 再点 [下载 route.json]"
    Write-Host "    4. 把 route.json 放到这个文件夹里"
    Write-Host ""
    Read-Host "  按回车退出"
    exit
}

# Load route
$raw = Get-Content $routeFile -Raw -Encoding UTF8
$route = $raw | ConvertFrom-Json
$points = $route.points
$interval = [int]$route.interval
$totalPts = $points.Count

Write-Host "  [OK] 路线已加载: $routeFile" -ForegroundColor Green
Write-Host "       $($route.laps) 圈, 约 $($route.distance_km) km" -ForegroundColor Gray
Write-Host "       配速 $($route.pace_min_km) 分/公里" -ForegroundColor Gray
Write-Host "       共 $totalPts 个GPS点, 每 ${interval} 秒换一次" -ForegroundColor Gray

$estMin = [math]::Ceiling($totalPts * $interval / 60)
Write-Host "       预计用时: 约 $estMin 分钟" -ForegroundColor Gray
Write-Host ""

# =============================================
# Calibration
# =============================================
Write-Host "  ================================================" -ForegroundColor Yellow
Write-Host "    校准模式" -ForegroundColor Yellow
Write-Host "  ================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  请打开爱思助手 -> 虚拟定位" -ForegroundColor White
Write-Host "  确保能看到右侧的 [纬度] [经度] 输入框" -ForegroundColor White
Write-Host "  和 [修改虚拟定位] 按钮" -ForegroundColor White
Write-Host ""

Write-Host "  [1/3] 把鼠标移到 [纬度] 输入框上, 按回车 " -ForegroundColor Cyan -NoNewline
Read-Host
$latPos = [System.Windows.Forms.Cursor]::Position
Write-Host "        已记录 ($($latPos.X), $($latPos.Y))" -ForegroundColor Green

Write-Host "  [2/3] 把鼠标移到 [经度] 输入框上, 按回车 " -ForegroundColor Cyan -NoNewline
Read-Host
$lonPos = [System.Windows.Forms.Cursor]::Position
Write-Host "        已记录 ($($lonPos.X), $($lonPos.Y))" -ForegroundColor Green

Write-Host "  [3/3] 把鼠标移到 [修改虚拟定位] 按钮上, 按回车 " -ForegroundColor Cyan -NoNewline
Read-Host
$btnPos = [System.Windows.Forms.Cursor]::Position
Write-Host "        已记录 ($($btnPos.X), $($btnPos.Y))" -ForegroundColor Green

Write-Host ""
Write-Host "  ================================================" -ForegroundColor Green
Write-Host "    校准完成!" -ForegroundColor Green
Write-Host ""
Write-Host "    注意事项:" -ForegroundColor Yellow
Write-Host "    - 运行期间不要移动爱思助手窗口" -ForegroundColor Yellow
Write-Host "    - 不要碰鼠标和键盘" -ForegroundColor Yellow
Write-Host "    - 按 Ctrl+C 可随时停止" -ForegroundColor Yellow
Write-Host ""
Write-Host "    现在打开支付宝校园跑, 准备好后按回车开始" -ForegroundColor White
Write-Host "  ================================================" -ForegroundColor Green
Read-Host "  按回车开始自动跑步"

# Prevent sleep
[Win32Auto]::PreventSleep()

Write-Host ""
Write-Host "  开始自动模拟GPS..." -ForegroundColor Green
Write-Host ""

$startTime = Get-Date
$stopped = $false

try {
    for ($i = 0; $i -lt $totalPts; $i++) {
        $pt = $points[$i]
        $lat = ([double]$pt.lat).ToString("F6")
        $lon = ([double]$pt.lon).ToString("F6")
        $pct = [math]::Round(100 * ($i + 1) / $totalPts)
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        $mins = [math]::Floor($elapsed / 60)
        $secs = [math]::Floor($elapsed % 60)

        # Input latitude
        Input-Value -X $latPos.X -Y $latPos.Y -Value $lat

        # Input longitude
        Input-Value -X $lonPos.X -Y $lonPos.Y -Value $lon

        # Click modify button
        Click-At -X $btnPos.X -Y $btnPos.Y

        # Progress bar
        $barFull = [math]::Floor($pct / 5)
        $bar = ([string][char]9608) * $barFull + ([string][char]9617) * (20 - $barFull)
        $line = "  $bar ${pct}% | ${mins}:$($secs.ToString('00')) | $($i+1)/$totalPts | $lat,$lon   "
        Write-Host "`r$line" -NoNewline

        # Wait
        if ($i -lt $totalPts - 1) {
            Start-Sleep -Seconds $interval
        }
    }
} catch {
    $stopped = $true
    Write-Host ""
    Write-Host ""
    Write-Host "  [!] 已停止" -ForegroundColor Yellow
}

# Allow sleep again
[Win32Auto]::AllowSleep()

if (-not $stopped) {
    $totalElapsed = ((Get-Date) - $startTime).TotalSeconds
    $tMins = [math]::Floor($totalElapsed / 60)
    $tSecs = [math]::Floor($totalElapsed % 60)

    Write-Host ""
    Write-Host ""
    Write-Host "  ================================================" -ForegroundColor Green
    Write-Host "    GPS模拟完成! 用时 ${tMins}分${tSecs}秒" -ForegroundColor Green
    Write-Host "    请在支付宝结束校园跑打卡" -ForegroundColor Yellow
    Write-Host "  ================================================" -ForegroundColor Green
}

Write-Host ""
Read-Host "  按回车退出"
