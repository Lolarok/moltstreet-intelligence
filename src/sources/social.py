"""
MoltStreet Intelligence — Social Signals Source
Searches Reddit public JSON for community sentiment on watchlist coins.
No API keys required. Free, like the rest of the project.

Inspired by last30days-skill's multi-source scoring architecture.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import math
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "MoltStreet/3.0 (intelligence scanner)",
    "Accept": "application/json",
}

# Subreddits to search (in order of relevance)
CRYPTO_SUBREDDITS = [
    "CryptoCurrency",
    "CryptoMarkets",
    "altcoin",
    "defi",
    "solana",
    "ethereum",
    "CryptoMoonShots",
    "SatoshiStreetBets",
]

# Subreddit-specific searches (map coin symbols to relevant subs)
COIN_SUBREDDITS = {
    "SOL": ["solana"],
    "ETH": ["ethereum", "ethfinance"],
    "BTC": ["bitcoin", "btc"],
    "HYPE": ["HyperliquidDEX"],
    "JUP": ["jup_ag"],
    "ONDO": ["OndoFinance"],
    "TAO": ["bittensor_"],
    "ENA": ["ethena_labs"],
    "PENDLE": ["Pendle_Finance"],
    "STRK": ["starknet"],
    "EIGEN": ["eigenlayer"],
}


def fetch_json(url: str, timeout: int = 15) -> dict | list | None:
    """Fetch JSON from URL."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def search_reddit(query: str, subreddit: str = None, limit: int = 25,
                  sort: str = "relevance", time_filter: str = "month") -> list[dict]:
    """Search Reddit using public JSON endpoint.
    
    Args:
        query: Search query
        subreddit: Restrict to specific subreddit (None = all)
        limit: Max results
        sort: Sort method (relevance, hot, top, new, comments)
        time_filter: Time window (hour, day, week, month, year, all)
    
    Returns:
        List of thread dicts with engagement data.
    """
    if subreddit:
        base = f"https://www.reddit.com/r/{subreddit}/search.json"
    else:
        base = "https://www.reddit.com/search.json"

    params = urllib.parse.urlencode({
        "q": query,
        "sort": sort,
        "t": time_filter,
        "limit": min(limit, 100),
        "restrict_sr": "true" if subreddit else "false",
        "raw_json": 1,
    })

    url = f"{base}?{params}"
    data = fetch_json(url)
    if not data or "data" not in data:
        return []

    threads = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        if not post.get("title"):
            continue

        created = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
        age_days = (datetime.now(timezone.utc) - created).total_seconds() / 86400

        threads.append({
            "title": post.get("title", ""),
            "subreddit": post.get("subreddit", ""),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "upvote_ratio": post.get("upvote_ratio", 0.5),
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "created_utc": post.get("created_utc", 0),
            "age_days": age_days,
            "selftext_preview": (post.get("selftext", "") or "")[:200],
            "author": post.get("author", ""),
            "flair": post.get("link_flair_text", ""),
            "is_self": post.get("is_self", False),
            "domain": post.get("domain", ""),
        })

    return threads


