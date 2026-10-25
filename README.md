# 基于 Scrapling 的 PlayZip 游戏库爬虫

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Built with Scrapling](https://img.shields.io/badge/built%20with-Scrapling-orange.svg)](https://github.com/D4Vinci/Scrapling)

> 一个基于 [Scrapling](https://github.com/D4Vinci/Scrapling) 的轻量级爬虫，自动抓取 [PlayZip](https://playzip.com/) 全部分类下的游戏列表，支持自动翻页、历史数据增量比对（新增 / 已下架），并将结果按分类输出为多 Sheet 的 Excel 文件。

## 📌 项目简介

PlayZip 是一个网络游戏分发平台。本项目利用 Scrapling 的 `StealthyFetcher`（内置 Cloudflare 绕过与浏览器指纹伪装）实现对站点全部分类页面的稳定抓取：

1. 获取站点全部分类及其链接；
2. 逐分类自动翻页，提取每款游戏名称；
3. 与本地历史 Excel 比对，标记「新增 / 已存在 / 已下架」；
4. 输出 `Game_Category_List.xlsx`，每个分类一个 Sheet。

适用于游戏库盘点、游戏上下架监控的数据底座，也可作为 Scrapling 反爬实战的学习样例。

## ✨ 功能特性

- **全分类自动发现**：从首页提取全部游戏分类及对应链接。
- **自动翻页**：识别分页控件的「下一页」并循环抓取，直至末页。
- **反爬对抗**：基于 `StealthyFetcher`，开启 `solve_cloudflare` 与 `impersonate="chrome"` 绕过 Cloudflare 与挑战。
- **增量更新**：读取本地历史 Excel，自动标注本次新增、已存在、已下架游戏，并保留首次收录与最后更新时间。
- **结构化输出**：每个分类一个 Sheet，列为 `游戏名称 / 首次收录时间 / 最后更新时间 / 状态`。
- **零配置开箱即用**：仅需修改少量顶部配置即可运行。

## 📁 目录结构

```
.
├── playzip_crawler.py        # 爬虫主程序（入口）
├── requirements.txt          # Python 依赖
├── .gitignore                # 忽略数据产物与日志
├── LICENSE                   # MIT 协议
├── README.md                 # 项目说明（本文件）
└── Game_Category_List.xlsx   # 爬取产出（运行生成，已被 .gitignore 忽略，不入库）
```

## 🔧 环境要求

- Python **3.8 及以上**
- 能够访问 PlayZip 的网络环境
- 需下载 Chromium 供 Scrapling / Playwright 使用

## 🚀 安装与配置

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd <repo>

# 2. 创建虚拟环境（可选但推荐）
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器内核（Scrapling 依赖）
playwright install chromium
```

## 💻 使用方法

直接运行主程序即可：

```bash
python playzip_crawler.py
```

程序执行流程：

1. 打印正在获取的分类列表；
2. 逐分类抓取并翻页，实时打印每页游戏数量；
3. 读取本地历史数据（若存在）并做增量比对；
4. 输出 / 更新 `Game_Category_List.xlsx`，并打印汇总信息。

> 首次运行无历史文件时，全部游戏记为「新增」。后续运行会自动比对，标记新增与下架。

### 示例输出

```
🔍 正在获取全部分类...
✅ 共找到 16 个分类
  · All
  · Action
  · Adventure
  · ...

📂 [1/16] 正在爬取分类：Action
   第 1 页：提取到 30 个游戏
   第 2 页：提取到 30 个游戏
   ...
   ✅ 该分类共 849 个游戏

📂 读取历史数据...
🔄 对比增量更新...

==================================================
✅ 保存完成：Game_Category_List.xlsx
📂 共 16 个分类，6038 个游戏
🆕 本次新增：XX 个游戏
⏰ 更新时间：2026-10-25 11:01:24
```

## 📊 输出说明

产出文件 `Game_Category_List.xlsx` 中，**每个分类对应一个 Sheet**（Sheet 名已对 `/ \ * ? [ ]` 等特殊字符做截断与净化，长度上限 31）。

每个 Sheet 包含 4 列：

| 列名 | 说明 |
| --- | --- |
| `游戏名称` | 游戏标题（分类内去重后按名称排序） |
| `首次收录时间` | 该游戏首次被本程序抓取到的日期时间 |
| `最后更新时间` | 最近一次被抓取到的日期时间 |
| `状态` | `✅ 新增` / `已存在` / `⚠️ 已下架` |

状态含义：

- **✅ 新增**：本次爬取到、且历史中不存在的游戏；
- **已存在**：本次与历史均存在的游戏（刷新「最后更新时间」）；
- **⚠️ 已下架**：历史存在、但本次未再出现的游戏（保留原始收录时间）。

## 🔄 增量更新机制

`merge_and_compare` 将本地历史与新抓取结果做集合运算：

- 新数据 ∩ 历史 → 标记「已存在」，刷新最后更新时间；
- 新数据 − 历史 → 标记「✅ 新增」，写入首次收录时间；
- 历史 − 新数据 → 标记「⚠️ 已下架」，保留原始时间。

因此每次运行都是**增量累积**，可直接用于长期监控游戏库变动。

## ⚙️ 可配置项

脚本顶部 `配置项` 区块：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `BASE_URL` | `https://playzip.com/` | 目标站点根地址 |
| `EXCEL_PATH` | `Game_Category_List.xlsx` | 输出 / 历史数据文件路径 |

如需抓取其他同类站点，可调整选择器（如 `.game_item`、`.pagination a`、`.genres_content ul li a`）以适配目标页面结构。

## ⚠️ 注意事项与局限性

- **单线程顺序抓取**：当前版本按分类、按页顺序请求。当站点分类多、页数大时（如 `All` 分类约 90+ 页）整体耗时较长，请耐心等待。
- **依赖站点结构**：解析选择器绑定 PlayZip 当前页面结构，站点改版后需同步更新规则。
- **Cloudflare 挑战**：`solve_cloudflare` 依赖 Scrapling 的反爬能力，极端情况下可能需调整 `impersonate` 参数或等待挑战窗口。
- **数据用途**：请仅将抓取数据用于个人学习、研究与合法分析，遵守目标站点的 `robots.txt` 与服务条款，合理控制请求频率，避免对站点造成压力。

## 🗺️ 路线图

- [ ] 并发 / 异步抓取（多线程或 asyncio）以提升大规模分类的采集效率
- [ ] 增加请求间隔与随机延时，进一步降低被风控风险
- [ ] 支持断点续爬与失败重试
- [ ] 可选导出 CSV / JSON
- [ ] 增加分类维度的统计报表

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 📢 免责声明

本项目仅用于技术学习与数据采集实践。使用者须自行承担因使用本程序产生的任何风险与法律责任，并确保在遵守相关法律法规及目标网站服务条款的前提下使用。作者不对使用本程序导致的任何后果负责。
