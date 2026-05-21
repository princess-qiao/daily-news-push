#!/usr/bin/env python3
"""
每日国际新闻推送 - 通过 Server酱 推送到微信
"""

import requests
import os
import sys
from datetime import datetime


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


def fetch_huanqiu():
    """从环球网抓取国际新闻"""
    url = "https://world.huanqiu.com/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.encoding = "utf-8"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")

        items = []
        # 尝试多种选择器抓取新闻标题/链接
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if not text or len(text) < 10:
                continue
            # 环球网文章链接通常包含 /article/ 或特定路径
            if "/article/" in href or "huanqiu.com" in href:
                if text not in [x["title"] for x in items]:
                    full_url = href if href.startswith("http") else f"https:{href}"
                    items.append({"title": text, "url": full_url})

        # 去重并按长度排序取最有价值的12条
        seen = set()
        unique = []
        for it in items:
            t = it["title"].replace(" ", "")[:30]
            if t not in seen:
                seen.add(t)
                unique.append(it)

        unique.sort(key=lambda x: len(x["title"]), reverse=True)
        return unique[:12]

    except Exception as e:
        print(f"[WARN] 环球网抓取失败: {e}")
        return []


def fetch_people():
    """备用源: 人民网国际新闻"""
    try:
        from bs4 import BeautifulSoup
        url = "http://world.people.com.cn/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        items = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if not text or len(text) < 12:
                continue
            if "world.people.com.cn" in href or href.startswith("/n1"):
                full_url = href if href.startswith("http") else f"http:{href}"
                items.append({"title": text, "url": full_url})

        seen = set()
        unique = []
        for it in items:
            t = it["title"].replace(" ", "")[:30]
            if t not in seen:
                seen.add(t)
                unique.append(it)

        unique.sort(key=lambda x: len(x["title"]), reverse=True)
        return unique[:12]
    except Exception as e:
        print(f"[WARN] 人民网抓取失败: {e}")
        return []


def fetch_163():
    """备用源: 网易国际新闻"""
    try:
        from bs4 import BeautifulSoup
        url = "https://news.163.com/world/"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        items = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if not text or len(text) < 12:
                continue
            if "163.com" in href:
                items.append({"title": text, "url": href})

        seen = set()
        unique = []
        for it in items:
            t = it["title"].replace(" ", "")[:30]
            if t not in seen:
                seen.add(t)
                unique.append(it)

        unique.sort(key=lambda x: len(x["title"]), reverse=True)
        return unique[:12]
    except Exception as e:
        print(f"[WARN] 网易抓取失败: {e}")
        return []


def format_message(news_list, source_name):
    """格式化为 Markdown 消息"""
    today = datetime.now().strftime("%Y-%m-%d %A")
    lines = [
        f"# 🌍 每日国际新闻早报",
        f"**{today}** | 来源: {source_name}",
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

    print(f"[INFO] 开始抓取国际新闻...")
    news = []

    # 按优先级尝试多个源
    sources = [
        ("环球网", fetch_huanqiu),
        ("人民网", fetch_people),
        ("网易新闻", fetch_163),
    ]

    for name, fetcher in sources:
        print(f"[INFO] 尝试 {name}...")
        news = fetcher()
        if news:
            print(f"[OK] {name} 抓取到 {len(news)} 条新闻")
            content = format_message(news, name)
            send_to_wechat("🌍 每日国际新闻早报", content, send_key)
            return
        else:
            print(f"[INFO] {name} 未获取到新闻")

    # 所有源都失败
    print(f"[FAIL] 所有新闻源均失败")
    send_to_wechat(
        "🌍 每日国际新闻早报",
        f"**{datetime.now().strftime('%Y-%m-%d')}**\n\n"
        "⚠️ 今日新闻获取失败，请检查网络或数据源是否可用。\n\n"
        "_自动推送将在明天重试_",
        send_key
    )


if __name__ == "__main__":
    main()
