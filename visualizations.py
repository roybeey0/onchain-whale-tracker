"""
visualizations.py
Generate 5 whale analytics visualizations using matplotlib + seaborn.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import seaborn as sns
from collections import defaultdict
from pathlib import Path

# ──────────────────────────────────────────────
# Style config
# ──────────────────────────────────────────────
DARK_BG = "#0d1117"
CARD_BG = "#161b22"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
YELLOW = "#e3b341"
RED = "#f85149"
PURPLE = "#bc8cff"
CYAN = "#79c0ff"
ORANGE = "#d29922"

TOKEN_COLORS = {
    "USDT": "#26a17b",
    "USDC": "#2775ca",
    "LINK": "#2a5ada",
    "UNI": "#ff007a",
}

OUTPUT_DIR = Path("outputs")


def _setup_style():
    plt.rcParams.update(
        {
            "figure.facecolor": DARK_BG,
            "axes.facecolor": CARD_BG,
            "axes.edgecolor": "#30363d",
            "axes.labelcolor": "#c9d1d9",
            "axes.titlecolor": "#e6edf3",
            "axes.grid": True,
            "grid.color": "#21262d",
            "grid.linewidth": 0.5,
            "text.color": "#c9d1d9",
            "xtick.color": "#8b949e",
            "ytick.color": "#8b949e",
            "legend.facecolor": "#161b22",
            "legend.edgecolor": "#30363d",
            "font.family": "DejaVu Sans",
            "font.size": 10,
        }
    )


def _save(fig: plt.Figure, filename: str, dpi: int = 150) -> str:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    return str(path)


# ──────────────────────────────────────────────
# Chart 1 — Whale Activity Over Time
# ──────────────────────────────────────────────

def plot_whale_activity_over_time(whale_df: pd.DataFrame) -> str:
    """Line chart: whale tx count + volume per hour."""
    _setup_style()

    if whale_df.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.text(0.5, 0.5, "No whale data", ha="center", va="center", color=ACCENT)
        return _save(fig, "01_whale_activity_over_time.png")

    df = whale_df.copy()
    df["hour"] = df["timestamp"].dt.floor("h")
    hourly = (
        df.groupby("hour")
        .agg(tx_count=("tx_hash", "count"), volume_usd=("value_usd", "sum"))
        .reset_index()
    )

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    fig.suptitle("Whale Activity Over Time", fontsize=16, color="#e6edf3", fontweight="bold", y=0.98)

    # Top: tx count
    ax1.fill_between(hourly["hour"], hourly["tx_count"], alpha=0.3, color=ACCENT)
    ax1.plot(hourly["hour"], hourly["tx_count"], color=ACCENT, linewidth=2, marker="o", markersize=4)
    ax1.set_ylabel("Whale Tx Count", fontsize=11)
    ax1.set_title("Transactions per Hour", fontsize=11, color="#8b949e")

    # Bottom: volume
    ax2.fill_between(hourly["hour"], hourly["volume_usd"] / 1e6, alpha=0.3, color=GREEN)
    ax2.plot(hourly["hour"], hourly["volume_usd"] / 1e6, color=GREEN, linewidth=2, marker="o", markersize=4)
    ax2.set_ylabel("Volume (USD millions)", fontsize=11)
    ax2.set_title("Volume per Hour (USD M)", fontsize=11, color="#8b949e")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=35, ha="right")

    for ax in [ax1, ax2]:
        ax.spines[:].set_color("#30363d")

    plt.tight_layout()
    path = _save(fig, "01_whale_activity_over_time.png")
    return path


# ──────────────────────────────────────────────
# Chart 2 — Top Whales by Volume
# ──────────────────────────────────────────────

def plot_top_whales_by_volume(whale_df: pd.DataFrame, top_n: int = 15) -> str:
    """Horizontal bar: top whale addresses by total USD volume."""
    _setup_style()

    if whale_df.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No whale data", ha="center", va="center", color=ACCENT)
        return _save(fig, "02_top_whales_by_volume.png")

    # Aggregate by address (from + to)
    from_vol = whale_df.groupby("from_address")["value_usd"].sum().rename("sent")
    to_vol = whale_df.groupby("to_address")["value_usd"].sum().rename("received")
    combined = pd.concat([from_vol, to_vol], axis=1).fillna(0)
    combined["total"] = combined["sent"] + combined["received"]
    combined = combined.nlargest(top_n, "total").reset_index().rename(columns={"index": "address"})
    combined["short_addr"] = combined["address"].apply(lambda a: f"{a[:6]}...{a[-4:]}")

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.suptitle(f"Top {top_n} Whale Addresses by Volume", fontsize=15, color="#e6edf3", fontweight="bold")

    y = np.arange(len(combined))
    bar_recv = ax.barh(y, combined["received"] / 1e6, color=GREEN, alpha=0.85, label="Received", height=0.5)
    bar_sent = ax.barh(y, combined["sent"] / 1e6, left=combined["received"] / 1e6, color=RED, alpha=0.85, label="Sent", height=0.5)

    ax.set_yticks(y)
    ax.set_yticklabels(combined["short_addr"], fontsize=9)
    ax.set_xlabel("Volume (USD millions)", fontsize=11)
    ax.invert_yaxis()

    # Value labels on total
    for i, row in combined.iterrows():
        ax.text(
            row["total"] / 1e6 + 0.2,
            i,
            f"${row['total']/1e6:.1f}M",
            va="center",
            fontsize=8,
            color="#c9d1d9",
        )

    ax.legend(handles=[bar_recv, bar_sent], loc="lower right")
    ax.spines[:].set_color("#30363d")
    plt.tight_layout()
    return _save(fig, "02_top_whales_by_volume.png")


# ──────────────────────────────────────────────
# Chart 3 — Transaction Size Distribution
# ──────────────────────────────────────────────

def plot_transaction_size_distribution(all_df: pd.DataFrame, threshold: float = 100_000) -> str:
    """Log-scale histogram of transaction sizes with whale threshold line."""
    _setup_style()

    if all_df.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "No data", ha="center", va="center", color=ACCENT)
        return _save(fig, "03_transaction_size_distribution.png")

    df = all_df[all_df["value_usd"] > 0].copy()
    log_vals = np.log10(df["value_usd"].clip(lower=1))

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.suptitle("Transaction Size Distribution (Log Scale)", fontsize=15, color="#e6edf3", fontweight="bold")

    # Color whale vs retail
    whale_mask = df["value_usd"] >= threshold
    log_whale = np.log10(df.loc[whale_mask, "value_usd"].clip(lower=1))
    log_retail = np.log10(df.loc[~whale_mask, "value_usd"].clip(lower=1))

    bins = np.linspace(log_vals.min(), log_vals.max(), 50)
    ax.hist(log_retail, bins=bins, color=CYAN, alpha=0.7, label="Retail txs", edgecolor="none")
    ax.hist(log_whale, bins=bins, color=YELLOW, alpha=0.85, label="Whale txs", edgecolor="none")

    # Threshold line
    thresh_log = np.log10(threshold)
    ax.axvline(thresh_log, color=RED, linewidth=2, linestyle="--", label=f"Whale threshold (${threshold/1e3:.0f}K)")

    # X-axis labels
    ticks = [3, 4, 5, 6, 7, 8]
    labels = ["$1K", "$10K", "$100K", "$1M", "$10M", "$100M"]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Transaction Size (USD)", fontsize=11)
    ax.set_ylabel("Number of Transactions", fontsize=11)
    ax.legend()
    ax.spines[:].set_color("#30363d")
    plt.tight_layout()
    return _save(fig, "03_transaction_size_distribution.png")


# ──────────────────────────────────────────────
# Chart 4 — Whale vs Retail Comparison
# ──────────────────────────────────────────────

def plot_whale_vs_retail(all_df: pd.DataFrame, threshold: float = 100_000) -> str:
    """2x2 comparison: count, volume, avg size, token breakdown."""
    _setup_style()

    if all_df.empty:
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))
        return _save(fig, "04_whale_vs_retail_comparison.png")

    whale_df = all_df[all_df["value_usd"] >= threshold]
    retail_df = all_df[all_df["value_usd"] < threshold]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Whale vs Retail — Side-by-Side Comparison", fontsize=15, color="#e6edf3", fontweight="bold")

    cats = ["Whale", "Retail"]
    colors = [YELLOW, CYAN]

    # 1. Count
    ax = axes[0, 0]
    counts = [len(whale_df), len(retail_df)]
    bars = ax.bar(cats, counts, color=colors, alpha=0.85, width=0.5)
    ax.set_title("Transaction Count", fontsize=11)
    ax.set_ylabel("Count")
    for bar, val in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(counts) * 0.01,
                f"{val:,}", ha="center", fontsize=10, color="#c9d1d9")

    # 2. Volume
    ax = axes[0, 1]
    vols = [whale_df["value_usd"].sum() / 1e6, retail_df["value_usd"].sum() / 1e6]
    bars = ax.bar(cats, vols, color=colors, alpha=0.85, width=0.5)
    ax.set_title("Total Volume (USD M)", fontsize=11)
    ax.set_ylabel("Volume ($M)")
    for bar, val in zip(bars, vols):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(vols) * 0.01,
                f"${val:.1f}M", ha="center", fontsize=10, color="#c9d1d9")

    # 3. Avg tx size
    ax = axes[1, 0]
    avgs = [
        whale_df["value_usd"].mean() / 1e3 if not whale_df.empty else 0,
        retail_df["value_usd"].mean() / 1e3 if not retail_df.empty else 0,
    ]
    bars = ax.bar(cats, avgs, color=colors, alpha=0.85, width=0.5)
    ax.set_title("Avg Transaction Size", fontsize=11)
    ax.set_ylabel("Avg Size ($K)")
    for bar, val in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(avgs) * 0.01,
                f"${val:.0f}K", ha="center", fontsize=10, color="#c9d1d9")

    # 4. Token breakdown donut
    ax = axes[1, 1]
    token_vol = all_df.groupby("token")["value_usd"].sum()
    wedge_colors = [TOKEN_COLORS.get(t, "#8b949e") for t in token_vol.index]
    wedges, texts, autotexts = ax.pie(
        token_vol,
        labels=token_vol.index,
        colors=wedge_colors,
        autopct="%1.1f%%",
        startangle=140,
        wedgeprops=dict(width=0.55, edgecolor=DARK_BG, linewidth=2),
    )
    for at in autotexts:
        at.set_color("#e6edf3")
        at.set_fontsize(9)
    ax.set_title("Volume by Token", fontsize=11)
    ax.set_facecolor(DARK_BG)

    for ax in axes.flat[:3]:
        ax.spines[:].set_color("#30363d")

    plt.tight_layout()
    return _save(fig, "04_whale_vs_retail_comparison.png")


# ──────────────────────────────────────────────
# Chart 5 — Whale Flow Network (Sankey-style)
# ──────────────────────────────────────────────

def plot_whale_flow_network(whale_df: pd.DataFrame, top_n: int = 10) -> str:
    """Chord-like flow chart: top whale addresses and flows between them."""
    _setup_style()

    if whale_df.empty or len(whale_df) < 3:
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, "Insufficient whale data for network", ha="center", va="center", color=ACCENT, fontsize=14)
        ax.set_facecolor(DARK_BG)
        return _save(fig, "05_whale_flow_network.png")

    # Get top whale addresses by total volume
    from_vol = whale_df.groupby("from_address")["value_usd"].sum()
    to_vol = whale_df.groupby("to_address")["value_usd"].sum()
    combined_vol = from_vol.add(to_vol, fill_value=0).nlargest(top_n)
    top_addrs = set(combined_vol.index)

    # Filter to edges between top addresses
    edges_df = whale_df[
        whale_df["from_address"].isin(top_addrs) & whale_df["to_address"].isin(top_addrs)
    ]

    if edges_df.empty:
        # Show all inter-whale flows (even if not in top_n)
        edges_df = whale_df.copy()
        top_addrs = set(pd.concat([whale_df["from_address"], whale_df["to_address"]]).value_counts().head(top_n).index)
        edges_df = whale_df[
            whale_df["from_address"].isin(top_addrs) | whale_df["to_address"].isin(top_addrs)
        ]

    # Build node list
    nodes = list(top_addrs)
    node_idx = {addr: i for i, addr in enumerate(nodes)}
    short = {addr: f"{addr[:6]}...{addr[-4:]}" for addr in nodes}

    # Positions on a circle
    n = len(nodes)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    radius = 1.0
    pos = {addr: (radius * np.cos(a), radius * np.sin(a)) for addr, a in zip(nodes, angles)}

    fig, ax = plt.subplots(figsize=(13, 11))
    fig.suptitle("Whale Flow Network", fontsize=15, color="#e6edf3", fontweight="bold")
    ax.set_aspect("equal")
    ax.set_facecolor(DARK_BG)

    # Draw edges
    edge_vols = edges_df.groupby(["from_address", "to_address"])["value_usd"].sum().reset_index()
    max_vol = edge_vols["value_usd"].max() if len(edge_vols) > 0 else 1

    for _, row in edge_vols.iterrows():
        src = row["from_address"]
        dst = row["to_address"]
        if src not in pos or dst not in pos:
            continue
        x0, y0 = pos[src]
        x1, y1 = pos[dst]
        vol_frac = row["value_usd"] / max_vol
        lw = 0.5 + vol_frac * 4
        alpha = 0.3 + vol_frac * 0.5
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=ACCENT,
                lw=lw,
                alpha=alpha,
                connectionstyle="arc3,rad=0.2",
            ),
        )

    # Draw nodes
    node_sizes = combined_vol.reindex(nodes).fillna(1)
    min_s, max_s = node_sizes.min(), node_sizes.max()
    for addr in nodes:
        x, y = pos[addr]
        size_norm = (node_sizes.get(addr, 1) - min_s) / (max_s - min_s + 1e-9)
        circle_r = 0.06 + size_norm * 0.08
        circle = plt.Circle((x, y), circle_r, color=YELLOW, zorder=5, alpha=0.9)
        ax.add_patch(circle)
        # Label
        label_x = x * 1.18
        label_y = y * 1.18
        ax.text(label_x, label_y, short[addr], ha="center", va="center",
                fontsize=7.5, color="#e6edf3", zorder=6,
                bbox=dict(boxstyle="round,pad=0.2", facecolor=CARD_BG, edgecolor="#30363d", alpha=0.85))

    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    ax.axis("off")

    # Legend
    legend_handles = [
        mpatches.Patch(color=YELLOW, label="Whale Address"),
        mpatches.Patch(color=ACCENT, label="Transfer Flow"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=9)

    plt.tight_layout()
    return _save(fig, "05_whale_flow_network.png")


# ──────────────────────────────────────────────
# Bonus Chart 6 — Heatmap by Hour & Token
# ──────────────────────────────────────────────

def plot_activity_heatmap(whale_df: pd.DataFrame) -> str:
    """Heatmap: whale activity by hour of day vs token."""
    _setup_style()

    if whale_df.empty:
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.text(0.5, 0.5, "No data", ha="center", va="center", color=ACCENT)
        return _save(fig, "06_activity_heatmap.png")

    df = whale_df.copy()
    df["hour_of_day"] = df["timestamp"].dt.hour
    pivot = df.pivot_table(values="value_usd", index="token", columns="hour_of_day", aggfunc="sum", fill_value=0)
    # Fill missing hours
    for h in range(24):
        if h not in pivot.columns:
            pivot[h] = 0
    pivot = pivot[sorted(pivot.columns)]

    fig, ax = plt.subplots(figsize=(16, 5))
    fig.suptitle("Whale Volume Heatmap (by Hour of Day)", fontsize=14, color="#e6edf3", fontweight="bold")

    sns.heatmap(
        pivot / 1e6,
        ax=ax,
        cmap="YlOrRd",
        linewidths=0.3,
        linecolor="#0d1117",
        annot=True,
        fmt=".1f",
        annot_kws={"size": 8, "color": "#0d1117"},
        cbar_kws={"label": "Volume (USD M)", "shrink": 0.8},
    )
    ax.set_xlabel("Hour of Day (UTC)", fontsize=11)
    ax.set_ylabel("Token", fontsize=11)
    ax.tick_params(colors="#c9d1d9")

    plt.tight_layout()
    return _save(fig, "06_activity_heatmap.png")


# ──────────────────────────────────────────────
# Run all visualizations
# ──────────────────────────────────────────────

def generate_all_visualizations(
    all_df: pd.DataFrame,
    whale_df: pd.DataFrame,
    threshold: float = 100_000,
) -> list[str]:
    """Generate all charts and return list of saved file paths."""
    paths = []
    charts = [
        ("Whale Activity Over Time", lambda: plot_whale_activity_over_time(whale_df)),
        ("Top Whales by Volume", lambda: plot_top_whales_by_volume(whale_df)),
        ("Transaction Size Distribution", lambda: plot_transaction_size_distribution(all_df, threshold)),
        ("Whale vs Retail Comparison", lambda: plot_whale_vs_retail(all_df, threshold)),
        ("Whale Flow Network", lambda: plot_whale_flow_network(whale_df)),
        ("Activity Heatmap", lambda: plot_activity_heatmap(whale_df)),
    ]
    for i, (name, fn) in enumerate(charts, 1):
        try:
            path = fn()
            paths.append(path)
            print(f"  Done [{i}/{len(charts)}] {name} → {path}")
        except Exception as e:
            print(f"  Error [{i}/{len(charts)}] {name} failed: {e}")
    return paths
