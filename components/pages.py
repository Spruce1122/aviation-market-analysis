"""Five-module Streamlit workspace built on the shared analysis pipeline."""
from copy import copy
from dataclasses import replace
import logging
import numpy as np
import pandas as pd
import streamlit as st

from core.ask_direction_metrics import build_direction_metrics, select_direction_extremes
from core.ask_rpk_metrics import build_country_dynamic_metrics, build_representative_index_data
from core.catalog import CHARTS, TABLES, MODULE_ITEMS, HOW_TO_READ, display_label, source_fields
from core.config import PROJECT_ROOT
from core.pandemic import build_balanced_pandemic_plf
from core.view_data import chart_data
from plots.registry import render_chart, ChartUnavailable, PLOT_LOCK
from plots.country_index import plot_f05, plot_a01_absolute
from plots.dynamic_type import plot_f06
from plots.direction import plot_f07
from plots.style import setup_plotting_style
from tables.build_tables import ranking_for_period, direction_counts_for_period, direction_ranking_for_period, make_t03
from components.chart_info import chart_info
from components.download import chart_downloads, table_downloads, full_download
from components.time_selector import year_range, period_controls, actual_range
from utils.export import csv_bytes, xlsx_bytes

LOGGER = logging.getLogger("aviation_dashboard")


def _activate_plot_fonts():
    try:
        setup_plotting_style(LOGGER, require_cjk=True)
        return True
    except RuntimeError as exc:
        st.warning(str(exc))
        return False


def _range_text(series):
    span = actual_range(series)
    return "无有效年份" if span is None else f"{span[0]}—{span[1]}"


def _country_options(metrics):
    names = metrics.sort_values("Time").drop_duplicates("Country Code", keep="last").set_index("Country Code")["Country Name"].to_dict()
    options = sorted(names, key=lambda code: str(names[code]))
    return names, options, lambda code: f"{names.get(code, code)} ({code})"


def _read_expander(code):
    with st.expander("如何读这张图" if code.startswith(("F", "A")) else "如何解读这张表"):
        for line in HOW_TO_READ[code]:
            st.markdown(f"- {line}")


def _show_figure(bundle, code, fig=None, data=None, key_suffix=""):
    try:
        if fig is None:
            fig = render_chart(bundle, code)
        if data is None:
            data = chart_data(bundle, code)
        with PLOT_LOCK:
            st.pyplot(fig, clear_figure=False, width="stretch", dpi=150, bbox_inches="tight")
        _read_expander(code)
        chart_info(bundle, code)
        chart_downloads(fig, data, CHARTS[code][1], code + key_suffix)
        with st.expander("查看当前图的数据"):
            st.dataframe(data, hide_index=True, width="stretch")
    except ChartUnavailable as exc:
        st.warning(str(exc))
        _read_expander(code)
        chart_info(bundle, code)


def _show_table(code, sheets, default_sheet=None, key_suffix=""):
    sheet_names = list(sheets)
    index = sheet_names.index(default_sheet) if default_sheet in sheet_names else 0
    sheet = st.selectbox("工作表", sheet_names, index=index, key=f"sheet_{code}_{key_suffix}") if len(sheet_names) > 1 else sheet_names[0]
    frame = sheets[sheet]
    st.dataframe(frame, hide_index=True, width="stretch", height=min(580, max(210, (len(frame)+1)*35)))
    _read_expander(code)
    table_downloads(code, sheet, frame, sheets)


