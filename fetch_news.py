#!/usr/bin/env python3
"""
每日国际新闻推送 - 只推送前一天的新闻
来源: 路透社, CNN, 半岛电视台, 参考消息, 环球网, 人民网, 网易新闻
"""

import requests
import os
import sys
import re
import feedparser
from datetime import datetime, timedelta


def send_to_wechat(title, content, send_key):
    """通过 Server酱 推送消息到微信"""
    url = f"https://sctapi.ftqq.com/{send_key}.send"
    payload = {"title": title[:128], "desp": content}
    try:
        resp = requests.post(url, json=payload, timeout=30)
        result = resp.json()
        if result.get("code") == 0:
            print(f"[OK] 推送成功")
            return True
        else:
            print(f"[FAIL] 推送失败: {result}")
            return False
    except Exception as e:
        print(f"[ERROR] 推送异常: {e}")
        return False


def yesterday():
    return datetime.now() - timedelta(days=1)


def dedup_and_sort(items, max_items=12):
    seen = set()
    unique = []
    for it in items:
        t = it["title"].replace(" ", "")[:30]
        if t not in seen:
            seen.add(t)
            unique.append(it)
    unique.sort(key=lambda x: len(x["title"]), reverse=True)
    return unique[:max_items]


# ──────────────────────────────────────────────
# RSS 国际源
# ──────────────────────────────────────────────

def fetch_rss(urls, source_name, max_items=12):
    """通用 RSS 抓取，按发布日期过滤前一天的新闻"""
    target = yesterday().date()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    all_items = []

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            feed = feedparser.parse(r.content)
            for entry in feed.entries:
                t = entry.get("title", "").strip()
                l = entry.get("link", "").strip()
                if not t or not l:
                    continue
                pub = None
                if entry.get("published_parsed"):
                    pub = datetime(*entry.published_parsed[:6])
                elif entry.get("updated_parsed"):
                    pub = datetime(*entry.updated_parsed[:6])
                all_items.append({
                    "title": t, "url": l,
                    "_date": pub.date() if pub else None
                })
            if all_items:
                print(f"  [{source_name}] 获取 {len(all_items)} 条")
                break
        except Exception as e:
            print(f"  [{source_name}] 失败: {e}")

    strict = [i for i in all_items if i["_date"] == target]
    result = strict if len(strict) >= 5 else all_items
    return dedup_and_sort(result, max_items)


def fetch_reuters():
    return fetch_rss([
        "https://www.reuters.com/tools/rss/worldNews",
        "http://feeds.reuters.com/reuters/worldNews",
    ], "路透社")


def fetch_cnn():
    return fetch_rss([
        "http://rss.cnn.com/rss/edition_world.rss",
        "http://rss.cnn.com/rss/edition.rss",
    ], "CNN")


def fetch_aljazeera():
    return fetch_rss([
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.aljazeera.com/xml/rss/news.xml",
    ], "半岛电视台")


# ──────────────────────────────────────────────
# 国内源（HTML 抓取）
# ──────────────────────────────────────────────

def match_date_in_url(url, target_date):
    patterns = [
        rf'/{target_date.year}/{target_date.month:02d}{target_date.day:02d}/',
        rf'{target_date.year}{target_date.month:02d}{target_date.day:02d}',
        rf'{target_date.year}-{target_date.month:02d}-{target_date.day:02d}',
    ]
    url_normalized = url.replace(' ', '')
    for p in patterns:
        if p in url_normalized:
            return True
    return False


def fetch_html_links(urls, domain_check, date_target, min_len=10):
    """通用 HTML 抓取"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            r.encoding = "utf-8"
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            items = []

            for link in soup.find_all("a", href=True):
                href = link["href"]
                text = link.get_text(strip=True)
                if not text or len(text) < min_len:
                    continue
                if domain_check(href):
                    full_url = href if href.startswith("http") else (
                        f"https:{href}" if href.startswith("//") else
                        f"{url.rstrip('/')}/{href.lstrip('/')}"
                    )
                    if match_date_in_url(full_url, date_target):
                        items.append({"title": text, "url": full_url})

            if len(items) < 5:
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True)
                    if not text or len(text) < min_len:
                        continue
                    if domain_check(href):
                        full_url = href if href.startswith("http") else (
                            f"https:{href}" if href.startswith("//") else
                            f"{url.rstrip('/')}/{href.lstrip('/')}"
                        )
                        items.append({"title": text, "url": full_url})

            if items:
                return dedup_and_sort(items)
        except Exception as e:
            print(f"  [HTML] {url}: {e}")
            continue

    return []


def fetch_cankaoxiaoxi():
    return fetch_html_links(
        ["https://world.cankaoxiaoxi.com/", "https://www.cankaoxiaoxi.com/"],
        lambda h: "cankaoxiaoxi.com" in h,
        yesterday()
    )


def fetch_huanqiu():
    return fetch_html_links(
        ["https://world.huanqiu.com/"],
        lambda h: "/article/" in h or "huanqiu.com" in h,
        yesterday()
    )


def fetch_people():
    return fetch_html_links(
        ["http://world.people.com.cn/"],
        lambda h: "world.people.com.cn" in h or h.startswith("/n1"),
        yesterday(),
        min_len=12
    )


def fetch_163():
    return fetch_html_links(
        ["https://news.163.com/world/"],
        lambda h: "163.com" in h,
        yesterday(),
        min_len=12
    )


# ──────────────────────────────────────────────
# 格式化 & 主流程
# ──────────────────────────────────────────────

def format_message(news_list, source_name):
    today_str = datetime.now().strftime("%Y-%m-%d %A")
    yesterday_str = yesterday().strftime("%Y-%m-%d")
    lines = [
        f"# 🌍 国际新闻早报",
        f"**{today_str}** | 昨日新闻 ({yesterday_str}) | 来源: {source_name}",
        "",
        "---",
        ""
    ]
    for i, item in enumerate(news_list, 1):
        title = item["title"].replace(" ", "")
        url = item.get("url", "")
        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")

    lines.extend([
        "",
        "---",
        "",
        "_每日上午8:00自动推送 | Powered by Server酱_"
    ])
    return "\n".join(lines)


def main():
    send_key = os.environ.get("SENDKEY")
    if not send_key:
        print("[ERROR] 环境变量 SENDKEY 未设置")
        sys.exit(1)

    print(f"[INFO] 开始抓取前一日国际新闻...")

    sources = [
        ("路透社",      fetch_reuters),
        ("CNN",         fetch_cnn),
        ("半岛电视台",   fetch_aljazeera),
        ("参考消息",     fetch_cankaoxiaoxi),
        ("环球网",      fetch_huanqiu),
        ("人民网",      fetch_people),
        ("网易新闻",    fetch_163),
    ]

    for name, fetcher in sources:
        print(f"[INFO] 尝试 {name}...")
        news = fetcher()
        if not news:
            print(f"[INFO] {name} 未获取到前一日新闻")
            continue

        print(f"[OK] {name} 抓取到 {len(news)} 条新闻")
        content = format_message(news, name)
        send_to_wechat("🌍 国际新闻早报（昨日要闻）", content, send_key)
        return

    print(f"[FAIL] 所有新闻源均失败")
    send_to_wechat(
        "🌍 国际新闻早报",
        f"**{datetime.now().strftime('%Y-%m-%d')}**\n\n"
        "⚠️ 昨日新闻获取失败，请检查网络或数据源是否可用。\n\n"
        "_自动推送将在明天重试_",
        send_key
    )


if __name__ == "__main__":
    main()
