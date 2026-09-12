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

def plot_f04(metrics, config=DEFAULT_CONFIG, logger=LOGGER,
             bottom_title="图4 不同市场规模国家的ASK–RPK同步性与偏离"):
    common = metrics.loc[metrics["common_growth_sample"] & metrics["market_size_group"].notna()].copy()
    rows = []
    for group in ["Large", "Medium", "Small"]:
        part = common.loc[common["market_size_group"].eq(group)]
        rows.append(
            {
                "group": group,
                "corr": part["ASK_growth"].corr(part["RPK_growth"]),
                "mean_abs_gap_pp": part["abs_growth_gap"].mean() * 100,
                "opposite_share_pct": part["opposite_direction"].mean() * 100,
                "N": len(part),
            }
        )
    summary = pd.DataFrame(rows)
    labels = [MARKET_LABELS[group] for group in summary["group"]]
    colors = [COLORS[group] for group in summary["group"]]

    fig, axes = plt.subplots(1, 3, figsize=(14.5, 5.5))
    specs = [
        ("corr", "A ASK–RPK增长相关系数", lambda x: f"{x:.2f}"),
        ("mean_abs_gap_pp", "B 平均绝对增长差", lambda x: f"{x:.1f}pp"),
        ("opposite_share_pct", "C 反方向变化比例", lambda x: f"{x:.1f}%"),
    ]
    for ax, (column, title, formatter) in zip(axes, specs):
        values = summary[column].to_numpy()
        bars = ax.bar(labels, values, color=colors, width=0.62, edgecolor="white", linewidth=0.7)
        ax.axhline(0, color=COLORS["reference"], lw=0.9)
        ax.set_title(title, pad=12)
        if column == "corr":
            lower = min(-0.05, float(np.nanmin(values)) - 0.22)
            upper = max(0.15, float(np.nanmax(values)) + 0.28)
        else:
            lower = 0
            upper = max(float(np.nanmax(values)) * 1.38, 1.0)
        ax.set_ylim(lower, upper)
        if column == "mean_abs_gap_pp":
            ax.set_ylabel("百分点")
        elif column == "opposite_share_pct":
            ax.set_ylabel("占有效共同增长样本（%）")
            ax.yaxis.set_major_formatter(percent_formatter(0))
        style_axis(ax, "y")
        _annotate_bar_panel(ax, bars, values, summary["N"], formatter, 0.035)
    fig.subplots_adjust(left=0.065, right=0.99, top=0.82, bottom=0.22, wspace=0.25)
    add_bottom_title(fig, bottom_title, 0.018)
    return fig


def _annotate_bar_panel(ax, bars, values, n_values, formatter, offset_ratio=0.04):
    ymin, ymax = ax.get_ylim()
    span = ymax - ymin
    for bar, value, n_value in zip(bars, values, n_values):
        if not np.isfinite(value):
            ax.text(bar.get_x() + bar.get_width() / 2, 0, f'无有效值\nN={int(n_value)}',
                    ha='center', va='bottom', fontsize=9.2)
            continue
        offset = span * offset_ratio
        y = value + offset if value >= 0 else value - offset
        va = "bottom" if value >= 0 else "top"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            f"{formatter(value)}\nN={int(n_value)}",
            ha="center",
            va=va,
            fontsize=9.2,
            linespacing=1.25,
            clip_on=False,
        )