def overview(bundle, font_status):
    m = bundle.metrics
    st.subheader("数据概览")
    st.caption(f"当前Excel：{bundle.loaded.filename}　｜　内容指纹：{bundle.loaded.digest[:12]}　｜　数据来源：{st.session_state.get('source_label', '测试输入')}")
    cards = st.columns(4)
    cards[0].metric("Data国家数量", f"{m['Country Code'].nunique():,}")
    cards[1].metric("Data原始年份", f"{int(m.Time.min())}—{int(m.Time.max())}")
    cards[2].metric("ASK/RPK共同增长样本", f"{int(m.common_growth_sample.sum()):,}")
    cards[3].metric("方向分析可用国家", f"{len(bundle.direction):,}")

    st.markdown("#### 航空指标实际有效年份")
    coverage = pd.DataFrame([
        ["ASK水平有效年份", _range_text(m.loc[m.ASKs.gt(0), "Time"]), int(m.ASKs.gt(0).sum())],
        ["RPK水平有效年份", _range_text(m.loc[m.RPKs.gt(0), "Time"]), int(m.RPKs.gt(0).sum())],
        ["ASK同比有效年份", _range_text(m.loc[m.ASK_growth.notna(), "Time"]), int(m.ASK_growth.notna().sum())],
        ["RPK同比有效年份", _range_text(m.loc[m.RPK_growth.notna(), "Time"]), int(m.RPK_growth.notna().sum())],
        ["共同同比有效年份", _range_text(m.loc[m.common_growth_sample, "Time"]), int(m.common_growth_sample.sum())],
        ["有效PLF年份", _range_text(m.loc[m.PLF.gt(0) & m.PLF.le(100), "Time"]), int((m.PLF.gt(0) & m.PLF.le(100)).sum())],
    ], columns=["指标", "实际年份范围", "有效观测数"])
    st.dataframe(coverage, hide_index=True, width="stretch")

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("#### 数据质量检查")
        if bundle.loaded.direction is None:
            st.warning("Data已通过；当前Excel缺少country_year_ask_capacity，方向分析暂不可用。")
        else:
            st.success("Data和country_year_ask_capacity均已通过结构校验。")
        for note in bundle.warnings:
            st.warning(note)
        with st.expander("字段检查与完整校验报告"):
            st.dataframe(pd.DataFrame(bundle.loaded.checks), hide_index=True, width="stretch")
            st.text(bundle.loaded.report)
            st.download_button("下载校验报告", bundle.loaded.report.encode("utf-8"), "validation_report.txt", on_click="ignore")
    with right:
        st.markdown("#### 数据覆盖与分组")
        groups = m.drop_duplicates("Country Code").market_size_group.value_counts()
        st.dataframe(pd.DataFrame({"市场规模组": ["Large", "Medium", "Small"], "国家数": [int(groups.get(x, 0)) for x in ["Large", "Medium", "Small"]]}), hide_index=True, width="stretch")
        if bundle.loaded.direction is not None:
            d = bundle.loaded.direction
            st.write(f"ASK_out/in原始覆盖：{d.country_code.nunique()}国，{int(d.year.min())}—{int(d.year.max())}")
        st.caption("Data中的最早和最晚年份包含宏观数据覆盖；航空图表时间控件按ASK、RPK或方向指标的实际有效年份生成。")
    st.caption(f"图表中文字体：{font_status.get('cjk_family') or '未找到'}　｜　图表英文字体：{font_status.get('latin_family') or '未找到'}　｜　{font_status.get('font_validation_message', '尚未自检')}")
    st.divider()
    full_download(bundle)


def full_sample_page(bundle):
    st.subheader("全样本分析")
    code = st.selectbox("选择图表", MODULE_ITEMS["全样本分析"], format_func=display_label, key="full_sample_item")
    st.markdown(f"### {display_label(code)}")
    m = bundle.metrics
    temp = copy(bundle)

    if code in ("F02", "F03"):
        valid = m.loc[m[["ASK_growth", "RPK_growth"]].notna().any(axis=1), "Time"]
        st.caption(f"ASK同比实际覆盖：{_range_text(m.loc[m.ASK_growth.notna(), 'Time'])}　｜　RPK同比实际覆盖：{_range_text(m.loc[m.RPK_growth.notna(), 'Time'])}")
        selected = year_range("开始年份—结束年份", valid, "full_range_"+code)
    elif code in ("F01", "F04"):
        valid = m.loc[m.common_growth_sample, "Time"]
        st.caption(f"ASK/RPK共同同比实际覆盖：{_range_text(valid)}")
        selected = year_range("开始年份—结束年份", valid, "full_range_"+code)
    else:
        selected = None

    if selected:
        temp.metrics = m.loc[m.Time.between(*selected)].copy()
        temp.config = replace(bundle.config, trend_year_start=None, trend_year_end=None)

    if code in ("A02", "A03"):
        if code == "A02":
            valid_plf = m.loc[m.PLF.gt(0) & m.PLF.le(100), "Time"]
            st.caption(f"有效PLF实际覆盖：{_range_text(valid_plf)}")
        else:
            st.caption(f"ASK/RPK共同同比实际覆盖：{_range_text(m.loc[m.common_growth_sample, 'Time'])}")
        chosen = period_controls(m, bundle.config, code, valid_plf if code == "A02" else None)
        if chosen is None:
            return
        temp.config = replace(bundle.config, period_pre_start=chosen[0], period_pre_end=chosen[1],
                              period_shock_year=chosen[2], period_recovery_year=chosen[3])
        temp.balanced = build_balanced_pandemic_plf(m, temp.config)
    _show_figure(temp, code, key_suffix="_interactive")


