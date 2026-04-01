"""
MoltStreet Intelligence — Configuration
All tunable parameters in one place.
"""

# ── Watchlist ──────────────────────────────────────────────────────────────
# (coingecko_id, symbol, category, thesis)
WATCHLIST = [
    ("hyperliquid",             "HYPE",   "perp",       "Dominant perp DEX, real revenue, bear-resilient"),
    ("bittensor",               "TAO",    "ai",         "AI compute marketplace, subnet growth"),
    ("ondo-finance",            "ONDO",   "rwa",        "RWA leader, BlackRock ties, institutional push"),
    ("jupiter-exchange-solana", "JUP",    "dex",        "Solana #1 DEX aggregator, deep value"),
    ("ethena",                  "ENA",    "stablecoin", "USDe yield stablecoin"),
    ("pendle",                  "PENDLE", "yield",      "Yield tokenization pioneer, DeFi primitive"),
    ("berachain-bera",          "BERA",   "l1",         "Novel PoL consensus, strong DeFi ecosystem"),
    ("kaito",                   "KAITO",  "ai-social",  "AI info marketplace, early momentum"),
    ("starknet",                "STRK",   "l2",         "ZK rollup L2, Ethereum scaling"),
    ("eigenlayer",              "EIGEN",  "restaking",  "Restaking pioneer, ETH security layer"),
    ("sonic-3",                 "S",      "l1",         "High-perf EVM L1, DeFi ecosystem"),
    ("grass",                   "GRASS",  "depin-ai",   "DePIN/AI data network"),
    ("resolv",                  "RESOLV", "stablecoin", "Delta-neutral stablecoin, micro-cap"),
    ("drift-protocol",          "DRIFT",  "perp",       "Solana perp DEX, institutional grade"),
]

# ── Sector Filters (for alpha_hunter mode) ────────────────────────────────
SECTORS = {
    "perp":  ["hyperliquid", "gmx", "dydx", "vertex", "aevo", "drift-protocol", "jupiter-exchange-solana"],
    "rwa":   ["ondo-finance", "maple", "centrifuge", "superstate", "backed", "clearpool", "goldfinch"],
    "ai":    ["bittensor", "fetch-ai", "singularitynet", "allora", "ritual", "autonolas", "kaito", "grass"],
    "l2":    ["starknet", "arbitrum", "optimism", "zksync", "scroll", "blast", "taiko"],
    "defi":  ["aave", "uniswap", "lido", "eigenlayer", "pendle", "ethena", "sky", "morpho"],
    "infra": ["chainlink", "pyth", "wormhole", "layerzero", "axelar", "hyperlane"],
    "l1":    ["berachain-bera", "sonic-3", "sui", "solana", "avalanche-2", "near"],
}

# ── Scoring Weights (must sum to 1.0) ─────────────────────────────────────
WEIGHTS = {
    "momentum_24h":    0.08,
    "momentum_7d":     0.12,
    "momentum_30d":    0.08,
    "ath_discount":    0.12,
    "volume_mcap":     0.08,
    "tvl_level":       0.05,
    "tvl_change_7d":   0.08,
    "fear_greed":      0.05,
    "github_activity": 0.09,
    "mcap_upside":     0.08,
    "social":          0.17,  # Reddit engagement + sentiment
}

# ── Thresholds ─────────────────────────────────────────────────────────────
ALERT_THRESHOLD = 65      # Score >= this = ALERT
WATCH_THRESHOLD = 50      # Score >= this = WATCH
STRONG_BUY      = 78      # Score >= this = STRONG BUY

# ── API Settings ───────────────────────────────────────────────────────────
COINGECKO_DELAY   = 1.5   # Seconds between CoinGecko calls (rate limit)
GITHUB_DELAY      = 0.5   # Seconds between GitHub calls
REQUEST_TIMEOUT   = 20    # HTTP timeout in seconds
MAX_RETRIES       = 3     # Retry failed requests

# ── Email (override with env vars) ────────────────────────────────────────
EMAIL_FROM = "italiamolt5@gmail.com"
EMAIL_TO   = "italiamolt5@gmail.com"
# SMTP_PASSWORD or Mail_apppassword env var

# ── GitHub (optional, increases rate limit) ───────────────────────────────
# GITHUB_TOKEN env var

# ── Protocol Repos for GitHub Activity ────────────────────────────────────
GITHUB_REPOS = {
    "HYPE":   "hyperliquid-dex/node",
    "ONDO":   "",
    "PENDLE": "pendle-finance/pendle-core-v2-public",
    "JUP":    "",
    "KAITO":  "",
    "GRASS":  "",
    "DRIFT":  "drift-labs/protocol-v2",
    "BERA":   "berachain/beacon-kit",
    "ENA":    "",
    "STRK":   "starkware-libs/starknet",
    "EIGEN":  "Layr-Labs/eigenlayer-contracts",
    "S":      "",
    "TAO":    "opentensor/bittensor",
    "RESOLV": "",
}
