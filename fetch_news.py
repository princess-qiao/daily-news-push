#!/usr/bin/env python3
"""
每日国际新闻推送 - 只推送前一天的新闻
来源: 新华网, The Diplomat, 寰球经济(ce.cn), 人民网, Wired, CNN, 半岛电视台
"""

import requests
import os
import sys
import re
import feedparser
from datetime import datetime, timedelta


def send_to_wechat(title, content, send_key):
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


def strip_html(text):
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")


def dedup_and_sort(items, max_items=15):
    seen = set()
    unique = []
    for it in items:
        t = it["title"].replace(" ", "")[:30]
        if t not in seen:
            seen.add(t)
            unique.append(it)
    return unique[:max_items]


# ──────────────────────────────────────────────
# 翻译
# ──────────────────────────────────────────────

def batch_translate(texts, source="en", target="zh-CN"):
    if not texts:
        return texts
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source, target=target)
        merged = "\n---\n".join(texts)
        result = translator.translate(merged)
        translated = [t.strip() for t in result.split("---")]
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
        return texts


# ──────────────────────────────────────────────
# 主题关键词
# ──────────────────────────────────────────────

EN_TOPIC_KEYWORDS = [
    "sanction", "war", "conflict", "ceasefire", "cease-fire", "cease fire",
    "negotiation", "diplomat", "diplomatic", "military", "NATO", "United Nations",
    "nuclear", "missile", "territory", "sovereignty", "summit", "border",
    "defense", "tension", "troop", "soldier", "attack", "strike", "killed",
    "force", "army", "navy", "fleet", "alliance", "treaty", "ambassador",
    "geopolitical", "crisis", "protest", "refugee", "rebel", "uprising",
    "invasion", "occupation",
    "Israel", "Hamas", "Gaza", "Ukraine", "Russia", "China", "Taiwan",
    "South China Sea", "Iran", "North Korea", "Middle East", "Palestine",
    "Syria", "Yemen", "Afghanistan", "Iraq", "Lebanon", "Hezbollah",
    "India", "Pakistan", "Japan", "South Korea", "Philippines",
    "Africa", "Europe", "Asia", "Pacific", "Arctic",
    "economy", "economic", "trade", "tariff", "inflation", "interest rate",
    "stock market", "GDP", "central bank", "Federal Reserve", "federal reserve",
    "debt", "fiscal", "monetary policy", "recession", "unemployment",
    "growth", "market", "investment", "export", "import", "manufacturing",
    "consumer", "price", "oil", "gold", "currency", "dollar", "yuan",
    "rate hike", "rate cut", "quantitative easing", "tightening",
    "bond", "yield", "commodity", "crude", "supply chain",
    "infrastructure", "real estate", "bubble",
    "global economy", "trade war",
    "policy", "legislation", "reform", "executive order", "government",
    "parliament", "election", "vote", "constitutional", "regulation",
    "president", "congress", "senate", "bill", "law", "administration",
    "cabinet", "democrat", "republican", "party", "prime minister",
    "court", "ruling", "ban", "restriction", "referendum",
    "impeach", "resign", "immigration", "human rights",
    "artificial intelligence", "AI", "machine learning", "chatgpt",
    "chip", "semiconductor", "quantum", "space", "satellite",
    "internet", "algorithm", "autonomous", "robot", "battery",
    "software", "hardware", "technology", "digital", "launch",
    "rocket", "space station", "moon", "Mars", "probe",
    "Apple", "Google", "Microsoft", "Amazon", "Tesla", "Nvidia",
    "Intel", "Samsung", "TSMC", "Huawei", "Meta",
    "cloud", "data center", "cyber", "cybersecurity",
    "climate", "carbon", "energy", "renewable", "solar", "nuclear",
    "vaccine", "drug", "gene", "medical", "biotech",
    "net-zero", "emission", "environment",
]

