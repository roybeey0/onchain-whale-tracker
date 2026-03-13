#!/usr/bin/env python3
"""
main.py — On-Chain Whale Tracker
CLI entry point with interactive menu.

Usage:
    python main.py
    python main.py --token USDT USDC --threshold 500000 --blocks 3600
    python main.py --demo
"""

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, FloatPrompt, IntPrompt
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align
from rich.columns import Columns

from whale_tracker import (
    TOKENS,
    fetch_whale_data,
    display_whale_alerts,
    display_summary_stats,
)
from visualizations import generate_all_visualizations

console = Console()

# ──────────────────────────────────────────────
# Banner
# ──────────────────────────────────────────────
BANNER = """
[bold cyan]
╔═════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ ██╗    ██╗██╗  ██╗ █████╗ ██╗     ███████╗    ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗  ║
║ ██║    ██║██║  ██║██╔══██╗██║     ██╔════╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗ ║
║ ██║ █╗ ██║███████║███████║██║     █████╗         ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝ ║
║ ██║███╗██║██╔══██║██╔══██║██║     ██╔══╝         ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗ ║
║ ╚███╔███╔╝██║  ██║██║  ██║███████╗███████╗       ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║ ║
║  ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ║
╚═════════════════════════════════════════════════════════════════════════════════════════════════════════╝
[/bold cyan]
[dim]          On-Chain Whale Tracker  |  Ethereum ERC-20  |  Built by Roy Bey (roybeey.com)[/dim]
"""

DEMO_DATA_FILE = Path("demo_data.csv")


# ──────────────────────────────────────────────
# API key helpers
# ──────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("ETHERSCAN_API_KEY", "K6JY4PC1G8R55ENJNW8VD5NFNT241T2QBD")
    if key:
        console.print(f"[green]Done Using ETHERSCAN_API_KEY from environment[/green]")
        return key

    console.print(
        Panel(
            "[bold yellow]Etherscan API Key Required[/bold yellow]\n\n"
            "Get your FREE key at: [cyan]https://etherscan.io/myapikey[/cyan]\n\n"
            "Steps:\n"
            "  1. Register at etherscan.io\n"
            "  2. Go to My Profile → API Keys\n"
            "  3. Create a new key (free tier: 5 req/sec, 100K/day)\n\n"
            "Or set env var: [green]export ETHERSCAN_API_KEY=your_key[/green]",
            border_style="yellow",
            title="Setup",
        )
    )
    key = Prompt.ask("[bold]Enter your Etherscan API key[/bold]", password=True)
    return key.strip()


# ──────────────────────────────────────────────
# Demo data generator (no API needed)
# ──────────────────────────────────────────────

