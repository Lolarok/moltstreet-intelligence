#!/usr/bin/env python3
"""
MoltStreet Intelligence v3.0
Unified crypto scanner — all signals, one tool.

Usage:
    python3 main.py                          # Scan watchlist
    python3 main.py --top 20                 # Top 20 results
    python3 main.py --sector ai              # Filter by sector
    python3 main.py --email                  # Send email alerts
    python3 main.py --json                   # JSON output
    python3 main.py --dashboard              # Generate dashboard data.json
    python3 main.py --min-tvl 1000000        # Min TVL filter (for sector scans)

Data: CoinGecko + DeFiLlama + GitHub + Fear & Greed
Cost: $0/month (GitHub Actions free tier)
"""
import sys
import os
import json
import argparse
import time
from datetime import datetime, timezone

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    WATCHLIST, SECTORS, GITHUB_REPOS,
    COINGECKO_DELAY, GITHUB_DELAY, ALERT_THRESHOLD, WATCH_THRESHOLD,
)
from src.sources.coingecko import get_coin_data, get_trending, get_global_fear_greed
from src.sources.defillama import get_tvl_data, get_dex_volumes, get_perp_volumes
from src.sources.github import get_all_github_activity
from src.scoring import compute_score, rating
from src.alerts import send_email_alert


def fusd(n: float) -> str:
    """Format as USD string."""
    if n >= 1e9: return f"${n / 1e9:.2f}B"
    if n >= 1e6: return f"${n / 1e6:.1f}M"
    if n >= 1e3: return f"${n / 1e3:.0f}K"
    return f"${n:.0f}"


def cpct(p: float) -> str:
    """Format percentage with emoji."""
    s = "🚀" if p > 50 else "📈" if p > 20 else "↗" if p > 0 else "↘" if p > -20 else "📉"
    return f"{s}{'+' if p > 0 else ''}{p:.1f}%"