CN_TOPIC_KEYWORDS = [
    "制裁", "冲突", "战争", "停火", "谈判", "外交", "军事",
    "北约", "欧盟", "联合国", "中美", "中俄", "台湾", "南海",
    "朝鲜", "伊朗", "乌克兰", "俄罗斯", "边境", "主权", "峰会",
    "导弹", "核武器", "国防", "领土", "联盟", "海域", "大使",
    "撤军", "部署", "军演", "局势", "核问题", "中东", "亚太",
    "地缘", "危机", "抗议", "政变", "难民",
    "关税", "贸易战", "升级", "紧张", "对抗", "分歧",
    "会谈", "对话", "武装", "部队", "袭击", "空袭", "爆炸",
    "以色列", "巴勒斯坦", "哈马斯", "加沙",
    "叙利亚", "利比亚", "也门", "阿富汗", "伊拉克",
    "印度", "巴基斯坦", "日本", "韩国", "菲律宾",
    "非洲", "拉丁美洲",
    "经济", "贸易", "通胀", "利率", "股市", "美元",
    "人民币", "GDP", "央行", "美联储", "债务", "财政",
    "货币政策", "供应链", "失业", "投资", "市场", "出口",
    "进口", "产业", "制造", "消费", "物价",
    "经济衰退", "降息", "加息", "汇率", "外汇", "储备",
    "黄金", "石油", "原油", "大宗商品", "期货", "债券",
    "房地产", "基建",
    "美国经济", "中国经济", "全球经济",
    "政策", "法案", "立法", "法规", "改革", "行政令", "政府",
    "议会", "选举", "投票", "宪法", "最高法院", "总统", "国会",
    "内阁", "任期", "弹劾", "辞职", "上任",
    "民主党", "共和党", "党派",
    "总理", "首相", "主席", "领导人", "政权",
    "禁令", "限制", "封锁", "出口管制",
    "AI", "人工智能", "大模型", "机器", "芯片", "半导体", "5G",
    "6G", "量子", "航天", "卫星", "互联网", "算法", "数据",
    "机器人", "新能源", "电池", "科技", "太空", "发射",
    "自动驾驶", "数字化", "软件", "硬件", "网络", "火箭",
    "空间站", "探月", "登月", "火星", "探测器",
    "华为", "苹果", "谷歌", "微软", "亚马逊", "特斯拉",
    "英伟达", "英特尔", "三星", "台积电",
    "操作系统", "云计算", "数据中心",
    "气候变化", "碳中和", "排放",
    "核能", "风能", "太阳能", "可再生能源",
]


def matches_english(text, keywords):
    lower = text.lower()
    for kw in keywords:
        if kw.lower() in lower:
            return True
    return False


def matches_chinese(text, keywords):
    for kw in keywords:
        if kw in text:
            return True
    return False


# ──────────────────────────────────────────────
# RSS 源（英文过滤 → 翻译 → 中文二次确认）
# ──────────────────────────────────────────────