def search_coin_social(coin_symbol: str, coin_name: str = None,
                       delay: float = 0.8) -> dict:
    """Search Reddit for social signals about a specific coin.
    
    Args:
        coin_symbol: Ticker symbol (e.g., "SOL")
        coin_name: Full name (e.g., "Solana") — used for broader search
        delay: Seconds between requests to avoid rate limiting
    
    Returns:
        Dict with social metrics and top threads.
    """
    all_threads = []
    queries_searched = []

    # Build search queries
    queries = [coin_symbol]
    if coin_name:
        queries.append(coin_name)

    # 1. Search coin-specific subreddits first (highest signal)
    coin_subs = COIN_SUBREDDITS.get(coin_symbol, [])
    for sub in coin_subs:
        threads = search_reddit(
            query=coin_symbol,
            subreddit=sub,
            limit=15,
            sort="top",
            time_filter="month"
        )
        all_threads.extend(threads)
        queries_searched.append(f"r/{sub}:{coin_symbol}")
        time.sleep(delay)

    # 2. Search general crypto subreddits
    for sub in CRYPTO_SUBREDDITS[:4]:  # Top 4 general subs
        threads = search_reddit(
            query=coin_symbol,
            subreddit=sub,
            limit=10,
            sort="relevance",
            time_filter="month"
        )
        all_threads.extend(threads)
        queries_searched.append(f"r/{sub}:{coin_symbol}")
        time.sleep(delay)

    # 3. If we have a name, search with it too (catches discussions using full name)
    if coin_name:
        threads = search_reddit(
            query=coin_name,
            subreddit="CryptoCurrency",
            limit=10,
            sort="relevance",
            time_filter="month"
        )
        all_threads.extend(threads)
        queries_searched.append(f"r/CryptoCurrency:{coin_name}")
        time.sleep(delay)

    # Deduplicate by URL
    seen_urls = set()
    unique_threads = []
    for t in all_threads:
        if t["url"] not in seen_urls:
            seen_urls.add(t["url"])
            unique_threads.append(t)

    # Filter to last 30 days only
    recent = [t for t in unique_threads if t["age_days"] <= 30]

    # Compute engagement metrics
    if not recent:
        return {
            "total_threads": 0,
            "total_score": 0,
            "total_comments": 0,
            "avg_score": 0,
            "avg_ratio": 0,
            "top_score": 0,
            "sentiment_signal": 50,  # Neutral
            "engagement_signal": 0,
            "social_score": 0,
            "top_threads": [],
            "queries": queries_searched,
        }

    total_score = sum(t["score"] for t in recent)
    total_comments = sum(t["num_comments"] for t in recent)
    avg_ratio = sum(t["upvote_ratio"] for t in recent) / len(recent)
    top_score = max(t["score"] for t in recent)

    # Sentiment signal based on upvote ratio
    # >0.85 = very positive, <0.5 = controversial/negative
    sentiment_signal = int(avg_ratio * 100)

    # Engagement signal (log-scaled, like last30days)
    engagement_raw = (
        0.50 * math.log1p(total_score) +
        0.35 * math.log1p(total_comments) +
        0.15 * math.log1p(len(recent))
    )

    # Normalize engagement to 0-100 scale
    # Rough calibration: log1p(500) ≈ 6.2 → high engagement
    engagement_signal = min(100, int(engagement_raw * 18))

    # Composite social score
    social_score = int(
        0.40 * engagement_signal +
        0.30 * sentiment_signal +
        0.30 * min(100, len(recent) * 10)  # Volume of discussion
    )

    # Sort top threads by score
    top_threads = sorted(recent, key=lambda t: t["score"], reverse=True)[:5]

    return {
        "total_threads": len(recent),
        "total_score": total_score,
        "total_comments": total_comments,
        "avg_score": round(total_score / len(recent), 1),
        "avg_ratio": round(avg_ratio, 3),
        "top_score": top_score,
        "sentiment_signal": sentiment_signal,
        "engagement_signal": engagement_signal,
        "social_score": min(100, social_score),
        "top_threads": [
            {
                "title": t["title"],
                "subreddit": t["subreddit"],
                "score": t["score"],
                "comments": t["num_comments"],
                "url": t["url"],
                "age_days": round(t["age_days"], 1),
            }
            for t in top_threads
        ],
        "queries": queries_searched,
    }


def get_social_batch(symbols: list[str], name_map: dict = None,
                     delay: float = 0.8) -> dict:
    """Search social signals for multiple coins.
    
    Args:
        symbols: List of ticker symbols
        name_map: Optional {symbol: full_name} mapping
        delay: Seconds between coin searches
    
    Returns:
        Dict keyed by symbol with social metrics.
    """
    results = {}
    for i, sym in enumerate(symbols):
        name = (name_map or {}).get(sym)
        print(f"    Scanning r/{sym}...", end="", flush=True)
        data = search_coin_social(sym, name, delay=delay)
        threads_found = data["total_threads"]
        score = data["social_score"]
        print(f" {threads_found} threads, social score: {score}")
        results[sym.upper()] = data

        # Rate limit: pause between coins (Reddit is strict)
        if i < len(symbols) - 1:
            time.sleep(delay * 2)

    return results
