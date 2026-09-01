from dataclasses import replace
import numpy as np
import pandas as pd
import streamlit as st
from core.catalog import CHARTS,TABLES,source_fields
from core.config import PROJECT_ROOT
from core.view_data import chart_data,country_summary
from plots.registry import render_chart,ChartUnavailable,PLOT_LOCK
from plots.country_detail import plot_country_detail
from plots.country_index import plot_f05
from plots.style import setup_plotting_style
from components.chart_info import sample_info,chart_info
from components.download import chart_downloads,table_downloads,full_download
from utils.export import csv_bytes,xlsx_bytes
import logging

def overview(bundle,font_status):
    m=bundle.metrics
    st.subheader('数据概览')
    st.caption(f'当前Excel：{bundle.loaded.filename}　｜　内容指纹：{bundle.loaded.digest[:12]}　｜　数据来源：{st.session_state.get("source_label", "测试输入")}')
    first=st.columns(3)
    first[0].metric('Data国家数量',f'{m["Country Code"].nunique():,}')
    first[1].metric('Data年份范围',f'{int(m.Time.min())}—{int(m.Time.max())}')
    first[2].metric('ASK/RPK共同增长样本',f'{int(m.common_growth_sample.sum()):,}')
    second=st.columns(3)
    second[0].metric('ASK正值观测',f'{int(m.ASKs.gt(0).sum()):,}')
    second[1].metric('RPK正值观测',f'{int(m.RPKs.gt(0).sum()):,}')
    second[2].metric('方向分析可用国家',f'{len(bundle.direction):,}')
    st.caption(f'ASK非缺失 {m.ASKs.notna().sum():,} · RPK非缺失 {m.RPKs.notna().sum():,} · '
               f'ASK独立同比 {m.ASK_growth.notna().sum():,} · RPK独立同比 {m.RPK_growth.notna().sum():,} · PLF平衡样本 {len(bundle.balanced)}国')
    left,right=st.columns([1.4,1])
    with left:
        st.markdown('#### 数据质量检查')
        if bundle.loaded.direction is None: st.warning('部分分析可用：缺少方向数据工作表。')
        else: st.success('两张分析工作表校验通过，使用原报告计算规则。')
        for note in bundle.warnings: st.warning(note)
        with st.expander('字段检查与完整校验报告'):
            st.dataframe(pd.DataFrame(bundle.loaded.checks),hide_index=True,width='stretch')
            st.text(bundle.loaded.report)
            st.download_button('下载校验报告',bundle.loaded.report.encode('utf-8'),'validation_report.txt',on_click='ignore')
    with right:
        st.markdown('#### 本次分析口径')
        counts=m.drop_duplicates('Country Code').market_size_group.value_counts()
        st.dataframe(pd.DataFrame({'规模':['Large','Medium','Small'],'国家数':[int(counts.get(k,0)) for k in ['Large','Medium','Small']]}),hide_index=True,width='stretch')
        st.write(f'方向分析区间：{bundle.config.direction_start}—{bundle.config.direction_end}')
        if bundle.loaded.direction is not None:
            d=bundle.loaded.direction
            st.caption(f'方向原始数据：{d.country_code.nunique()}国，{int(d.year.min())}—{int(d.year.max())}')
        st.caption('分组使用全样本期平均ASK；疫情与排名分析使用固定研究区间。')
    if not(font_status['times_new_roman'] and font_status['simsun']):
        st.info(f'字体回退：英文 {font_status["latin_family"]}；中文 {font_status["cjk_family"]}。Windows安装指定字体后自动优先使用Times New Roman与宋体。')
    st.divider()
    full_download(bundle)

def chart_controls(bundle,code):
    c=bundle.config
    if code in ('F02','F03'):
        valid=bundle.metrics.loc[bundle.metrics[['ASK_growth','RPK_growth']].notna().any(axis=1),'Time']
        if len(valid) and valid.min()<valid.max():
            lo,hi=int(valid.min()),int(valid.max())
            value=(max(lo,c.trend_year_start or lo),min(hi,c.trend_year_end or hi))
            if value[0]>value[1]: value=(lo,hi)
            selected=st.slider('显示年份范围（不改变同比基期或规模分组）',lo,hi,value,key=f'{code}_range_{bundle.loaded.digest[:12]}')
            if selected!=(c.trend_year_start or lo,c.trend_year_end or hi):
                st.session_state.config=replace(c,trend_year_start=selected[0],trend_year_end=selected[1]);st.rerun()
    if code=='F05':
        names=bundle.metrics.drop_duplicates('Country Code').set_index('Country Code')['Country Name'].to_dict()
        options=list(dict.fromkeys([*c.representative_countries,*sorted(names)]))
        chosen=st.multiselect('选择代表国家（1—12国）',options,default=list(c.representative_countries),
            format_func=lambda x:f'{names.get(x,x)} ({x})',max_selections=12,key='representatives_'+bundle.loaded.digest[:12])
        if chosen and tuple(chosen)!=c.representative_countries:
            st.session_state.config=replace(c,representative_countries=tuple(chosen));st.rerun()
        if not chosen:
            st.info('请至少选择一个国家。');return False
    return True

def chart_page(bundle,module):
    choices=[code for code,info in CHARTS.items() if info[2]==module]
    code=st.selectbox('选择图表',choices,format_func=lambda x:f'{x} · {CHARTS[x][0]}',key='chart_'+module)
    st.subheader(CHARTS[code][0])
    st.caption(CHARTS[code][4])
    if not chart_controls(bundle,code):return
    try:
        cache=st.session_state.setdefault('figure_cache',{})
        if code not in cache:
            with st.spinner('按当前数据绘制图表…'):cache[code]=render_chart(bundle,code)
        fig=cache[code]
        with PLOT_LOCK:st.pyplot(fig,clear_figure=False,width='stretch',dpi=150,bbox_inches='tight')
        sample_info(bundle,code)
        chart_info(bundle,code)
        chart_downloads(fig,chart_data(bundle,code),CHARTS[code][1],code)
        with st.expander('查看当前图的数据'):
            st.dataframe(chart_data(bundle,code),hide_index=True,width='stretch')
    except ChartUnavailable as exc:
        st.warning(str(exc));chart_info(bundle,code)

