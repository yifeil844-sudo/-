"""
校园跑 GPS 模拟器
- 在浏览器卫星地图上画操场路线
- 设置圈数和配速
- 通过 USB 自动向 iPhone 注入模拟 GPS
"""

import os, math, time, threading, webbrowser, json
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

# ── 全局状态 ────────────────────────────────────────────────
state = {
    "running": False,
    "lap": 0,
    "total_laps": 0,
    "distance_m": 0.0,
    "elapsed_s": 0,
    "progress": 0,
    "status_msg": "就绪，等待开始",
}
stop_evt = threading.Event()


# ── GPS 工具函数 ────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_track(waypoints, laps, pace_sec_km):
    """按 1 秒间隔生成 (lat, lon, lap, dist_m) 列表"""
    speed = 1000.0 / pace_sec_km  # m/s
    n = len(waypoints)
    pts = []
    accum = 0.0
    for lap in range(laps):
        for i in range(n):
            a = waypoints[i]
            b = waypoints[(i + 1) % n]
            seg_dist = haversine(a[0], a[1], b[0], b[1])
            steps = max(2, int(seg_dist / speed))
            for s in range(steps):
                t = s / steps
                lat = a[0] + t * (b[0] - a[0])
                lon = a[1] + t * (b[1] - a[1])
                dist = accum + t * seg_dist
                pts.append((lat, lon, lap + 1, dist))
            accum += seg_dist
    return pts


# ── GPS 注入线程 ────────────────────────────────────────────
def sim_worker(waypoints, laps, pace_sec_km):
    global state
    svc = None
    try:
        state["status_msg"] = "正在连接 iPhone（请确认已插线并信任此电脑）…"

        # 兼容不同版本的 pymobiledevice3
        try:
            from pymobiledevice3.lockdown import create_using_usbmux
            lockdown = create_using_usbmux()
        except ImportError:
            from pymobiledevice3.lockdown import LockdownClient
            lockdown = LockdownClient()

        from pymobiledevice3.services.simulate_location import SimulateLocationService
        svc = SimulateLocationService(lockdown)

        track = build_track(waypoints, laps, pace_sec_km)
        total = len(track)

        state["status_msg"] = "📍 GPS 模拟运行中，请打开支付宝校园跑开始打卡…"
        t0 = time.time()

        for i, (lat, lon, lap, dist) in enumerate(track):
            if stop_evt.is_set():
                break
            svc.set(lat, lon)
            state.update({
                "lap": lap,
                "total_laps": laps,
                "distance_m": round(dist),
                "elapsed_s": int(time.time() - t0),
                "progress": round(100 * i / total),
            })
            time.sleep(1)

        svc.stop()
        mins = int((time.time() - t0) // 60)
        secs = int((time.time() - t0) % 60)
        state["status_msg"] = f"✅ 完成！共跑 {round(dist/1000,2)} km，用时 {mins}分{secs:02d}秒"

    except ImportError:
        state["status_msg"] = "❌ 缺少依赖，请重新运行 start.bat 安装依赖"
    except Exception as e:
        err = str(e)
        if "developer" in err.lower() or "instrument" in err.lower():
            state["status_msg"] = (
                "❌ 需要开启开发者模式：\n"
                "iPhone 设置 → 隐私与安全 → 开发者模式 → 开启 → 重启"
            )
        elif "lockdown" in err.lower() or "usbmux" in err.lower() or "usb" in err.lower():
            state["status_msg"] = "❌ iPhone 未连接，请用数据线连接并在手机上点「信任」"
        elif "pair" in err.lower():
            state["status_msg"] = "❌ 未配对，请在 iPhone 上点「信任此电脑」"
        else:
            state["status_msg"] = f"❌ 错误：{err[:120]}"
    finally:
        if svc:
            try:
                svc.stop()
            except Exception:
                pass
        state["running"] = False


# ── Flask 路由 ──────────────────────────────────────────────
@app.route("/")
def index():
    return send_file(os.path.join(BASE, "campus_run_map.html"))


@app.route("/start", methods=["POST"])
def start():
    if state["running"]:
        return jsonify({"error": "已在运行中"})
    data = request.json
    waypoints = data["waypoints"]
    laps = int(data["laps"])
    pace = float(data["pace"]) * 60  # min/km → sec/km

    if len(waypoints) < 3:
        return jsonify({"error": "至少需要 3 个标记点"})

    stop_evt.clear()
    state.update({"running": True, "lap": 0, "distance_m": 0,
                  "elapsed_s": 0, "progress": 0})

    threading.Thread(target=sim_worker, args=(waypoints, laps, pace), daemon=True).start()
    return jsonify({"ok": True})


@app.route("/stop", methods=["POST"])
def stop():
    stop_evt.set()
    return jsonify({"ok": True})


@app.route("/status")
def status():
    return jsonify(state)


if __name__ == "__main__":
    print("=" * 50)
    print("  校园跑 GPS 模拟器 已启动")
    print("  浏览器自动打开，请按页面操作")
    print("=" * 50)
    webbrowser.open("http://localhost:5001")
    app.run(port=5001, debug=False, use_reloader=False)
