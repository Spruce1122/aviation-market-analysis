"""Period-aware Streamlit pages using static HTML/PNG result rendering."""
from __future__ import annotations

from dataclasses import replace
import logging
import numpy as np
import pandas as pd
import streamlit as st

from components.download import chart_downloads
from components.safe_render import render_analysis_context, render_figure_html, render_kpi_cards, render_message, render_table_html
from components.time_selector import mode_text, period_slug, period_text, select_year_range
from core.ask_rpk_metrics import build_country_dynamic_metrics, build_representative_index_data
from core.catalog import CHARTS, TABLES, source_fields
from core.config import ASK_DIRECTION_END, ASK_DIRECTION_START, PROJECT_ROOT, RANKING_END_YEAR, RANKING_START_YEAR
from core.period_analysis import (UNIT_SCALE, annual_country_detail, country_mean_growth, direction_display,
    direction_extremes, direction_for_period, level_summary, market_sync_summary, period_growth_rows,
    plf_year_summary, ranking_for_period, t02_for_period)
from plots.country_index import plot_f05
from plots.covid import plot_a02_period, plot_a03_period
from plots.direction import plot_f07_selected
from plots.dynamic_type import plot_f06
from plots.growth_scatter import plot_f01_period
from plots.growth_trend import plot_f02
from plots.level_compare import plot_a01_levels
from plots.market_size_trend import plot_f03
from plots.market_sync import plot_f04
from plots.registry import PLOT_LOCK
from plots.style import setup_plotting_style
from utils.export import csv_bytes, xlsx_bytes

LOGGER = logging.getLogger("aviation_dashboard")
RESULT_ERROR = "当前结果暂时无法生成，请检查数据覆盖范围。"


def _country_options(bundle):
    identity=bundle.metrics.sort_values("Time").drop_duplicates("Country Code",keep="last")
    names=identity.set_index("Country Code")["Country Name"].to_dict()
    return names,sorted(names,key=lambda code:(str(names[code]),code))


def _figure(key,builder):
    cache=st.session_state.setdefault("figure_cache",{})
    if key not in cache:
        with PLOT_LOCK:
            setup_plotting_style(LOGGER)
            cache[key]=builder()
    return cache[key]


def _render_downloads(fig,data,stem,key):
    chart_downloads(fig,data,stem,key)
    with st.expander("查看当前图数据（预览前100行）"):
        render_table_html(data,max_rows=100,caption=f"预览前100行；完整数据共{len(data):,}行。")


def _context(start,end,mode,extra=()):
    return [("时期",period_text(start,end)),("模式",mode_text(mode)),("区间年份",end-start+1),*extra]


def _growth_display(frame):
    """Build a download-safe table with percentages and explicit units."""
    result=frame.copy()
    rename={
        "Country Name":"国家","Country Code":"ISO","Time":"年份",
        "ASK_growth":"ASK增长率（%）","RPK_growth":"RPK增长率（%）",
        "growth_gap":"增长差（百分点）","abs_growth_gap":"增长差绝对值（百分点）",
    }
    for source in ["ASK_growth","RPK_growth","growth_gap","abs_growth_gap"]:
        if source in result:
            result[source]=result[source]*100
    return result.rename(columns={k:v for k,v in rename.items() if k in result.columns})


def _clamp_int_state(key,minimum,maximum,default):
    current=int(st.session_state.get(key,default))
    st.session_state[key]=min(max(current,minimum),maximum)