def generate_demo_data(n: int = 1500, threshold: float = 100_000) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate realistic synthetic whale data for demo/testing."""
    import numpy as np
    rng = np.random.default_rng(42)
    now = pd.Timestamp.now()

    tokens = ["USDT", "USDC", "LINK", "UNI"]
    prices = {"USDT": 1.0, "USDC": 1.0, "LINK": 18.5, "UNI": 9.8}

    addrs = [f"0x{''.join(rng.choice(list('0123456789abcdef'), 40))}" for _ in range(60)]

    records = []
    for i in range(n):
        token = rng.choice(tokens)
        price = prices[token]
        # Log-normal distribution skewed toward small txs with whale outliers
        log_val = rng.normal(loc=10.5, scale=2.2)
        value_usd = float(np.exp(log_val))
        value_usd = max(10, min(value_usd, 50_000_000))
        value_tokens = value_usd / price
        hours_ago = rng.uniform(0, 24)
        ts = now - pd.Timedelta(hours=hours_ago)

        records.append(
            {
                "token": token,
                "tx_hash": f"0x{''.join(rng.choice(list('0123456789abcdef'), 64))}",
                "block": int(21_500_000 - hours_ago * 300),
                "timestamp": ts,
                "from_address": rng.choice(addrs),
                "to_address": rng.choice(addrs),
                "value_tokens": value_tokens,
                "value_usd": value_usd,
                "price_usd": price,
            }
        )

    all_df = pd.DataFrame(records)
    all_df = all_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    whale_df = all_df[all_df["value_usd"] >= threshold].copy()
    console.print(
        f"[bold green]Demo data: {len(all_df):,} txs | {len(whale_df):,} whale txs[/bold green]"
    )
    return all_df, whale_df


# ──────────────────────────────────────────────
# Interactive menu
# ──────────────────────────────────────────────

def show_menu():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Key", style="bold cyan", width=4)
    table.add_column("Action", style="white")

    items = [
        ("1", "Fetch live on-chain data (Etherscan API)"),
        ("2", "Run with demo / synthetic data"),
        ("3", "Load data from CSV"),
        ("4", "Show whale alerts (terminal table)"),
        ("5", "Generate all visualizations (6 charts)"),
        ("6", "Export data to CSV"),
        ("7", "Display summary statistics"),
        ("8", "Configure settings"),
        ("Q", "Quit"),
    ]
    for key, action in items:
        table.add_row(f"[{key}]", action)

    console.print(
        Panel(table, title="[bold]Main Menu[/bold]", border_style="cyan", expand=False)
    )


def configure_settings(config: dict) -> dict:
    console.print(Panel("[bold]Settings[/bold]", border_style="yellow"))
    console.print(f"Current tokens: [cyan]{', '.join(config['tokens'])}[/cyan]")
    token_input = Prompt.ask(
        "Tokens (comma-separated, options: USDT USDC LINK UNI)",
        default=",".join(config["tokens"]),
    )
    tokens = [t.strip().upper() for t in token_input.split(",") if t.strip().upper() in TOKENS]
    if not tokens:
        tokens = ["USDT", "USDC"]
    config["tokens"] = tokens

    config["threshold"] = FloatPrompt.ask(
        "Whale threshold (USD)", default=config["threshold"]
    )
    config["blocks_back"] = IntPrompt.ask(
        "Blocks to look back (~300 blocks/hour)", default=config["blocks_back"]
    )
    console.print(
        f"[green]Done Config saved: tokens={tokens}, threshold=${config['threshold']:,.0f}, "
        f"blocks={config['blocks_back']:,}[/green]"
    )
    return config


def export_to_csv(all_df: pd.DataFrame, whale_df: pd.DataFrame):
    Path("outputs").mkdir(exist_ok=True)
    if not all_df.empty:
        all_df.to_csv("outputs/all_transactions.csv", index=False)
        console.print("[green]Done outputs/all_transactions.csv[/green]")
    if not whale_df.empty:
        whale_df.to_csv("outputs/whale_transactions.csv", index=False)
        console.print("[green]Done outputs/whale_transactions.csv[/green]")
    if all_df.empty and whale_df.empty:
        console.print("[yellow]No data to export. Fetch data first.[/yellow]")


# ──────────────────────────────────────────────
# Main interactive loop
# ──────────────────────────────────────────────

def run_interactive(args):
    console.print(BANNER)

    config = {
        "tokens": args.token if args.token else ["USDT", "USDC", "LINK", "UNI"],
        "threshold": args.threshold,
        "blocks_back": args.blocks,
    }

    all_df = pd.DataFrame()
    whale_df = pd.DataFrame()

    if args.demo:
        console.print("[cyan]Running in DEMO mode...[/cyan]")
        all_df, whale_df = generate_demo_data(threshold=config["threshold"])

    while True:
        console.print()
        show_menu()
        choice = Prompt.ask("[bold cyan]Choose[/bold cyan]", choices=["1","2","3","4","5","6","7","8","q","Q"], default="Q")

        if choice.upper() == "Q":
            console.print("[bold cyan]Goodbye! Stay on-chain.[/bold cyan]")
            break

        elif choice == "1":
            api_key = get_api_key()
            if api_key:
                all_df, whale_df = fetch_whale_data(
                    api_key,
                    config["tokens"],
                    config["threshold"],
                    config["blocks_back"],
                )
            else:
                console.print("[red]No API key provided.[/red]")

        elif choice == "2":
            all_df, whale_df = generate_demo_data(threshold=config["threshold"])

        elif choice == "3":
            csv_path = Prompt.ask("CSV file path", default="outputs/all_transactions.csv")
            try:
                all_df = pd.read_csv(csv_path, parse_dates=["timestamp"])
                whale_df = all_df[all_df["value_usd"] >= config["threshold"]].copy()
                console.print(f"[green]Done Loaded {len(all_df):,} rows from {csv_path}[/green]")
            except Exception as e:
                console.print(f"[red]Error loading CSV: {e}[/red]")

        elif choice == "4":
            if whale_df.empty:
                console.print("[yellow]No data. Fetch first (option 1 or 2).[/yellow]")
            else:
                limit = IntPrompt.ask("How many alerts to show", default=20)
                display_whale_alerts(whale_df, limit=limit)

        elif choice == "5":
            if all_df.empty:
                console.print("[yellow]No data. Fetch first (option 1 or 2).[/yellow]")
            else:
                console.print("[bold cyan]Generating visualizations...[/bold cyan]")
                paths = generate_all_visualizations(all_df, whale_df, config["threshold"])
                console.print(f"[bold green]{len(paths)} charts saved to outputs/[/bold green]")

        elif choice == "6":
            export_to_csv(all_df, whale_df)

        elif choice == "7":
            display_summary_stats(all_df, whale_df, config["threshold"])

        elif choice == "8":
            config = configure_settings(config)


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="On-Chain Whale Tracker — Monitor large Ethereum ERC-20 transactions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                          # Interactive menu
  python main.py --demo                                   # Run with demo data
  python main.py --token USDT USDC --threshold 500000    # Custom tokens & threshold
  python main.py --token LINK --blocks 1800              # Last ~6h of LINK transfers
        """,
    )
    parser.add_argument("--token", nargs="+", choices=list(TOKENS.keys()), help="ERC-20 tokens to track")
    parser.add_argument("--threshold", type=float, default=100_000, help="Whale threshold in USD (default: 100000)")
    parser.add_argument("--blocks", type=int, default=7200, help="Block lookback window (default: 7200 ≈ 24h)")
    parser.add_argument("--demo", action="store_true", help="Use synthetic demo data (no API key needed)")
    parser.add_argument("--no-menu", action="store_true", help="Run fetch + viz headlessly and exit")

    args = parser.parse_args()

    if args.no_menu:
        # Headless mode: fetch → alert → viz → export → done
        console.print(BANNER)
        if args.demo:
            all_df, whale_df = generate_demo_data(threshold=args.threshold)
        else:
            api_key = get_api_key()
            tokens = args.token or list(TOKENS.keys())
            all_df, whale_df = fetch_whale_data(api_key, tokens, args.threshold, args.blocks)

        display_summary_stats(all_df, whale_df, args.threshold)
        display_whale_alerts(whale_df, limit=10)
        generate_all_visualizations(all_df, whale_df, args.threshold)
        export_to_csv(all_df, whale_df)
    else:
        run_interactive(args)


if __name__ == "__main__":
    main()
