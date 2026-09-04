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

def plot_f06(country_dynamic, config=DEFAULT_CONFIG, logger=LOGGER, highlight_codes=()):
    plot_data = country_dynamic.dropna(subset=["corr_ask_rpk", "mean_abs_growth_gap"]).copy()
    plot_data["gap_pp"] = plot_data["mean_abs_growth_gap"] * 100
    n_min, n_max = plot_data["n_valid"].min(), plot_data["n_valid"].max()
    denom = max(float(n_max - n_min), 1.0)
    plot_data["point_size"] = 55 + 95 * (plot_data["n_valid"] - n_min) / denom

    fig, ax = plt.subplots(figsize=(11.5, 7.6))
    present_types = []
    for dynamic_type in ["长期高同步型", "ASK相对领先型", "RPK相对领先型", "高波动型", "过渡型"]:
        part = plot_data.loc[plot_data["dynamic_type"].eq(dynamic_type)]
        if part.empty:
            continue
        present_types.append(dynamic_type)
        ax.scatter(
            part["corr_ask_rpk"], part["gap_pp"], s=part["point_size"],
            alpha=0.72, color=COLORS[dynamic_type], edgecolors="white", linewidths=0.55,
            label=dynamic_type,
        )
    ax.set_xlabel("ASK增长与RPK增长的Pearson相关系数", labelpad=8)
    ax.set_ylabel("平均绝对增长差（百分点）", labelpad=8)
    ax.set_xlim(-1.05, 1.05)
    style_axis(ax, "both")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.11), ncol=min(5, len(present_types)), frameon=False)

    highlighted = plot_data.loc[plot_data["Country Code"].isin(highlight_codes)]
    if not highlighted.empty:
        ax.scatter(highlighted["corr_ask_rpk"], highlighted["gap_pp"],
                   s=highlighted["point_size"] + 85, facecolors="none", edgecolors="#111827",
                   linewidths=1.5, zorder=5)

    label_codes = set(F06_FIXED_LABEL_COUNTRIES)
    label_codes.update(highlight_codes)
    label_codes.update(plot_data.nlargest(F06_AUTO_LABEL_EACH_TAIL, "mean_abs_growth_gap")["Country Code"])
    label_codes.update(plot_data.nsmallest(F06_AUTO_LABEL_EACH_TAIL, "corr_ask_rpk")["Country Code"])
    label_data = plot_data.loc[plot_data["Country Code"].isin(label_codes)].copy()
    texts = []
    for _, row in label_data.iterrows():
        right_side = row["corr_ask_rpk"] > 0.75
        texts.append(
            ax.text(
                row["corr_ask_rpk"] - (0.012 if right_side else 0),
                row["gap_pp"], row["Country Code"],
                fontsize=9.0, ha="right" if right_side else "center", va="bottom", clip_on=True,
            )
        )
    adjust_text_labels(texts, ax, logger)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.84, bottom=0.15)
    add_bottom_title(fig, "图6 国家动态关系类型散点图", 0.018)
    return fig