def _shared_country_selector(bundle, key="country_analysis_selection"):
    names, options, fmt = _country_options(bundle.metrics)
    defaults = [code for code in bundle.config.representative_countries if code in options][:6]
    selected = st.multiselect("选择国家（1—30国）", options, default=defaults, max_selections=30, format_func=fmt, key=key)
    return names, options, fmt, selected


def country_analysis_page(bundle):
    st.subheader("分国家ASK/RPK分析")
    code = st.selectbox("选择图表或统计表", MODULE_ITEMS["分国家ASK/RPK分析"], format_func=display_label, key="country_item")
    st.markdown(f"### {display_label(code)}")
    m = bundle.metrics

    if code == "T01":
        positive = m.loc[m.ASKs.gt(0) & m.RPKs.gt(0), "Time"]
        selected = year_range("统计开始年份—结束年份", positive, "t01_range")
        if selected is None:
            return
        ranking = ranking_for_period(m, *selected)
        if ranking.empty:
            st.warning("所选时期没有ASK与RPK共同为正的国家。")
            return
        metric = st.radio("排名指标", ["ASK", "RPK"], horizontal=True)
        top_n = st.number_input("Top N", 1, len(ranking), min(10, len(ranking)), 1)
        rank_col = metric + "排名"
        top = ranking.sort_values([rank_col, "Country Code"]).head(int(top_n))
        st.caption("ASK与RPK单位：座公里；多年按共同有效年份均值排名，单年使用当年值。")
        st.dataframe(top, hide_index=True, width="stretch")
        names, options, fmt = _country_options(m)
        chosen = st.selectbox("查询某个国家", options, format_func=fmt, key="t01_country")
        row = ranking.loc[ranking["Country Code"].eq(chosen)]
        if row.empty:
            st.info("该国在所选时期没有ASK与RPK共同为正的观测。")
        else:
            r = row.iloc[0]
            cards = st.columns(4)
            cards[0].metric("ASK排名", f"第{int(r['ASK排名'])} / {len(ranking)}名")
            cards[1].metric("RPK排名", f"第{int(r['RPK排名'])} / {len(ranking)}名")
            cards[2].metric("加权PLF", f"{r['加权PLF（%）']:.1f}%")
            cards[3].metric("有效年份", f"{int(r['有效年份'])}")
            st.dataframe(row, hide_index=True, width="stretch")
        sheets = {f"{metric}_Top{int(top_n)}": top, "全部国家排名": ranking}
        _read_expander(code)
        table_downloads(code, list(sheets)[0], top, sheets)
        return

    if code == "T02":
        selected = year_range("统计开始年份—结束年份", m.loc[m.common_growth_sample, "Time"], "t02_range")
        if selected is None:
            return
        summary, detail = direction_counts_for_period(m, *selected)
        _show_table(code, {"汇总": summary, "国家年份明细": detail}, "汇总", "period")
        return

    _, _, fmt, countries = _shared_country_selector(bundle)
    if not countries:
        st.info("请至少选择一个国家。")
        return

    if code == "A01":
        level_years = m.loc[m.ASKs.gt(0) | m.RPKs.gt(0), "Time"]
        selected = year_range("显示开始年份—结束年份", level_years, "a01_range")
        if selected is None:
            return
        mode = st.radio("展示方式", ["绝对规模", "指数走势"], horizontal=True)
        filtered = m.loc[m.Time.between(*selected) & m["Country Code"].isin(countries)].copy()
        cfg = replace(bundle.config, representative_countries=tuple(countries))
        if not _activate_plot_fonts():
            return
        with PLOT_LOCK:
            if mode == "绝对规模":
                fig = plot_a01_absolute(filtered, countries)
                data = filtered[["Country Name", "Country Code", "Time", "ASKs", "RPKs"]]
            else:
                data = build_representative_index_data(filtered, countries)
                fig = plot_f05(data, cfg, bottom_title="附图1 自选国家ASK/RPK指数走势")
        temp = copy(bundle); temp.config = cfg; temp.indices = data
        _show_figure(temp, code, fig=fig, data=data, key_suffix="_"+mode)
        return

    selected = year_range("分析开始年份—结束年份", m.loc[m.common_growth_sample, "Time"], "f06_range")
    if selected is None:
        return
    filtered = m.loc[m.Time.between(*selected)].copy()
    try:
        dynamic, thresholds = build_country_dynamic_metrics(filtered, bundle.config)
    except ValueError as exc:
        st.warning(str(exc))
        return
    if not _activate_plot_fonts():
        return
    with PLOT_LOCK:
        fig = plot_f06(dynamic, bundle.config, countries)
    data = dynamic.copy()
    data["重点显示"] = data["Country Code"].isin(countries)
    temp = copy(bundle); temp.dynamic = dynamic; temp.thresholds = thresholds; temp.metrics = filtered
    _show_figure(temp, code, fig=fig, data=data, key_suffix="_period")
    with st.expander("查看当前分类阈值"):
        st.dataframe(thresholds, hide_index=True, width="stretch")