def fetch_rss(urls, source_name):
    target = yesterday().date()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    raw_items = []

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
                summary = ""
                for field in ("summary", "description", "content"):
                    val = entry.get(field, "")
                    if val:
                        if isinstance(val, list):
                            val = " ".join(v.get("value", "") for v in val if hasattr(v, "get"))
                        summary = strip_html(val)[:200]
                        break
                pub = None
                if entry.get("published_parsed"):
                    pub = datetime(*entry.published_parsed[:6])
                elif entry.get("updated_parsed"):
                    pub = datetime(*entry.updated_parsed[:6])
                raw_items.append({
                    "title": t, "url": l, "summary": summary,
                    "_date": pub.date() if pub else None
                })
            if raw_items:
                print(f"  [{source_name}] RSS 获取 {len(raw_items)} 条")
                break
        except Exception as e:
            print(f"  [{source_name}] 失败: {e}")

    strict_date = [i for i in raw_items if i["_date"] == target]
    candidates = strict_date if len(strict_date) >= 5 else raw_items
    candidates = dedup_and_sort(candidates, 15)

    matched = []
    for item in candidates:
        text = item["title"] + " " + item.get("summary", "")
        if matches_english(text, EN_TOPIC_KEYWORDS):
            matched.append(item)

    if not matched:
        print(f"  [{source_name}] 英文关键词无匹配")
        return []

    titles = [it["title"] for it in matched]
    translated = batch_translate(titles)
    for i, it in enumerate(matched):
        if i < len(translated):
            it["title"] = translated[i]

    summaries = [it["summary"] for it in matched if it["summary"]]
    if summaries:
        trans_sum = batch_translate(summaries)
        si = 0
        for it in matched:
            if it["summary"] and si < len(trans_sum):
                it["summary"] = trans_sum[si]
                si += 1

    final = []
    for item in matched:
        text = item["title"] + " " + item.get("summary", "")
        if matches_chinese(text, CN_TOPIC_KEYWORDS):
            final.append(item)

    print(f"  [{source_name}] 主题匹配 {len(final)} 条")
    return final[:6]


def fetch_geopolitical():
    """The Diplomat — 亚太地缘政治分析"""
    return fetch_rss(["https://thediplomat.com/feed/"], "The Diplomat")


def fetch_wired():
    """Wired — 科技"""
    return fetch_rss(["https://www.wired.com/feed/rss"], "Wired")


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
# HTML 源（中国）
# ──────────────────────────────────────────────

def match_date_in_url(url, target_date):
    patterns = [
        rf'/{target_date.year}/{target_date.month:02d}{target_date.day:02d}/',
        rf'{target_date.year}{target_date.month:02d}{target_date.day:02d}',
        rf'{target_date.year}-{target_date.month:02d}-{target_date.day:02d}',
    ]
    url_normalized = url.replace(" ", "")
    for p in patterns:
        if p in url_normalized:
            return True
    return False


def fetch_html_links(urls, domain_check, date_target, min_len=10):
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

            def extract_summary(link):
                for el in [link.parent, link.find_parent(["h1","h2","h3","h4","dt","li"])]:
                    if not el:
                        continue
                    for sib in el.find_next_siblings():
                        txt = sib.get_text(strip=True)
                        if 15 < len(txt) < 200:
                            return txt[:120]
                return ""

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
                        items.append({"title": text, "url": full_url, "summary": extract_summary(link)})

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
                        items.append({"title": text, "url": full_url, "summary": extract_summary(link)})

            if items:
                return dedup_and_sort(items)
        except Exception as e:
            print(f"  [HTML] {url}: {e}")
            continue
    return []


def fetch_xinhua():
    """新华网国际新闻 (news.cn)"""
    return fetch_html_links(
        ["http://www.xinhuanet.com/world/"],
        lambda h: "news.cn" in h,
        yesterday(),
        min_len=10
    )


def fetch_globalecon():
    """寰球经济 - 中国经济网国际频道"""
    return fetch_html_links(
        ["http://intl.ce.cn/", "http://intl.ce.cn/newm/hq/index_1.shtml"],
        lambda h: "ce.cn" in h,
        yesterday(),
        min_len=10
    )


def fetch_people():
    """人民网国际新闻"""
    return fetch_html_links(
        ["http://world.people.com.cn/"],
        lambda h: "people.com.cn" in h,
        yesterday(),
        min_len=12
    )


# ──────────────────────────────────────────────
# 从文章页面抓取概要
# ──────────────────────────────────────────────

