# MoltStreet Intelligence v3.0

**Unified crypto scanner — all signals, one tool.**

Combines the best of `moltstreet-tools` and `crypto-early-radar` into a single, production-ready scanner.

## 🚀 Come farlo partire (passo-passo)

### Prerequisiti
- **Python 3.10+** ([download](https://python.org))
- **Git**

### Passo 1: Clona il repository
```bash
git clone https://github.com/Lolarok/moltstreet-intelligence.git
cd moltstreet-intelligence
```

### Passo 2: (Opzionale) GitHub token per rate limits migliori
```bash
export GITHUB_TOKEN=your_github_pat
```
Senza token: 60 richieste/ora. Con token: 5,000/ora.

### Passo 3: Esegui lo scanner
```bash
# Scan base
python3 src/main.py

# Top 10 con dashboard HTML
python3 src/main.py --top 10 --dashboard

# Filtra per settore
python3 src/main.py --sector ai

# Output JSON
python3 src/main.py --json
```

### Passo 4: Apri la dashboard
```bash
# Dopo aver generato i dati con --dashboard
open dashboard/index.html
# Mac: open dashboard/index.html
# Windows: start dashboard/index.html
# Linux: xdg-open dashboard/index.html
```

### Passo 5: Email alerts (opzionale)
```bash
export MAIL_APPPASSWORD=your_gmail_app_password
python3 src/main.py --email
```

### Nessuna dipendenza da installare!
Tutto usa Python stdlib + API gratuite. Zero pip install.

---

## What It Does

Every day, the scanner:
1. Fetches live prices from **CoinGecko** (free API)
2. Fetches TVL + DEX/perp volumes from **DeFiLlama** (free API)
3. Checks **Fear & Greed** index (contrarian signal)
4. Measures **GitHub activity** (dev commits + stars)
5. Detects **trending coins** on CoinGecko
6. Scores each project 0-100 with a weighted multi-factor model
7. Generates a **live dashboard** + **email alerts**

## Signals

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| 24h Momentum | 10% | Short-term price direction |
| 7d Momentum | 15% | Near-term trend |
| 30d Momentum | 10% | Sustained movement |
| ATH Discount | 15% | Value vs all-time high (contrarian) |
| Volume/MCap | 10% | Genuine trading interest |
| TVL Level | 5% | DeFi capital deployed |
| TVL Change 7d | 10% | DeFi growth momentum |
| Fear & Greed | 5% | Market sentiment (contrarian) |
| GitHub Activity | 10% | Developer health |
| MCap Upside | 10% | Small cap = asymmetric returns |

**Ratings:** 78+ = STRONG BUY | 65+ = ALERT | 50+ = WATCH | <50 = HOLD

## Quick Start

```bash
# Scan your watchlist
python3 src/main.py

# Top 10 with dashboard
python3 src/main.py --top 10 --dashboard

# Sector filter + email
python3 src/main.py --sector ai --email

# JSON output
python3 src/main.py --json
```

## Dashboard

```bash
# Generate data.json
python3 src/main.py --dashboard

# Open dashboard
open dashboard/index.html
```

The dashboard auto-refreshes from `dashboard/data.json`. Features:
- Fear & Greed widget
- Category filters (perps, L1s, L2s, DeFi, AI, RWA, etc.)
- Sortable columns
- Score breakdown per project

## Automation (GitHub Actions)

Runs daily at 07:00 UTC. Requires one secret:

1. Go to **Settings > Secrets > Actions**
2. Add `MAIL_APPPASSWORD` (Gmail app password for alerts)
3. Push to GitHub — it runs automatically

## Configuration

All settings in `src/config.py`:

- **WATCHLIST** — coins to scan
- **WEIGHTS** — scoring model weights (must sum to 1.0)
- **SECTORS** — category filters
- **GITHUB_REPOS** — protocol repos for activity tracking
- **ALERT_THRESHOLD** / **WATCH_THRESHOLD** — score cutoffs

## RSS Aggregator

Separate tool for auto-posting to WordPress:

```bash
# Post to all sites
python3 rss/aggregator.py

# Dry run
python3 rss/aggregator.py --dry-run --site crypto
```

Requires env vars: `WP_AI_URL`, `WP_AI_USER`, `WP_AI_PASSWORD` (per site).

## Data Sources

| Source | Data | Cost |
|--------|------|------|
| CoinGecko | Prices, markets, trending | Free (10-30 calls/min) |
| DeFiLlama | TVL, DEX volumes, perp volumes | Free (unlimited) |
| Alternative.me | Fear & Greed index | Free |
| GitHub API | Commit activity, stars | Free (60/hr unauthenticated, 5000/hr with token) |

**Total cost: $0/month**

## Structure

```
moltstreet-intelligence/
├── src/
│   ├── config.py          ← watchlist, weights, thresholds
│   ├── sources/
│   │   ├── coingecko.py   ← prices, markets, trending
│   │   ├── defillama.py   ← TVL, DEX/perp volumes
│   │   ├── github.py      ← commits + stars
│   │   └── feargreed.py   ← Fear & Greed index
│   ├── scoring.py         ← weighted scoring engine
│   ├── alerts.py          ← email alerts
│   └── main.py            ← CLI orchestrator
├── dashboard/
│   ├── index.html         ← live dashboard
│   └── data.json          ← generated
├── rss/
│   └── aggregator.py      ← WordPress auto-poster
├── .github/workflows/
│   └── scanner.yml        ← daily cron
└── README.md
```

## What Changed From v2

- **Merged** moltstreet-tools + crypto-early-radar into one tool
- **Added** Fear & Greed + GitHub activity signals
- **Added** DEX + perp volume data (from alpha_hunter)
- **Added** weighted scoring model (configurable)
- **Added** sector filtering (perp, rwa, ai, l2, defi, infra, l1)
- **Added** proper rate limiting + error handling
- **Added** sortable, filterable dashboard
- **Added** GitHub Actions daily cron
- **Removed** hardcoded values (everything is in config.py)

---

*Not financial advice. DYOR. MoltStreet Intelligence v3.0*
