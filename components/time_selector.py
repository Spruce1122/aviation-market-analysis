"""Reusable selectors constrained by each indicator's actual coverage."""
import streamlit as st


def actual_range(series):
    values = series.dropna()
    if values.empty:
        return None
    return int(values.min()), int(values.max())


def year_range(label, years, key, default=None):
    coverage = actual_range(years)
    if coverage is None:
        st.warning("当前指标没有有效年份。")
        return None
    lo, hi = coverage
    if lo == hi:
        st.caption(f"{label}：{lo}")
        return lo, hi
    value = default or (lo, hi)
    value = (max(lo, int(value[0])), min(hi, int(value[1])))
    if value[0] > value[1]:
        value = (lo, hi)
    return st.slider(label, lo, hi, value, key=key)


def period_controls(metrics, config, key_prefix, years=None):
    valid = metrics.loc[metrics["common_growth_sample"], "Time"] if years is None else years
    coverage = actual_range(valid)
    if coverage is None:
        st.warning("当前数据没有ASK/RPK共同同比有效年份。")
        return None
    lo, hi = coverage
    cols = st.columns(4)
    pre_start = cols[0].number_input("第一时期起始年", lo, hi, max(lo, min(hi, config.period_pre_start)), key=key_prefix+"_pre_start")
    pre_end = cols[1].number_input("第一时期结束年", lo, hi, max(lo, min(hi, config.period_pre_end)), key=key_prefix+"_pre_end")
    year_2 = cols[2].number_input("第二时期年份", lo, hi, max(lo, min(hi, config.period_shock_year)), key=key_prefix+"_year2")
    year_3 = cols[3].number_input("第三时期年份", lo, hi, max(lo, min(hi, config.period_recovery_year)), key=key_prefix+"_year3")
    if pre_start > pre_end:
        st.warning("第一时期起始年份应早于或等于结束年份。")
        return None
    return int(pre_start), int(pre_end), int(year_2), int(year_3)
