from io import BytesIO
from pathlib import Path

import pandas as pd

from core.config import DEFAULT_CONFIG, SAMPLE_FILE
from core.data_loader import load_data
from core.pipeline import build_analysis
from core.session import sync_analysis
from core.catalog import MODULES, MODULE_ITEMS, display_label
from tables.build_tables import ranking_for_period, direction_counts_for_period


def _workbook_bytes(data: pd.DataFrame, direction: pd.DataFrame | None = None) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="Data", index=False)
        if direction is not None:
            direction.to_excel(writer, sheet_name="country_year_ask_capacity", index=False)
    return output.getvalue()


def test_baseline_reproduces_reference_counts():
    payload = SAMPLE_FILE.read_bytes()
    bundle = build_analysis(load_data(payload, SAMPLE_FILE.name))
    assert len(bundle.metrics) == 4732
    assert bundle.metrics["Country Code"].nunique() == 182
    assert int(bundle.metrics["common_growth_sample"].sum()) == 777
    assert bundle.metrics.groupby("market_size_group")["Country Code"].nunique().to_dict() == {
        "Large": 40,
        "Medium": 78,
        "Small": 40,
    }
    assert set(bundle.tables) == {"T01", "T02", "T03", "T04"}


def test_missing_direction_sheet_is_partial_but_ask_rpk_remains_available():
    data = pd.read_excel(SAMPLE_FILE, sheet_name="Data")
    bundle = build_analysis(load_data(_workbook_bytes(data), "updated.xlsx"))
    assert bundle.loaded.direction is None
    assert bundle.direction.empty
    assert int(bundle.metrics["common_growth_sample"].sum()) == 777
    assert set(bundle.tables) == {"T01", "T02"}
    assert "PARTIAL" in bundle.loaded.report


def test_same_filename_new_content_invalidates_cache_and_recomputes():
    data = pd.read_excel(SAMPLE_FILE, sheet_name="Data")
    direction = pd.read_excel(SAMPLE_FILE, sheet_name="country_year_ask_capacity")
    original = _workbook_bytes(data, direction)
    changed = data.copy()
    target = changed["ASKs"].gt(0) & changed["RPKs"].gt(0)
    row = changed.index[target][0]
    code = changed.loc[row, "Country Code"]
    year = int(changed.loc[row, "Time"])
    changed.loc[row, "ASKs"] = float(changed.loc[row, "ASKs"]) * 1.25
    updated = _workbook_bytes(changed, direction)

    state = {}
    first = sync_analysis(state, original, "same_name.xlsx", DEFAULT_CONFIG)
    first_digest = first.loaded.digest
    first_value = first.metrics.loc[
        first.metrics["Country Code"].eq(code) & first.metrics["Time"].eq(year), "ASKs"
    ].iloc[0]
    second = sync_analysis(state, updated, "same_name.xlsx", DEFAULT_CONFIG)

    assert second.loaded.digest != first_digest
    assert state["load_count"] == 2
    assert state["compute_count"] == 2
    second_value = second.metrics.loc[
        second.metrics["Country Code"].eq(code) & second.metrics["Time"].eq(year), "ASKs"
    ].iloc[0]
    assert second_value != first_value


def test_duplicate_country_year_is_rejected():
    data = pd.read_excel(SAMPLE_FILE, sheet_name="Data")
    valid = data["Country Code"].notna() & data["Time"].notna()
    duplicate = pd.concat([data, data.loc[[data.index[valid][0]]]], ignore_index=True)
    payload = _workbook_bytes(duplicate)
    try:
        load_data(payload, "duplicate.xlsx")
    except Exception as exc:
        assert "重复" in str(exc)
    else:
        raise AssertionError("重复国家—年份未被拒绝")


def test_navigation_and_labels_follow_new_information_architecture():
    assert MODULES == [
        "数据概览", "全样本分析", "分国家ASK/RPK分析",
        "出发侧（ASK_out）与到达侧（ASK_in）分析", "数据与方法说明",
    ]
    assert MODULE_ITEMS["全样本分析"] == ["F02", "F01", "F03", "F04", "A02", "A03"]
    assert "F05" not in sum(MODULE_ITEMS.values(), [])
    assert display_label("F02") == "ASK/RPK年度增长率趋势"
    assert display_label("A01") == "自选国家ASK/RPK规模与指数比较"
    assert display_label("T01") == "ASK/RPK国家排名与排名查询"

    expected_labels = {
        "全样本分析": [
            "ASK/RPK年度增长率趋势",
            "ASK与RPK年度增长同步与偏离",
            "不同规模市场ASK/RPK增长趋势",
            "不同规模市场ASK/RPK同步性与偏离",
            "PLF年度变化与市场规模比较",
            "ASK/RPK年度增长关系分时期观察",
        ],
        "分国家ASK/RPK分析": [
            "ASK/RPK国家排名与排名查询",
            "自选国家ASK/RPK规模与指数比较",
            "国家ASK/RPK动态关系类型",
            "各国ASK/RPK年度变化方向统计",
        ],
        "出发侧（ASK_out）与到达侧（ASK_in）分析": [
            "ASK_out / ASK_in国家规模排名",
            "ASK_out与ASK_in方向不对称",
            "ASK_out / ASK_in极端不对称国家",
        ],
    }
    for module, labels in expected_labels.items():
        assert [display_label(code) for code in MODULE_ITEMS[module]] == labels


def test_period_rankings_and_direction_counts_change_with_selected_years():
    bundle = build_analysis(load_data(SAMPLE_FILE.read_bytes(), SAMPLE_FILE.name))
    early = ranking_for_period(bundle.metrics, 2016, 2019)
    later = ranking_for_period(bundle.metrics, 2020, 2021)
    assert not early.empty and not later.empty
    assert not early.set_index("Country Code")[["ASK", "RPK"]].equals(
        later.set_index("Country Code")[["ASK", "RPK"]]
    )
    summary, detail = direction_counts_for_period(bundle.metrics, 2020, 2020)
    assert int(summary.loc[summary["变化方向"].eq("同时下降"), "观测数"].iloc[0]) > 0
    assert detail["Time"].eq(2020).all()


def test_actual_air_indicator_coverage_differs_from_raw_time_coverage():
    bundle = build_analysis(load_data(SAMPLE_FILE.read_bytes(), SAMPLE_FILE.name))
    m = bundle.metrics
    assert int(m.Time.min()) == 2000
    assert int(m.loc[m.RPK_growth.notna(), "Time"].min()) > int(m.Time.min())