def fetch_article_summary(url):
    """访问文章页面，提取首段作为概要"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = "utf-8"
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        # 找正文区域优先：排除导航、页脚等
        for cls in ["rm_txt_con", "article-body", "article_content", "content",
                     "page_content", "articleContent", "news-content", "art_con"]:
            div = soup.find("div", class_=cls)
            if div:
                t = div.get_text(strip=True)
                if len(t) > 30:
                    return t[:150].replace("\n", " ").replace("\r", "")
        # 后备：找第一个长文本的 p 标签
        for tag in soup.find_all("p"):
            t = tag.get_text(strip=True)
            if len(t) > 50:
                return t[:150].replace("\n", " ").replace("\r", "")
        # 后备：找第一个有长文本的块级元素（跳过导航）
        for tag in soup.find_all(["div", "span"]):
            t = tag.get_text(strip=True)
            if len(t) > 50 and "首页" not in t[:20]:
                return t[:150].replace("\n", " ").replace("\r", "")
        return ""
    except Exception as e:
        print(f"  [摘要抓取] 失败: {url[:50]} - {e}")
        return ""


def enrich_summaries(items):
    """为所有中文源条目从文章页面抓取概要"""
    if not items:
        return items
    for item in items:
        url = item.get("url", "")
        if url:
            print(f"  [摘要] 抓取: {item['title'][:30]}...")
            item["summary"] = fetch_article_summary(url)
    return items


# ──────────────────────────────────────────────
# 中文源主题筛选
# ──────────────────────────────────────────────

def filter_chinese(items):
    items = enrich_summaries(items)
    matched = []
    for item in items:
        text = item["title"] + " " + item.get("summary", "")
        if matches_chinese(text, CN_TOPIC_KEYWORDS):
            matched.append(item)
    return matched[:6]


# ──────────────────────────────────────────────
# 格式化
# ──────────────────────────────────────────────

def format_message(news_list, source_name):
    today_str = datetime.now().strftime("%Y-%m-%d %A")
    yesterday_str = yesterday().strftime("%Y-%m-%d")
    lines = [
        f"# 🌍 国际新闻早报",
        f"**{today_str}** | 昨日新闻 ({yesterday_str}) | {source_name}",
        "",
        "---",
        ""
    ]
    for i, item in enumerate(news_list, 1):
        title = item["title"].replace(" ", "")
        url = item.get("url", "")
        src = item.get("_source", "")
        summary = item.get("summary", "").strip()
        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")
        if src:
            lines.append(f"   `{src}`")
        if summary:
            s = summary[:120].replace("\n", " ")
            lines.append(f"   > {s}")

    lines.extend([
        "",
        "---",
        "",
        "_每日上午8:00自动推送 | Powered by Server酱_"
    ])
    return "\n".join(lines)


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def main():
    send_key = os.environ.get("SENDKEY")
    if not send_key:
        print("[ERROR] 环境变量 SENDKEY 未设置")
        sys.exit(1)

    print(f"[INFO] 开始抓取前一日国际新闻...")

    sources = [
        ("新华网",       fetch_xinhua,       False),
        ("The Diplomat", fetch_geopolitical, True),
        ("寰球经济",     fetch_globalecon,   False),
        ("人民网",       fetch_people,       False),
        ("Wired",       fetch_wired,        True),
        ("CNN",         fetch_cnn,          True),
        ("半岛电视台",    fetch_aljazeera,    True),
    ]

    aggregated = []
    seen_titles = set()

    for name, fetcher, is_rss in sources:
        print(f"[INFO] 尝试 {name}...")
        news = fetcher()
        if not news:
            print(f"[INFO] {name} 无结果")
            continue

        if not is_rss:
            news = filter_chinese(news)

        if not news:
            print(f"[INFO] {name} 主题匹配不足")
            continue

        count = 0
        for item in news:
            key = item["title"].replace(" ", "")[:30]
            if key not in seen_titles:
                seen_titles.add(key)
                item["_source"] = name
                aggregated.append(item)
                count += 1
                if count >= min(2, len(news)):
                    break

        print(f"[OK] {name} 取 {count} 条")

    if aggregated:
        print(f"[OK] 汇总 {len(aggregated)} 条")
        content = format_message(aggregated, "多源汇总")
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
