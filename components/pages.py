"""Streamlit pages. Formal results use static HTML/PNG renderers for cloud stability."""
from __future__ import annotations

from dataclasses import replace
import logging
import pandas as pd
import streamlit as st

from components.chart_info import sample_info, chart_info
from components.download import chart_downloads, table_downloads, full_download
from components.safe_render import render_figure_html, render_kpi_cards, render_message, render_table_html
from core.ask_rpk_metrics import build_interval_dynamic_data, build_representative_index_data
from core.catalog import CHARTS, TABLES, source_fields
from core.config import MIN_VALID_GROWTH_YEARS, PROJECT_ROOT, RANKING_END_YEAR, RANKING_MIN_COMMON_YEARS, RANKING_START_YEAR
from core.view_data import chart_data
from plots.country_index import plot_f05
from plots.dynamic_type import plot_f06
from plots.growth_lead import plot_a01
from plots.registry import ChartUnavailable, PLOT_LOCK, render_chart
from plots.style import setup_plotting_style
from utils.export import csv_bytes, xlsx_bytes

LOGGER = logging.getLogger("aviation_dashboard")
RESULT_ERROR = "当前结果暂时无法生成，请检查数据覆盖范围。"


def overview(bundle, font_status):
    m = bundle.metrics
    st.subheader("数据概览")
    st.caption(f"当前Excel：{bundle.loaded.filename}　｜　内容指纹：{bundle.loaded.digest[:12]}　｜　数据仅在当前会话处理")
    render_kpi_cards([
        ("Data国家数量", f"{m['Country Code'].nunique():,}"),
        ("Data年份范围", f"{int(m.Time.min())}—{int(m.Time.max())}"),
        ("ASK/RPK共同增长样本", f"{int(m.common_growth_sample.sum()):,}"),
        ("ASK正值观测", f"{int(m.ASKs.gt(0).sum()):,}"),
        ("RPK正值观测", f"{int(m.RPKs.gt(0).sum()):,}"),
        ("方向分析可用国家", f"{len(bundle.direction):,}"),
    ])
    st.markdown("#### 数据质量检查")
    if bundle.loaded.direction is None:
        render_message("部分分析可用：当前Excel缺少country_year_ask_capacity工作表。", "warning")
    else:
        render_message("两张分析工作表均已校验，采用固定研究口径。", "success")
    for note in bundle.warnings:
        render_message(note, "warning")
    with st.expander("字段检查与完整校验报告"):
        render_table_html(pd.DataFrame(bundle.loaded.checks), max_rows=100)
        st.text(bundle.loaded.report)
        st.download_button("下载校验报告", bundle.loaded.report.encode("utf-8"), "validation_report.txt", on_click="ignore")
    st.markdown("#### 本次分析口径")
    counts = m.drop_duplicates("Country Code").market_size_group.value_counts()
    render_table_html(pd.DataFrame({"规模": ["Large", "Medium", "Small"], "国家数": [int(counts.get(k, 0)) for k in ["Large", "Medium", "Small"]]}))
    st.caption(f"固定方向区间：{bundle.config.direction_start}—{bundle.config.direction_end}；分组按全样本期平均ASK，前40/后40固定。")
    if not (font_status["times_new_roman"] and font_status["simsun"]):
        render_message(f"服务器字体回退：英文 {font_status['latin_family']}；中文 {font_status['cjk_family']}。")
    st.divider()
    full_download(bundle)


def _render_chart_result(bundle, code, fig, data):
    render_figure_html(fig, CHARTS[code][0], dpi=170)
    sample_info(bundle, code)
    chart_info(bundle, code)
    chart_downloads(fig, data, CHARTS[code][1], code)
    with st.expander("查看当前图的数据（预览前100行）"):
        render_table_html(data, max_rows=100, caption=f"预览100行以内；完整数据共 {len(data):,} 行。")
        st.download_button("下载完整图数据 CSV", csv_bytes(data), CHARTS[code][1] + "_data.csv", "text/csv", key=code+"_full_csv", on_click="ignore")