def table_page(bundle):
    code=st.selectbox('选择统计表',list(TABLES),format_func=lambda x:f'{x} · {TABLES[x][0]}',key='table_id')
    st.subheader(TABLES[code][0]);st.caption(TABLES[code][2])
    if code not in bundle.tables:
        st.warning('当前缺少可用方向数据，请检查country_year_ask_capacity及分析区间。');return
    sheets=bundle.tables[code]
    sheet=st.selectbox('工作表',list(sheets),key='sheet_'+code)
    frame=sheets[sheet].copy()
    query=st.text_input('国家 / ISO / 内容搜索',placeholder='输入国家名称或ISO代码',key='query_'+code)
    if query:
        mask=frame.astype(str).apply(lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)
        frame=frame.loc[mask]
    st.dataframe(frame,hide_index=True,width='stretch',height=min(560,max(200,(len(frame)+1)*35)),
                 column_config={c:st.column_config.NumberColumn(format='%.3f') for c in ['R','ln_R'] if c in frame})
    st.caption(f'显示 {len(frame)} 行。点击列标题排序，宽表可横向滚动；CSV导出当前搜索结果，XLSX保留整张表的所有工作表。')
    table_downloads(code,sheet,frame,sheets)
    with st.expander('数据来源与计算说明'):
        sheet_name,fields=source_fields(code)
        st.write(bundle.loaded.filename)
        st.code('\n'.join(sheet_name+'!'+f for f in fields),language=None)
        st.write(TABLES[code][2])

def country_page(bundle,comparison=False):
    st.subheader('多国对比' if comparison else '单国分析')
    names=bundle.metrics.drop_duplicates('Country Code').set_index('Country Code')['Country Name'].to_dict()
    options=sorted(names,key=lambda c:str(names[c]))
    fmt=lambda x:f'{names[x]} ({x})'
    if comparison:
        default=[c for c in ['CHN','IND','ETH','KEN'] if c in options]
        codes=st.multiselect('选择2—5个国家',options,default=default[:5],max_selections=5,format_func=fmt,key='compare_countries')
        if len(codes)<2:st.info('请至少选择两个国家。');return
    else:
        default=options.index('ETH') if 'ETH' in options else 0
        codes=[st.selectbox('国家',options,index=default,format_func=fmt,key='single_country')]
    summary=country_summary(bundle,codes)
    rename={'Country Code':'ISO','Country Name':'国家','mean_ASK':'平均ASK','mean_RPK':'平均RPK',
        'median_valid_PLF':'有效PLF中位数（%）','n_valid_PLF':'PLF有效年份数','market_size_group':'市场规模组',
        'corr_ask_rpk':'增长相关系数','mean_abs_growth_gap':'平均绝对增长差（百分点）',
        'n_valid':'共同增长有效年数','dynamic_type':'动态类型','mean_ASK_out':'平均ASK_out',
        'mean_ASK_in':'平均ASK_in','R':'R','ln_R':'ln(R)','n_years':'方向有效年份数'}
    display=summary.copy()
    display['mean_abs_growth_gap']*=100
    display=display[[c for c in rename if c in display]].rename(columns=rename)
    if not comparison:
        row=display.iloc[0]
        cards=st.columns(4)
        for target,col in zip(cards,['平均ASK','平均RPK','有效PLF中位数（%）','市场规模组']):
            value=row[col]
            target.metric(col, '无有效数据' if pd.isna(value) else (f'{value:,.2f}' if isinstance(value,(float,int,np.number)) else str(value)))
    st.dataframe(display,hide_index=True,width='stretch')
    st.caption('平均ASK、平均RPK分别取全样本期非缺失值均值；PLF卡片为0<PLF≤100%的年份中位数。'
               '动态指标仅展示达到最低有效年数的国别结果；空值表示样本不足。方向均值采用当前方向分析区间。')
    m=bundle.metrics.loc[bundle.metrics['Country Code'].isin(codes)]
    idx=bundle.all_indices.loc[bundle.all_indices['Country Code'].isin(codes)]
    with PLOT_LOCK:
        setup_plotting_style(logging.getLogger('aviation_dashboard'))
        if comparison:
            fig=plot_f05(idx,replace(bundle.config,representative_countries=tuple(codes)))
            fig.texts[-1].set_text('多国对比 ASK与RPK指数走势')
        else:fig=plot_country_detail(m,idx,fmt(codes[0]))
        st.pyplot(fig,clear_figure=False,width='stretch',dpi=150)
    stem='compare_'+'_'.join(codes) if comparison else 'country_'+codes[0]
    chart_downloads(fig,idx if comparison else m,stem,stem)
    a,b=st.columns(2)
    a.download_button('下载国别指标 CSV',csv_bytes(display),stem+'_summary.csv',on_click='ignore')
    b.download_button('下载国别数据 XLSX',xlsx_bytes({'国别指标':display,'国家年度指标':m,'指数':idx}),stem+'.xlsx',on_click='ignore')

def methods_page():
    st.subheader('数据与方法说明')
    st.caption('每个结果均可追溯到原始字段、样本条件、派生指标和当前参数。')
    st.markdown((PROJECT_ROOT/'DATA_AND_FIGURE_GUIDE.md').read_text(encoding='utf-8'))
