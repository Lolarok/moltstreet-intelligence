"""
MoltStreet Intelligence — DeFiLlama Source
TVL data, DEX volumes, perp volumes.
"""
from . import fetch_json

BASE = "https://api.llama.fi"


def get_tvl_data() -> dict:
    """Fetch TVL for all protocols.
    Returns dict keyed by symbol: {tvl, tvl_change_7d}
    """
    data = fetch_json(f"{BASE}/protocols")
    if not data:
        return {}
    out = {}
    for p in data:
        sym = (p.get("symbol") or "").upper()
        if sym:
            out[sym] = {
                "tvl": p.get("tvl", 0) or 0,
                "tvl_change_7d": p.get("change_7d", 0) or 0,
            }
    return out


def get_dex_volumes() -> dict:
    """Fetch 24h DEX volumes.
    Returns dict keyed by lowercase name: {vol_24h, change_7d}
    """
    url = (
        f"{BASE}/overview/dexs"
        f"?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=true"
    )
    data = fetch_json(url)
    if not data:
        return {}
    out = {}
    for p in data.get("protocols", []):
        name = (p.get("name", "")).lower()
        out[name] = {
            "vol_24h": p.get("total24h", 0) or 0,
            "change_7d": p.get("change_7d", 0) or 0,
        }
    return out


def get_perp_volumes() -> dict:
    """Fetch 24h perpetual DEX volumes.
    Returns dict keyed by lowercase name: {vol_24h, change_7d}
    """
    url = (
        f"{BASE}/overview/derivatives"
        f"?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=true"
    )
    data = fetch_json(url)
    if not data:
        return {}
    out = {}
    for p in data.get("protocols", []):
        name = (p.get("name", "")).lower()
        out[name] = {
            "vol_24h": p.get("total24h", 0) or 0,
            "change_7d": p.get("change_7d", 0) or 0,
        }
    return out
