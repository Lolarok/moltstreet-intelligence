#!/usr/bin/env python3
"""
MoltStreet RSS Aggregator
Fetches RSS feeds and posts to WordPress as drafts.
"""
import os
import sys
import json
import hashlib
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Install: pip install requests")
    sys.exit(1)

# ── WordPress Sites ────────────────────────────────────────────────────────
WP_SITES = {
    "ai": {
        "url": os.environ.get("WP_AI_URL", "https://ainotizieitalia.com"),
        "user": os.environ.get("WP_AI_USER", "admin"),
        "password": os.environ.get("WP_AI_PASSWORD", ""),
    },
    "basket": {
        "url": os.environ.get("WP_BASKET_URL", "https://basketitalia.com"),
        "user": os.environ.get("WP_BASKET_USER", "admin"),
        "password": os.environ.get("WP_BASKET_PASSWORD", ""),
    },
    "crypto": {
        "url": os.environ.get("WP_CRYPTO_URL", "https://cryptoanalisi.com"),
        "user": os.environ.get("WP_CRYPTO_USER", "admin"),
        "password": os.environ.get("WP_CRYPTO_PASSWORD", ""),
    },
}

# ── RSS Feeds per site ─────────────────────────────────────────────────────
FEEDS = {
    "ai": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    ],
    "basket": [
        "https://www.gazzetta.it/rss/basket.xml",
    ],
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://decrypt.co/feed",
    ],
}

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_cache.json")


def load_cache():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]


def fetch_rss(url):
    """Simple RSS fetcher using stdlib."""
    import urllib.request
    import xml.etree.ElementTree as ET

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MoltStreet-RSS/3.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read().decode())
    except Exception as e:
        print(f"  Feed error: {e}")
        return []

    items = []
    # RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()[:500]
        if title and link:
            items.append({"title": title, "link": link, "summary": desc, "source": url})
    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        title = (entry.findtext("atom:title", namespaces=ns) or "").strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        desc = (entry.findtext("atom:summary", namespaces=ns) or "").strip()[:500]
        if title and link:
            items.append({"title": title, "link": link, "summary": desc, "source": url})

    return items


def score_article(article, site_key):
    """Simple relevance scoring."""
    score = 50
    title = article["title"].lower()
    summary = article["summary"].lower()
    text = title + " " + summary

    if site_key == "ai":
        keywords = ["ai", "artificial intelligence", "machine learning", "llm", "gpt", "chatgpt", "openai"]
    elif site_key == "crypto":
        keywords = ["bitcoin", "ethereum", "crypto", "defi", "blockchain", "solana", "token"]
    elif site_key == "basket":
        keywords = ["basket", "nba", "serie a", "euroleague", "basketball"]
    else:
        keywords = []

    for kw in keywords:
        if kw in title: score += 15
        elif kw in summary: score += 8

    return min(100, score)


def post_to_wp(article, site_key):
    """Post article as draft to WordPress."""
    cfg = WP_SITES[site_key]
    if not cfg["password"]:
        return None

    src = article["source"]
    lnk = article["link"]
    content = f'<p><em>Fonte: <a href="{lnk}">{src}</a></em></p><p>{article["summary"]}...</p>'

    try:
        r = requests.post(
            f"{cfg['url']}/wp-json/wp/v2/posts",
            json={"title": article["title"], "content": content, "status": "draft"},
            auth=(cfg["user"], cfg["password"]),
            timeout=30,
        )
        r.raise_for_status()
        print(f"  POSTED: {article['title'][:60]}")
        return r.json().get("id")
    except Exception as e:
        print(f"  FAIL: {e}")
        return None


def run(site="all", max_posts=5, dry_run=False):
    print(f"MoltStreet RSS Aggregator | {datetime.now():%Y-%m-%d %H:%M}")
    cache = load_cache()
    sites = list(WP_SITES.keys()) if site == "all" else [site]
    total = 0

    for sk in sites:
        print(f"\n{sk.upper()}:")
        feeds = FEEDS.get(sk, [])
        articles = []
        for feed_url in feeds:
            articles.extend(fetch_rss(feed_url))

        scored = sorted(
            [(score_article(a, sk), a) for a in articles],
            key=lambda x: x[0],
            reverse=True,
        )

        n = 0
        for score, a in scored:
            if n >= max_posts or score < 40:
                continue
            uid = hash_url(a["link"])
            if uid in cache:
                continue

            print(f"  [{score}] {a['title'][:65]}")
            if not dry_run:
                pid = post_to_wp(a, sk)
                if pid:
                    cache[uid] = {"posted": datetime.now().isoformat(), "site": sk}
                    save_cache(cache)
                    n += 1
                    total += 1
                    time.sleep(2)
            else:
                n += 1
                total += 1

    print(f"\nDone: {total} articles")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="MoltStreet RSS Aggregator")
    p.add_argument("--site", default="all", choices=["all", "ai", "basket", "crypto"])
    p.add_argument("--max", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    run(a.site, a.max, a.dry_run)
