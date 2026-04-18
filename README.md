# MoltStreet Intelligence v3.1

**Unified crypto scanner — all signals, one tool.**

Combines market data, on-chain metrics, developer activity, and **Reddit community sentiment** into a single, production-ready scanner.

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
# Scan base (includi social Reddit)
python3 src/main.py

# Top 10 con dashboard
python3 src/main.py --top 10 --dashboard

# Filtra per settore
python3 src/main.py --sector ai

# Output JSON
python3 src/main.py --json

# Scan veloce (skip Reddit)
python3 src/main.py --no-social
```

### Passo 4: Apri la dashboard
```bash
# Dopo aver generato i dati con --dashboard
open dashboard/index.html
```

### Passo 5: Email alerts (opzionale)
### Passo 6: Telegram alerts (opzionale)
```bash
export TELEGRAM_BOT_TOKEN=your_token_here
export TELEGRAM_CHAT_ID=your_chat_id
python3 src/main.py --telegram
```
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
5. Searches **Reddit** for community sentiment & engagement
6. Detects **trending coins** on CoinGecko
7. Scores each project 0-100 with a weighted multi-factor model
8. Generates a **live dashboard** + **email alerts**

## Signals

| Signal | Weight | What It Measures |
|--------|--------|-----------------|
| 24h Momentum | 8% | Short-term price direction |
| 7d Momentum | 12% | Near-term trend |
| 30d Momentum | 8% | Sustained movement |
| ATH Discount | 12% | Value vs all-time high (contrarian) |
| Volume/MCap | 8% | Genuine trading interest |
| TVL Level | 5% | DeFi capital deployed |
| TVL Change 7d | 8% | DeFi growth momentum |
| Fear & Greed | 5% | Market sentiment (contrarian) |
| GitHub Activity | 9% | Developer health |
| MCap Upside | 8% | Small cap = asymmetric returns |
| **Social (Reddit)** | **17%** | Community engagement + sentiment |

**Ratings:** 78+ = STRONG BUY | 65+ = ALERT | 50+ = WATCH | <50 = HOLD

## Social Signals (New in v3.1)

Reddit community data is now a first-class signal:

- **Engagement:** Thread upvotes, comment counts, discussion volume
- **Sentiment:** Average upvote ratio (bullish vs bearish sentiment)
- **Discovery:** Auto-searches coin-specific subreddits (r/solana, r/HyperliquidDEX, etc.)
- **Scoring:** Log-scaled engagement + sentiment weighting (adapted from [last30days-skill](https://github.com/mvanhorn/last30days-skill))

Subreddits covered: r/CryptoCurrency, r/CryptoMarkets, r/altcoin, r/defi + coin-specific subs.

No API keys required — uses Reddit's public JSON endpoint.

## Dashboard

```bash
# Generate data.json
python3 src/main.py --dashboard

# Open dashboard
open dashboard/index.html
```

The dashboard includes per-coin social data: thread count, upvotes, sentiment score, and top threads with links.

## Data Sources

| Source | Data | Cost |
|--------|------|------|
| CoinGecko | Prices, markets, trending | Free |
| DeFiLlama | TVL, DEX volumes, perp volumes | Free |
| Alternative.me | Fear & Greed index | Free |
| GitHub API | Commit activity, stars | Free |
| Reddit | Community sentiment + engagement | Free (public JSON) |

**Total cost: $0/month**

## Configuration

All settings in `src/config.py`:

- **WATCHLIST** — coins to scan
- **WEIGHTS** — scoring model weights (must sum to 1.0)
- **SECTORS** — category filters
- **GITHUB_REPOS** — protocol repos for activity tracking
- **COIN_SUBREDDITS** (in `social.py`) — coin-specific subreddits

## Structure

```
moltstreet-intelligence/
├── src/
│   ├── config.py          ← watchlist, weights, thresholds
│   ├── sources/
│   │   ├── coingecko.py   ← prices, markets, trending
│   │   ├── defillama.py   ← TVL, DEX/perp volumes
│   │   ├── github.py      ← commits + stars
│   │   ├── feargreed.py   ← Fear & Greed index
│   │   └── social.py      ← Reddit sentiment [NEW]
│   ├── scoring.py         ← weighted scoring engine
│   ├── alerts.py          ← email alerts
│   └── main.py            ← CLI orchestrator
├── dashboard/
│   ├── index.html         ← live dashboard
│   └── data.json          ← generated
├── .github/workflows/
│   └── scanner.yml        ← daily cron
└── README.md
```

## What Changed From v3.0

- **Added** Reddit social signals source (`src/sources/social.py`)
- **Added** social signal scoring (17% weight in composite)
- **Added** coin-specific subreddit search (r/solana, r/HyperliquidDEX, etc.)
- **Added** `--no-social` flag for faster scans
- **Added** social data to dashboard output (threads, upvotes, sentiment, top threads)
- **Rebalanced** all weights to accommodate social signal (total still 1.0)
- Multi-signal scoring architecture inspired by [last30days-skill](https://github.com/mvanhorn/last30days-skill)

---

*Not financial advice. DYOR. MoltStreet Intelligence v3.1*

## Related Projects

- [🧠 Guida AI 2026](https://lolarok.github.io/guida-ai-2026/) — I 10 Strumenti AI Più Interessanti del 2026
- [signalhub](https://lolarok.github.io/signalhub/) — Live crypto dashboard
- [crypto-trading-agents](https://github.com/Lolarok/crypto-trading-agents) — Multi-Agent LLM trading framework
- [market-radar](https://github.com/Lolarok/market-radar) — Multi-source financial scanner
