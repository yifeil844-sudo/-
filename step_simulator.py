"""
步频模拟器 - iPhone 步数工具
支持两种方案：
  1. 引导用户在iPhone上一次性创建快捷指令（推荐）
  2. 在Windows上生成步数CSV文件，传输到iPhone导入
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import http.server
import socketserver
import socket
import csv
import os
import random
import datetime
from io import BytesIO

try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False


GUIDE_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║       📱 iOS 快捷指令设置教程（一次设置，永久使用）          ║
╚══════════════════════════════════════════════════════════════╝

设置完成后：点一下开始，点一下停止，不需要电脑。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 第一步：打开快捷指令 App
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

① 在 iPhone 桌面找到「快捷指令」
   图标：橙色背景，中间是白色菱形方块

   ▶ 如果找不到：下拉搜索框 → 输入"快捷指令"

② 进入 App 后，点右上角的「+」号

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 第二步：添加「重复」框
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

③ 页面显示"添加操作"，点击它

④ 屏幕上方出现搜索框，输入：重复
   在结果里找「重复」（图标是两个循环箭头）
   ⚠️ 不要选"重复播放"，要选圆形箭头的「重复」

⑤ 页面上出现了一个「重复」框
   点框里写着"10次"的数字
   改为：999（这样能持续运行约16小时）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 第三步：加入"获取随机数"（在重复框内部）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⑥ 重要：点击「重复」框内部的「添加操作」或「+」
   ⚠️ 必须是框的内部！不是框外面的+号

⑦ 搜索框输入：随机数
   选「获取随机数」

⑧ 配置参数：
   • 最小值（Minimum）→ 点击数字改为：150
   • 最大值（Maximum）→ 点击数字改为：190

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 第四步：加入"记录健康样本"（在重复框内部）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⑨ 继续点「重复」框内的「+」

⑩ 搜索框输入：记录健康   （或英文：log health）
   选「记录健康样本」

⑪ 配置参数：
   • 「类型」→ 点击 → 选「步数」（Steps）
   • 「数量」→ 点击数字旁边的小图标（像魔法棒/蓝色圆圈）
              → 弹出菜单选「随机数」（就是刚才获取的随机数）
   • 「日期」→ 保持默认（当前日期）
   • 「时长」→ 改为：1 分钟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 第五步：加入"等待 60 秒"（在重复框内部）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⑫ 继续点「重复」框内的「+」

⑬ 搜索：等待  （或英文：wait）
   选「等待」

⑭ 点时长数字，改为：60（秒）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 第六步：保存快捷指令
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⑮ 点右上角「完成」或「✓」

⑯ 给这个快捷指令起名：步频器  → 点「完成」

══════════════════════════════════════════════════════════════

 🟢 如何【开启】步频器：
    打开「快捷指令」App → 找到「步频器」→ 点▶️ 运行

 🔴 如何【关闭】步频器：
    从手机底部上滑 → 长按「快捷指令」App → 上滑关闭
    或者：打开「快捷指令」App → 点右上角「×」停止

══════════════════════════════════════════════════════════════

 ⚠️ 常见问题：

 Q：找不到「记录健康样本」动作？
 A：需要 iOS 16.0 或更高版本
    检查：设置 → 通用 → 关于本机 → 软件版本

 Q：步数没有出现在支付宝？
 A：支付宝每隔几分钟同步一次苹果健康数据
    支付宝 → 运动 → 右上角刷新，等1-2分钟再看

 Q：第一次运行时有授权弹窗？
 A：选「允许」即可，这是允许快捷指令写入健康数据

 Q：手机锁屏后停止了？
 A：建议使用时插上充电线，在快捷指令运行页面保持屏幕亮着
    或者：设置 → 显示与亮度 → 自动锁定 → 改为"永不"
    （用完记得改回来）

══════════════════════════════════════════════════════════════

快捷指令结构总览（检查用）：

┌─────────────────────────────┐
│  重复 999 次                │
│  ┌───────────────────────┐  │
│  │ 获取随机数            │  │
│  │   最小: 150           │  │
│  │   最大: 190           │  │
│  │                       │  │
│  │ 记录健康样本          │  │
│  │   类型: 步数          │  │
│  │   数量: [随机数]      │  │
│  │   时长: 1分钟         │  │
│  │                       │  │
│  │ 等待 60 秒            │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
"""


class StepSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("步频模拟器  |  iPhone 步数工具")
        self.root.geometry("640x680")
        self.root.resizable(True, True)

        self.server = None
        self.csv_path = None

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Microsoft YaHei", 12, "bold"))
        style.configure("Big.TButton", font=("Microsoft YaHei", 11), padding=6)

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="  📱 快捷指令（推荐）  ")
        self._build_guide_tab(tab1)

        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="  📂 生成步数文件（备用）  ")
        self._build_csv_tab(tab2)

    # ── Tab 1: guide ──────────────────────────────────────────

    def _build_guide_tab(self, parent):
        info = ttk.Label(
            parent,
            text="✅ 设置一次，之后在 iPhone 上一键开关，无需电脑",
            style="Title.TLabel",
            foreground="#2a7a2a",
        )
        info.pack(anchor="w", padx=10, pady=(8, 2))

        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        sb = ttk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        txt = tk.Text(
            frame,
            wrap=tk.WORD,
            yscrollcommand=sb.set,
            font=("Microsoft YaHei", 10),
            padx=12,
            pady=8,
            bg="#fafafa",
        )
        txt.pack(fill=tk.BOTH, expand=True)
        sb.config(command=txt.yview)

        txt.insert(tk.END, GUIDE_TEXT)
        txt.config(state=tk.DISABLED)

    # ── Tab 2: CSV generator ──────────────────────────────────

    def _build_csv_tab(self, parent):
        # — Config —
        cfg = ttk.LabelFrame(parent, text="⚙️  参数设置", padding=12)
        cfg.pack(fill=tk.X, padx=10, pady=8)

        now = datetime.datetime.now()

        # Start time
        ttk.Label(cfg, text="开始时间：").grid(row=0, column=0, sticky="w", pady=4)
        self.start_var = tk.StringVar(value=now.strftime("%H:%M"))
        ttk.Entry(cfg, textvariable=self.start_var, width=9).grid(
            row=0, column=1, sticky="w", padx=6
        )
        ttk.Label(cfg, text="格式 HH:MM，如 09:30", foreground="gray").grid(
            row=0, column=2, sticky="w"
        )

        # Duration
        ttk.Label(cfg, text="持续时长：").grid(row=1, column=0, sticky="w", pady=4)
        self.dur_var = tk.IntVar(value=60)
        ttk.Spinbox(cfg, from_=5, to=480, textvariable=self.dur_var, width=7).grid(
            row=1, column=1, sticky="w", padx=6
        )
        ttk.Label(cfg, text="分钟（5 ~ 480）").grid(row=1, column=2, sticky="w")

        # Step range
        ttk.Label(cfg, text="步频范围：").grid(row=2, column=0, sticky="w", pady=4)
        rng = ttk.Frame(cfg)
        rng.grid(row=2, column=1, columnspan=2, sticky="w")
        self.min_var = tk.IntVar(value=150)
        self.max_var = tk.IntVar(value=190)
        ttk.Spinbox(rng, from_=80, to=250, textvariable=self.min_var, width=6).pack(
            side=tk.LEFT
        )
        ttk.Label(rng, text="  到  ").pack(side=tk.LEFT)
        ttk.Spinbox(rng, from_=80, to=250, textvariable=self.max_var, width=6).pack(
            side=tk.LEFT
        )
        ttk.Label(rng, text="  步/分钟").pack(side=tk.LEFT)

        # — Buttons —
        btn_row = ttk.Frame(parent)
        btn_row.pack(fill=tk.X, padx=10, pady=2)

        ttk.Button(
            btn_row,
            text="📊  生成步数文件",
            style="Big.TButton",
            command=self.generate_csv,
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.srv_btn = ttk.Button(
            btn_row,
            text="📡  开启传输服务器",
            style="Big.TButton",
            command=self.toggle_server,
            state=tk.DISABLED,
        )
        self.srv_btn.pack(side=tk.LEFT)

        # — Status log —
        log_frame = ttk.LabelFrame(parent, text="📋  状态信息", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        log_inner = ttk.Frame(log_frame)
        log_inner.pack(fill=tk.BOTH, expand=True)

        sb2 = ttk.Scrollbar(log_inner)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)

        self.log = tk.Text(
            log_inner,
            height=7,
            wrap=tk.WORD,
            yscrollcommand=sb2.set,
            font=("Consolas", 10),
            bg="#f0f4f0",
        )
        self.log.pack(fill=tk.BOTH, expand=True)
        sb2.config(command=self.log.yview)
        self.log.config(state=tk.DISABLED)

        self.qr_lbl = ttk.Label(log_frame)
        self.qr_lbl.pack(pady=4)

        # — Import instructions —
        ins = ttk.LabelFrame(parent, text="📲  不需要任何 App！直接手动输入到「健康」", padding=8)
        ins.pack(fill=tk.X, padx=10, pady=(0, 8))
        ttk.Label(
            ins,
            text=(
                "点「生成步数文件」后，下方会显示要输入的数字。\n"
                "然后按以下步骤在 iPhone 上操作（无需安装任何额外 App）：\n\n"
                "① 打开 iPhone 自带「健康」App（白色+红心图标）\n"
                "② 底部点「浏览」→ 搜索「步数」→ 点进去\n"
                "③ 右上角点「+」（添加数据）\n"
                "④ 按下方表格逐条输入时间和步数，每条点「添加」\n"
                "⑤ 打开支付宝 → 运动 → 下拉刷新，等 1~3 分钟"
            ),
            justify=tk.LEFT,
            font=("Microsoft YaHei", 10),
        ).pack(anchor="w")

    # ── Logic ────────────────────────────────────────────────

    def _log(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def generate_csv(self):
        try:
            h, m = map(int, self.start_var.get().strip().split(":"))
        except ValueError:
            messagebox.showerror("格式错误", "开始时间格式不对，请输入 HH:MM（如 09:30）")
            return

        dur = self.dur_var.get()
        lo, hi = self.min_var.get(), self.max_var.get()
        if lo >= hi:
            messagebox.showerror("参数错误", "最小步频必须小于最大步频")
            return

        today = datetime.date.today()
        base = datetime.datetime(today.year, today.month, today.day, h, m)

        rows = []
        for i in range(dur):
            t0 = base + datetime.timedelta(minutes=i)
            t1 = t0 + datetime.timedelta(minutes=1)
            rows.append(
                {
                    "startDate": t0.strftime("%Y-%m-%d %H:%M:%S"),
                    "endDate": t1.strftime("%Y-%m-%d %H:%M:%S"),
                    "value": random.randint(lo, hi),
                    "unit": "count",
                    "sourceName": "步频模拟器",
                }
            )

        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steps_data.csv")
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f, fieldnames=["startDate", "endDate", "value", "unit", "sourceName"]
            )
            w.writeheader()
            w.writerows(rows)

        self.csv_path = out
        total = sum(r["value"] for r in rows)
        self._log(f"✅ 已生成 {dur} 分钟步数数据")
        self._log(f"   {rows[0]['startDate']}  →  {rows[-1]['endDate']}")
        self._log(f"   总步数：{total:,}  平均：{total // dur} 步/分钟")
        self._log("═" * 48)
        self._log("📱 在 iPhone「健康」App 手动输入（无需任何额外App）")
        self._log("   健康App → 浏览 → 步数 → 右上角「+」")
        self._log("─" * 48)

        # Show manual entry table (one row per 30 minutes)
        interval = 30
        entry_num = 1
        for i in range(0, dur, interval):
            chunk = rows[i : i + interval]
            chunk_steps = sum(r["value"] for r in chunk)
            chunk_time = chunk[0]["startDate"][11:16]  # HH:MM
            self._log(f"   第{entry_num}条  时间: {chunk_time}    步数: {chunk_steps:,}")
            entry_num += 1

        self._log("─" * 48)
        self._log(f"   ✨ 嫌麻烦？一次输完：时间 {rows[0]['startDate'][11:16]}  步数 {total:,}")
        self._log("═" * 48)
        self.srv_btn.config(state=tk.NORMAL)

    def toggle_server(self):
        if self.server is None:
            self._start_server()
        else:
            self._stop_server()

    @staticmethod
    def _local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _start_server(self):
        if not self.csv_path or not os.path.exists(self.csv_path):
            messagebox.showerror("错误", "请先点「生成步数文件」")
            return

        csv_dir = os.path.dirname(self.csv_path)

        class _Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=csv_dir, **kw)

            def log_message(self, fmt, *args):  # silence access logs
                pass

        self.server = socketserver.TCPServer(("", 8080), _Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

        ip = self._local_ip()
        url = f"http://{ip}:8080/steps_data.csv"

        self._log(f"\n📡 服务器已启动  →  {url}")
        self._log("   请确保 iPhone 与电脑连接同一 WiFi！")

        if HAS_QR:
            try:
                qr = qrcode.QRCode(box_size=5, border=2)
                qr.add_data(url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                pil_img = Image.open(buf).resize((180, 180))
                tk_img = ImageTk.PhotoImage(pil_img)
                self.qr_lbl.config(image=tk_img, text="")
                self.qr_lbl.image = tk_img
                self._log("   📷 用 iPhone 相机对准上方二维码扫描")
            except Exception:
                self._log(f"   手动在 iPhone Safari 输入：{url}")
        else:
            self._log(f"   手动在 iPhone Safari 输入：{url}")
            self._log("   (安装 qrcode pillow 后可自动显示二维码)")

        self.srv_btn.config(text="⏹  停止服务器")

    def _stop_server(self):
        if self.server:
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            self.server = None
        self.srv_btn.config(text="📡  开启传输服务器")
        self._log("\n⏹ 服务器已停止")

    def on_close(self):
        self._stop_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = StepSimulatorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
