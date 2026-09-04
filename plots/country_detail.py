"""Web-only views of existing raw, index and growth-gap fields."""
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from plots.style import COLORS, style_axis, add_bottom_title

def plot_country_detail(metrics, indices, name):
    fig, axes = plt.subplots(3,1,figsize=(11.0,11.5))
    m = metrics.sort_values('Time')
    m = m.loc[m[['ASKs','RPKs']].notna().any(axis=1)]
    axes[0].plot(m.Time,m.ASKs,color=COLORS['ASK'],label='ASK',lw=1.8,marker='o',ms=4)
    axes[0].plot(m.Time,m.RPKs,color=COLORS['RPK'],label='RPK',lw=1.8,marker='s',ms=4)
    axes[0].set_ylabel('原始数据单位')
    axes[0].set_title('A ASK / RPK原始走势',pad=12)
    if not indices.empty:
        axes[1].plot(indices.Time,indices.ASK_index,color=COLORS['ASK'],lw=1.8,marker='o',ms=4)
        axes[1].plot(indices.Time,indices.RPK_index,color=COLORS['RPK'],lw=1.8,marker='s',ms=4)
    else:
        axes[1].text(.5,.5,'无共同为正基期',transform=axes[1].transAxes,ha='center')
    axes[1].axhline(100,color=COLORS['reference'],ls='--')
    axes[1].set_ylabel('指数（基期=100）')
    axes[1].set_title('B ASK / RPK指数走势',pad=12)
    g=metrics.loc[metrics.common_growth_sample]
    axes[2].bar(g.Time,g.growth_gap*100,color=[COLORS['RPK'] if v>=0 else COLORS['ASK'] for v in g.growth_gap])
    axes[2].axhline(0,color=COLORS['reference'])
    axes[2].set_ylabel('增长差（百分点）')
    axes[2].set_title('C 年度RPK−ASK增长差',pad=12)
    for ax in axes:
        style_axis(ax,'y')
        ax.set_xlabel('年份',labelpad=7)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True,nbins=8))
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',ncol=2,frameon=False)
    fig.subplots_adjust(left=.13,right=.97,top=.92,bottom=.10,hspace=.58)
    add_bottom_title(fig,f'单国分析 {name}',.018)
    plt.close(fig)
    return fig
