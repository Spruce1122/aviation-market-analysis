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

def plot_f02(metrics, config=DEFAULT_CONFIG, logger=LOGGER,
             bottom_title="图2 ASK与RPK年度增长率中位数趋势"):
    ask = metrics.dropna(subset=["ASK_growth"]).groupby("Time")["ASK_growth"].median().mul(100)
    rpk = metrics.dropna(subset=["RPK_growth"]).groupby("Time")["RPK_growth"].median().mul(100)
    years = sorted(set(ask.index).union(rpk.index))

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.plot(ask.index, ask.values, color=COLORS["ASK"], marker="o", lw=2.0, ms=5.5, label="ASK")
    ax.plot(rpk.index, rpk.values, color=COLORS["RPK"], marker="s", lw=2.0, ms=5.2, label="RPK")
    ax.axhline(0, color=COLORS["reference"], lw=1.0)
    ax.set_xlabel("年份", labelpad=8)
    ax.set_ylabel("年度增长率中位数（%）", labelpad=8)
    ax.yaxis.set_major_formatter(percent_formatter(0))
    ax.set_xticks(years)
    if len(years) > 10:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=10))
    style_axis(ax, "y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.1), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.84, bottom=0.20)
    add_bottom_title(fig, bottom_title, 0.018)
    return fig

