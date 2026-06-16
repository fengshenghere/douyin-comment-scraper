"""刷新抖音 Cookie（从 CDP 浏览器）"""
from playwright.sync_api import sync_playwright
import os

COOKIE_FILE = "cookies.txt"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:28800")
    ctx = browser.contexts[0]
    cookies = ctx.cookies()
    
    lines = [f"{c['name']}={c['value']}" for c in cookies]
    content = "; ".join(lines)
    
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 已保存 {len(cookies)} 个 Cookie 到 {os.path.abspath(COOKIE_FILE)}")
    browser.close()
