"""Period-aware ASK/RPK level comparisons for selected countries."""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from core.period_analysis import UNIT_SCALE
from plots.style import COLORS, add_bottom_title, style_axis


def plot_a01_levels(summary, single=False, title="附图1 自选国家ASK/RPK规模比较"):
    data=summary.dropna(subset=["ASK","RPK"],how="all").copy()
    data["ASK_display"],data["RPK_display"]=data.ASK/UNIT_SCALE,data.RPK/UNIT_SCALE
    data=data.sort_values("ASK_display",ascending=True)
    y=np.arange(len(data)); h=.36
    fig,ax=plt.subplots(figsize=(11.2,max(5.0,len(data)*.42+1.8)))
    ax.barh(y+h/2,data.ASK_display,height=h,color=COLORS["ASK"],label="ASK")
    ax.barh(y-h/2,data.RPK_display,height=h,color=COLORS["RPK"],label="RPK")
    ax.set_yticks(y,[f"{n} ({c})" for n,c in zip(data["Country Name"],data["Country Code"])])
    prefix="当年" if single else "时期平均"
    ax.set_xlabel(f"{prefix}展示值（ASK：亿座公里；RPK：亿客公里）")
    ax.legend(loc="upper center",bbox_to_anchor=(.5,1.04),ncol=2,frameon=False);style_axis(ax,"x")
    fig.subplots_adjust(left=.27,right=.98,top=.91,bottom=.13);add_bottom_title(fig,title,.012)
    return fig
