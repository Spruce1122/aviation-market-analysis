"""Workbook loading with an explicit column whitelist."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .config import DATA_COLUMNS, DATA_SHEET, DIRECTION_COLUMNS, DIRECTION_SHEET


def _read_required_columns(
    workbook: Path, sheet_name: str, required_columns: list[str]
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    header = pd.read_excel(workbook, sheet_name=sheet_name, nrows=0)
    missing = [column for column in required_columns if column not in header.columns]
    if missing:
        raise ValueError(
            f"Sheet '{sheet_name}' 缺少必需字段: {', '.join(missing)}"
        )

    frame = pd.read_excel(
        workbook,
        sheet_name=sheet_name,
        usecols=required_columns,
    )
    raw_rows = len(frame)
    all_blank = frame[required_columns].isna().all(axis=1)
    blank_rows_removed = int(all_blank.sum())
    frame = frame.loc[~all_blank].copy()
    metadata = {
        "raw_rows": raw_rows,
        "blank_rows_removed": blank_rows_removed,
        "rows_after_blank_removal": len(frame),
    }
    return frame, metadata


def load_input_workbook(
    workbook: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, int]]]:
    """Load only the two approved sheets and the ten approved raw fields."""
    if not workbook.exists():
        raise FileNotFoundError(
            f"输入文件不存在: {workbook}. 请将文件放入 input 目录并保持文件名不变。"
        )

    excel = pd.ExcelFile(workbook)
    required_sheets = [DATA_SHEET, DIRECTION_SHEET]
    missing_sheets = [sheet for sheet in required_sheets if sheet not in excel.sheet_names]
    if missing_sheets:
        raise ValueError(f"工作簿缺少必需Sheet: {', '.join(missing_sheets)}")

    data, data_meta = _read_required_columns(workbook, DATA_SHEET, DATA_COLUMNS)
    direction, direction_meta = _read_required_columns(
        workbook, DIRECTION_SHEET, DIRECTION_COLUMNS
    )
    return data, direction, {DATA_SHEET: data_meta, DIRECTION_SHEET: direction_meta}

