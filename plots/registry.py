"""One renderer used by page previews and all downloaded figures."""
import logging
import threading
import numpy as np
import matplotlib.pyplot as plt
from core.view_data import chart_data, trend_metrics
from plots.style import setup_plotting_style
from plots.growth_scatter import plot_f01
from plots.growth_trend import plot_f02
from plots.market_size_trend import plot_f03
from plots.market_sync import plot_f04
from plots.country_index import plot_f05
from plots.dynamic_type import plot_f06
from plots.direction import plot_f07
from plots.covid import plot_a02, plot_a03

PLOT_LOCK = threading.RLock()
LOGGER = logging.getLogger('aviation_dashboard')

class ChartUnavailable(ValueError):
    pass

def render_chart(bundle, code):
    data = chart_data(bundle, code)
    if data.empty:
        raise ChartUnavailable('当前数据或参数下没有满足本图条件的有效样本。请检查数据覆盖和样本要求。')
    if code in ('F02','F03') and not data[['ASK_growth','RPK_growth']].notna().any().any():
        raise ChartUnavailable('当前年份范围内没有有效同比，请调整年份范围。')
    with PLOT_LOCK:
        random_state = np.random.get_state()
        np.random.seed(0)
        try:
            setup_plotting_style(LOGGER)
            m,c = bundle.metrics,bundle.config
            if code=='F01': fig=plot_f01(m,c)
            elif code=='F02': fig=plot_f02(trend_metrics(bundle),c)
            elif code=='F03': fig=plot_f03(trend_metrics(bundle),c)
            elif code=='F04': fig=plot_f04(m,c)
            elif code=='F05': fig=plot_f05(bundle.indices,c)
            elif code=='F06': fig=plot_f06(bundle.dynamic,c)
            elif code=='F07': fig=plot_f07(bundle.direction_low,bundle.direction_high,c)
            elif code=='A01': fig=plot_f05(bundle.indices,c,bottom_title='附图1 自选国家ASK/RPK指数比较')
            elif code=='A02': fig=plot_a02(m,c)
            elif code=='A03': fig=plot_a03(m,c)
            else: raise KeyError(code)
            plt.close(fig)  # Remove pyplot global registry; Figure remains usable by st.pyplot/savefig.
            return fig
        finally:
            np.random.set_state(random_state)
