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

def plot_f03(metrics, config=DEFAULT_CONFIG, logger=LOGGER):
    panels = [("Large", "A 大型市场"), ("Medium", "B 中型市场"), ("Small", "C 小型市场")]
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 5.1), sharey=True)
    for ax, (group, title) in zip(axes, panels):
        part = metrics.loc[metrics["market_size_group"].eq(group)]
        ask = part.dropna(subset=["ASK_growth"]).groupby("Time")["ASK_growth"].median().mul(100)
        rpk = part.dropna(subset=["RPK_growth"]).groupby("Time")["RPK_growth"].median().mul(100)
        ax.plot(ask.index, ask.values, color=COLORS["ASK"], marker="o", lw=1.8, ms=4.7, label="ASK")
        ax.plot(rpk.index, rpk.values, color=COLORS["RPK"], marker="s", lw=1.8, ms=4.5, label="RPK")
        ax.axhline(0, color=COLORS["reference"], lw=0.9)
        ax.set_title(title, pad=10)
        ax.set_xlabel("年份", labelpad=7)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
        ax.yaxis.set_major_formatter(percent_formatter(0))
        style_axis(ax, "y")
    axes[0].set_ylabel("年度增长率中位数（%）", labelpad=8)
    handles = [
        Line2D([0], [0], color=COLORS["ASK"], marker="o", lw=2, label="ASK"),
        Line2D([0], [0], color=COLORS["RPK"], marker="s", lw=2, label="RPK"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.98), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.23, wspace=0.16)
    add_bottom_title(fig, "图3 不同规模市场的ASK与RPK增长趋势", 0.02)
    return fig