def chart_page(bundle, module):
    choices = [code for code, info in CHARTS.items() if info[2] == module]
    code = st.selectbox("选择图表", choices, format_func=lambda x: f"{x} · {CHARTS[x][0]}", key="chart_"+module)
    st.subheader(CHARTS[code][0])
    st.caption(CHARTS[code][4])
    try:
        cache = st.session_state.setdefault("figure_cache", {})
        if code not in cache:
            with st.spinner("按当前数据绘制图表…"):
                cache[code] = render_chart(bundle, code)
        _render_chart_result(bundle, code, cache[code], chart_data(bundle, code))
    except ChartUnavailable:
        render_message(RESULT_ERROR, "warning")
    except Exception:
        LOGGER.exception("Chart %s failed", code)
        render_message(RESULT_ERROR, "warning")


def _country_options(bundle):
    identity = bundle.metrics.sort_values("Time").drop_duplicates("Country Code", keep="last")
    names = identity.set_index("Country Code")["Country Name"].to_dict()
    return names, sorted(names, key=lambda code: (str(names[code]), code))


def dynamic_page(bundle):
    st.subheader("国家动态分析")
    names, options = _country_options(bundle)
    defaults = [c for c in bundle.config.representative_countries if c in options]
    chosen = st.multiselect("选择并高亮国家（可搜索国家名称或ISO，1—30国）", options, default=defaults, max_selections=30,
        format_func=lambda c: f"{names[c]} ({c})", key="dynamic_countries_"+bundle.loaded.digest[:12])
    years = sorted(int(y) for y in bundle.metrics.Time.dropna().unique())
    start, end = st.select_slider("分析年份范围", options=years, value=(years[0], years[-1]), key="dynamic_years_"+bundle.loaded.digest[:12])
    code = st.selectbox("选择图表", ["F05", "F06", "A01"], format_func=lambda x: f"{x} · {CHARTS[x][0]}", key="dynamic_chart")
    if not chosen:
        render_message("请至少选择一个国家。", "warning")
        return
    st.caption("同比增长先在完整国家序列上按连续年份计算，再筛选所选区间；Excel不会重新读取。")
    try:
        with PLOT_LOCK:
            setup_plotting_style(LOGGER)
            config = replace(bundle.config, representative_countries=tuple(chosen))
            if code == "F05":
                data = build_representative_index_data(bundle.metrics, chosen, start, end)
                available = set(data["Country Code"].unique())
                unavailable = [f"{names[c]} ({c})" for c in chosen if c not in available]
                if unavailable:
                    render_message("所选区间没有ASK与RPK共同正值基期：" + "、".join(unavailable), "warning")
                if data.empty:
                    raise ValueError("No valid index series")
                fig = plot_f05(data, config)
                dynamic = pd.DataFrame()
            elif code == "F06":
                dynamic, thresholds = build_interval_dynamic_data(bundle.metrics, start, end, bundle.config)
                data = dynamic.copy()
                fig = plot_f06(dynamic, config, highlight_codes=chosen)
                render_table_html(thresholds, max_rows=30, caption="所选区间合格国家样本重新计算的动态分类阈值")
            else:
                dynamic, _ = build_interval_dynamic_data(bundle.metrics, start, end, bundle.config)
                data = dynamic.loc[dynamic.n_valid.ge(MIN_VALID_GROWTH_YEARS)].copy()
                fig = plot_a01(dynamic, config)
        render_figure_html(fig, CHARTS[code][0], dpi=170)
        middle = ("可绘制指数国家", f"{data['Country Code'].nunique():,}") if code == "F05" else ("合格动态国家", f"{len(dynamic):,}")
        render_kpi_cards([("所选区间", f"{start}—{end}"), middle, ("已选择国家", f"{len(chosen):,}")])
        chart_downloads(fig, data, CHARTS[code][1], f"{code}_{start}_{end}")
        with st.expander("查看当前图的数据（预览前100行）"):
            render_table_html(data, max_rows=100)
            st.download_button("下载完整图数据 CSV", csv_bytes(data), f"{code}_{start}_{end}_data.csv", "text/csv", key=f"dynamic_csv_{code}", on_click="ignore")
    except Exception:
        LOGGER.exception("Dynamic chart %s failed for %s-%s", code, start, end)
        render_message(RESULT_ERROR, "warning")