def overview(bundle,font_status):
    m=bundle.metrics
    st.subheader("数据概览")
    st.caption(f"当前Excel：{bundle.loaded.filename}　｜　内容指纹：{bundle.loaded.digest[:12]}　｜　数据仅在当前会话处理")
    render_kpi_cards([("Data国家数量",f"{m['Country Code'].nunique():,}"),("Data年份范围",f"{int(m.Time.min())}—{int(m.Time.max())}"),
        ("ASK/RPK共同增长样本",f"{int(m.common_growth_sample.sum()):,}"),("ASK正值观测",f"{int(m.ASKs.gt(0).sum()):,}"),
        ("RPK正值观测",f"{int(m.RPKs.gt(0).sum()):,}"),("方向原始国家",f"{0 if bundle.loaded.direction is None else bundle.loaded.direction.country_code.nunique():,}")])
    if bundle.loaded.direction is None:render_message("部分分析可用：当前Excel缺少country_year_ask_capacity工作表。","warning")
    else:render_message("两张分析工作表均已通过结构与数值校验。","success")
    for note in bundle.warnings:render_message(note,"warning")
    with st.expander("字段检查与完整校验报告"):
        render_table_html(pd.DataFrame(bundle.loaded.checks),max_rows=100);st.text(bundle.loaded.report)
        st.download_button("下载校验报告",bundle.loaded.report.encode("utf-8"),"validation_report.txt",on_click="ignore")
    counts=m.drop_duplicates("Country Code").market_size_group.value_counts()
    render_table_html(pd.DataFrame({"固定规模组":["Large","Medium","Small"],"国家数":[int(counts.get(x,0)) for x in ["Large","Medium","Small"]]}))
    st.caption("市场规模组始终按完整输入期平均ASK确定：前40国Large、后40国Small、其余Medium；选择时期不会重分组。")
    if not(font_status["times_new_roman"] and font_status["simsun"]):render_message(f"服务器字体回退：英文{font_status['latin_family']}；中文{font_status['cjk_family']}。")


def chart_page(bundle,module):
    lo,hi=int(bundle.metrics.Time.min()),int(bundle.metrics.Time.max())
    if st.button("恢复默认设置",key="ask_rpk_reset"):
        st.session_state["ask_rpk_chart"]="F01";st.session_state["ask_rpk_start_year"]=lo;st.session_state["ask_rpk_end_year"]=hi
        st.session_state["f01_label_mode"]="仅标注选择国家";st.session_state["f01_countries"]=[c for c in ["CHN","USA","IND","ETH","KEN","ZMB"] if c in set(bundle.metrics["Country Code"])]
    choices=["F01","F02","F03","F04"]
    code=st.selectbox("选择图表",choices,format_func=lambda x:f"{x} · {CHARTS[x][0]}",key="ask_rpk_chart")
    start,end,mode=select_year_range(bundle.metrics,"ask_rpk",column="Time",show_reset=False)
    names,options=_country_options(bundle)
    label_mode="不标注";selected=[]
    if code=="F01":
        label_mode=st.radio("国家标签",["不标注","仅标注选择国家","标注偏离最大10国"],index=1,horizontal=True,key="f01_label_mode")
        if label_mode=="仅标注选择国家":
            defaults=[c for c in ["CHN","USA","IND","ETH","KEN","ZMB"] if c in options]
            selected=st.multiselect("标注国家",options,default=defaults,max_selections=30,format_func=lambda c:f"{names[c]} ({c})",key="f01_countries")
    render_analysis_context("当前分析条件",_context(start,end,mode,[("图表",code),("标注",label_mode)]))
    try:
        filtered=period_growth_rows(bundle.metrics,start,end)
        if code=="F01":
            data=country_mean_growth(bundle.metrics,start,end)
            key=(code,bundle.loaded.digest,tuple(selected),start,end,label_mode)
            lm={"不标注":"none","仅标注选择国家":"selected","标注偏离最大10国":"largest"}[label_mode]
            fig=_figure(key,lambda:plot_f01_period(data,lm,selected))
            download_data=_growth_display(data)
        elif code=="F02":
            data=filtered.groupby("Time").agg(ASK_growth=("ASK_growth","median"),RPK_growth=("RPK_growth","median"),ASK_N=("ASK_growth","count"),RPK_N=("RPK_growth","count")).reset_index()
            fig=_figure((code,bundle.loaded.digest,start,end),lambda:plot_f02(filtered,bundle.config))
            download_data=_growth_display(data)
            if mode=="single":render_message("单年趋势只有一个时间点。","warning")
        elif code=="F03":
            data=filtered.groupby(["market_size_group","Time"]).agg(ASK_growth=("ASK_growth","median"),RPK_growth=("RPK_growth","median"),ASK_N=("ASK_growth","count"),RPK_N=("RPK_growth","count")).reset_index()
            fig=_figure((code,bundle.loaded.digest,start,end),lambda:plot_f03(filtered,bundle.config))
            download_data=_growth_display(data)
        else:
            data=market_sync_summary(bundle.metrics,start,end)
            fig=_figure((code,bundle.loaded.digest,start,end),lambda:plot_f04(filtered,bundle.config))
            download_data=data
        render_figure_html(fig,CHARTS[code][0]);render_kpi_cards([("有效国家",f"{filtered.loc[filtered.common_growth_sample,'Country Code'].nunique():,}"),("有效国家—年份",f"{int(filtered.common_growth_sample.sum()):,}")])
        stem=f"{code}_{period_slug(start,end)}";_render_downloads(fig,download_data,stem,stem)
    except Exception:
        LOGGER.exception("ASK/RPK chart failed: %s",code);render_message(RESULT_ERROR,"warning")


