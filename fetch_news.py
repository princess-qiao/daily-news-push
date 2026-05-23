#!/usr/bin/env python3
"""
姣忔棩鍥介檯鏂伴椈鎺ㄩ€?- 鍙帹閫佸墠涓€澶╃殑鏂伴椈
鏉ユ簮: 鏂板崕缃? The Diplomat, 瀵扮悆缁忔祹(ce.cn), 浜烘皯缃? Wired, CNN, 鍗婂矝鐢佃鍙?"""

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
            print(f"[OK] 鎺ㄩ€佹垚鍔?)
            return True
        else:
            print(f"[FAIL] 鎺ㄩ€佸け璐? {result}")
            return False
    except Exception as e:
        print(f"[ERROR] 鎺ㄩ€佸紓甯? {e}")
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


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 缈昏瘧
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def batch_translate(texts, source="en", target="zh-CN"):
    if not texts:
        return texts
    try:
        from deep_translator import GoogleTranslator
        import concurrent.futures
        translator = GoogleTranslator(source=source, target=target)
        merged = "\n---\n".join(texts)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(translator.translate, merged)
            result = future.result(timeout=15)
        translated = [t.strip() for t in result.split("---")]
        if len(translated) != len(texts):
            translated = []
            for t in texts:
                try:
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        f = ex.submit(translator.translate, t)
                        translated.append(f.result(timeout=10))
                except:
                    translated.append(t)
        return translated
    except concurrent.futures.TimeoutError:
        print(f"  [缈昏瘧] 瓒呮椂(15s)锛岃烦杩囩炕璇?)
        return texts
    except Exception as e:
        print(f"  [缈昏瘧] 澶辫触: {e}")
        return texts


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 涓婚鍏抽敭璇?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

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
    "鍒惰", "鍐茬獊", "鎴樹簤", "鍋滅伀", "璋堝垽", "澶栦氦", "鍐涗簨",
    "鍖楃害", "娆х洘", "鑱斿悎鍥?, "涓編", "涓縿", "鍙版咕", "鍗楁捣",
    "鏈濋矞", "浼婃湕", "涔屽厠鍏?, "淇勭綏鏂?, "杈瑰", "涓绘潈", "宄颁細",
    "瀵煎脊", "鏍告鍣?, "鍥介槻", "棰嗗湡", "鑱旂洘", "娴峰煙", "澶т娇",
    "鎾ゅ啗", "閮ㄧ讲", "鍐涙紨", "灞€鍔?, "鏍搁棶棰?, "涓笢", "浜氬お",
    "鍦扮紭", "鍗辨満", "鎶楄", "鏀垮彉", "闅炬皯",
    "鍏崇◣", "璐告槗鎴?, "鍗囩骇", "绱у紶", "瀵规姉", "鍒嗘",
    "浼氳皥", "瀵硅瘽", "姝﹁", "閮ㄩ槦", "琚嚮", "绌鸿", "鐖嗙偢",
    "浠ヨ壊鍒?, "宸村嫆鏂潶", "鍝堥┈鏂?, "鍔犳矙",
    "鍙欏埄浜?, "鍒╂瘮浜?, "涔熼棬", "闃垮瘜姹?, "浼婃媺鍏?,
    "鍗板害", "宸村熀鏂潶", "鏃ユ湰", "闊╁浗", "鑿插緥瀹?,
    "闈炴床", "鎷変竵缇庢床",
    "缁忔祹", "璐告槗", "閫氳儉", "鍒╃巼", "鑲″競", "缇庡厓",
    "浜烘皯甯?, "GDP", "澶", "缇庤仈鍌?, "鍊哄姟", "璐㈡斂",
    "璐у竵鏀跨瓥", "渚涘簲閾?, "澶变笟", "鎶曡祫", "甯傚満", "鍑哄彛",
    "杩涘彛", "浜т笟", "鍒堕€?, "娑堣垂", "鐗╀环",
    "缁忔祹琛伴€€", "闄嶆伅", "鍔犳伅", "姹囩巼", "澶栨眹", "鍌ㄥ",
    "榛勯噾", "鐭虫补", "鍘熸补", "澶у畻鍟嗗搧", "鏈熻揣", "鍊哄埜",
    "鎴垮湴浜?, "鍩哄缓",
    "缇庡浗缁忔祹", "涓浗缁忔祹", "鍏ㄧ悆缁忔祹",
    "鏀跨瓥", "娉曟", "绔嬫硶", "娉曡", "鏀归潻", "琛屾斂浠?, "鏀垮簻",
    "璁細", "閫変妇", "鎶曠エ", "瀹硶", "鏈€楂樻硶闄?, "鎬荤粺", "鍥戒細",
    "鍐呴榿", "浠绘湡", "寮瑰娋", "杈炶亴", "涓婁换",
    "姘戜富鍏?, "鍏卞拰鍏?, "鍏氭淳",
    "鎬荤悊", "棣栫浉", "涓诲腑", "棰嗗浜?, "鏀挎潈",
    "绂佷护", "闄愬埗", "灏侀攣", "鍑哄彛绠″埗",
    "AI", "浜哄伐鏅鸿兘", "澶фā鍨?, "鏈哄櫒", "鑺墖", "鍗婂浣?, "5G",
    "6G", "閲忓瓙", "鑸ぉ", "鍗槦", "浜掕仈缃?, "绠楁硶", "鏁版嵁",
    "鏈哄櫒浜?, "鏂拌兘婧?, "鐢垫睜", "绉戞妧", "澶┖", "鍙戝皠",
    "鑷姩椹鹃┒", "鏁板瓧鍖?, "杞欢", "纭欢", "缃戠粶", "鐏",
    "绌洪棿绔?, "鎺㈡湀", "鐧绘湀", "鐏槦", "鎺㈡祴鍣?,
    "鍗庝负", "鑻规灉", "璋锋瓕", "寰蒋", "浜氶┈閫?, "鐗规柉鎷?,
    "鑻变紵杈?, "鑻辩壒灏?, "涓夋槦", "鍙扮Н鐢?,
    "鎿嶄綔绯荤粺", "浜戣绠?, "鏁版嵁涓績",
    "姘斿€欏彉鍖?, "纰充腑鍜?, "鎺掓斁",
    "鏍歌兘", "椋庤兘", "澶槼鑳?, "鍙啀鐢熻兘婧?,
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


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# RSS 婧愶紙鑻辨枃杩囨护 鈫?缈昏瘧 鈫?涓枃浜屾纭锛?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def fetch_rss(urls, source_name):
    """RSS 鎶撳彇锛屾墍鏈?URL 澶辫触鍚庤嚜鍔ㄥ洖閫€鍒?HTML 椤甸潰鎶撳彇"""
    target = yesterday().date()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    raw_items = []

    # 灏濊瘯 RSS锛堝涓鐢?URL锛?    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=8)
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
                print(f"  [{source_name}] RSS 鑾峰彇 {len(raw_items)} 鏉?)
                break
        except Exception as e:
            emsg = str(e)
            if "10061" in emsg or "actively refused" in emsg:
                print(f"  [{source_name}] 杩炴帴琚嫆({url[:50]})锛岃烦杩?)
            else:
                print(f"  [{source_name}] RSS 澶辫触({url[:50]}): {emsg[:60]}")

    # RSS 鍏ㄩ儴澶辫触 鈫?HTML 椤甸潰鎶撳彇鍥為€€
    if not raw_items:
        print(f"  [{source_name}] RSS 鍏ㄥけ璐ワ紝灏濊瘯 HTML 椤甸潰鎶撳彇...")
        from bs4 import BeautifulSoup
        for url in urls:
            try:
                base = url.split("/feed", 1)[0].rstrip("/")
                if "rss" in url or "xml" in url:
                    base = "/".join(url.split("/")[:3])
                r = requests.get(base, headers=headers, timeout=5)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                count = 0
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True)
                    if not text or len(text) < 15:
                        continue
                    full_url = href if href.startswith("http") else (
                        f"https:{href}" if href.startswith("//") else
                        f"{base.rstrip('/')}/{href.lstrip('/')}"
                    )
                    raw_items.append({
                        "title": text, "url": full_url, "summary": "",
                        "_date": None
                    })
                    count += 1
                    if count >= 30:
                        break
                if raw_items:
                    print(f"  [{source_name}] HTML 鎶撳彇 {len(raw_items)} 鏉?)
                    break
            except Exception as e:
                emsg = str(e)
                if "10061" in emsg or "actively refused" in emsg:
                    print(f"  [{source_name}] HTML 杩炴帴琚嫆锛岃烦杩?)
                    break  # 鏁翠釜鍩熷悕閮借澧欙紝涓嶅啀璇曞叾浠?URL
                print(f"  [{source_name}] HTML 鍥為€€澶辫触: {emsg[:60]}")
                continue

    if not raw_items:
        print(f"  [{source_name}] 鎵€鏈夋柟寮忓潎澶辫触锛岃烦杩?)
        return []

    strict_date = [i for i in raw_items if i["_date"] == target]
    candidates = strict_date if len(strict_date) >= 5 else raw_items
    candidates = dedup_and_sort(candidates, 15)

    matched = []
    for item in candidates:
        text = item["title"] + " " + item.get("summary", "")
        if matches_english(text, EN_TOPIC_KEYWORDS):
            matched.append(item)

    if not matched:
        print(f"  [{source_name}] 鑻辨枃鍏抽敭璇嶆棤鍖归厤")
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

    print(f"  [{source_name}] 涓婚鍖归厤 {len(final)} 鏉?)
    return final[:6]


def fetch_geopolitical():
    """The Diplomat 鈥?浜氬お鍦扮紭鏀挎不鍒嗘瀽"""
    return fetch_rss([
        "https://thediplomat.com/feed/",
        "https://thediplomat.com/feed.xml",
        "https://thediplomat.com/",
    ], "The Diplomat")


def fetch_wired():
    """Wired 鈥?绉戞妧"""
    return fetch_rss(["https://www.wired.com/feed/rss"], "Wired")


def fetch_cnn():
    return fetch_rss([
        "http://rss.cnn.com/rss/edition_world.rss",
        "http://rss.cnn.com/rss/edition.rss",
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "http://rss.cnn.com/rss/cnn_world.rss",
        "https://edition.cnn.com/services/rss/",
    ], "CNN")


def fetch_aljazeera():
    return fetch_rss([
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.aljazeera.com/xml/rss/news.xml",
        "https://www.aljazeera.com/",
    ], "鍗婂矝鐢佃鍙?)


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# HTML 婧愶紙涓浗锛?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

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
    """鏂板崕缃戝浗闄呮柊闂?(news.cn)"""
    return fetch_html_links(
        ["http://www.xinhuanet.com/world/"],
        lambda h: "news.cn" in h,
        yesterday(),
        min_len=10
    )


def fetch_globalecon():
    """瀵扮悆缁忔祹 - 涓浗缁忔祹缃戝浗闄呴閬?""
    return fetch_html_links(
        ["http://intl.ce.cn/", "http://intl.ce.cn/newm/hq/index_1.shtml"],
        lambda h: "ce.cn" in h,
        yesterday(),
        min_len=10
    )


def fetch_people():
    """浜烘皯缃戝浗闄呮柊闂?""
    return fetch_html_links(
        ["http://world.people.com.cn/"],
        lambda h: "people.com.cn" in h,
        yesterday(),
        min_len=12
    )


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 浠庢枃绔犻〉闈㈡姄鍙栨瑕?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def fetch_article_summary(url):
    """璁块棶鏂囩珷椤甸潰锛屾彁鍙栭娈典綔涓烘瑕?""
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
        # 鎵炬鏂囧尯鍩熶紭鍏堬細鎺掗櫎瀵艰埅銆侀〉鑴氱瓑
        for cls in ["rm_txt_con", "article-body", "article_content", "content",
                     "page_content", "articleContent", "news-content", "art_con"]:
            div = soup.find("div", class_=cls)
            if div:
                t = div.get_text(strip=True)
                if len(t) > 30:
                    return t[:150].replace("\n", " ").replace("\r", "")
        # 鍚庡锛氭壘绗竴涓暱鏂囨湰鐨?p 鏍囩
        for tag in soup.find_all("p"):
            t = tag.get_text(strip=True)
            if len(t) > 50:
                return t[:150].replace("\n", " ").replace("\r", "")
        # 鍚庡锛氭壘绗竴涓湁闀挎枃鏈殑鍧楃骇鍏冪礌锛堣烦杩囧鑸級
        for tag in soup.find_all(["div", "span"]):
            t = tag.get_text(strip=True)
            if len(t) > 50 and "棣栭〉" not in t[:20]:
                return t[:150].replace("\n", " ").replace("\r", "")
        return ""
    except Exception as e:
        print(f"  [鎽樿鎶撳彇] 澶辫触: {url[:50]} - {e}")
        return ""


def enrich_summaries(items):
    """涓烘墍鏈変腑鏂囨簮鏉＄洰浠庢枃绔犻〉闈㈡姄鍙栨瑕?""
    if not items:
        return items
    for item in items:
        url = item.get("url", "")
        if url:
            print(f"  [鎽樿] 鎶撳彇: {item['title'][:30]}...")
            item["summary"] = fetch_article_summary(url)
    return items


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 涓枃婧愪富棰樼瓫閫?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def filter_chinese(items):
    items = enrich_summaries(items)
    matched = []
    for item in items:
        text = item["title"] + " " + item.get("summary", "")
        if matches_chinese(text, CN_TOPIC_KEYWORDS):
            matched.append(item)
    return matched[:6]


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 鏍煎紡鍖?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def format_message(news_list, source_name):
    today_str = datetime.now().strftime("%Y-%m-%d %A")
    yesterday_str = yesterday().strftime("%Y-%m-%d")
    lines = [
        f"# 馃實 鍥介檯鏂伴椈鏃╂姤",
        f"**{today_str}** | 鏄ㄦ棩鏂伴椈 ({yesterday_str}) | {source_name}",
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
        "_姣忔棩涓婂崍8:00鑷姩鎺ㄩ€?| Powered by Server閰盻"
    ])
    return "\n".join(lines)


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 涓绘祦绋?# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def main():
    send_key = os.environ.get("SENDKEY")
    if not send_key:
        print("[ERROR] 鐜鍙橀噺 SENDKEY 鏈缃?)
        sys.exit(1)

    print(f"[INFO] 寮€濮嬫姄鍙栧墠涓€鏃ュ浗闄呮柊闂?..")

    sources = [
        ("鏂板崕缃?,       fetch_xinhua,       False),
        ("The Diplomat", fetch_geopolitical, True),
        ("瀵扮悆缁忔祹",     fetch_globalecon,   False),
        ("浜烘皯缃?,       fetch_people,       False),
        ("Wired",       fetch_wired,        True),
        ("CNN",         fetch_cnn,          True),
        ("鍗婂矝鐢佃鍙?,    fetch_aljazeera,    True),
    ]

    aggregated = []
    seen_titles = set()

    for name, fetcher, is_rss in sources:
        print(f"[INFO] 灏濊瘯 {name}...")
        news = fetcher()
        if not news:
            print(f"[INFO] {name} 鏃犵粨鏋?)
            continue

        if not is_rss:
            news = filter_chinese(news)

        if not news:
            print(f"[INFO] {name} 涓婚鍖归厤涓嶈冻")
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

        print(f"[OK] {name} 鍙?{count} 鏉?)

    if aggregated:
        print(f"[OK] 姹囨€?{len(aggregated)} 鏉?)
        content = format_message(aggregated, "澶氭簮姹囨€?)
        send_to_wechat("馃實 鍥介檯鏂伴椈鏃╂姤锛堟槰鏃ヨ闂伙級", content, send_key)
        return

    print(f"[FAIL] 鎵€鏈夋柊闂绘簮鍧囧け璐?)
    send_to_wechat(
        "馃實 鍥介檯鏂伴椈鏃╂姤",
        f"**{datetime.now().strftime('%Y-%m-%d')}**\n\n"
        "鈿狅笍 鏄ㄦ棩鏂伴椈鑾峰彇澶辫触锛岃妫€鏌ョ綉缁滄垨鏁版嵁婧愭槸鍚﹀彲鐢ㄣ€俓n\n"
        "_鑷姩鎺ㄩ€佸皢鍦ㄦ槑澶╅噸璇昣",
        send_key
    )


if __name__ == "__main__":
    main()
