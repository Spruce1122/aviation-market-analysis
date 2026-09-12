"""Generate A01–A03 from shared processed DataFrames."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from .config import (
    ADDITIONAL_FIGURE_DIR,
    MIN_VALID_GROWTH_YEARS,
    N_GROWTH_GAP_EXTREMES,
    PANDEMIC_PRE_END,
    PANDEMIC_PRE_MIN_OBS,
    PANDEMIC_PRE_START,
    PANDEMIC_RECOVERY_YEAR,
    PANDEMIC_SHOCK_YEAR,
    SCATTER_LABEL_COUNTRIES,
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


def make_a01(country_dynamic: pd.DataFrame, logger: logging.Logger) -> Path:
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
    path = ADDITIONAL_FIGURE_DIR / "A01_国家层面ASK_RPK增长领先比较.png"
    save_figure(fig, path)
    logger.info("A01完成，国家数=%d", len(data))
    return path


def build_balanced_pandemic_plf(metrics: pd.DataFrame) -> pd.DataFrame:
    """Construct one country-level PLF value per period for a balanced sample."""
    valid = metrics.loc[metrics["PLF"].gt(0) & metrics["PLF"].le(100)].copy()
    pre = valid.loc[valid["Time"].between(PANDEMIC_PRE_START, PANDEMIC_PRE_END)]
    pre_stats = (
        pre.groupby("Country Code")
        .agg(pre_plf=("PLF", "median"), pre_n=("PLF", "count"))
        .reset_index()
    )
    shock = valid.loc[valid["Time"].eq(PANDEMIC_SHOCK_YEAR), ["Country Code", "PLF"]].rename(
        columns={"PLF": "shock_plf"}
    )
    recovery = valid.loc[
        valid["Time"].eq(PANDEMIC_RECOVERY_YEAR), ["Country Code", "PLF"]
    ].rename(columns={"PLF": "recovery_plf"})
    identity = (
        metrics.sort_values("Time")
        .drop_duplicates("Country Code", keep="last")
        [["Country Code", "Country Name", "market_size_group"]]
    )
    balanced = pre_stats.merge(shock, on="Country Code", how="inner").merge(
        recovery, on="Country Code", how="inner"
    )
    balanced = balanced.loc[balanced["pre_n"].ge(PANDEMIC_PRE_MIN_OBS)].merge(
        identity, on="Country Code", how="left"
    )
    return balanced


def make_a02(metrics: pd.DataFrame, logger: logging.Logger) -> tuple[Path, pd.DataFrame]:
    balanced = build_balanced_pandemic_plf(metrics)
    period_columns = ["pre_plf", "shock_plf", "recovery_plf"]
    period_labels = ["疫情前\n2016—2019", "疫情冲击\n2020", "初步恢复\n2021"]
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
    add_bottom_title(fig, "附图2 疫情冲击前后PLF变化", 0.018)
    path = ADDITIONAL_FIGURE_DIR / "A02_疫情冲击前后PLF变化.png"
    save_figure(fig, path)
    logger.info("A02完成，平衡样本国家数=%d", len(balanced))
    return path, balanced


def _label_representative_points(ax, part: pd.DataFrame, logger: logging.Logger) -> None:
    labels = []
    for code in SCATTER_LABEL_COUNTRIES:
        candidate = part.loc[part["Country Code"].eq(code)]
        if candidate.empty:
            continue
        # One label per country per panel: use the largest absolute deviation.
        row = candidate.loc[candidate["growth_gap"].abs().idxmax()]
        labels.append(
            ax.text(row["x"], row["y"], code, fontsize=9.0, ha="center", va="bottom", clip_on=True)
        )
    adjust_text_labels(labels, ax, logger)


def make_a03(metrics: pd.DataFrame, logger: logging.Logger) -> Path:
    common = metrics.loc[metrics["common_growth_sample"]].copy()
    common["x"] = common["ASK_growth"] * 100
    common["y"] = common["RPK_growth"] * 100
    panels = [
        (common["Time"].between(PANDEMIC_PRE_START, PANDEMIC_PRE_END), "A 疫情前2016—2019"),
        (common["Time"].eq(PANDEMIC_SHOCK_YEAR), "B 2020"),
        (common["Time"].eq(PANDEMIC_RECOVERY_YEAR), "C 2021"),
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
    add_bottom_title(fig, "附图3 疫情前后ASK与RPK增长关系", 0.018)
    path = ADDITIONAL_FIGURE_DIR / "A03_疫情前后ASK_RPK增长关系.png"
    save_figure(fig, path)
    logger.info("A03完成，显示范围=[%.2f, %.2f]%%", low, high)
    return path


def make_all_additional_figures(
    metrics: pd.DataFrame,
    country_dynamic: pd.DataFrame,
    logger: logging.Logger,
) -> tuple[list[Path], pd.DataFrame]:
    a01 = make_a01(country_dynamic, logger)
    a02, balanced = make_a02(metrics, logger)
    a03 = make_a03(metrics, logger)
    return [a01, a02, a03], balanced