def direction_analysis_page(bundle):
    st.subheader("出发侧（ASK_out）与到达侧（ASK_in）分析")
    if bundle.loaded.direction is None:
        st.warning("当前Excel缺少country_year_ask_capacity工作表，本模块需要ASK_out和ASK_in原始数据。")
        return
    code = st.selectbox("选择图表或统计表", MODULE_ITEMS["出发侧（ASK_out）与到达侧（ASK_in）分析"], format_func=display_label, key="direction_item")
    st.markdown(f"### {display_label(code)}")
    raw = bundle.loaded.direction
    pair = raw.loc[raw.ASK_out.notna() & raw.ASK_in.notna(), "year"]
    selected = year_range("分析开始年份—结束年份", pair, "direction_range", (bundle.config.direction_start, bundle.config.direction_end))
    if selected is None:
        return
    cfg = replace(bundle.config, direction_start=selected[0], direction_end=selected[1])
    direction = build_direction_metrics(raw, cfg)
    if direction.empty:
        st.warning("所选时期没有ASK_out和ASK_in均可用于计算的国家。")
        return
    low, high = select_direction_extremes(direction, cfg)

    if code == "T04":
        metric = st.radio("排名指标", ["ASK_out", "ASK_in"], horizontal=True)
        top_n = st.number_input("Top N", 1, len(direction), min(10, len(direction)), 1, key="t04_topn")
        frame = direction_ranking_for_period(direction, metric, int(top_n))
        st.caption("ASK_out和ASK_in单位：座公里；多年按所选期共同有效年份均值排名，单年使用当年值。")
        _show_table(code, {f"{metric}_Top{int(top_n)}": frame}, key_suffix="period")
        return

    if code == "T03":
        each_side = st.number_input("每侧国家数", 1, min(30, len(direction)), min(cfg.top_direction_n, len(direction)), 1, key="t03_n")
        cfg = replace(cfg, top_direction_n=int(each_side))
        low, high = select_direction_extremes(direction, cfg)
        _show_table(code, make_t03(low, high, config=cfg), key_suffix="period")
        return

    names = direction.set_index("country_code")["country_name"].to_dict()
    options = sorted(names, key=lambda x: str(names[x]))
    chosen = st.multiselect("选择国家；留空时显示ln(R)两端极端国家", options, max_selections=30,
                            format_func=lambda x: f"{names[x]} ({x})", key="f07_countries")
    if chosen:
        data = direction.loc[direction.country_code.isin(chosen)].copy()
        data["extreme_group"] = np.where(data.ln_R.lt(0), "ASK_in相对占优", "ASK_out相对占优")
        lower = data.loc[data.ln_R.lt(0)]
        upper = data.loc[data.ln_R.ge(0)]
    else:
        data = pd.concat([low, high], ignore_index=True).drop_duplicates("country_code")
        lower, upper = low, high
    if not _activate_plot_fonts():
        return
    with PLOT_LOCK:
        fig = plot_f07(lower, upper, cfg)
    temp = copy(bundle); temp.config = cfg; temp.direction = direction; temp.direction_low = lower; temp.direction_high = upper
    _show_figure(temp, code, fig=fig, data=data, key_suffix="_period")


def methods_page():
    st.subheader("数据与方法说明")
    st.caption("说明顺序与网页模块一致；用于理解指标、读图规则、更新后的正常变化及解释边界。")
    st.markdown((PROJECT_ROOT / "DATA_AND_FIGURE_GUIDE.md").read_text(encoding="utf-8"))
