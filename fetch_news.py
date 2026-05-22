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
# 翻译 (英→中)
# ──────────────────────────────────────────────

def batch_translate(texts, source="en", target="zh-CN"):
    """批量翻译英文标题为中文"""
    if not texts:
        return texts
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source, target=target)
        # 合并翻译，用分隔符避免逐条调用
        merged = "\n---\n".join(texts)
        result = translator.translate(merged)
        translated = [t.strip() for t in result.split("---")]
        # 如果翻译结果数量不匹配，逐条翻译
        if len(translated) != len(texts):
            translated = []
            for t in texts:
                try:
                    translated.append(translator.translate(t))
                except:
                    translated.append(t)
        return translated
    except Exception as e:
        print(f"  [翻译] 失败: {e}")
        return texts  # 翻译失败返回原文


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
    result = dedup_and_sort(result, max_items)

    # 翻译英文标题为中文
    titles = [it["title"] for it in result]
    translated = batch_translate(titles)
    for i, it in enumerate(result):
        if i < len(translated) and translated[i] != it["title"]:
            it["title"] = translated[i]

    return result


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


# ──────────────────────────────────────────────
# 主题筛选
# ──────────────────────────────────────────────

TOPIC_KEYWORDS = [
    # 地缘政治
    "制裁", "冲突", "战争", "停火", "谈判", "外交", "军事",
    "北约", "欧盟", "联合国", "中美", "中俄", "台湾", "南海",
    "朝鲜", "伊朗", "乌克兰", "俄罗斯", "边境", "主权", "峰会",
    "导弹", "核武器", "国防", "领土", "联盟", "海域", "大使",
    "撤军", "部署", "军演", "局势", "核问题", "中东", "亚太",
    # 经济
    "经济", "贸易", "关税", "通胀", "利率", "股市", "美元",
    "人民币", "GDP", "央行", "美联储", "债务", "财政",
    "货币政策", "供应链", "失业", "投资", "市场", "出口",
    "进口", "产业", "制造业", "服务业", "消费", "物价",
    "经济衰退", "经济制裁", "贸易战", "经济合作",
    # 政策
    "政策", "法案", "立法", "法规", "改革", "行政令", "政府",
    "议会", "选举", "投票", "宪法", "最高法院", "总统", "国会",
    "参议院", "众议院", "条例", "修订", "新政", "白宫",
    "国务院", "外交部", "商务部", "国防部", "国务院",
    # 科技
    "AI", "人工智能", "芯片", "半导体", "5G", "量子", "航天",
    "卫星", "互联网", "算法", "机器人", "新能源", "电池",
    "科技", "太空", "发射", "自动驾驶", "数字化",
    "大模型", "机器学习", "数据", "软件", "硬件", "网络",
    "火箭", "空间站", "探月",
]


def topic_filter(items, min_match=5):
    """按主题筛选并排序, 只保留匹配关键词的新闻"""
    scored = []
    for item in items:
        title = item["title"].lower()
        score = sum(1 for kw in TOPIC_KEYWORDS if kw.lower() in title)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    result = [item for _, item in scored]

    # 如果筛选后不够, 放宽限制(取原文前15条)
    if len(result) < min_match:
        return items[:15]
    return result[:12]


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

        print(f"[OK] {name} 抓取到 {len(news)} 条")
        # 按主题筛选
        filtered = topic_filter(news)
        if len(filtered) < 3:
            print(f"  [筛选] 主题匹配不足, 跳过此源")
            continue

        print(f"  [筛选] 主题匹配 {len(filtered)} 条")
        content = format_message(filtered, name)
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
