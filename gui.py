#!/usr/bin/env python3
"""
抖音评论抓取器 - GUI 图形界面 v1.2
修复：立即显示日志 + CDP connect 超时 + 线程异常捕获
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os
import sys
import socket
import io
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


class DouyinScraperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("抖音评论抓取器 v1.2")
        self.root.geometry("860x720")
        self.root.minsize(700, 600)

        self.scraper = None
        self.scraping = False
        self._stop_flag = False

        # 变量
        self.cdp_var = tk.StringVar(value="http://127.0.0.1:28800")
        self.output_var = tk.StringVar(value="")
        self.cookie_var = tk.StringVar(value="cookies.txt")
        self.progress_var = tk.StringVar(value="就绪")
        self.status_var = tk.StringVar(value="等待开始...")
        self.sub_var = tk.BooleanVar(value=False)
        self.max_comments_var = tk.StringVar(value="")   # 空=无限制
        self.conn_status_var = tk.StringVar(value="🔍 检测中...")

        self._setup_ui()
        self._center_window()
        self._auto_detect_output()
        self._check_connection()
        self._auto_detect_cookie()

    # =====================================
    # UI 搭建
    # =====================================

    def _setup_ui(self):
        root = self.root
        root.configure(padx=14, pady=10)

        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 14, "bold"))
        style.configure("Section.TLabel", font=("微软雅黑", 10, "bold"))
        style.configure("Action.TButton", font=("微软雅黑", 10))
        style.configure("Small.TButton", font=("微软雅黑", 9))

        # 标题
        title_frame = ttk.Frame(root)
        title_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(title_frame, text="🎬 抖音评论抓取器",
                  style="Title.TLabel").pack(side="left")
        ttk.Label(title_frame, text="v1.2",
                  foreground="gray").pack(side="left", padx=(6, 0))

        # ── 输入区 ──
        input_frame = ttk.LabelFrame(root, text="📥 视频输入", padding=8)
        input_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(input_frame,
                  text="粘贴抖音分享链接或分享文本（自动提取链接）：").pack(anchor="w")
        self.url_text = tk.Text(input_frame, height=4, font=("Consolas", 10), wrap="word")
        self.url_text.pack(fill="x", pady=(4, 0))

        hint_frame = ttk.Frame(input_frame)
        hint_frame.pack(fill="x", pady=(4, 0))
        ttk.Label(hint_frame,
                  text="💡 支持：完整URL / v.douyin.com 短链 / 复制分享文本（自动识别）",
                  foreground="gray", font=("微软雅黑", 8)).pack(anchor="w")

        # ── 设置区 ──
        settings_frame = ttk.LabelFrame(root, text="⚙ 抓取设置", padding=8)
        settings_frame.pack(fill="x", pady=(0, 8))

        # 连接状态行
        conn_row = ttk.Frame(settings_frame)
        conn_row.pack(fill="x", pady=(0, 6))
        ttk.Label(conn_row, textvariable=self.conn_status_var,
                  foreground="gray").pack(side="left")
        ttk.Button(conn_row, text="🔗 自动连接浏览器",
                   style="Small.TButton",
                   command=self._auto_connect).pack(side="left", padx=(8, 0))

        # CDP + 输出目录
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=(0, 4))
        ttk.Label(row1, text="浏览器 CDP：").pack(side="left")
        ttk.Entry(row1, textvariable=self.cdp_var, width=28,
                  font=("Consolas", 9)).pack(side="left", padx=(4, 12))
        ttk.Label(row1, text="输出目录：").pack(side="left")
        ttk.Entry(row1, textvariable=self.output_var, width=20,
                  font=("Consolas", 9)).pack(side="left", padx=(4, 4))
        ttk.Button(row1, text="浏览...", style="Small.TButton",
                   command=self._browse_output).pack(side="left")

        # Cookie + 最大评论数
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill="x", pady=(0, 4))
        ttk.Label(row2, text="🍪 Cookie：").pack(side="left")
        ttk.Entry(row2, textvariable=self.cookie_var, width=30,
                  font=("Consolas", 9)).pack(side="left", padx=(4, 4))
        ttk.Button(row2, text="💾 保存", style="Small.TButton",
                   command=self._save_cookie).pack(side="left")
        ttk.Button(row2, text="浏览...", style="Small.TButton",
                   command=self._browse_cookie).pack(side="left", padx=(4, 0))
        self.cookie_status = ttk.Label(row2, text="", foreground="gray")
        self.cookie_status.pack(side="left", padx=(8, 0))

        # 最大评论数 + 子评论
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill="x", pady=(6, 0))
        ttk.Label(row3, text="📊 最大评论数：").pack(side="left")
        ttk.Entry(row3, textvariable=self.max_comments_var, width=8,
                  font=("Consolas", 9)).pack(side="left", padx=(4, 4))
        ttk.Label(row3, text="（留空=全部）", foreground="gray",
                  font=("微软雅黑", 8)).pack(side="left")
        ttk.Checkbutton(
            row3, text="📎 包含子评论（较慢）",
            variable=self.sub_var,
        ).pack(side="left", padx=(24, 0))

        # ── 按钮区 ──
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", pady=(0, 8))

        self.start_btn = ttk.Button(btn_frame, text="▶ 开始抓取",
                                     style="Action.TButton",
                                     command=self._start_scrape)
        self.start_btn.pack(side="left")

        self.stop_btn = ttk.Button(btn_frame, text="■ 停止",
                                    style="Action.TButton",
                                    command=self._stop_scrape, state="disabled")
        self.stop_btn.pack(side="left", padx=(8, 0))

        ttk.Button(btn_frame, text="📂 打开目录",
                    style="Action.TButton",
                    command=self._open_output).pack(side="left", padx=(8, 0))

        self.progress_label = ttk.Label(btn_frame, textvariable=self.progress_var,
                                        foreground="gray")
        self.progress_label.pack(side="right")

        # ── 进度条 ──
        self.progress_bar = ttk.Progressbar(root, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 4))

        # ── 日志区 ──
        log_frame = ttk.LabelFrame(root, text="📋 运行日志", padding=4)
        log_frame.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, height=14, font=("Consolas", 9),
            wrap="word", state="disabled",
            bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white",
        )
        self.log_area.pack(fill="both", expand=True)

        self.log_area.tag_config("success", foreground="#4ec9b0")
        self.log_area.tag_config("error", foreground="#f44747")
        self.log_area.tag_config("info", foreground="#569cd6")
        self.log_area.tag_config("warn", foreground="#dcdcaa")
        self.log_area.tag_config("time", foreground="#808080")

        # ── 状态栏 ──
        status_bar = ttk.Frame(root)
        status_bar.pack(fill="x", pady=(4, 0))
        ttk.Label(status_bar, textvariable=self.status_var,
                  foreground="gray").pack(side="left")

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # =====================================
    # 工具方法
    # =====================================

    def _log(self, text, tag=""):
        """线程安全写日志"""
        def _write():
            self.log_area.configure(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_area.insert("end", f"[{ts}] ", "time")
            self.log_area.insert("end", text + "\n", tag)
            self.log_area.see("end")
            self.log_area.configure(state="disabled")
        self.root.after(0, _write)

    def _auto_detect_output(self):
        script_dir = os.path.dirname(os.path.abspath(__file__)) or "."
        self.output_var.set(script_dir)

    def _check_connection(self):
        cdp = self.cdp_var.get().strip()
        try:
            from urllib.parse import urlparse
            parsed = urlparse(cdp)
            host = parsed.hostname or "127.0.0.1"
            s = socket.create_connection((host, parsed.port or 28800), timeout=2)
            s.close()
            self.conn_status_var.set("✅ 浏览器已连接")
        except Exception:
            self.conn_status_var.set("⚠ 未连接 — 点「自动连接」启动浏览器")

    def _auto_connect(self):
        self.conn_status_var.set("⏳ 启动浏览器...")
        self.root.update()

        def _do():
            try:
                import subprocess
                subprocess.Popen([
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    "--remote-debugging-port=28800",
                    "--user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\edge_cdp",
                    "https://www.douyin.com",
                ])
                for _ in range(30):
                    time.sleep(1)
                    try:
                        s = socket.create_connection(("127.0.0.1", 28800), timeout=1)
                        s.close()
                        break
                    except Exception:
                        continue
                self.root.after(0, lambda: self.conn_status_var.set("✅ 浏览器已连接"))
                self._log("✅ 浏览器已启动并连接", "success")
            except Exception as e:
                self.root.after(0, lambda: self.conn_status_var.set(f"❌ 启动失败: {e}"))
                self._log(f"❌ 浏览器启动失败: {e}", "error")

        threading.Thread(target=_do, daemon=True).start()

    def _browse_output(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_var.set(path)

    def _open_output(self):
        out = self.output_var.get().strip()
        if out:
            os.makedirs(out, exist_ok=True)
            os.startfile(out)

    def _browse_cookie(self):
        path = filedialog.askopenfilename(
            title="选择 Cookie 文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="cookies.txt",
        )
        if path:
            self.cookie_var.set(path)
            self._auto_detect_cookie()

    def _auto_detect_cookie(self):
        path = self.cookie_var.get().strip()
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                cookie_count = content.count("=")
                self.cookie_status.configure(
                    text=f"✅ 已加载 ({cookie_count}个)", foreground="#4ec9b0")
            except Exception:
                self.cookie_status.configure(text="⚠ 读取失败", foreground="#f44747")
        else:
            self.cookie_status.configure(text="", foreground="gray")

    def _save_cookie(self):
        cdp = self.cdp_var.get().strip()
        path = self.cookie_var.get().strip() or "cookies.txt"

        def _do():
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser = p.chromium.connect_over_cdp(cdp)
                    ctx = browser.contexts[0]
                    cookies = ctx.cookies()
                    lines = [f"{c['name']}={c['value']}" for c in cookies]
                    content = "; ".join(lines)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.root.after(0, lambda: self.cookie_status.configure(
                        text=f"✅ 已保存 {len(cookies)}个", foreground="#4ec9b0"))
                    self._log(f"💾 Cookie 已保存: {path} ({len(cookies)}个)", "success")
            except Exception as e:
                self.root.after(0, lambda: self._log(f"❌ Cookie 保存失败: {e}", "error"))
                self.root.after(0, lambda: messagebox.showwarning(
                    "保存失败", f"无法获取 Cookie:\n{e}\n\n请确认浏览器已打开抖音并已登录。"))

        threading.Thread(target=_do, daemon=True).start()

    def _set_ui_state(self, running: bool):
        self.start_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.url_text.configure(state="disabled" if running else "normal")

    def _stop_scrape(self):
        self._stop_flag = True
        self._log("⏸ 正在停止...", "warn")
        self.status_var.set("正在停止...")

    # =====================================
    # 核心抓取逻辑
    # =====================================

    def _start_scrape(self):
        raw = self.url_text.get("1.0", "end-1c").strip()
        if not raw:
            messagebox.showwarning("提示", "请输入抖音分享链接或分享文本")
            return

        # 解析链接（在主线程做，避免卡 UI）
        try:
            if raw.startswith("http"):
                share_url = raw
            else:
                from dy_scraper import DouyinScraper
                share_url = DouyinScraper.parse_share_text(raw)
        except ValueError:
            messagebox.showwarning("提示", "无法从文本中提取抖音链接，请确认格式正确")
            return

        output_dir = self.output_var.get().strip()
        cookie_path = self.cookie_var.get().strip()
        include_sub = self.sub_var.get()

        max_comments_str = self.max_comments_var.get().strip()
        try:
            max_comments = int(max_comments_str) if max_comments_str else None
        except ValueError:
            messagebox.showwarning("提示", "最大评论数必须是数字")
            return

        # 清空日志（主线程）
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")
        self._log(f"▶ 开始抓取: {share_url}", "info")
        self._log(f"  最大评论数: {'无限制' if max_comments is None else max_comments}", "info")

        # 切 UI 状态
        self._stop_flag = False
        self.scraping = True
        self._set_ui_state(True)
        self.progress_bar["value"] = 0
        self.progress_var.set("准备中...")
        self.status_var.set("正在抓取..." + (" (含子评论)" if include_sub else ""))

        thread = threading.Thread(
            target=self._scrape_thread,
            args=(share_url, output_dir, cookie_path, include_sub, max_comments),
            daemon=True,
        )
        thread.start()

    def _scrape_thread(self, share_url, output_dir, cookie_path, include_sub, max_comments):
        os.makedirs(output_dir, exist_ok=True)

        # ── 加载 Cookie ──
        cookie_str = None
        if cookie_path and os.path.exists(cookie_path):
            try:
                with open(cookie_path, "r", encoding="utf-8") as f:
                    cookie_str = f.read().strip()
                self._log(f"📋 Cookie 已加载 ({cookie_path})", "info")
            except Exception as e:
                self._log(f"⚠ Cookie 读取失败: {e}", "warn")
        elif cookie_path and "=" in cookie_path:
            cookie_str = cookie_path
            self._log("📋 使用传入的 Cookie 字符串", "info")

        # ── 连接浏览器（加超时保护）──
        self._log("🔗 正在连接浏览器...", "info")
        self.progress_var.set("连接浏览器...")

        from dy_scraper import DouyinScraper
        try:
            self.scraper = DouyinScraper(cookie_str=cookie_str)
            self.scraper.connect(timeout=15)   # ← 加 15s 超时
            self._log("✅ 已连接浏览器", "success")
        except Exception as e:
            self._log(f"❌ 浏览器连接失败: {e}", "error")
            self._log("💡 请确认 CDP 浏览器已启动，或点击「🔗 自动连接」", "warn")
            self._finish_scrape(False)
            return

        # ── 解析视频 ──
        self._log("🔍 解析视频链接...", "info")
        self.progress_var.set("解析视频...")
        try:
            full_url = DouyinScraper.resolve_share_link(share_url)
            video_id = DouyinScraper.extract_video_id(full_url)
            self._log(f"🔗 链接: {share_url}", "info")
            self._log(f"🆔 视频ID: {video_id}", "info")
            self._log(f"📄 视频页: https://www.douyin.com/video/{video_id}", "info")
        except Exception as e:
            self._log(f"❌ 链接解析失败: {e}", "error")
            self._finish_scrape(False)
            return

        start_time = time.time()

        # ── 导航到视频页（激活 cookie 上下文 + 获取标题）──
        video_title_raw = ""
        try:
            video_url = f"https://www.douyin.com/video/{video_id}"
            self.scraper.page.goto(video_url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
            video_title_raw = self.scraper.page.title()
            video_title = DouyinScraper._safe_filename(video_title_raw)
            self._log(f"📺 标题: {video_title_raw[:40]}... → 文件名: {video_title}", "info")
        except Exception as e:
            self._log(f"⚠ 获取标题失败: {e}", "warn")
            video_title = ""

        # ── 抓取主评论 ──
        self._log("📥 正在抓取主评论（每页显示进度）...", "info")
        self.progress_var.set("抓取中...")

        all_comments = []
        cursor = 0
        page_num = 0
        total_claimed = 0
        count = 30

        while True:
            if self._stop_flag:
                self._log("⏸ 用户停止", "warn")
                break

            result = self.scraper._fetch_page(video_id, cursor, count)
            status = result.get("status_code", -1)
            has_more = result.get("has_more", 0)
            next_cursor = result.get("cursor", 0)
            comments = result.get("comments", [])
            page_num += 1

            self._log(
                f"  第 {page_num} 页 | cursor={cursor} | 获取 {len(comments)} 条"
                f" | has_more={has_more}",
                "info",
            )

            if status != 0 or not comments:
                self._log(f"  ⚠ 停止: status={status}, got={len(comments)}", "warn")
                break

            for c in comments:
                user_info = c.get("user", {})
                avatar_list = (user_info.get("avatar_thumb") or {}).get("url_list", [])
                all_comments.append({
                    "cid": c.get("cid"),
                    "text": c.get("text"),
                    "user": user_info.get("nickname"),
                    "uid": user_info.get("uid"),
                    "sec_uid": user_info.get("sec_uid"),
                    "avatar": avatar_list[0] if avatar_list else None,
                    "likes": c.get("digg_count", 0),
                    "time": c.get("create_time", 0),
                    "replies": c.get("reply_comment_total", 0),
                    "ip": c.get("ip_label"),
                    "sub_comments": [],
                })

            if total_claimed == 0 and comments:
                total_claimed = comments[0].get(
                    "item_comment_total", result.get("total", 0)
                )

            if max_comments and len(all_comments) >= max_comments:
                self._log(f"  ✋ 已达到最大评论数 {max_comments}，停止", "info")
                all_comments = all_comments[:max_comments]
                break

            if not has_more:
                break
            cursor = next_cursor
            time.sleep(0.2)

            # 进度
            if total_claimed and total_claimed > 0:
                pct = min(100, int(len(all_comments) / total_claimed * 100))
                self.root.after(0, lambda v=pct: setattr(self.progress_bar, "value", v))
                self.root.after(0, lambda n=len(all_comments), t=total_claimed:
                    self.progress_var.set(f"已抓 {n}/{t} ({int(n/t*100)}%)"))
            else:
                self.root.after(0, lambda n=len(all_comments), p=page_num:
                    self.progress_var.set(f"第 {p} 页，共 {n} 条"))

        if self._stop_flag:
            self._finish_scrape(False)
            return

        main_count = len(all_comments)
        self._log(f"✅ 主评论抓取完成: {main_count} 条（视频声称 {total_claimed}）", "success")

        # ── 子评论 ──
        total_subs = 0
        if include_sub and all_comments and not self._stop_flag:
            self._log("🔽 正在抓取子评论...", "info")
            parents_with_replies = [c for c in all_comments if c["replies"] > 0]
            total_parents = len(parents_with_replies)
            self._log(f"  共 {total_parents} 条有回复的评论", "info")

            for idx, c in enumerate(parents_with_replies):
                if self._stop_flag:
                    break
                try:
                    subs = self.scraper.fetch_sub_comments(video_id, c["cid"])
                    c["sub_comments"] = subs
                    total_subs += len(subs)
                    self._log(f"  {c['user']}: {len(subs)} 条子回复", "info")
                except Exception:
                    pass

                pct = int((idx + 1) / total_parents * 100) if total_parents else 0
                self.root.after(0, lambda v=pct: setattr(self.progress_bar, "value", v))
                self.root.after(0, lambda i=idx+1, t=total_parents:
                    self.progress_var.set(f"子评论 {i}/{t}"))
                time.sleep(0.15)

        # ── 导出 Excel ──
        self._log("💾 正在导出 Excel...", "info")
        self.progress_var.set("导出中...")
        safe_name = f"{video_title}.xlsx" if video_title else f"dy_{video_id}.xlsx"
        out_path = os.path.join(output_dir, safe_name)
        try:
            self.scraper.export_excel(all_comments, out_path)
            self._log(f"💾 已保存: {out_path}", "success")
        except Exception as e:
            self._log(f"❌ 导出失败: {e}", "error")

        # ── 汇总 ──
        elapsed = time.time() - start_time
        total_likes = sum(c["likes"] for c in all_comments)
        has_replies = sum(1 for c in all_comments if c["replies"] > 0)

        self._log("")
        self._log("=" * 50, "info")
        self._log(f"📊 抓取完成！", "success")
        self._log(f"   主评论: {main_count} 条", "info")
        if total_subs:
            self._log(f"   子评论: {total_subs} 条", "info")
        self._log(f"   总点赞: {total_likes}", "info")
        self._log(f"   有回复: {has_replies} 条", "info")
        self._log(f"   耗时: {elapsed:.1f} 秒", "info")
        self._log(f"   导出: {os.path.basename(out_path)}", "info")
        self._log("=" * 50, "info")

        self.progress_bar["value"] = 100
        self.status_var.set(
            f"完成 — {main_count}条主评论"
            + (f" + {total_subs}条子评论" if total_subs else "")
            + f" — {elapsed:.0f}秒"
        )
        self._finish_scrape(True)

    def _finish_scrape(self, ok: bool):
        self.scraping = False
        self._stop_flag = False
        self.root.after(0, lambda: self._set_ui_state(False))
        if self.scraper:
            try:
                self.scraper.disconnect()
            except Exception:
                pass


# ───────────────────────────────────────
# 入口
# ───────────────────────────────────────

def main():
    app = DouyinScraperGUI()
    app.root.mainloop()


if __name__ == "__main__":
    main()