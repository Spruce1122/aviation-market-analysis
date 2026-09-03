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

def plot_f07(direction_low, direction_high, config=DEFAULT_CONFIG, logger=LOGGER):
    data = pd.concat([direction_low, direction_high], ignore_index=True).drop_duplicates("country_code").sort_values(["ln_R", "country_code"])
    colors = [COLORS[group] for group in data["extreme_group"]]
    fig, ax = plt.subplots(figsize=(11.5, max(8.6, len(data) * 0.43 + 1.8)))
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
    max_name = max((len(str(name)) for name in data["country_name"]), default=12)
    left = min(0.39, max(0.25, 0.21 + max_name * 0.0045))
    fig.subplots_adjust(left=left, right=0.94, top=0.91, bottom=0.14)
    add_bottom_title(fig, "图7 ASK_out与ASK_in方向不对称国家比较", 0.014)
    return fig


def plot_f07_selected(direction_data, sort_by="ln(R)", single=False, logger=LOGGER):
    data=direction_data.copy()
    if sort_by=="ASK规模":data=data.sort_values(["mean_ASK_out","country_code"])
    elif sort_by=="国家名称":data=data.sort_values(["country_name","country_code"],ascending=False)
    else:data=data.sort_values(["ln_R","country_code"])
    data["extreme_group"]=np.where(data.ln_R.lt(0),"ASK_in相对占优","ASK_out相对占优")
    colors=[COLORS[g] for g in data.extreme_group]
    fig,ax=plt.subplots(figsize=(11.5,max(5.2,len(data)*.43+1.8)))
    bars=ax.barh(data.country_name,data.ln_R,color=colors,height=.68,edgecolor="white")
    ax.axvline(0,color="#666C72",lw=1);style_axis(ax,"x")
    formula="ASK_out / ASK_in" if single else "mean(ASK_out) / mean(ASK_in)"
    ax.set_xlabel(f"ln(R)，R = {formula}")
    min_x,max_x=float(data.ln_R.min()),float(data.ln_R.max());span=max(max_x-min_x,.2);margin=max(span*.2,.1);ax.set_xlim(min_x-margin,max_x+margin)
    for bar,(_,row) in zip(bars,data.iterrows()):
        off=span*.025;x=row.ln_R+off if row.ln_R>=0 else row.ln_R-off
        ax.text(x,bar.get_y()+bar.get_height()/2,f"R={row.R:.2f}",ha="left" if row.ln_R>=0 else "right",va="center",fontsize=9,clip_on=False)
    ax.text(.02,1.015,"ASK_in相对占优",transform=ax.transAxes,color=COLORS["ASK_in相对占优"],ha="left")
    ax.text(.98,1.015,"ASK_out相对占优",transform=ax.transAxes,color=COLORS["ASK_out相对占优"],ha="right")
    max_name=max((len(str(x)) for x in data.country_name),default=12);left=min(.42,max(.25,.21+max_name*.0045))
    fig.subplots_adjust(left=left,right=.94,top=.90,bottom=.14);add_bottom_title(fig,"图7 ASK_out与ASK_in方向不对称国家比较",.012)
    return fig
