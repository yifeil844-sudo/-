"""
校园跑 GPS 模拟器 - 自动注入 iPhone 定位
支持 iOS 16 / 17 / 18
"""
import sys, os, time, json, glob

def find_route_file():
    """在常见位置查找路线文件"""
    search = [
        "campus_route.json",
        os.path.join(os.path.expanduser("~"), "Downloads", "campus_route.json"),
        os.path.join(os.path.expanduser("~"), "Desktop", "campus_route.json"),
    ]
    for p in search:
        if os.path.exists(p):
            return p
    dl = os.path.join(os.path.expanduser("~"), "Downloads")
    found = sorted(glob.glob(os.path.join(dl, "campus_route*.json")), key=os.path.getmtime, reverse=True)
    if found:
        return found[0]
    return None


def connect():
    """尝试多种方式连接 iPhone，返回 (service_provider, method)"""

    # 方法1: iOS 17+ USB 直连隧道（不需要管理员权限）
    try:
        from pymobiledevice3.remote.module_connectivity import start_tunnel_over_usbmux
        print("  → 尝试 USB 直连隧道（iOS 17+）...")
        tunnel = start_tunnel_over_usbmux()
        print("  ✅ USB 隧道已建立")
        return tunnel.service_provider, "dvt"
    except ImportError:
        print("  → USB 直连隧道不可用（pymobiledevice3 版本较旧）")
    except Exception as e:
        err = str(e).lower()
        if "no device" in err or "usbmux" in err:
            print("  ⚠️ 未检测到 iPhone，请检查 USB 连接")
        else:
            print(f"  → USB 隧道失败: {e}")

    # 方法2: 通过已运行的 tunneld 服务
    try:
        from pymobiledevice3.tunneld import get_tunneld_devices
        print("  → 尝试查找已运行的隧道服务...")
        devices = get_tunneld_devices()
        if devices:
            print("  ✅ 已连接到隧道服务")
            return devices[0], "dvt"
        print("  → 没有找到隧道服务")
    except ImportError:
        pass
    except Exception as e:
        print(f"  → 隧道服务查找失败: {e}")

    # 方法3: iOS 16 及以下直连
    try:
        from pymobiledevice3.lockdown import create_using_usbmux
        print("  → 尝试直连（iOS 16 及以下）...")
        lockdown = create_using_usbmux()
        ver = lockdown.product_version
        print(f"  ✅ 已连接: {lockdown.display_name} (iOS {ver})")
        major = int(ver.split(".")[0])
        if major >= 17:
            print(f"  ⚠️ iOS {ver} 需要用隧道方式连接")
            return lockdown, "try_both"
        return lockdown, "dt"
    except Exception as e:
        print(f"  → 直连失败: {e}")

    return None, None


def simulate_dvt(sp, points):
    """iOS 17+ DVT 方式模拟定位"""
    from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
    from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation

    with DvtSecureSocketProxyService(sp) as dvt:
        loc = LocationSimulation(dvt)
        run_loop(loc, points)
        try:
            loc.clear()
        except Exception:
            pass


def simulate_dt(lockdown, points):
    """iOS 16 及以下 DtSimulateLocation 方式"""
    from pymobiledevice3.services.simulate_location import DtSimulateLocation

    with DtSimulateLocation(lockdown) as svc:
        run_loop(svc, points)
        try:
            svc.clear()
        except Exception:
            pass


def run_loop(loc_svc, points):
    """核心循环：每秒设置一个 GPS 坐标点"""
    total = len(points)
    t0 = time.time()

    for i, pt in enumerate(points):
        loc_svc.set(pt[0], pt[1])

        elapsed = time.time() - t0
        mins, secs = divmod(int(elapsed), 60)
        pct = 100 * (i + 1) // total
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r  {bar} {pct:3d}% │ ⏱ {mins:02d}:{secs:02d} │ 📍 {pt[0]:.5f},{pt[1]:.5f}", end="", flush=True)

        target = t0 + (i + 1)
        wait = target - time.time()
        if wait > 0:
            time.sleep(wait)

    print()


def main():
    print()
    print("=" * 52)
    print("       🏃 校园跑 GPS 模拟器")
    print("=" * 52)

    # 1. 加载路线
    path = find_route_file()
    if not path:
        print()
        print("❌ 找不到路线文件 campus_route.json")
        print()
        print("   操作步骤：")
        print("   1. 双击 campus_run_map.html 打开卫星地图")
        print("   2. 在地图上画操场路线")
        print("   3. 点「生成路线文件」下载 campus_route.json")
        print("   4. 把 campus_route.json 放到这个文件夹里")
        print("   5. 重新运行本程序")
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    pts = data["points"]
    laps = data.get("laps", "?")
    dist = data.get("distance_km", "?")
    pace = data.get("pace_min_km", "?")
    lap_m = data.get("lap_m", "?")

    print(f"\n📍 路线已加载: {path}")
    print(f"   {laps} 圈 × {lap_m}m ≈ {dist} km")
    print(f"   配速 {pace} min/km，共 {len(pts)} 秒")

    # 2. 连接 iPhone
    print(f"\n🔌 正在连接 iPhone...")
    sp, method = connect()

    if sp is None:
        print()
        print("═" * 52)
        print("❌ 无法连接 iPhone，请逐项检查：")
        print()
        print("  □ iPhone 用 USB 数据线连上电脑了吗？")
        print("  □ iPhone 上点了「信任此电脑」？")
        print("  □ 电脑上安装了 iTunes 吗？")
        print("    （微软商店搜 iTunes 安装，提供USB驱动）")
        print("  □ iPhone 开发者模式是否开启？")
        print("    设置→隐私与安全→开发者模式→开启→重启手机")
        print()
        print("  全部确认后重新运行本程序")
        print("═" * 52)
        return

    # 3. 开始模拟
    print()
    print("═" * 52)
    print("  GPS 模拟即将开始！")
    print()
    print("  ① 把手机放到摇步器上（产生步频）")
    print("  ② 打开支付宝 → 校园跑 → 开始打卡")
    print("  ③ 按回车键开始 GPS 模拟 ↓")
    print("═" * 52)
    input("\n  按回车键开始 >>> ")

    print()
    try:
        if method == "dvt":
            simulate_dvt(sp, pts)
        elif method == "dt":
            simulate_dt(sp, pts)
        elif method == "try_both":
            try:
                simulate_dt(sp, pts)
            except Exception:
                print("\n  → 切换到 DVT 模式...")
                sp2, _ = connect()
                if sp2:
                    simulate_dvt(sp2, pts)
                else:
                    raise Exception("DVT 连接失败")
    except KeyboardInterrupt:
        print("\n\n⏹ 已手动停止")
    except Exception as e:
        print(f"\n\n❌ 模拟过程出错: {e}")
        if "developer" in str(e).lower():
            print("   请确保 iPhone 已开启开发者模式")
            print("   设置 → 隐私与安全 → 开发者模式 → 开启")
        return

    print()
    print("✅ GPS 模拟完成！请在支付宝结束打卡")
    print("   iPhone 定位已恢复正常")


if __name__ == "__main__":
    main()
