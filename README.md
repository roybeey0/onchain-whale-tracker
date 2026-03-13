# On-Chain Whale Tracker

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Ethereum](https://img.shields.io/badge/Ethereum-ERC--20-627EEA?style=for-the-badge&logo=ethereum&logoColor=white)
![Etherscan](https://img.shields.io/badge/Etherscan-API-21325B?style=for-the-badge&logo=ethereum&logoColor=white)
![Rich](https://img.shields.io/badge/Rich-Terminal_UI-FF6B6B?style=for-the-badge)
![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Monitor large Ethereum wallet movements in real-time using on-chain data.**  
Filter whale transactions, visualize wallet behavior, and export analytics — all from your terminal.

[Features](#features) · [Quickstart](#quickstart) · [Interactive Menu](#interactive-menu) · [Visualizations](#visualizations) · [Portfolio](#portfolio-context)

</div>

---

## What is a Whale?

In crypto markets, a **whale** is a wallet that transacts very large amounts — movements large enough to potentially shift market prices. This tool detects and visualizes whale-scale ERC-20 token transfers on Ethereum in near real-time using the [Etherscan API](https://etherscan.io/apis).

---

## Features

- **Live on-chain data** — Fetch recent `Transfer` events from USDT, USDC, LINK, and UNI contracts
- **Configurable whale threshold** — Default `$100,000 USD`; adjust to your needs
- **Rich terminal UI** — Color-coded alerts with size badges (`[MEGA]` for >$10M, `[LARGE]` for >$1M)
- **6 visualizations** — Activity timeline, top wallets, size distribution, whale vs retail, flow network, and heatmap
- **CSV export** — All transactions + filtered whale transactions saved to `outputs/`
- **Demo mode** — Full run with synthetic data, no API key needed
- **Interactive CLI menu** — 8 options to navigate like a dashboard

---

## Project Structure

```
onchain-whale-tracker/
├── main.py              # CLI entry point + interactive menu
├── whale_tracker.py     # Etherscan data fetching & processing core
├── visualizations.py    # 6 matplotlib/seaborn charts
├── requirements.txt     # Python dependencies
├── outputs/             # Generated charts + CSV exports (auto-created)
│   ├── 01_whale_activity_over_time.png
│   ├── 02_top_whales_by_volume.png
│   ├── 03_transaction_size_distribution.png
│   ├── 04_whale_vs_retail_comparison.png
│   ├── 05_whale_flow_network.png
│   ├── 06_activity_heatmap.png
│   ├── all_transactions.csv
│   └── whale_transactions.csv
└── README.md
```

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/roybeey0/onchain-whale-tracker.git
cd onchain-whale-tracker
pip install -r requirements.txt
```

### 2. Get an Etherscan API Key (free)

1. Register at [etherscan.io](https://etherscan.io/register)
2. Go to **My Profile → API Keys**
3. Click **Add** — free tier: 5 requests/sec, 100K calls/day

```bash
# Windows
set ETHERSCAN_API_KEY=your_api_key_here

# Mac / Linux
export ETHERSCAN_API_KEY=your_api_key_here
```

### 3. Run

```bash
# Interactive menu (recommended)
python main.py

# Demo mode — no API key needed
python main.py --demo

# Headless: fetch USDT + USDC, $500K threshold, generate charts, export CSV
python main.py --token USDT USDC --threshold 500000 --no-menu

# Last 6 hours of LINK whale activity
python main.py --token LINK --blocks 1800 --no-menu
```

---

## Sample Terminal Output

```
╭──────────────────────────────────────────────────────╮
│ Session Summary                                      │
│                                                      │
│   Total transactions  : 1,247                        │
│   Whale transactions  : 83   (6.7% of txs)           │
│   Total volume        : $412,803,511                 │
│   Whale volume        : $398,220,104  (96.5% of vol) │
│   Unique whale addrs  : 31                           │
│   Largest tx          : $18,422,000                  │
│   Threshold           : $100,000                     │
╰──────────────────────────────────────────────────────╯

              Whale Transactions Detected
╭────┬─────────────────────┬───────┬──────────────────────┬──────────────────╮
│ #  │ Time                │ Token │ Value (USD)          │ Value (Token)    │
├────┼─────────────────────┼───────┼──────────────────────┼──────────────────┤
│ 1  │ 2026-03-13 09:42    │ USDT  │ [MEGA] $18,422,000   │ 18,422,000.00    │
│ 2  │ 2026-03-13 09:38    │ USDC  │ [LARGE]  $4,100,500  │  4,100,500.00    │
│ 3  │ 2026-03-13 09:31    │ LINK  │         $287,430     │     15,537.84    │
╰────┴─────────────────────┴───────┴──────────────────────┴──────────────────╯
```

---

## Interactive Menu

Run `python main.py` to open the interactive menu:

```
[1]  Fetch live on-chain data (Etherscan API)
[2]  Run with demo / synthetic data
[3]  Load data from CSV
[4]  Show whale alerts (terminal table)
[5]  Generate all visualizations (6 charts)
[6]  Export data to CSV
[7]  Display summary statistics
[8]  Configure settings
[Q]  Quit
```

### Option 1 — Fetch Live Data
Connects to Etherscan API and fetches the latest ERC-20 Transfer events.  
Requires a valid API key set via environment variable or entered manually at the prompt.

### Option 2 — Demo / Synthetic Data
Generates 1,500 realistic synthetic transactions locally — no API key needed.  
Good for testing visualizations and exploring the tool before using live data.

### Option 3 — Load Data from CSV
Loads previously exported data from a CSV file so you can re-run analysis without fetching from the API again.

**Default path** (just press Enter):
```
CSV file path (outputs/all_transactions.csv):
```

**Custom path example** — load whale-only transactions:
```
CSV file path (outputs/all_transactions.csv): outputs\whale_transactions.csv
```

**Full path example** (Windows):
```
CSV file path (outputs/all_transactions.csv): C:\Users\roybeey\Downloads\onchain-whale-tracker\outputs\all_transactions.csv
```

The two CSV files available in `outputs/` after running option 6:
- `all_transactions.csv` — every transaction fetched (retail + whale)
- `whale_transactions.csv` — only transactions above the whale threshold

### Option 4 — Show Whale Alerts
Displays a color-coded table of whale transactions in the terminal.

**Default:** shows 20 rows. You can enter any number:
```
How many alerts to show (20): 20     ← press Enter for default
How many alerts to show (20): 50     ← show 50 rows
How many alerts to show (20): 100    ← show 100 rows
```

Transaction size badges:
- `[MEGA]` — transaction >= $10,000,000
- `[LARGE]` — transaction >= $1,000,000
- *(no badge)* — transaction >= threshold (default $100,000)

### Option 5 — Generate Visualizations
Generates all 6 charts and saves them to `outputs/` as PNG files (dark theme, 150 DPI).

### Option 6 — Export to CSV
Saves two CSV files to `outputs/`:
- `outputs/all_transactions.csv`
- `outputs/whale_transactions.csv`

### Option 7 — Summary Statistics
Displays a summary panel: total txs, whale txs, total volume, whale volume, unique addresses, and largest transaction.

### Option 8 — Configure Settings
Change the tracker settings before fetching. All settings revert to default when you restart the program.

**Default values (no configuration needed):**

| Setting | Default | Description |
|---------|---------|-------------|
| Tokens | USDT, USDC, LINK, UNI | All 4 tokens tracked |
| Whale threshold | $100,000 | Minimum USD to be classified as whale |
| Blocks back | 7,200 | Lookback window (~24 hours at 12 sec/block) |

**Example — track only USDT and USDC with a $500K threshold over the last 12 hours:**
```
Tokens (comma-separated, options: USDT USDC LINK UNI): USDT,USDC
Whale threshold (USD): 500000
Blocks to look back: 3600
```

**Example — track only LINK with a $50K threshold:**
```
Tokens (comma-separated, options: USDT USDC LINK UNI): LINK
Whale threshold (USD): 50000
Blocks to look back: 7200
```

**Block window reference:**

| Blocks | Approximate Timeframe |
|--------|----------------------|
| 300 | ~1 hour |
| 1,800 | ~6 hours |
| 3,600 | ~12 hours |
| 7,200 | ~24 hours (default) |
| 14,400 | ~48 hours |

---

## Recommended Workflow

```
[1] Fetch live data
      ↓
[7] Check summary stats
      ↓
[4] View whale alerts
      ↓
[5] Generate visualizations
      ↓
[6] Export to CSV
      ↓
[3] Next time: load from CSV instead of fetching again
```

---

## Visualizations

All 6 charts are saved to `outputs/` in PNG format (dark theme, 150 DPI).

| # | File | Description |
|---|------|-------------|
| 1 | `01_whale_activity_over_time.png` | Hourly tx count + volume timeline |
| 2 | `02_top_whales_by_volume.png` | Top 15 addresses: sent vs received volume |
| 3 | `03_transaction_size_distribution.png` | Log-scale histogram, whale vs retail colored |
| 4 | `04_whale_vs_retail_comparison.png` | 2x2 panel: count, volume, avg size, token breakdown |
| 5 | `05_whale_flow_network.png` | Circular network: top addresses + transfer flow arrows |
| 6 | `06_activity_heatmap.png` | Token x hour-of-day volume heatmap |

---

## How It Works

```
Etherscan API
     |
     v
getLogs (Transfer topic0)          <- ERC-20 Transfer events
     |
     v
Parse hex data -> addresses, amounts
     |
     v
CoinGecko API -> token USD prices
     |
     v
Filter: value_usd >= threshold      <- Whale detection
     |
     |---> Rich terminal alerts
     |---> 6 matplotlib/seaborn charts
     └---> CSV export
```

The Transfer event signature:
```
Transfer(address indexed from, address indexed to, uint256 value)
topic0: 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
```

---

## Tokens Tracked

| Token | Contract | Decimals |
|-------|----------|----------|
| USDT | `0xdAC17F958D2ee523a2206206994597C13D831ec7` | 6 |
| USDC | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` | 6 |
| LINK | `0x514910771AF9Ca656af840dff83E8264EcF986CA` | 18 |
| UNI | `0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984` | 18 |

---

## Tech Stack

| Library | Use |
|---------|-----|
| `requests` | Etherscan & CoinGecko API calls |
| `pandas` | Data wrangling and aggregation |
| `matplotlib` | Chart rendering (dark theme) |
| `seaborn` | Heatmap and styled charts |
| `rich` | Terminal UI: tables, panels, prompts |
| `numpy` | Numerical operations |

---

## CLI Flags (Advanced)

```
usage: main.py [-h] [--token {USDT,USDC,LINK,UNI} ...] [--threshold THRESHOLD]
               [--blocks BLOCKS] [--demo] [--no-menu]

options:
  --token         ERC-20 tokens to track (default: all 4)
  --threshold     Whale threshold in USD (default: 100000)
  --blocks        Block lookback window (default: 7200 ~ 24h)
  --demo          Use synthetic demo data, no API key needed
  --no-menu       Headless run: fetch -> alerts -> charts -> CSV -> exit
```

---

## Portfolio Context

This project is part of my Web3/on-chain analytics portfolio, alongside:

- **OKX Trading Bot** — Automated crypto trading via OKX API
- **CodeT5 Code Generator** — Fine-tuned LLM for code generation
- **Genetic Algorithm Optimizer** — Metaheuristic optimization framework
- **Crypto Market EDA** — Exploratory analysis of crypto market data
- **Python Blockchain + Wallet Analytics** — Custom blockchain implementation
- **Smart Contract Interaction (Web3.py)** — On-chain contract calls & events

View full portfolio: [roybeey.com](https://roybeey.com)

---

## License

MIT — see [LICENSE](LICENSE) for details.