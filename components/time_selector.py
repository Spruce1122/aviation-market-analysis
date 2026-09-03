"""Independent year selectors shared by all analytical modules."""
from __future__ import annotations

import pandas as pd
import streamlit as st


def _available_years(data: pd.DataFrame, column: str) -> list[int]:
    return sorted(pd.to_numeric(data[column], errors="coerce").dropna().astype(int).unique().tolist())


def select_year_range(
    data: pd.DataFrame,
    key_prefix: str,
    default_start: int | None = None,
    default_end: int | None = None,
    column: str = "Time",
    show_reset: bool = True,
) -> tuple[int, int, str]:
    years = _available_years(data, column)
    if not years:
        raise ValueError("没有可选择的有效年份。")
    lo, hi = years[0], years[-1]
    start_default = min(max(default_start if default_start is not None else lo, lo), hi)
    end_default = min(max(default_end if default_end is not None else hi, lo), hi)
    if start_default > end_default:
        start_default, end_default = lo, hi
    start_key, end_key = f"{key_prefix}_start_year", f"{key_prefix}_end_year"
    if show_reset and st.button("恢复默认设置", key=f"{key_prefix}_reset_years"):
        st.session_state[start_key] = start_default
        st.session_state[end_key] = end_default
    left, right = st.columns(2)
    start = left.selectbox("开始年份", years, index=years.index(start_default), key=start_key)
    end = right.selectbox("结束年份", years, index=years.index(end_default), key=end_key)
    if start > end:
        st.warning("开始年份晚于结束年份，系统已按较早年份—较晚年份解释。")
        start, end = end, start
    return int(start), int(end), "single" if start == end else "multi"


def mode_text(mode: str) -> str:
    return "单年" if mode == "single" else "多年平均"


def period_text(start_year: int, end_year: int) -> str:
    return str(start_year) if start_year == end_year else f"{start_year}—{end_year}"


def period_slug(start_year: int, end_year: int) -> str:
    return str(start_year) if start_year == end_year else f"{start_year}-{end_year}"