def dynamic_page(bundle):
    st.subheader("国家动态分析")
    names,options=_country_options(bundle);defaults=[c for c in bundle.config.representative_countries if c in options]
    if st.button("恢复默认设置",key="dynamic_reset"):
        st.session_state["dynamic_countries"]=defaults;st.session_state["dynamic_start_year"]=int(bundle.metrics.Time.min());st.session_state["dynamic_end_year"]=int(bundle.metrics.Time.max())
        st.session_state["dynamic_chart"]="A01";st.session_state["a01_display"]="绝对规模"
    selected=st.multiselect("选择国家（1—30国）",options,default=defaults,max_selections=30,format_func=lambda c:f"{names[c]} ({c})",key="dynamic_countries")
    start,end,mode=select_year_range(bundle.metrics,"dynamic",column="Time",show_reset=False)
    code=st.selectbox("选择图表",["A01","F05","F06"],format_func=lambda x:f"{x} · {CHARTS[x][0]}",key="dynamic_chart")
    display_mode=st.radio("展示方式",["绝对规模","指数化比较"],horizontal=True,key="a01_display") if code=="A01" else None
    render_analysis_context("当前分析条件",_context(start,end,mode,[("国家","、".join(selected[:6])+("等" if len(selected)>6 else "")),("已选择国家",len(selected)),("图表",code),*( [("展示方式",display_mode)] if display_mode else [] )]))
    if not selected:render_message("请至少选择一个国家。","warning");return
    try:
        stem_countries="_".join(selected) if len(selected)<=5 else f"{len(selected)}countries"
        config=replace(bundle.config,representative_countries=tuple(selected))
        if code=="F06":
            if end-start+1<3:
                render_message("该指标需要至少3个有效年度增长观测。当前时间范围不足，请扩大时间区间。","warning");return
            period=period_growth_rows(bundle.metrics,start,end)
            try:dynamic,thresholds=build_country_dynamic_metrics(period,replace(bundle.config,min_dynamic_years=3))
            except ValueError:
                render_message("该指标需要至少3个有效年度增长观测。当前时间范围不足，请扩大时间区间。","warning");return
            data=dynamic.copy()
            for source,label in [("median_growth_gap","增长差中位数（百分点）"),("mean_abs_growth_gap","平均绝对增长差（百分点）"),("opposite_share","反方向比例（%）"),("growth_gap_std","增长差标准差（百分点）")]:
                data[label]=data[source]*100
            data=data[["Country Name","Country Code","corr_ask_rpk","增长差中位数（百分点）","平均绝对增长差（百分点）","反方向比例（%）","增长差标准差（百分点）","n_valid","dynamic_type"]].rename(columns={"Country Name":"国家","Country Code":"ISO","corr_ask_rpk":"ASK/RPK增长相关系数","n_valid":"有效同比年份数","dynamic_type":"动态类型"})
            fig=_figure((code,bundle.loaded.digest,tuple(selected),start,end),lambda:plot_f06(dynamic,config,highlight_codes=selected))
            render_table_html(thresholds,max_rows=20,caption="当前时期重新计算的分类阈值")
        else:
            levels=level_summary(bundle.metrics,start,end,selected)
            indices=build_representative_index_data(bundle.metrics,selected,start,end)
            unavailable=[f"{names[c]} ({c})" for c in selected if c not in set(indices["Country Code"].unique())]
            if unavailable:render_message("所选时期无ASK与RPK共同正值基期："+"、".join(unavailable),"warning")
            use_index=(code=="F05" or display_mode=="指数化比较") and mode=="multi"
            if mode=="single" and (code=="F05" or display_mode=="指数化比较"):
                render_message("单年模式下指数走势无法形成时间变化，已切换为当年ASK/RPK规模比较。","warning")
            if use_index:
                data=indices;title="图5 自选国家ASK/RPK指数走势" if code=="F05" else "附图1 自选国家ASK/RPK指数化比较"
                fig=_figure((code,bundle.loaded.digest,tuple(selected),start,end,"index"),lambda:plot_f05(indices,config,bottom_title=title))
            else:
                data=levels[["Country Name","Country Code","ASK_valid_years","RPK_valid_years","pair_valid_years","period_years","period_PLF"]].copy()
                data["ASK（亿座公里）"]=levels.ASK/UNIT_SCALE;data["RPK（亿客公里）"]=levels.RPK/UNIT_SCALE
                data=data.rename(columns={"Country Name":"国家","Country Code":"ISO","ASK_valid_years":"ASK有效年份数","RPK_valid_years":"RPK有效年份数","pair_valid_years":"共同有效年份数","period_years":"时期年份数","period_PLF":"区间PLF（%）"})
                title="附图1 自选国家ASK/RPK规模比较" if code=="A01" else "图5 单年ASK/RPK规模比较"
                fig=_figure((code,bundle.loaded.digest,tuple(selected),start,end,"level"),lambda:plot_a01_levels(levels,mode=="single",title))
        render_figure_html(fig,CHARTS[code][0]);render_kpi_cards([("已选择国家",len(selected)),("ASK有效国家",int(level_summary(bundle.metrics,start,end,selected).ASK.notna().sum())),("RPK有效国家",int(level_summary(bundle.metrics,start,end,selected).RPK.notna().sum()))])
        stem=f"{code}_{stem_countries}_{period_slug(start,end)}";_render_downloads(fig,data,stem,stem)
    except Exception:
        LOGGER.exception("Dynamic chart failed: %s",code);render_message(RESULT_ERROR,"warning")


