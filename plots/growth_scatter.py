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


def plot_f01_period(country_growth, label_mode="selected", label_codes=None, logger=LOGGER):
    sample = country_growth.loc[country_growth["common_growth_sample"] & country_growth["market_size_group"].notna()].copy()
    sample["x"], sample["y"] = sample.ASK_growth * 100, sample.RPK_growth * 100
    low, high = robust_common_limits([sample.x, sample.y])
    fig, ax = plt.subplots(figsize=(8.7, 7.5))
    for group in ["Large", "Medium", "Small"]:
        p = sample.loc[sample.market_size_group.eq(group)]
        ax.scatter(p.x, p.y, s=38, alpha=.68, color=COLORS[group], edgecolors="white", linewidths=.4)
    ax.plot([low,high],[low,high],color=COLORS["reference"],lw=1.2,ls="--")
    ax.set(xlim=(low,high),ylim=(low,high),xlabel="ASK增长率（%）",ylabel="RPK增长率（%）")
    ax.set_aspect("equal",adjustable="box"); ax.xaxis.set_major_formatter(percent_formatter(0)); ax.yaxis.set_major_formatter(percent_formatter(0)); style_axis(ax,"both")
    ax.legend(handles=_market_legend_handles(),loc="upper center",bbox_to_anchor=(.5,1.09),ncol=3,frameon=False)
    codes=set(label_codes or [])
    if label_mode=="largest":
        codes=set(sample.assign(dev=(sample.y-sample.x).abs()).nlargest(10,"dev")["Country Code"])
    if label_mode=="none":codes=set()
    texts=[];offsets=[]
    labelled=sample.loc[sample["Country Code"].isin(codes)].sort_values("Country Code")
    for i,(_,r) in enumerate(labelled.iterrows()):
        # Give adjustText a dispersed deterministic starting position.  This
        # materially reduces collisions when several selected countries sit
        # in the same growth cluster.
        angle=2*math.pi*(i%8)/8 + (math.pi/8 if (i//8)%2 else 0)
        radius=30+10*(i//8);offset=(radius*math.cos(angle),radius*math.sin(angle));offsets.append(offset)
        texts.append(ax.annotate(
            r["Country Code"],xy=(r.x,r.y),xytext=offset,
            textcoords="offset points",fontsize=8.4,ha="center",va="center",annotation_clip=True,
            bbox={"boxstyle":"round,pad=.12","facecolor":"white","edgecolor":"none","alpha":.78},
            arrowprops={"arrowstyle":"-","color":"#7D858C","lw":.5,"shrinkA":3,"shrinkB":3},
        ))
    adjust_text_labels(texts,ax,logger,draw_arrows=False)
    # Annotation offset coordinates are more reliable than data coordinates
    # across Matplotlib backends; restore the dispersed offsets after
    # adjustText has resolved any backend-specific text extents.
    for text,offset in zip(texts,offsets):text.set_position(offset)
    # Some Matplotlib/adjustText combinations report an oversized arrow
    # extent to bbox_inches='tight'.  Export this fully laid-out figure on its
    # native canvas instead; labels themselves are constrained to the axes.
    fig._aviation_native_bbox = True
    fig.subplots_adjust(left=.13,right=.97,top=.88,bottom=.15); add_bottom_title(fig,"图1 ASK与RPK年度增长的同步与偏离",.018)
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
