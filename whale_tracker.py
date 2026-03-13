"""
whale_tracker.py
Core module for fetching and processing on-chain whale transactions
via Etherscan API.
"""

import requests
import pandas as pd
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# ──────────────────────────────────────────────
# ERC-20 Token Config
# ──────────────────────────────────────────────
TOKENS = {
    "USDT": {
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
        "symbol": "USDT",
        "color": "green",
    },
    "USDC": {
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "decimals": 6,
        "symbol": "USDC",
        "color": "bright_cyan",
    },
    "LINK": {
        "address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "decimals": 18,
        "symbol": "LINK",
        "color": "blue",
    },
    "UNI": {
        "address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "decimals": 18,
        "symbol": "UNI",
        "color": "magenta",
    },
}

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"

COINGECKO_IDS = {
    "USDT": "tether",
    "USDC": "usd-coin",
    "LINK": "chainlink",
    "UNI": "uniswap",
}

_price_cache: dict = {}


def fetch_token_prices(tokens: list[str]) -> dict:
    ids = ",".join(COINGECKO_IDS[t] for t in tokens if t in COINGECKO_IDS)
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ids, "vs_currencies": "usd"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        prices = {}
        for token in tokens:
            cg_id = COINGECKO_IDS.get(token)
            if cg_id and cg_id in data:
                prices[token] = data[cg_id]["usd"]
            elif token in ("USDT", "USDC"):
                prices[token] = 1.0
            else:
                prices[token] = 0.0
        return prices
    except Exception as e:
        console.print(f"[yellow]WARNING: Price fetch failed: {e}. Using fallback prices.[/yellow]")
        return {t: (1.0 if t in ("USDT", "USDC") else 0.0) for t in tokens}