def direction_page(bundle):
    st.subheader("ASK方向结构")
    if bundle.loaded.direction is None:render_message("当前Excel没有满足ASK方向分析条件的数据。","warning");return
    raw=bundle.loaded.direction;all_years=sorted(raw.year.unique())
    default_start=max(min(all_years),ASK_DIRECTION_START);default_end=min(max(all_years),ASK_DIRECTION_END)
    names=raw.sort_values("year").drop_duplicates("country_code",keep="last").set_index("country_code").country_name.to_dict();options=sorted(names,key=lambda c:(names[c],c))
    default_ext=direction_extremes(direction_for_period(raw,default_start,default_end),9);defaults=[c for c in default_ext.country_code if c in options]
    if st.button("恢复默认设置",key="direction_reset"):
        st.session_state["direction_countries"]=defaults;st.session_state["direction_start_year"]=default_start;st.session_state["direction_end_year"]=default_end;st.session_state["direction_sort"]="ln(R)"
    start,end,mode=select_year_range(raw,"direction",ASK_DIRECTION_START,ASK_DIRECTION_END,"year",show_reset=False)
    period=direction_for_period(raw,start,end)
    selected=st.multiselect("选择国家（最多30国）",options,default=defaults,max_selections=30,format_func=lambda c:f"{names[c]} ({c})",key="direction_countries")
    if selected==defaults:render_message("当前使用默认示例国家，可自行修改。")
    sort_by=st.radio("排序方式",["ln(R)","ASK规模","国家名称"],horizontal=True,key="direction_sort")
    render_analysis_context("当前方向分析",_context(start,end,mode,[("国家","、".join(selected[:6])+("等" if len(selected)>6 else "")),("已选择国家",len(selected)),("排序",sort_by)]))
    if not selected:render_message("请至少选择一个国家。","warning");return
    data=period.loc[period.country_code.isin(selected)].copy()
    missing=[f"{names[c]} ({c})" for c in selected if c not in set(data.country_code)]
    if missing:render_message("所选时期缺少有效ASK_out/ASK_in："+"、".join(missing),"warning")
    if data.empty:render_message("当前Excel没有满足ASK方向分析条件的数据。","warning");return
    try:
        fig=_figure(("F07",bundle.loaded.digest,tuple(selected),start,end,sort_by),lambda:plot_f07_selected(data,sort_by,mode=="single"))
        render_figure_html(fig,CHARTS["F07"][0]);render_kpi_cards([("有效国家",len(data)),("R中位数",f"{data.R.median():.3f}"),("ln(R)中位数",f"{data.ln_R.median():.3f}")])
        shown=direction_display(data,start,end);stem=f"F07_{len(selected)}countries_{period_slug(start,end)}";_render_downloads(fig,shown,stem,stem)
        render_table_html(shown,max_rows=30,caption="当前选择国家的方向指标")
    except Exception:
        LOGGER.exception("Direction page failed");render_message(RESULT_ERROR,"warning")


