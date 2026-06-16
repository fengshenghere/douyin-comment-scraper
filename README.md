# 抖音视频评论爬取工具

通过浏览器 CDP 调用抖音评论 API，自动处理 `msToken` + `a_bogus` 签名。

## 功能

- ✅ **图形界面（GUI）** - 双击 `run.py` 即可，无需命令操作
- ✅ 分享链接自动解析（短链 → 视频ID）
- ✅ 全量评论抓取（按点赞降序排列）
- ✅ 子评论抓取（可选）
- ✅ Excel 导出（含头像链接、IP属地、时间戳）
- ✅ Cookie 注入（支持文件或直接粘贴字符串）
- ✅ 无需手动处理签名（浏览器自动计算）

## 前置条件

1. **Edge/Chrome 浏览器** 以 CDP 模式运行：
   ```powershell
   Start-Process "msedge.exe" -ArgumentList "--remote-debugging-port=28800", "--user-data-dir=C:\Users\Administrator\AppData\Local\edge_cdp"
   ```
2. Python 依赖：`pip install -r requirements.txt`
3. 浏览器已登录抖音（cookie 有效）

## 用法

### GUI 图形界面（推荐）
双击运行 `run.py`，界面包含：
- 视频链接输入框
- 自动连接浏览器按钮
- Cookie 注入（文件或字符串）
- 子评论开关
- 实时日志 + 进度条
- 一键打开输出目录

### 命令行模式

```bash
# 基础用法：分享链接
python dy_scraper.py "https://v.douyin.com/eZrw9DnN0aM/"

# 指定输出文件
python dy_scraper.py "https://v.douyin.com/xxx/" 我的导出.xlsx

# 复制整个分享文本（自动提取链接）
python dy_scraper.py "0.00 当智商团来到时光服！... https://v.douyin.com/xxx/"

# 包含子评论
python dy_scraper.py "https://v.douyin.com/xxx/" --subs --cookie cookies.txt
```

## API 协议

| 项目 | 值 |
|------|-----|
| 端点 | `GET douyin.com/aweme/v1/web/comment/list/` |
| 翻页 | `cursor`（数字递增），`has_more` 控制终止 |
| 每页 | 30条 |
| 签名 | msToken + a_bogus（浏览器自动计算） |
| 子评论端点 | `GET douyin.com/aweme/v1/web/comment/list/reply/` |

## Excel 输出

| 列 | 内容 |
|-----|------|
| 序号 | 按点赞降序排列 |
| 用户 | 抖音昵称 |
| UID | 用户ID |
| 评论文本 | 完整评论内容 |
| 点赞 | 点赞数 |
| 回复数 | 子回复数量 |
| 时间 | 评论时间 |
| IP属地 | 用户IP属地 |
| 头像链接 | 头像图片URL |

## 技术说明

**为什么需要 CDP 浏览器？**

抖音的评论 API 需要 `msToken`（每次生成，保存在 cookie）和 `a_bogus`（基于请求参数动态计算）两个签名参数。这两个参数的计算逻辑经过高度混淆，直接逆向难度极大。

**方案：在浏览器内发 fetch**

通过 Playwright 连接 CDP 浏览器，用 `page.evaluate()` 在浏览器 JS 上下文内直接调用 `fetch()`。浏览器会自动：
1. 携带登录态 cookie
2. 生成 `msToken`
3. 计算 `a_bogus` 签名

完全绕过手动签名计算。
