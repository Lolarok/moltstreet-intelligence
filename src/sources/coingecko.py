"""
MoltStreet Intelligence — CoinGecko Source
Prices, markets, trending coins.
"""
import time
from . import fetch_json

BASE = "https://api.coingecko.com/api/v3"


def get_coin_data(coin_ids: list[str], delay: float = 1.5) -> dict:
    """Fetch market data for a list of CoinGecko IDs.
    Returns dict keyed by coin id.
    """
    # Batch into groups of 50 (API limit)
    results = {}
    for i in range(0, len(coin_ids), 50):
        batch = coin_ids[i:i + 50]
        ids_str = ",".join(batch)
        url = (
            f"{BASE}/coins/markets?vs_currency=usd&ids={ids_str}"
            f"&order=market_cap_desc&per_page=50&page=1&sparkline=false"
            f"&price_change_percentage=7d,30d"
        )
        data = fetch_json(url)
        if data:
            for coin in data:
                results[coin["id"]] = coin
        if i + 50 < len(coin_ids):
            time.sleep(delay)
    return results


def get_trending() -> dict:
    """Fetch CoinGecko trending coins.
    Returns dict: {symbol_lower: score, name_lower: score}
    """
    data = fetch_json(f"{BASE}/search/trending")
    if not data:
        return {}
    trending = {}
    for i, item in enumerate(data.get("coins", [])[:10]):
        coin = item.get("item", {})
        score = 10 - i  # Higher rank = higher score
        sym = (coin.get("symbol", "")).lower()
        name = (coin.get("name", "")).lower()
        if sym:
            trending[sym] = score
        if name:
            trending[name] = score
    return trending


def get_global_fear_greed() -> tuple[int | None, int | None]:
    """Fetch Fear & Greed index from Alternative.me.
    Returns (current_value, 7d_trend).
    """
    data = fetch_json("https://api.alternative.me/fng/?limit=7")
    if not data or "data" not in data:
        return None, None
    values = [int(x["value"]) for x in data["data"]]
    current = values[0]
    trend = current - values[-1] if len(values) > 1 else 0
    return current, trend