def _etherscan_get(api_key: str, params: dict, retries: int = 3) -> dict | None:
    params["apikey"] = api_key
    params["chainid"] = 1
    for attempt in range(retries):
        try:
            r = requests.get(ETHERSCAN_BASE, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "1" or data.get("message") == "OK":
                return data
            if "Max rate limit" in str(data.get("result", "")):
                console.print("[yellow]Rate limited -- waiting 6s...[/yellow]")
                time.sleep(6)
                continue
            return data
        except requests.RequestException as e:
            console.print(f"[red]Request error (attempt {attempt+1}): {e}[/red]")
            time.sleep(2)
    return None


def fetch_transfer_logs(api_key: str, token: str, blocks_back: int = 7200) -> list[dict]:
    cfg = TOKENS[token]
    block_data = _etherscan_get(api_key, {"module": "proxy", "action": "eth_blockNumber"})
    if not block_data:
        return []
    latest_block = int(block_data["result"], 16)
    from_block = max(0, latest_block - blocks_back)

    console.print(f"  [dim]Fetching {token} transfers: blocks {from_block:,} -> {latest_block:,}[/dim]")

    params = {
        "module": "logs",
        "action": "getLogs",
        "address": cfg["address"],
        "topic0": TRANSFER_TOPIC,
        "fromBlock": from_block,
        "toBlock": latest_block,
        "page": 1,
        "offset": 1000,
    }

    data = _etherscan_get(api_key, params)
    if not data or not isinstance(data.get("result"), list):
        return []

    logs = data["result"]
    console.print(f"  [dim]Got {len(logs)} raw log entries for {token}[/dim]")
    return logs


def parse_transfer_logs(logs: list[dict], token: str, price_usd: float) -> pd.DataFrame:
    cfg = TOKENS[token]
    decimals = cfg["decimals"]
    records = []

    for log in logs:
        try:
            topics = log.get("topics", [])
            if len(topics) < 3:
                continue
            from_addr = "0x" + topics[1][-40:]
            to_addr = "0x" + topics[2][-40:]
            raw_value = int(log.get("data", "0x0"), 16)
            value_tokens = raw_value / (10 ** decimals)
            value_usd = value_tokens * price_usd
            timestamp = int(log.get("timeStamp", "0"), 16)
            dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
            records.append({
                "token": token,
                "tx_hash": log.get("transactionHash", ""),
                "block": int(log.get("blockNumber", "0x0"), 16),
                "timestamp": dt,
                "from_address": from_addr,
                "to_address": to_addr,
                "value_tokens": value_tokens,
                "value_usd": value_usd,
                "price_usd": price_usd,
            })
        except Exception:
            continue

    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df = df[df["value_tokens"] > 0].copy()
    return df


def fetch_whale_data(
    api_key: str,
    selected_tokens: list[str],
    whale_threshold_usd: float = 100_000,
    blocks_back: int = 7200,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    console.print(
        Panel.fit(
            f"[bold cyan]Fetching On-Chain Data[/bold cyan]\n"
            f"Tokens: {', '.join(selected_tokens)}\n"
            f"Whale threshold: [green]${whale_threshold_usd:,.0f}[/green]\n"
            f"Block window: ~{blocks_back // 300:.0f}h lookback",
            border_style="cyan",
        )
    )

    prices = fetch_token_prices(selected_tokens)
    console.print(
        "[bold]Token prices:[/bold] "
        + "  ".join(f"{t}: ${p:.4f}" for t, p in prices.items())
    )

    all_dfs = []
    for token in selected_tokens:
        color = TOKENS[token]["color"]
        console.print(f"\n[bold][{color}]Scanning {token}...[/{color}][/bold]")
        logs = fetch_transfer_logs(api_key, token, blocks_back)
        if not logs:
            console.print(f"  [yellow]No logs found for {token}[/yellow]")
            continue
        price = prices.get(token, 1.0)
        df = parse_transfer_logs(logs, token, price)
        if df.empty:
            console.print(f"  [yellow]No parseable transfers for {token}[/yellow]")
            continue
        all_dfs.append(df)
        console.print(f"  [green]Done: {len(df):,} transfers parsed[/green]")

    if not all_dfs:
        console.print("[red]No data fetched. Check API key and network.[/red]")
        return pd.DataFrame(), pd.DataFrame()

    all_df = pd.concat(all_dfs, ignore_index=True)
    all_df = all_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    whale_df = all_df[all_df["value_usd"] >= whale_threshold_usd].copy()

    console.print(
        f"\n[bold green]Done![/bold green]  "
        f"Total txs: [cyan]{len(all_df):,}[/cyan]  |  "
        f"Whale txs (>=${whale_threshold_usd:,.0f}): [yellow]{len(whale_df):,}[/yellow]"
    )
    return all_df, whale_df


def display_whale_alerts(whale_df: pd.DataFrame, limit: int = 15):
    if whale_df.empty:
        console.print("[yellow]No whale transactions to display.[/yellow]")
        return

    table = Table(
        title="Whale Transactions Detected",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Time", style="dim cyan", width=19)
    table.add_column("Token", justify="center", width=6)
    table.add_column("Value (USD)", justify="right", style="bold green", width=18)
    table.add_column("Value (Token)", justify="right", style="cyan", width=18)
    table.add_column("From", style="dim", width=14)
    table.add_column("To", style="dim", width=14)

    top = whale_df.head(limit)
    for i, (_, row) in enumerate(top.iterrows(), 1):
        token_cfg = TOKENS.get(row["token"], {})
        color = token_cfg.get("color", "white")
        usd = row["value_usd"]
        if usd >= 10_000_000:
            badge = "[MEGA] "
        elif usd >= 1_000_000:
            badge = "[LARGE] "
        else:
            badge = ""

        table.add_row(
            str(i),
            row["timestamp"].strftime("%Y-%m-%d %H:%M"),
            f"[{color}]{row['token']}[/{color}]",
            f"{badge}${usd:>14,.0f}",
            f"{row['value_tokens']:>16,.2f}",
            f"{row['from_address'][:6]}...{row['from_address'][-4:]}",
            f"{row['to_address'][:6]}...{row['to_address'][-4:]}",
        )

    console.print(table)
    console.print(f"[dim]Showing top {min(limit, len(whale_df))} of {len(whale_df):,} whale transactions[/dim]")


def display_summary_stats(all_df: pd.DataFrame, whale_df: pd.DataFrame, threshold: float):
    if all_df.empty:
        return

    total_vol = all_df["value_usd"].sum()
    whale_vol = whale_df["value_usd"].sum() if not whale_df.empty else 0
    whale_pct = (whale_vol / total_vol * 100) if total_vol > 0 else 0
    unique_whales = pd.concat([whale_df["from_address"], whale_df["to_address"]]).nunique() if not whale_df.empty else 0
    largest = whale_df["value_usd"].max() if not whale_df.empty else 0

    stats_text = (
        f"[bold]Session Summary[/bold]\n\n"
        f"  Total transactions  : [cyan]{len(all_df):,}[/cyan]\n"
        f"  Whale transactions  : [yellow]{len(whale_df):,}[/yellow]  "
        f"([dim]{len(whale_df)/len(all_df)*100:.1f}% of txs[/dim])\n"
        f"  Total volume        : [green]${total_vol:,.0f}[/green]\n"
        f"  Whale volume        : [yellow]${whale_vol:,.0f}[/yellow]  "
        f"([dim]{whale_pct:.1f}% of vol[/dim])\n"
        f"  Unique whale addrs  : [magenta]{unique_whales:,}[/magenta]\n"
        f"  Largest tx          : [bold red]${largest:,.0f}[/bold red]\n"
        f"  Threshold           : [dim]${threshold:,.0f}[/dim]"
    )
    console.print(Panel(stats_text, border_style="green", expand=False))
