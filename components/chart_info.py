import streamlit as st
import pandas as pd
from core.catalog import CHARTS,source_fields
from core.view_data import chart_data,trend_metrics

def sample_info(bundle,code):
    df=chart_data(bundle,code)
    identity='Country Code' if 'Country Code' in df else 'country_code'
    if code in ('F02','F03'):
        df=trend_metrics(bundle)
        df=df.loc[df[['ASK_growth','RPK_growth']].notna().any(axis=1)]
        identity='Country Code'
    if code=='F04':
        df=bundle.metrics.loc[bundle.metrics.common_growth_sample & bundle.metrics.market_size_group.notna()]
        identity='Country Code'
    countries=df[identity].nunique() if identity in df else 0
    year='Time' if 'Time' in df else None
    period=f'{int(df[year].min())}—{int(df[year].max())}' if year and not df.empty else '按本图样本定义'
    if code=='F07': period=f'{bundle.config.direction_start}—{bundle.config.direction_end}'
    if code=='A02': period='2016—2019 / 2020 / 2021'
    a,b,c=st.columns(3)
    a.metric('有效国家',f'{countries:,}')
    b.metric('当前数据行',f'{len(df):,}',help='国家汇总图为国家行；散点与时间序列输入为国家—年份行。')
    c.metric('分析时期',period)

def chart_info(bundle,code):
    sheet,fields=source_fields(code)
    with st.expander('原始数据 → 指标 → 图表 · 查看计算口径',expanded=False):
        st.write('原始Excel：',bundle.loaded.filename)
        st.code('\n'.join(f'{sheet}!{field}' for field in fields),language=None)
        st.markdown('**派生字段**：'+CHARTS[code][3])
        st.write(CHARTS[code][4])
        if code=='F06':
            st.write('顺序：高相关且低绝对差 → ASK相对领先 → RPK相对领先 → 高波动 → 过渡。阈值由当前合格国家样本重算。')
            st.dataframe(bundle.thresholds,hide_index=True,width='stretch')
        if code=='A02':
            st.warning('疫情前的国别汇总为PLF中位数，沿用实际原代码；不使用均值。')
        st.caption(f'文件内容SHA256：{bundle.loaded.digest}')