def direction_page(bundle):
    st.subheader("ASK方向结构")
    st.caption(CHARTS["F07"][4])
    if bundle.direction.empty:
        render_message("当前Excel没有满足ASK方向分析条件的数据。", "warning")
        return
    try:
        fig = render_chart(bundle, "F07")
        data = chart_data(bundle, "F07")
        render_figure_html(fig, CHARTS["F07"][0], dpi=170)
        render_kpi_cards([("固定分析时期", f"{bundle.config.direction_start}—{bundle.config.direction_end}"),
            ("方向有效国家", f"{len(bundle.direction):,}"), ("R中位数", f"{bundle.direction.R.median():.3f}"),
            ("ln(R)中位数", f"{bundle.direction.ln_R.median():.3f}")])
        chart_downloads(fig, data, CHARTS["F07"][1], "F07")
        with st.expander("查看当前图的数据"):
            render_table_html(data, max_rows=100)
    except Exception:
        LOGGER.exception("Direction chart failed")
        render_message(RESULT_ERROR, "warning")


def _ranking_page(bundle):
    metric = st.radio("排名指标", ["ASK", "RPK"], horizontal=True, key="ranking_metric")
    top_n = st.selectbox("显示数量", [10, 20, 30], key="ranking_n")
    rank_col = f"{metric}_rank"
    ranking = bundle.ranking.sort_values([rank_col, "Country Code"]).copy()
    columns = ["Country Name", "Country Code", "n_common_years", "mean_ASK", "mean_RPK", "ASK_rank", "RPK_rank", "weighted_PLF"]
    shown = ranking.head(top_n)[columns]
    render_table_html(shown, max_rows=top_n, formats={"weighted_PLF":"{:.2f}%"}, caption=f"2016—2021共同有效年份不少于5年的{metric}前{top_n}名")
    names, options = _country_options(bundle)
    selected = st.selectbox("查询单个国家排名", options, format_func=lambda c: f"{names[c]} ({c})", key="ranking_country")
    row = bundle.ranking.loc[bundle.ranking["Country Code"].eq(selected)]
    if not row.empty:
        r = row.iloc[0]
        n = len(bundle.ranking)
        render_kpi_cards([("ASK排名", f"{int(r.ASK_rank)}/{n}"), ("RPK排名", f"{int(r.RPK_rank)}/{n}"),
            ("共同有效年份", f"{int(r.n_common_years)}"), ("加权PLF", f"{r.weighted_PLF:.2f}%"),
            ("平均ASK", f"{r.mean_ASK:,.2f}"), ("平均RPK", f"{r.mean_RPK:,.2f}")])
    else:
        country = bundle.metrics.loc[bundle.metrics["Country Code"].eq(selected) & bundle.metrics.Time.between(RANKING_START_YEAR, RANKING_END_YEAR)
            & bundle.metrics.ASKs.gt(0) & bundle.metrics.RPKs.gt(0)]
        render_message(f"该国未进入排名：2016—2021共同有效年份为 {int(country.Time.nunique())}，排名最低要求为 {RANKING_MIN_COMMON_YEARS}。", "warning")
    a, b = st.columns(2)
    a.download_button("下载当前TopN CSV", csv_bytes(shown), f"T01_{metric}_Top{top_n}.csv", "text/csv", key="ranking_csv", on_click="ignore", width="stretch")
    b.download_button("下载完整排名 XLSX", xlsx_bytes({"完整排名": bundle.ranking}), "T01_完整航空市场排名.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="ranking_xlsx", on_click="ignore", width="stretch")


def table_page(bundle):
    code = st.selectbox("选择统计表", list(TABLES), format_func=lambda x: f"{x} · {TABLES[x][0]}", key="table_id")
    st.subheader(TABLES[code][0]); st.caption(TABLES[code][2])
    if code == "T01":
        _ranking_page(bundle); return
    if code not in bundle.tables:
        render_message("当前Excel没有满足ASK方向分析条件的数据。", "warning"); return
    sheets = bundle.tables[code]
    sheet = st.selectbox("工作表", list(sheets), key="sheet_"+code)
    frame = sheets[sheet].copy()
    query = st.text_input("国家 / ISO / 内容搜索", placeholder="输入国家名称或ISO代码", key="query_"+code)
    if query:
        frame = frame.loc[frame.astype(str).apply(lambda col: col.str.contains(query, case=False, regex=False)).any(axis=1)]
    render_table_html(frame, max_rows=30, caption=f"显示前 {min(len(frame),30)} 行，共 {len(frame)} 行；表内可横向滚动。")
    table_downloads(code, sheet, frame, sheets)
    with st.expander("数据来源与计算说明"):
        sheet_name, fields = source_fields(code)
        st.code("\n".join(sheet_name+"!"+field for field in fields), language=None)
        st.write(TABLES[code][2])


METHOD_SECTIONS = {
    "原始数据结构": """### 原始数据结构\n\n`Data`必须包含 `Country Name`、`Country Code`、`Time`、`ASKs`、`RPKs`。方向分析另需 `country_year_ask_capacity` 中的 `country_code`、`country_name`、`year`、`ASK_out`、`ASK_in`。国家—年份不得重复，年份必须可转整数，运输量不得为负；缺失年份和0值均不插值。""",
    "公共派生指标": """### 公共派生指标\n\n同比仅在同一国家相邻两年连续且本期、上期均为正时计算：`growth = value_t/value_(t-1)-1`。`growth_gap=RPK_growth-ASK_growth`，`abs_growth_gap=|growth_gap|`，`PLF=RPK/ASK×100`（ASK>0）。市场规模按全期平均ASK排序，前40为Large、后40为Small，其余为Medium。""",
    "ASK–RPK供需关系图": """### ASK–RPK供需关系图\n\n|图|原始字段|计算与样本|图形|\n|---|---|---|---|\n|F01|Data五字段|ASK/RPK共同连续同比|X=ASK增长，Y=RPK增长，颜色=规模，45°线|\n|F02|Data五字段|ASK、RPK独立同比，逐年跨国中位数|两条年度趋势线|\n|F03|Data五字段|固定规模组内独立同比中位数|三类规模市场趋势|\n|F04|Data五字段|共同同比的相关、绝对差、反向比例|规模市场比较|""",
    "国家动态分析": """### 国家动态分析\n\nF05在所选区间内以各国首次ASK、RPK共同正值年为基期，`index=value/value_base×100`。F06在所选区间共同同比样本上计算Pearson相关、增长差中位数、平均绝对差、反向比例、增长差标准差和有效年数，并按当期合格国家四分位阈值分类。A01按 `median(RPK_growth−ASK_growth)` 取最低、最高各10国。同比始终先由完整序列计算，再筛选区间。""",
    "ASK方向结构": """### ASK方向结构\n\nF07固定2000—2019，仅对ASK_out和ASK_in同时非缺失的年份取成对均值；均值均为正时，`R=mean_ASK_out/mean_ASK_in`，`ln_R=ln(R)`。自动选择ln(R)最低和最高各9国。""",
    "疫情扩展分析": """### 疫情扩展分析\n\nA02要求2016—2019至少2个0<PLF≤100%的观测，且2020、2021均有效；同一批国家比较疫情前国别PLF中位数、2020和2021。A03分别展示2016—2019、2020、2021的ASK/RPK共同同比散点，时期之间不强制平衡。""",
    "统计表": """### 统计表\n\nT01在2016—2021内要求ASK、RPK同时为正至少5年，以共同年份平均ASK/RPK排名，`weighted_PLF=ΣRPK/ΣASK×100`。T02统计共同同比的四种严格方向。T03与F07使用同一组方向极端国家。T04分别按mean_ASK_out和mean_ASK_in取前10国。""",
    "数据更新与运行规则": """### 数据更新与运行规则\n\n上传文件按内容SHA256识别，新文件会清除旧会话结果。数据只在当前会话内存处理，不写入公共目录，不跨用户复用。更新Excel后国家排序、同比、动态阈值、极端国家和TopN会自动变化；前40/后40、疫情期、排名期、方向期及最低有效年份属于固定研究设定。""",
}


def methods_page():
    st.subheader("数据与方法说明")
    section = st.selectbox("说明类别", list(METHOD_SECTIONS), key="method_section")
    st.markdown(METHOD_SECTIONS[section])
    try:
        content = (PROJECT_ROOT/"DATA_AND_FIGURE_GUIDE.md").read_text(encoding="utf-8")
    except OSError:
        LOGGER.exception("Guide file unavailable")
        content = "# 数据与图表说明\n\n网页内置方法说明仍然可用。"
    st.download_button("下载完整 DATA_AND_FIGURE_GUIDE.md", content.encode("utf-8"), "DATA_AND_FIGURE_GUIDE.md", "text/markdown", on_click="ignore")
