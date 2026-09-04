"""Pre-computation validation and deterministic type cleaning."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import numpy as np
import pandas as pd

from .config import DATA_COLUMNS, DATA_SHEET, DIRECTION_COLUMNS, DIRECTION_SHEET


CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


def _append_year_counts(lines: list[str], frame: pd.DataFrame, year: str, cols: list[str]) -> None:
    lines.append("各年份有效国家数:")
    counts = frame.groupby(year)[cols].count().sort_index()
    lines.append(counts.to_string())


def _clean_and_validate_sheet(
    frame: pd.DataFrame,
    sheet_name: str,
    required: list[str],
    code_col: str,
    name_col: str,
    year_col: str,
    value_cols: list[str],
    lines: list[str],
    fatal: list[str],
) -> pd.DataFrame:
    lines.append("")
    lines.append(f"[{sheet_name}]")
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        fatal.append(f"{sheet_name} 缺少字段: {missing_columns}")
        return frame

    result = frame[required].copy()
    lines.append(f"校验输入行数: {len(result):,}")
    lines.append("缺失值数量:")
    lines.append(result.isna().sum().to_string())

    for column in [code_col, name_col]:
        partial_missing = result[column].isna()
        if partial_missing.any():
            fatal.append(
                f"{sheet_name}.{column} 存在 {int(partial_missing.sum())} 条缺失记录"
            )
        result[column] = result[column].astype("string").str.strip()

    result[code_col] = result[code_col].str.upper()
    invalid_codes = result[code_col].notna() & ~result[code_col].str.match(CODE_PATTERN)
    lines.append(f"不符合3位大写字母格式的代码数: {int(invalid_codes.sum())}")
    if invalid_codes.any():
        lines.append(
            "WARNING 代码格式异常: "
            + ", ".join(result.loc[invalid_codes, code_col].dropna().unique()[:20])
        )

    raw_year = result[year_col]
    numeric_year = pd.to_numeric(raw_year, errors="coerce")
    bad_year = raw_year.notna() & numeric_year.isna()
    non_integer = numeric_year.notna() & ~np.isclose(numeric_year % 1, 0)
    missing_year = numeric_year.isna()
    if bad_year.any() or non_integer.any() or missing_year.any():
        fatal.append(
            f"{sheet_name}.{year_col} 无法转换为整数: 非数值{int(bad_year.sum())}条, "
            f"非整数{int(non_integer.sum())}条, 缺失{int(missing_year.sum())}条"
        )
    if not (bad_year.any() or non_integer.any() or missing_year.any()):
        result[year_col] = numeric_year.astype(int)

    for column in value_cols:
        raw_value = result[column]
        numeric_value = pd.to_numeric(raw_value, errors="coerce")
        parse_failure = raw_value.notna() & numeric_value.isna()
        if parse_failure.any():
            fatal.append(
                f"{sheet_name}.{column} 存在 {int(parse_failure.sum())} 条非数值内容"
            )
        result[column] = numeric_value
        negative_count = int((numeric_value < 0).sum())
        zero_count = int((numeric_value == 0).sum())
        lines.append(
            f"{column}: 非缺失 {int(numeric_value.notna().sum()):,}; "
            f"负数 {negative_count:,}; 0值 {zero_count:,}; 正值 {int((numeric_value > 0).sum()):,}"
        )
        if negative_count:
            fatal.append(f"{sheet_name}.{column} 出现 {negative_count} 个负数")

    if year_col in result and pd.api.types.is_integer_dtype(result[year_col]):
        duplicates = result.duplicated([code_col, year_col], keep=False)
        duplicate_count = int(duplicates.sum())
        lines.append(f"国家—年份重复行数: {duplicate_count:,}")
        if duplicate_count:
            fatal.append(f"{sheet_name} 存在 {duplicate_count} 条国家—年份重复记录")
        lines.append(
            f"年份范围: {int(result[year_col].min())}—{int(result[year_col].max())}"
        )
        lines.append(f"国家代码数: {result[code_col].nunique():,}")
        for column in value_cols:
            positive = result.loc[result[column] > 0, year_col]
            coverage = "无正值年份" if positive.empty else f"{int(positive.min())}—{int(positive.max())}"
            lines.append(f"{column}正值年份覆盖: {coverage}")
        _append_year_counts(lines, result, year_col, value_cols)

    return result


def validate_and_clean(
    data: pd.DataFrame,
    direction: pd.DataFrame,
    loader_metadata: dict[str, dict[str, int]],
    report_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate, write a report, and return typed copies for analysis."""
    lines = [
        "航空市场复现项目：数据校验报告",
        f"生成时间: {datetime.now().isoformat(timespec='seconds')}",
        "规则: 缺失年份不插值；0值保留；各指标按自身规则判断0是否有效。",
    ]
    for sheet, meta in loader_metadata.items():
        lines.append(
            f"{sheet}: Excel读取行数 {meta['raw_rows']:,}; "
            f"整行全空记录 {meta['blank_rows_removed']:,}; "
            f"进入校验行数 {meta['rows_after_blank_removal']:,}"
        )

    fatal: list[str] = []
    clean_data = _clean_and_validate_sheet(
        data,
        DATA_SHEET,
        DATA_COLUMNS,
        "Country Code",
        "Country Name",
        "Time",
        ["ASKs", "RPKs"],
        lines,
        fatal,
    )
    clean_direction = _clean_and_validate_sheet(
        direction,
        DIRECTION_SHEET,
        DIRECTION_COLUMNS,
        "country_code",
        "country_name",
        "year",
        ["ASK_out", "ASK_in"],
        lines,
        fatal,
    )

    lines.append("")
    if fatal:
        lines.append("校验结论: FAILED")
        lines.extend(f"ERROR {message}" for message in fatal)
    else:
        lines.append("校验结论: PASSED")
        lines.append("必需字段、主键、年份格式和非负性检查均通过。")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if fatal:
        raise ValueError("数据校验失败，详见 output/logs/data_validation_report.txt")
    return clean_data, clean_direction

