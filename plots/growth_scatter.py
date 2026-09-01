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

def plot_f01(metrics, config=DEFAULT_CONFIG, logger=LOGGER):
    sample = metrics.loc[metrics["common_growth_sample"] & metrics["market_size_group"].notna()].copy()
    sample["x"] = sample["ASK_growth"] * 100
    sample["y"] = sample["RPK_growth"] * 100
    low, high = robust_common_limits([sample["x"], sample["y"]])

    fig, ax = plt.subplots(figsize=(8.4, 7.4))
    for group in ["Large", "Medium", "Small"]:
        part = sample.loc[sample["market_size_group"].eq(group)]
        ax.scatter(
            part["x"], part["y"], s=34, alpha=0.62,
            color=COLORS[group], edgecolors="white", linewidths=0.35,
        )
    ax.plot([low, high], [low, high], color=COLORS["reference"], lw=1.2, ls="--", zorder=0)
    ax.set_xlim(low, high)
    ax.set_ylim(low, high)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("ASK年度增长率（%）", labelpad=8)
    ax.set_ylabel("RPK年度增长率（%）", labelpad=8)
    ax.xaxis.set_major_formatter(percent_formatter(0))
    ax.yaxis.set_major_formatter(percent_formatter(0))
    style_axis(ax, "both")
    ax.legend(
        handles=_market_legend_handles(), loc="upper center",
        bbox_to_anchor=(0.5, 1.09), ncol=3, frameon=False,
    )
    fig.subplots_adjust(left=0.13, right=0.97, top=0.88, bottom=0.15)
    add_bottom_title(fig, "图1 ASK与RPK年度增长的同步与偏离", 0.018)
    return fig


def _market_legend_handles():
    return [
        Line2D(
            [0], [0], marker="o", linestyle="", markersize=7,
            markerfacecolor=COLORS[group], markeredgecolor="white",
            label=MARKET_LABELS[group],
        )
        for group in ["Large", "Medium", "Small"]
    ]


