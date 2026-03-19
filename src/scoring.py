"""
MoltStreet Intelligence — Scoring Engine
Combines all signals into a 0-100 composite score.
"""
from src.config import WEIGHTS, GITHUB_REPOS


def clamp(value: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, value))


def score_momentum_24h(pct: float) -> float:
    """Score 24h price change. Range: 0-100."""
    if pct > 10:  return 90
    if pct > 5:   return 75
    if pct > 2:   return 60
    if pct > 0:   return 50
    if pct > -2:  return 40
    if pct > -5:  return 25
    if pct > -10: return 10
    return 0


def score_momentum_7d(pct: float) -> float:
    """Score 7d price change. Range: 0-100."""
    if pct > 30:  return 95
    if pct > 20:  return 85
    if pct > 10:  return 70
    if pct > 5:   return 55
    if pct > 0:   return 45
    if pct > -5:  return 35
    if pct > -10: return 20
    if pct > -20: return 10
    return 0


def score_momentum_30d(pct: float) -> float:
    """Score 30d price change. Range: 0-100."""
    if pct > 50:  return 95
    if pct > 30:  return 80
    if pct > 15:  return 65
    if pct > 5:   return 50
    if pct > 0:   return 40
    if pct > -15: return 25
    if pct > -30: return 10
    return 0


def score_ath_discount(pct_from_ath: float) -> float:
    """Score distance from ATH (negative = below ATH). Range: 0-100.
    Deeper discount = higher score (contrarian value).
    """
    d = abs(pct_from_ath)
    if d > 95:  return 95
    if d > 90:  return 85
    if d > 75:  return 70
    if d > 50:  return 50
    if d > 30:  return 30
    if d > 15:  return 15
    return 5


def score_volume_mcap(volume: float, mcap: float) -> float:
    """Score volume/market cap ratio. Range: 0-100."""
    if mcap <= 0 or volume <= 0:
        return 10
    ratio = volume / mcap
    if ratio > 0.50: return 95
    if ratio > 0.30: return 85
    if ratio > 0.15: return 70
    if ratio > 0.08: return 50
    if ratio > 0.03: return 30
    return 10


def score_tvl_level(tvl: float) -> float:
    """Score TVL level. Range: 0-100."""
    if tvl > 10e9:  return 90
    if tvl > 1e9:   return 75
    if tvl > 500e6: return 60
    if tvl > 100e6: return 45
    if tvl > 10e6:  return 25
    return 10


def score_tvl_change_7d(pct: float) -> float:
    """Score TVL 7d change. Range: 0-100."""
    if pct > 50:  return 95
    if pct > 20:  return 80
    if pct > 10:  return 65
    if pct > 0:   return 50
    if pct > -10: return 30
    if pct > -20: return 15
    return 5


def score_fear_greed(value: int | None) -> float:
    """Score Fear & Greed (contrarian — extreme fear = high score). Range: 0-100."""
    if value is None:
        return 50  # Neutral if no data
    # Invert: low F&G = high score (buy when others fear)
    return clamp(100 - value, 0, 100)


def score_github_activity(commits_4w: int, stars: int) -> float:
    """Score GitHub activity. Range: 0-100."""
    # Commits component (0-60)
    if commits_4w > 200: c = 60
    elif commits_4w > 100: c = 50
    elif commits_4w > 50: c = 40
    elif commits_4w > 20: c = 30
    elif commits_4w > 5: c = 15
    else: c = 5

    # Stars component (0-40)
    if stars > 10000: s = 40
    elif stars > 5000: s = 30
    elif stars > 1000: s = 20
    elif stars > 100: s = 10
    else: s = 5

    return clamp(c + s, 0, 100)


def score_mcap_upside(mcap: float) -> float:
    """Score market cap upside potential (smaller = more upside). Range: 0-100."""
    m = mcap / 1e6  # Convert to millions
    if m < 50:    return 95
    if m < 100:   return 85
    if m < 250:   return 70
    if m < 500:   return 55
    if m < 1000:  return 40
    if m < 5000:  return 25
    return 10


def compute_score(coin_data: dict, tvl_info: dict, gh_data: dict | None,
                  fg_value: int | None) -> tuple[float, dict]:
    """Compute composite score for a coin.
    Returns (score_0_100, breakdown_dict).
    """
    p24 = coin_data.get("price_change_percentage_24h", 0) or 0
    p7 = coin_data.get("price_change_percentage_7d_in_currency", 0) or 0
    p30 = coin_data.get("price_change_percentage_30d_in_currency", 0) or 0
    ath = coin_data.get("ath_change_percentage", 0) or 0
    vol = coin_data.get("total_volume", 0) or 0
    mcap = coin_data.get("market_cap", 0) or 0
    tvl = tvl_info.get("tvl", 0) if tvl_info else 0
    tvl_7d = tvl_info.get("tvl_change_7d", 0) if tvl_info else 0

    gh_commits = gh_data.get("commits_4w", 0) if gh_data else 0
    gh_stars = gh_data.get("stars", 0) if gh_data else 0

    # Individual scores
    scores = {
        "momentum_24h":    score_momentum_24h(p24),
        "momentum_7d":     score_momentum_7d(p7),
        "momentum_30d":    score_momentum_30d(p30),
        "ath_discount":    score_ath_discount(ath),
        "volume_mcap":     score_volume_mcap(vol, mcap),
        "tvl_level":       score_tvl_level(tvl),
        "tvl_change_7d":   score_tvl_change_7d(tvl_7d),
        "fear_greed":      score_fear_greed(fg_value),
        "github_activity": score_github_activity(gh_commits, gh_stars),
        "mcap_upside":     score_mcap_upside(mcap),
    }

    # Weighted composite
    composite = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

    # Build readable breakdown
    breakdown = {}
    for k, v in scores.items():
        breakdown[k] = round(v, 1)

    return round(clamp(composite), 1), breakdown


def rating(score: float) -> str:
    from src.config import ALERT_THRESHOLD, WATCH_THRESHOLD, STRONG_BUY
    if score >= STRONG_BUY:      return "STRONG BUY"
    if score >= ALERT_THRESHOLD: return "ALERT"
    if score >= WATCH_THRESHOLD: return "WATCH"
    if score >= 35:              return "CAUTION"
    return "HOLD"
