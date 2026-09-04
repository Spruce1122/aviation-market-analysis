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

def plot_f05(index_data, config=DEFAULT_CONFIG, logger=LOGGER, bottom_title="图5 代表性国家ASK与RPK指数走势"):
    countries = config.representative_countries
    rows = max(1, math.ceil(len(countries) / 3))
    cols = min(3, max(1, len(countries)))
    fig, axes = plt.subplots(rows, cols, figsize=(12.4 if cols == 3 else 4.2 * cols, 12.8 if rows == 4 else max(4.2, rows * 3.2)), sharex=True, squeeze=False)
    axes_flat = axes.ravel()
    for ax, code in zip(axes_flat, countries):
        part = index_data.loc[index_data["Country Code"].eq(code)].sort_values("Time")
        if part.empty:
            ax.text(0.5, 0.5, f"{code}\n无共同有效数据", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(code, pad=8)
        else:
            ax.plot(part["Time"], part["ASK_index"], color=COLORS["ASK"], marker="o", ms=3.6, lw=1.6)
            ax.plot(part["Time"], part["RPK_index"], color=COLORS["RPK"], marker="s", ms=3.4, lw=1.6)
            ax.axhline(100, color=COLORS["reference"], lw=0.8, ls="--")
            ax.set_title(f"{part['Country Name'].iloc[0]} ({code})", pad=8)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
        style_axis(ax, "y")
    for ax in axes_flat[len(countries):]:
        ax.set_visible(False)
    for row in range(rows):
        axes[row, 0].set_ylabel("指数（基期=100）")
    for ax in axes_flat[max(0, len(countries) - cols):len(countries)]:
        ax.set_xlabel("年份", labelpad=7)
        ax.tick_params(axis="x", rotation=0)
    handles = [
        Line2D([0], [0], color=COLORS["ASK"], marker="o", lw=2, label="ASK"),
        Line2D([0], [0], color=COLORS["RPK"], marker="s", lw=2, label="RPK"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.93, bottom=0.09, wspace=0.22, hspace=0.34)
    add_bottom_title(fig, bottom_title, 0.014)
    return fig


def plot_a01_absolute(metrics, countries, logger=LOGGER):
    """Small multiples of ASK/RPK levels for selected countries."""
    rows = max(1, math.ceil(len(countries) / 3))
    cols = min(3, max(1, len(countries)))
    fig, axes = plt.subplots(rows, cols, figsize=(12.4 if cols == 3 else 4.2 * cols,
                            max(4.4, rows * 3.25)), squeeze=False)
    axes_flat = axes.ravel()
    for ax, code in zip(axes_flat, countries):
        part = metrics.loc[metrics["Country Code"].eq(code)].sort_values("Time")
        if part.empty:
            ax.text(.5, .5, f"{code}\n无有效数据", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(code)
        else:
            ax.plot(part["Time"], part["ASKs"], color=COLORS["ASK"], marker="o", ms=3.4, lw=1.6)
            ax.plot(part["Time"], part["RPKs"], color=COLORS["RPK"], marker="s", ms=3.2, lw=1.6)
            ax.set_title(f"{part['Country Name'].iloc[0]} ({code})", pad=8)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
        style_axis(ax, "y")
    for ax in axes_flat[len(countries):]:
        ax.set_visible(False)
    for row in range(rows):
        axes[row, 0].set_ylabel("座公里")
    for ax in axes_flat[max(0, len(countries)-cols):len(countries)]:
        ax.set_xlabel("年份")
    handles = [
        Line2D([0], [0], color=COLORS["ASK"], marker="o", lw=2, label="ASK"),
        Line2D([0], [0], color=COLORS["RPK"], marker="s", lw=2, label="RPK"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, .985), ncol=2, frameon=False)
    fig.subplots_adjust(left=.085, right=.985, top=.92, bottom=.10, wspace=.22, hspace=.34)
    add_bottom_title(fig, "附图1 自选国家ASK/RPK绝对规模比较", .016)
    return fig
