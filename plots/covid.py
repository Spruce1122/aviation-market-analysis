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

from core.pandemic import build_balanced_pandemic_plf

def plot_a02(metrics, config=DEFAULT_CONFIG, logger=LOGGER,
             bottom_title="附图2 PLF年度变化与市场规模比较"):
    balanced = build_balanced_pandemic_plf(metrics, config)
    period_columns = ["pre_plf", "shock_plf", "recovery_plf"]
    period_labels = [f"第一时期\n{config.period_pre_start}—{config.period_pre_end}",
                     f"第二时期\n{config.period_shock_year}",
                     f"第三时期\n{config.period_recovery_year}"]
    x = np.arange(3)

    overall = pd.DataFrame(
        {
            "median": [balanced[col].median() for col in period_columns],
            "q25": [balanced[col].quantile(0.25) for col in period_columns],
            "q75": [balanced[col].quantile(0.75) for col in period_columns],
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(13.8, 5.7), sharey=True)
    ax = axes[0]
    ax.fill_between(x, overall["q25"], overall["q75"], color=COLORS["Medium"], alpha=0.22, label="25%—75%分位区间")
    ax.plot(x, overall["median"], color=COLORS["ASK"], marker="o", ms=6.2, lw=2.1, label="中位数")
    ax.set_xticks(x, period_labels)
    ax.set_title("A 全样本PLF分布", pad=11)
    ax.set_ylabel("PLF（%）", labelpad=8)
    ax.yaxis.set_major_formatter(percent_formatter(0))
    style_axis(ax, "y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), frameon=False)

    ax = axes[1]
    group_handles = []
    for group in ["Large", "Medium", "Small"]:
        part = balanced.loc[balanced["market_size_group"].eq(group)]
        values = [part[col].median() for col in period_columns]
        line, = ax.plot(
            x, values, color=COLORS[group], marker="o", ms=5.8, lw=2.0,
            label=f"{MARKET_LABELS[group]}（N={len(part)}）",
        )
        group_handles.append(line)
    ax.set_xticks(x, period_labels)
    ax.set_title("B 不同市场规模PLF中位数", pad=11)
    ax.yaxis.set_major_formatter(percent_formatter(0))
    style_axis(ax, "y")
    ax.legend(handles=group_handles, loc="upper center", bbox_to_anchor=(0.5, 1.02), frameon=False)

    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.22, wspace=0.14)
    add_bottom_title(fig, bottom_title, 0.018)
    return fig


def plot_a03(metrics, config=DEFAULT_CONFIG, logger=LOGGER,
             bottom_title="附图3 ASK/RPK年度增长关系分时期观察"):
    common = metrics.loc[metrics["common_growth_sample"]].copy()
    common["x"] = common["ASK_growth"] * 100
    common["y"] = common["RPK_growth"] * 100
    panels = [
        (common["Time"].between(config.period_pre_start, config.period_pre_end), f"A {config.period_pre_start}—{config.period_pre_end}"),
        (common["Time"].eq(config.period_shock_year), f"B {config.period_shock_year}"),
        (common["Time"].eq(config.period_recovery_year), f"C {config.period_recovery_year}"),
    ]
    selected = [common.loc[mask].copy() for mask, _ in panels]
    low, high = robust_common_limits(
        [pd.concat([part["x"], part["y"]], ignore_index=True) for part in selected]
    )

    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.2), sharex=True, sharey=True)
    for ax, part, (_, title) in zip(axes, selected, panels):
        ax.scatter(part["x"], part["y"], s=34, alpha=0.62, color=COLORS["ASK"], edgecolors="white", linewidths=0.35)
        ax.plot([low, high], [low, high], color=COLORS["reference"], lw=1.0, ls="--")
        ax.set_xlim(low, high)
        ax.set_ylim(low, high)
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(title, pad=10)
        ax.set_xlabel("ASK年度增长率（%）", labelpad=7)
        ax.xaxis.set_major_formatter(percent_formatter(0))
        ax.yaxis.set_major_formatter(percent_formatter(0))
        style_axis(ax, "both")
        _label_representative_points(ax, part, logger)
    axes[0].set_ylabel("RPK年度增长率（%）", labelpad=8)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.86, bottom=0.22, wspace=0.14)
    add_bottom_title(fig, bottom_title, 0.018)
    return fig


def _label_representative_points(ax, part: pd.DataFrame, logger: logging.Logger) -> None:
    offsets = {"CHN": (8, -16), "USA": (-8, 9), "ZMB": (-8, -15)}
    for code in SCATTER_LABEL_COUNTRIES:
        candidate = part.loc[part["Country Code"].eq(code)]
        if candidate.empty:
            continue
        # One label per country per panel: use the largest absolute deviation.
        row = candidate.loc[candidate["growth_gap"].abs().idxmax()]
        dx, dy = offsets.get(code, (4, 5))
        ax.annotate(code, (row["x"], row["y"]), xytext=(dx, dy), textcoords="offset points",
                    fontsize=9.0, ha="left" if dx >= 0 else "right", va="bottom", clip_on=True)
