"""Generate F01–F07 from shared processed DataFrames."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

from .config import (
    CORE_FIGURE_DIR,
    F06_AUTO_LABEL_EACH_TAIL,
    F06_FIXED_LABEL_COUNTRIES,
    REPRESENTATIVE_COUNTRIES,
)
from .plotting_style import (
    COLORS,
    MARKET_LABELS,
    add_bottom_title,
    adjust_text_labels,
    percent_formatter,
    robust_common_limits,
    save_figure,
    style_axis,
)


def _market_legend_handles():
    return [
        Line2D(
            [0], [0], marker="o", linestyle="", markersize=7,
            markerfacecolor=COLORS[group], markeredgecolor="white",
            label=MARKET_LABELS[group],
        )
        for group in ["Large", "Medium", "Small"]
    ]


def make_f01(metrics: pd.DataFrame, logger: logging.Logger) -> Path:
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
    path = CORE_FIGURE_DIR / "F01_ASK_RPK年度增长同步与偏离.png"
    save_figure(fig, path)
    logger.info("F01完成，共同增长样本=%d，显示范围=[%.2f, %.2f]%%", len(sample), low, high)
    return path


def make_f02(metrics: pd.DataFrame, logger: logging.Logger) -> Path:
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
    add_bottom_title(fig, "图2 ASK与RPK年度增长率中位数趋势", 0.018)
    path = CORE_FIGURE_DIR / "F02_ASK_RPK年度增长率中位数趋势.png"
    save_figure(fig, path)
    logger.info("F02完成，ASK年份=%d，RPK年份=%d", ask.size, rpk.size)
    return path


def make_f03(metrics: pd.DataFrame, logger: logging.Logger) -> Path:
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
    path = CORE_FIGURE_DIR / "F03_不同规模市场ASK_RPK增长趋势.png"
    save_figure(fig, path)
    logger.info("F03完成")
    return path


def _annotate_bar_panel(ax, bars, values, n_values, formatter, offset_ratio=0.04):
    ymin, ymax = ax.get_ylim()
    span = ymax - ymin
    for bar, value, n_value in zip(bars, values, n_values):
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


def make_f04(metrics: pd.DataFrame, logger: logging.Logger) -> Path:
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
    add_bottom_title(fig, "图4 不同市场规模国家的ASK–RPK同步性与偏离", 0.018)
    path = CORE_FIGURE_DIR / "F04_市场规模ASK_RPK同步性与偏离.png"
    save_figure(fig, path)
    logger.info("F04完成: %s", summary.to_dict("records"))
    return path


def make_f05(index_data: pd.DataFrame, logger: logging.Logger) -> Path:
    fig, axes = plt.subplots(4, 3, figsize=(12.4, 12.8), sharex=True)
    axes_flat = axes.ravel()
    for ax, code in zip(axes_flat, REPRESENTATIVE_COUNTRIES):
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
    for row in range(4):
        axes[row, 0].set_ylabel("指数（基期=100）")
    for ax in axes[-1, :]:
        ax.set_xlabel("年份", labelpad=7)
        ax.tick_params(axis="x", rotation=0)
    handles = [
        Line2D([0], [0], color=COLORS["ASK"], marker="o", lw=2, label="ASK"),
        Line2D([0], [0], color=COLORS["RPK"], marker="s", lw=2, label="RPK"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.93, bottom=0.09, wspace=0.22, hspace=0.34)
    add_bottom_title(fig, "图5 代表性国家ASK与RPK指数走势", 0.014)
    path = CORE_FIGURE_DIR / "F05_代表性国家ASK_RPK指数走势.png"
    save_figure(fig, path)
    logger.info("F05完成，国家数=%d", index_data["Country Code"].nunique())
    return path


def make_f06(country_dynamic: pd.DataFrame, logger: logging.Logger) -> Path:
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

    label_codes = set(F06_FIXED_LABEL_COUNTRIES)
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
    path = CORE_FIGURE_DIR / "F06_国家动态关系类型散点图.png"
    save_figure(fig, path)
    logger.info("F06完成，国家数=%d，标注数=%d", len(plot_data), len(label_data))
    return path


def make_f07(direction_low: pd.DataFrame, direction_high: pd.DataFrame, logger: logging.Logger) -> Path:
    data = pd.concat([direction_low, direction_high], ignore_index=True).sort_values(["ln_R", "country_code"])
    colors = [COLORS[group] for group in data["extreme_group"]]
    fig, ax = plt.subplots(figsize=(10.0, 8.6))
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
    add_bottom_title(fig, "图7 ASK_out与ASK_in方向不对称国家比较", 0.014)
    path = CORE_FIGURE_DIR / "F07_ASK_out_in方向不对称.png"
    save_figure(fig, path)
    logger.info("F07完成，国家数=%d", len(data))
    return path


def make_all_core_figures(
    metrics: pd.DataFrame,
    index_data: pd.DataFrame,
    country_dynamic: pd.DataFrame,
    direction_low: pd.DataFrame,
    direction_high: pd.DataFrame,
    logger: logging.Logger,
) -> list[Path]:
    return [
        make_f01(metrics, logger),
        make_f02(metrics, logger),
        make_f03(metrics, logger),
        make_f04(metrics, logger),
        make_f05(index_data, logger),
        make_f06(country_dynamic, logger),
        make_f07(direction_low, direction_high, logger),
    ]
