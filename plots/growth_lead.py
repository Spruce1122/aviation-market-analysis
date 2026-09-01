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

def plot_a01(country_dynamic, config=DEFAULT_CONFIG, logger=LOGGER):
    eligible = country_dynamic.loc[
        country_dynamic["n_valid"].ge(MIN_VALID_GROWTH_YEARS)
    ].copy()
    low = (
        eligible.sort_values(["median_growth_gap", "Country Code"], ascending=[True, True])
        .head(N_GROWTH_GAP_EXTREMES)
        .copy()
    )
    high = (
        eligible.sort_values(["median_growth_gap", "Country Code"], ascending=[False, True])
        .head(N_GROWTH_GAP_EXTREMES)
        .copy()
    )
    low["side"] = "ASK增长相对领先"
    high["side"] = "RPK增长相对领先"
    data = pd.concat([low, high], ignore_index=True).drop_duplicates("Country Code")
    data = data.sort_values(["median_growth_gap", "Country Code"])
    data["gap_pp"] = data["median_growth_gap"] * 100
    colors = [COLORS["ASK"] if value < 0 else COLORS["RPK"] for value in data["gap_pp"]]

    fig, ax = plt.subplots(figsize=(10.2, 9.0))
    bars = ax.barh(data["Country Name"], data["gap_pp"], color=colors, height=0.68, edgecolor="white")
    ax.axvline(0, color="#656B72", lw=1.0)
    style_axis(ax, "x")
    ax.set_xlabel("median(RPK_growth − ASK_growth)（百分点）", labelpad=9)
    ax.xaxis.set_major_formatter(percent_formatter(0))
    min_x, max_x = float(data["gap_pp"].min()), float(data["gap_pp"].max())
    span = max_x - min_x
    margin = max(span * 0.18, 2.0)
    ax.set_xlim(min_x - margin, max_x + margin)
    for bar, (_, row) in zip(bars, data.iterrows()):
        value = row["gap_pp"]
        offset = max(span * 0.018, 0.25)
        ax.text(
            value + offset if value >= 0 else value - offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}pp",
            ha="left" if value >= 0 else "right",
            va="center",
            fontsize=9.2,
            clip_on=False,
        )
    ax.text(0.02, 1.015, "ASK增长相对领先", transform=ax.transAxes, color=COLORS["ASK"], ha="left")
    ax.text(0.98, 1.015, "RPK增长相对领先", transform=ax.transAxes, color=COLORS["RPK"], ha="right")
    fig.subplots_adjust(left=0.30, right=0.94, top=0.92, bottom=0.14)
    add_bottom_title(fig, "附图1 国家层面ASK与RPK增长领先比较", 0.014)
    return fig