def period_page(bundle):
    lo,hi=int(bundle.metrics.Time.min()),int(bundle.metrics.Time.max())
    if st.button("恢复默认设置",key="period_reset"):
        st.session_state["period_chart"]="A02";st.session_state["period_start_year"]=lo;st.session_state["period_end_year"]=hi
        st.session_state.pop("a03_years",None)
    st.subheader("时期扩展分析")
    code=st.selectbox("选择图表",["A02","A03"],format_func=lambda x:f"{x} · {CHARTS[x][0]}",key="period_chart")
    start,end,mode=select_year_range(bundle.metrics,"period",column="Time",show_reset=False)
    years=[int(y) for y in sorted(bundle.metrics.loc[bundle.metrics.Time.between(start,end),"Time"].unique())];shown_years=years
    if code=="A03" and len(years)>6:
        defaults=[years[0],*years[-5:]]
        shown_years=st.multiselect("展示年份（最多6个）",years,default=defaults,max_selections=6,key="a03_years")
    render_analysis_context("当前分析条件",_context(start,end,mode,[("图表",code),("展示年份","、".join(map(str,shown_years)) if code=="A03" else "全部")]))
    try:
        if code=="A02":
            overall,groups,raw=plf_year_summary(bundle.metrics,start,end);data=overall.merge(groups.pivot(index="Time",columns="market_size_group",values="median").reset_index(),on="Time",how="left")
            fig=_figure((code,bundle.loaded.digest,start,end),lambda:plot_a02_period(overall,groups,mode=="single"))
        else:
            if not shown_years:render_message("请至少选择一个展示年份。","warning");return
            raw=period_growth_rows(bundle.metrics,min(shown_years),max(shown_years));data=_growth_display(raw.loc[raw.Time.isin(shown_years)&raw.common_growth_sample].copy())
            fig=_figure((code,bundle.loaded.digest,start,end,tuple(shown_years)),lambda:plot_a03_period(bundle.metrics,shown_years))
        render_figure_html(fig,CHARTS[code][0]);render_kpi_cards([("有效国家",data["Country Code"].nunique() if "Country Code" in data else int(raw["Country Code"].nunique())),("数据行",len(data))])
        years_suffix="_"+"-".join(map(str,shown_years)) if code=="A03" and shown_years!=years else ""
        stem=f"{code}_{period_slug(start,end)}{years_suffix}";_render_downloads(fig,data,stem,stem)
    except Exception:
        LOGGER.exception("Period page failed: %s",code);render_message(RESULT_ERROR,"warning")


