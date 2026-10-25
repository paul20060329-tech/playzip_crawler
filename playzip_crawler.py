import datetime
import os
import pandas as pd
from urllib.parse import urljoin
from scrapling.fetchers import StealthyFetcher

# ========== 配置项 ==========
BASE_URL = "https://playzip.com/"
EXCEL_PATH = "Game_Category_List.xlsx"
CURRENT_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# ============================


def get_all_categories():
    """获取所有分类名称和对应的链接"""
    print("🔍 正在获取全部分类...")
    page = StealthyFetcher.fetch(
        BASE_URL,
        headless=True,
        solve_cloudflare=True,
        impersonate="chrome",
        network_idle=True
    )
    
    categories = {}
    cat_items = page.css(".genres_content ul li a")
    for item in cat_items:
        name = item.css("::text").get().strip()
        href = item.attrib.get("href", "")
        if name and href:
            full_url = urljoin(BASE_URL, href)
            categories[name] = full_url
    
    if not categories:
        cat_items = page.css(".category li a")
        for item in cat_items:
            name = item.css("::text").get().strip()
            href = item.attrib.get("href", "")
            if name and href:
                categories[name] = urljoin(BASE_URL, href)
    
    print(f"✅ 共找到 {len(categories)} 个分类")
    for name in categories:
        print(f"  · {name}")
    return categories


def crawl_single_category(url):
    """爬取单个分类下的所有游戏（自动翻页）"""
    games = set()
    current_url = url
    page_num = 1

    while current_url:
        page = StealthyFetcher.fetch(
            current_url,
            headless=True,
            solve_cloudflare=True,
            impersonate="chrome",
            network_idle=True
        )

        # 提取当前页的游戏名
        game_items = page.css(".game_item")
        for item in game_items:
            name = item.css(".game_info span::text").get()
            if name and name.strip():
                games.add(name.strip())

        print(f"   第 {page_num} 页：提取到 {len(game_items)} 个游戏")

        # 查找下一页链接
        next_link = None
        pagination_links = page.css(".pagination a")
        
        for link in pagination_links:
            text = link.css("::text").get().strip().lower()
            # 匹配常见的下一页标识：Next、>、»、下一页
            if text in ("next", ">", "»", "下一页", "next →"):
                href = link.attrib.get("href", "")
                # 排除禁用状态的按钮
                if href and "javascript:void" not in href:
                    next_link = urljoin(current_url, href)
                break

        # 没有下一页则结束循环
        if not next_link or next_link == current_url:
            break

        current_url = next_link
        page_num += 1

    return sorted(list(games))


def crawl_all_games():
    """遍历爬取所有分类的游戏"""
    categories = get_all_categories()
    if not categories:
        print("❌ 未获取到分类")
        return {}
    
    result = {}
    for idx, (cat_name, cat_url) in enumerate(categories.items(), 1):
        print(f"\n📂 [{idx}/{len(categories)}] 正在爬取分类：{cat_name}")
        games = crawl_single_category(cat_url)
        result[cat_name] = games
        print(f"   ✅ 该分类共 {len(games)} 个游戏")
    
    return result


def load_history_data():
    """读取本地已有的Excel历史数据"""
    if not os.path.exists(EXCEL_PATH):
        return {}
    
    history = {}
    with pd.ExcelFile(EXCEL_PATH) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            history[sheet_name] = df
    return history


def merge_and_compare(history, new_data):
    """合并新旧数据，对比新增/已存在/已下架"""
    result = {}
    all_categories = set(history.keys()) | set(new_data.keys())

    for cat in all_categories:
        new_games = new_data.get(cat, [])
        old_df = history.get(cat, pd.DataFrame(columns=["游戏名称", "首次收录时间", "最后更新时间", "状态"]))

        old_map = {}
        for _, row in old_df.iterrows():
            old_map[row["游戏名称"]] = {
                "首次收录时间": row["首次收录时间"],
                "最后更新时间": row["最后更新时间"]
            }

        rows = []
        # 处理本次爬取到的游戏
        for game in new_games:
            if game in old_map:
                rows.append({
                    "游戏名称": game,
                    "首次收录时间": old_map[game]["首次收录时间"],
                    "最后更新时间": CURRENT_TIME,
                    "状态": "已存在"
                })
                del old_map[game]
            else:
                rows.append({
                    "游戏名称": game,
                    "首次收录时间": CURRENT_TIME,
                    "最后更新时间": CURRENT_TIME,
                    "状态": "✅ 新增"
                })

        # 处理已下架的游戏
        for game, info in old_map.items():
            rows.append({
                "游戏名称": game,
                "首次收录时间": info["首次收录时间"],
                "最后更新时间": info["最后更新时间"],
                "状态": "⚠️ 已下架"
            })

        result[cat] = pd.DataFrame(rows)
    
    return result


def save_excel(data):
    """保存到Excel，每个分类一个sheet"""
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        for cat, df in data.items():
            safe_name = cat.replace("/", "_").replace("\\", "_").replace("*", "")\
                          .replace("?", "").replace("[", "").replace("]", "")[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)
    
    total_cat = len(data)
    total_game = sum(len(df) for df in data.values())
    new_count = sum(len(df[df["状态"] == "✅ 新增"]) for df in data.values())
    
    print(f"\n{'='*50}")
    print(f"✅ 保存完成：{EXCEL_PATH}")
    print(f"📂 共 {total_cat} 个分类，{total_game} 个游戏")
    print(f"🆕 本次新增：{new_count} 个游戏")
    print(f"⏰ 更新时间：{CURRENT_TIME}")


def main():
    new_data = crawl_all_games()
    if not new_data:
        return
    
    print("\n📂 读取历史数据...")
    history = load_history_data()

    print("🔄 对比增量更新...")
    merged = merge_and_compare(history, new_data)

    save_excel(merged)


if __name__ == "__main__":
    main()