def run_scan(sector: str = None, min_tvl: float = 0, top: int = 20) -> list[dict]:
    """Run the full scan pipeline. Returns scored results."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n⚡ MoltStreet Intelligence v3.0 — {now}\n")

    # ── Step 1: Fetch all data sources ────────────────────────────────
    print("[1/5] CoinGecko prices...")
    watchlist = WATCHLIST
    if sector and sector in SECTORS:
        # Filter to sector coins
        sector_ids = SECTORS[sector]
        watchlist = [w for w in WATCHLIST if w[0] in sector_ids]
        print(f"  Sector filter: {sector} → {len(watchlist)} coins from watchlist")

    coin_ids = [w[0] for w in watchlist]
    coin_data = get_coin_data(coin_ids, delay=COINGECKO_DELAY)
    print(f"  Got {len(coin_data)} coins")

    print("[2/5] DeFiLlama TVL + volumes...")
    tvl_data = get_tvl_data()
    dex_data = get_dex_volumes()
    perp_data = get_perp_volumes()
    print(f"  TVL: {len(tvl_data)} | DEX: {len(dex_data)} | Perp: {len(perp_data)}")

    print("[3/5] Fear & Greed index...")
    fg_value, fg_trend = get_global_fear_greed()
    fg_label = (
        "Extreme Fear" if fg_value and fg_value < 25 else
        "Fear" if fg_value and fg_value < 45 else
        "Neutral" if fg_value and fg_value < 56 else
        "Greed" if fg_value and fg_value < 75 else
        "Extreme Greed"
    ) if fg_value else "Unknown"
    print(f"  F&G: {fg_value} ({fg_label}) | Trend: {fg_trend:+d}/wk")

    print("[4/5] GitHub activity...")
    gh_data = get_all_github_activity(GITHUB_REPOS, delay=GITHUB_DELAY)
    print(f"  Got activity for {len(gh_data)} repos")

    print("[5/5] CoinGecko trending...")
    trending = get_trending()
    print(f"  {len(trending)} trending terms\n")

    # ── Step 2: Score everything ──────────────────────────────────────
    results = []
    for cg_id, symbol, category, note in watchlist:
        cd = coin_data.get(cg_id)
        if not cd:
            print(f"  [SKIP] {symbol} — no data")
            continue

        sym_upper = symbol.upper()
        tvl_info = tvl_data.get(sym_upper, {})
        gh_info = gh_data.get(sym_upper)

        score, breakdown = compute_score(cd, tvl_info, gh_info, fg_value)

        # Build signals list (human-readable reasons)
        signals = []
        p24 = cd.get("price_change_percentage_24h", 0) or 0
        p7 = cd.get("price_change_percentage_7d_in_currency", 0) or 0
        p30 = cd.get("price_change_percentage_30d_in_currency", 0) or 0
        ath = cd.get("ath_change_percentage", 0) or 0
        vol = cd.get("total_volume", 0) or 0
        mcap = cd.get("market_cap", 0) or 0

        if p24 > 5: signals.append(f"24h+{p24:.0f}%")
        if p7 > 10: signals.append(f"7d+{p7:.0f}%")
        if p30 > 20: signals.append(f"30d+{p30:.0f}%")
        if ath < -75: signals.append(f"ATH-{abs(ath):.0f}%")
        if mcap > 0 and vol / mcap > 0.15: signals.append(f"Vol/MC:{vol/mcap:.2f}")
        tvl = tvl_info.get("tvl", 0)
        if tvl > 1e9: signals.append(f"TVL${tvl/1e9:.1f}B")
        tvl_chg = tvl_info.get("tvl_change_7d", 0)
        if tvl_chg > 15: signals.append(f"TVL+{tvl_chg:.0f}%/7d")
        if gh_info and gh_info.get("commits_4w", 0) > 50: signals.append(f"GH:{gh_info['commits_4w']}commits/4w")

        results.append({
            "symbol": symbol,
            "category": category,
            "note": note,
            "score": score,
            "rating": rating(score),
            "signals": signals,
            "breakdown": breakdown,
            "price": cd.get("current_price", 0) or 0,
            "p24": p24,
            "p7": p7,
            "p30": p30,
            "ath_drop": ath,
            "mcap": mcap,
            "volume": vol,
            "tvl": tvl,
            "tvl_change_7d": tvl_chg,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def print_results(results: list[dict], top: int = 20):
    """Print formatted results to console."""
    results = results[:top]
    print(f"{'SYM':<10} {'SCORE':>6} {'PRICE':>12} {'24H':>8} {'7D':>8} {'30D':>8} {'SIGNAL':<14}")
    print("-" * 75)
    for r in results:
        print(
            f"{r['symbol']:<10} {r['score']:>5}  ${r['price']:>11,.4f}"
            f"  {r['p24']:>+7.1f}%  {r['p7']:>+7.1f}%  {r['p30']:>+7.1f}%"
            f"  {r['rating']}"
        )

    hot = [r for r in results if r["score"] >= ALERT_THRESHOLD]
    print(f"\n⚡ HIGH SIGNAL: {len(hot)} project(s)")
    for r in hot:
        print(f"  {r['symbol']}: {', '.join(r['signals'][:4])}")


def generate_dashboard(results: list[dict], fg_data: dict, output_path: str):
    """Generate data.json for the dashboard."""
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fear_greed": fg_data,
        "projects": [
            {
                "symbol": r["symbol"],
                "score": r["score"],
                "rating": r["rating"],
                "price": r["price"],
                "mcap_m": r["mcap"] / 1e6,
                "p7d": r["p7"],
                "ath_chg": r["ath_drop"],
                "volume": r["volume"],
                "tvl": r["tvl"],
                "breakdown": r["breakdown"],
                "signals": r["signals"],
            }
            for r in results
        ],
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n📊 Dashboard data saved → {output_path}")


def generate_curated(signalhub_public_path: str):
    """Generate curated.json for SignalHub from config watchlist + sectors."""
    from src.config import WATCHLIST, SECTORS

    # Map sector keys to labels + emojis
    sector_meta = {
        "perp":       {"label": "Perps",       "emoji": "📊"},
        "ai":         {"label": "AI",          "emoji": "🧠"},
        "rwa":        {"label": "RWA",         "emoji": "🏦"},
        "dex":        {"label": "DEX",         "emoji": "🔄"},
        "stablecoin": {"label": "Stablecoins", "emoji": "💵"},
        "yield":      {"label": "Yield",       "emoji": "🌾"},
        "l1":         {"label": "L1s",         "emoji": "⛓️"},
        "ai-social":  {"label": "AI Social",   "emoji": "🤖"},
        "l2":         {"label": "L2s",         "emoji": "📦"},
        "restaking":  {"label": "Restaking",   "emoji": "🔒"},
        "depin-ai":   {"label": "DePIN/AI",    "emoji": "📡"},
    }

    watchlist = [
        {"id": cid, "symbol": sym, "sector": cat, "thesis": note}
        for cid, sym, cat, note in WATCHLIST
    ]

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "watchlist": watchlist,
        "sectors": sector_meta,
    }

    os.makedirs(os.path.dirname(signalhub_public_path), exist_ok=True)
    with open(signalhub_public_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n🎯 Curated watchlist saved → {signalhub_public_path}")


def generate_analysis(results: list[dict], output_path: str):
    """Run AI agent analysis and save to JSON."""
    try:
        from src.agent import generate_analysis as agent_analyze
    except ImportError:
        print("⚠️  Agent module not found. Skipping AI analysis.")
        return

    scan_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "projects": results,
    }
    agent_analyze(scan_data, output_path)


def main():
    parser = argparse.ArgumentParser(description="MoltStreet Intelligence v3.0")
    parser.add_argument("--top", type=int, default=20, help="Number of results to show")
    parser.add_argument("--sector", type=str, choices=list(SECTORS.keys()), help="Filter by sector")
    parser.add_argument("--email", action="store_true", help="Send email alerts for high signals")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--dashboard", action="store_true", help="Generate dashboard data.json")
    parser.add_argument("--curated", action="store_true", help="Generate curated.json for SignalHub")
    parser.add_argument("--agent", action="store_true", help="Run AI analysis agent")
    parser.add_argument("--signalhub", type=str, help="Path to SignalHub public/ dir (for --curated)")
    parser.add_argument("--min-tvl", type=float, default=0, help="Min TVL filter")
    args = parser.parse_args()

    results = run_scan(sector=args.sector, min_tvl=args.min_tvl, top=args.top)

    if args.json:
        print(json.dumps(results[:args.top], indent=2))
        return

    print_results(results, top=args.top)

    fg_value, fg_trend = get_global_fear_greed()
    fg_label = "Unknown"
    if fg_value:
        if fg_value < 25: fg_label = "Extreme Fear"
        elif fg_value < 45: fg_label = "Fear"
        elif fg_value < 56: fg_label = "Neutral"
        elif fg_value < 75: fg_label = "Greed"
        else: fg_label = "Extreme Greed"
    fg_data = {"index": fg_value, "trend": fg_trend, "label": fg_label}

    if args.email:
        send_email_alert(results, fg_data)

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if args.dashboard:
        dashboard_path = os.path.join(base, "dashboard", "data.json")
        generate_dashboard(results, fg_data, dashboard_path)

    if args.curated:
        # Default: sibling signalhub/public/ directory
        signalhub_path = args.signalhub or os.path.join(
            os.path.dirname(base), "signalhub", "public", "curated.json"
        )
        generate_curated(signalhub_path)

    if args.agent:
        analysis_path = os.path.join(base, "dashboard", "analysis.json")
        generate_analysis(results, analysis_path)


if __name__ == "__main__":
    main()