def _ranking_page(bundle):
    if st.button("恢复默认设置",key="ranking_reset"):
        st.session_state["ranking_metric"]="ASK";st.session_state["ranking_start_year"]=max(int(bundle.metrics.Time.min()),RANKING_START_YEAR);st.session_state["ranking_end_year"]=min(int(bundle.metrics.Time.max()),RANKING_END_YEAR);st.session_state["ranking_top_n"]=10
    metric=st.radio("排名指标",["ASK","RPK"],horizontal=True,key="ranking_metric")
    start,end,mode=select_year_range(bundle.metrics,"ranking",RANKING_START_YEAR,RANKING_END_YEAR,"Time",show_reset=False)
    ranking=ranking_for_period(bundle.metrics,start,end,metric);max_n=max(1,len(ranking))
    _clamp_int_state("ranking_top_n",1,max_n,min(10,max_n))
    top_n=int(st.number_input("显示前N名",1,max_n,min(10,max_n),1,key="ranking_top_n"));shown=ranking.head(top_n)
    rank_col=f"{metric}_rank";cols=[rank_col,"Country Name","Country Code","有效年份","ASK（亿座公里）","RPK（亿客公里）","区间PLF（%）"]
    unit_names={"ASK（亿座公里）":"平均ASK（亿座公里）","RPK（亿客公里）":"平均RPK（亿客公里）"} if mode=="multi" else {}
    rename={rank_col:f"{metric}排名","Country Name":"国家","Country Code":"ISO",**unit_names}
    display=shown[cols].rename(columns=rename)
    render_analysis_context("当前排名条件",_context(start,end,mode,[("指标",metric),("有效国家",len(ranking)),("显示",f"Top {top_n}")]))
    level_cols=[c for c in display.columns if "亿座公里" in c or "亿客公里" in c]
    render_table_html(display,max_rows=top_n,formats={**{c:"{:,.2f}" for c in level_cols},"区间PLF（%）":"{:.2f}%"})
    slug=period_slug(start,end);a,b=st.columns(2)
    a.download_button("下载当前TopN CSV",csv_bytes(display),f"T01_{metric}_Top{top_n}_{slug}.csv","text/csv",key="t01_csv",on_click="ignore",width="stretch")
    full_display=ranking[cols].rename(columns=rename)
    b.download_button("下载完整排名 XLSX",xlsx_bytes({"完整排名":full_display}),f"T01_{metric}_Top{top_n}_{slug}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key="t01_xlsx",on_click="ignore",width="stretch")
    st.markdown("#### 国家年度明细查询")
    names,options=_country_options(bundle);code=st.selectbox("选择国家",options,format_func=lambda c:f"{names[c]} ({c})",key="annual_country")
    years=sorted(bundle.metrics.Time.unique());year=st.selectbox("选择年份",years,index=years.index(end) if end in years else len(years)-1,key="annual_year")
    d=annual_country_detail(bundle.metrics,code,int(year));render_analysis_context("国家年度查询",[("国家",f"{names[code]} ({code})"),("年份",int(year))])
    def value(x,fmt="{:,.2f}"):return "无有效数据" if pd.isna(x) else fmt.format(x)
    ask_rank="无有效数据" if d.get("ASK_rank") is None else f"第{d['ASK_rank']} / {d['ASK_N']}名 · 前{d['ASK_rank']/d['ASK_N']*100:.1f}%"
    rpk_rank="无有效数据" if d.get("RPK_rank") is None else f"第{d['RPK_rank']} / {d['RPK_N']}名 · 前{d['RPK_rank']/d['RPK_N']*100:.1f}%"
    render_kpi_cards([("ASK（亿座公里）",value(d.get("ASK",np.nan)/UNIT_SCALE)),("ASK当年排名",ask_rank),("ASK同比",value(d.get("ASK_growth",np.nan)*100,"{:.2f}%")),
        ("RPK（亿客公里）",value(d.get("RPK",np.nan)/UNIT_SCALE)),("RPK当年排名",rpk_rank),("RPK同比",value(d.get("RPK_growth",np.nan)*100,"{:.2f}%")),("当年PLF",value(d.get("PLF",np.nan),"{:.2f}%"))])
    if pd.isna(d.get("ASK",np.nan)):render_message("该国该年度没有有效ASK数据。","warning")
    if pd.isna(d.get("ASK_growth",np.nan)):render_message("ASK同比无法计算：缺少上一连续年度有效ASK。","warning")
    if pd.isna(d.get("RPK_growth",np.nan)):render_message("RPK同比无法计算：缺少上一连续年度有效RPK。","warning")


def _t02_page(bundle):
    lo,hi=int(bundle.metrics.Time.min()),int(bundle.metrics.Time.max())
    if st.button("恢复默认设置",key="t02_reset"):
        st.session_state["t02_start_year"]=lo;st.session_state["t02_end_year"]=hi;st.session_state["t02_view"]="汇总"
    start,end,mode=select_year_range(bundle.metrics,"t02",column="Time",show_reset=False);view=st.radio("查看模式",["汇总","国家明细"],horizontal=True,key="t02_view")
    summary,detail=t02_for_period(bundle.metrics,start,end);render_analysis_context("当前统计条件",_context(start,end,mode,[("查看模式",view),("有效国家—年份",len(detail))]))
    data=summary if view=="汇总" else detail;render_table_html(data,max_rows=30)
    slug=period_slug(start,end);st.download_button("下载当前结果CSV",csv_bytes(data),f"T02_{view}_{slug}.csv","text/csv",key="t02_csv",on_click="ignore")


def _t03_page(bundle):
    st.markdown("R = ASK_out / ASK_in。R > 1表示出发侧运力高于到达侧；R < 1表示到达侧运力高于出发侧；R = 1表示两侧基本对称。ln(R)用于在对称尺度上衡量偏离程度。多年模式下，R由所选时期平均ASK_out除以平均ASK_in计算。")
    if bundle.loaded.direction is None:render_message("当前Excel没有满足ASK方向分析条件的数据。","warning");return
    raw=bundle.loaded.direction
    default_start=max(int(raw.year.min()),ASK_DIRECTION_START);default_end=min(int(raw.year.max()),ASK_DIRECTION_END)
    if st.button("恢复默认设置",key="t03_reset"):
        st.session_state["t03_start_year"]=default_start;st.session_state["t03_end_year"]=default_end;st.session_state["t03_n"]=9
    start,end,mode=select_year_range(raw,"t03",ASK_DIRECTION_START,ASK_DIRECTION_END,"year",show_reset=False);period=direction_for_period(raw,start,end)
    _clamp_int_state("t03_n",1,max(1,len(period)),min(9,max(1,len(period))))
    n=int(st.number_input("每侧显示国家数",1,max(1,len(period)),min(9,max(1,len(period))),1,key="t03_n"));data=direction_extremes(period,n);display=direction_display(data,start,end)
    render_analysis_context("当前统计条件",_context(start,end,mode,[("每侧国家数",n),("方向有效国家",len(period))]));render_table_html(display,max_rows=min(2*n,60))
    slug=period_slug(start,end);st.download_button("下载当前T03 XLSX",xlsx_bytes({"方向极端国家":display}),f"T03_extreme{n}_{slug}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key="t03_xlsx",on_click="ignore")


def _t04_page(bundle):
    if bundle.loaded.direction is None:render_message("当前Excel没有满足ASK方向分析条件的数据。","warning");return
    raw=bundle.loaded.direction;default_start=max(int(raw.year.min()),ASK_DIRECTION_START);default_end=min(int(raw.year.max()),ASK_DIRECTION_END)
    if st.button("恢复默认设置",key="t04_reset"):
        st.session_state["t04_metric"]="ASK_out";st.session_state["t04_start_year"]=default_start;st.session_state["t04_end_year"]=default_end;st.session_state["t04_n"]=10
    metric=st.radio("指标",["ASK_out","ASK_in"],horizontal=True,key="t04_metric");start,end,mode=select_year_range(raw,"t04",ASK_DIRECTION_START,ASK_DIRECTION_END,"year",show_reset=False);period=direction_for_period(raw,start,end)
    _clamp_int_state("t04_n",1,max(1,len(period)),min(10,max(1,len(period))))
    n=int(st.number_input("显示前N名",1,max(1,len(period)),min(10,max(1,len(period))),1,key="t04_n"));col="mean_ASK_out" if metric=="ASK_out" else "mean_ASK_in";data=period.sort_values([col,"country_code"],ascending=[False,True]).head(n);display=direction_display(data,start,end)
    render_analysis_context("当前排名条件",_context(start,end,mode,[("指标",metric),("有效国家",len(period)),("显示",f"Top {n}")]));render_table_html(display,max_rows=n)
    slug=period_slug(start,end);st.download_button("下载当前T04 XLSX",xlsx_bytes({f"{metric}_Top{n}":display}),f"T04_{metric}_Top{n}_{slug}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key="t04_xlsx",on_click="ignore")


def table_page(bundle):
    code=st.selectbox("选择统计表",list(TABLES),format_func=lambda x:f"{x} · {TABLES[x][0]}",key="table_id");st.subheader(TABLES[code][0])
    try:
        if code=="T01":_ranking_page(bundle)
        elif code=="T02":_t02_page(bundle)
        elif code=="T03":_t03_page(bundle)
        else:_t04_page(bundle)
    except Exception:
        LOGGER.exception("Table failed: %s",code);render_message(RESULT_ERROR,"warning")


METHOD_SECTIONS={
    "原始数据结构":"""### 原始数据结构\n\n`Data`：Country Name、Country Code、Time、ASKs、RPKs。方向分析另需`country_year_ask_capacity`：country_code、country_name、year、ASK_out、ASK_in。缺失不插值，0值保留，负值和重复国家—年份拒绝。""",
    "公共派生指标":"""### 公共派生指标\n\n水平变量：单年直接取当年值，多年取所选年份有效观测算术平均。同比始终先用完整序列按`value_t/value_(t-1)-1`计算，再筛选用户时期。方向比率多年为`mean(ASK_out)/mean(ASK_in)`。展示水平值统一除以1e8。""",
    "ASK–RPK供需关系图":"""### ASK–RPK供需关系图\n\nF01单年每国一个当年增长点，多年每国一个期间平均增长点；F02、F03严格显示选择年份；F04按所选年份重算相关、平均绝对差与反方向比例。市场规模组仍由全样本平均ASK固定。""",
    "国家动态分析":"""### 国家动态分析\n\nA01严格使用自选国家，比较单年水平或多年平均水平；F05在所选区间内重设共同正值基期；F06按所选区间重算全部动态指标与分类阈值，至少需要3个有效增长年份。""",
    "ASK方向结构":"""### ASK方向结构\n\nF07只绘制自选国家。单年直接使用当年ASK_out/in；多年先分别取有效年度均值，再计算R和ln(R)。可按ln(R)、ASK规模或国家名称排序。""",
    "时期扩展分析":"""### 时期扩展分析\n\nA02逐年给出0<PLF≤100%的跨国中位数和四分位区间；A03每年一个ASK/RPK增长散点面板，最多显示6年。""",
    "统计表":"""### 统计表\n\nT01支持任意Top N、单年排名、多年均值排名与国家年度查询；T02按选择期汇总方向或显示国家明细；T03按当期ln(R)两端取用户指定数量；T04按ASK_out或ASK_in排名。""",
    "数据更新与运行规则":"""### 数据更新与运行规则\n\n每个模块拥有独立年份状态。缓存键包含文件指纹、国家、年份和图表参数，参数变化不会复用旧图。上传文件和结果只保存在当前会话内存。""",
}


def methods_page():
    st.subheader("数据与方法说明");section=st.selectbox("说明类别",list(METHOD_SECTIONS),key="method_section");st.markdown(METHOD_SECTIONS[section])
    try:content=(PROJECT_ROOT/"DATA_AND_FIGURE_GUIDE.md").read_text(encoding="utf-8")
    except OSError:LOGGER.exception("Guide unavailable");content="# 数据与图表说明\n\n网页内置说明仍可使用。"
    st.download_button("下载完整DATA_AND_FIGURE_GUIDE.md",content.encode("utf-8"),"DATA_AND_FIGURE_GUIDE.md","text/markdown",on_click="ignore")
