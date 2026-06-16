#!/usr/bin/env python3
"""
抖音评论抓取器 - 启动器
=======================

用法:
  python run.py              # 启动 GUI
  python run.py cli <链接>   # 命令行模式
"""

import sys
import os

# 确保脚本目录在 PATH 中
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

if len(sys.argv) > 1 and sys.argv[1] == "cli":
    # CLI 模式：传递剩余参数给 dy_scraper.py
    from dy_scraper import DouyinScraper, CDP_URL
    import subprocess
    subprocess.run([sys.executable, os.path.join(script_dir, "dy_scraper.py")] + sys.argv[2:])
else:
    # GUI 模式
    from gui import main
    main()
