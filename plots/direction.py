"""Migrated original Matplotlib function; returns Figure without file side effects."""
from __future__ import annotations
import logging
import math
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
from core.config import *
from plots.style import (COLORS, MARKET_LABELS, add_bottom_title, adjust_text_labels,
                         percent_formatter, robust_common_limits, style_axis)
LOGGER = logging.getLogger("aviation_dashboard")

def plot_f07(direction_low, direction_high, config=DEFAULT_CONFIG, logger=LOGGER,
             bottom_title="图7 ASK_out与ASK_in方向不对称国家比较"):
    data = pd.concat([direction_low, direction_high], ignore_index=True).drop_duplicates("country_code").sort_values(["ln_R", "country_code"])
    colors = [COLORS[group] for group in data["extreme_group"]]
    fig, ax = plt.subplots(figsize=(10.0, max(8.6, len(data) * 0.40 + 1.4)))
    bars = ax.barh(data["country_name"], data["ln_R"], color=colors, height=0.68, edgecolor="white")
    ax.axvline(0, color="#666C72", lw=1.0)
    style_axis(ax, "x")
    ax.set_xlabel("ln(R)，其中 R = mean(ASK_out) / mean(ASK_in)", labelpad=9)
    min_x, max_x = float(data["ln_R"].min()), float(data["ln_R"].max())
    span = max_x - min_x
    margin = max(span * 0.18, 0.08)
    ax.set_xlim(min_x - margin, max_x + margin)
    for bar, (_, row) in zip(bars, data.iterrows()):
        value = row["ln_R"]
        offset = span * 0.025 if span else 0.02
        x = value + offset if value >= 0 else value - offset
        ax.text(
            x, bar.get_y() + bar.get_height() / 2, f"R={row['R']:.2f}",
            ha="left" if value >= 0 else "right", va="center", fontsize=9.2, clip_on=False,
        )
    ax.text(0.02, 1.015, "ASK_in相对占优", transform=ax.transAxes, color=COLORS["ASK_in相对占优"], ha="left")
    ax.text(0.98, 1.015, "ASK_out相对占优", transform=ax.transAxes, color=COLORS["ASK_out相对占优"], ha="right")
    fig.subplots_adjust(left=0.29, right=0.94, top=0.91, bottom=0.14)
    add_bottom_title(fig, bottom_title, 0.014)
    return fig

