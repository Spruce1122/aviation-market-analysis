from dataclasses import replace
from pathlib import Path

import pandas as pd

from core.ask_rpk_metrics import build_interval_dynamic_data, build_representative_index_data
from core.config import DEFAULT_CONFIG
from core.data_loader import load_data
from core.pipeline import build_analysis
from plots.country_index import _layout, plot_f05
from plots.direction import plot_f07
from plots.dynamic_type import plot_f06


def test_formal_result_code_avoids_dynamic_frontend_components():
    roots = [Path("app.py"), Path("components")]
    forbidden = ("st.metric(", "st.dataframe(", "st.pyplot(", "st.data_editor(")
    for root in roots:
        files = [root] if root.is_file() else list(root.rglob("*.py"))
        for file in files:
            text = file.read_text(encoding="utf-8")
            assert not any(token in text for token in forbidden), (file, forbidden)


def test_dynamic_interval_uses_full_series_growth_and_resets_index(workbook):
    payload, codes = workbook
    bundle = build_analysis(load_data(payload, "World_Development_Indicators.xlsx"))
    selected = list(codes[:6])
    index = build_representative_index_data(bundle.metrics, selected, 2018, 2022)
    assert set(index["base_year"]) == {2018}
    bases = index.loc[index.Time.eq(index.base_year)]
    assert bases.ASK_index.eq(100).all() and bases.RPK_index.eq(100).all()
    interval = bundle.metrics.loc[bundle.metrics.Time.between(2018, 2022)]
    original_growth = bundle.metrics.loc[bundle.metrics.Time.eq(2018), "ASK_growth"].reset_index(drop=True)
    filtered_growth = interval.loc[interval.Time.eq(2018), "ASK_growth"].reset_index(drop=True)
    pd.testing.assert_series_equal(original_growth, filtered_growth)
    dynamic, thresholds = build_interval_dynamic_data(bundle.metrics, 2018, 2022)
    assert not dynamic.empty and len(thresholds) == 7


def test_country_layout_scales_to_thirty_and_figures_render(workbook):
    payload, codes = workbook
    bundle = build_analysis(load_data(payload, "World_Development_Indicators.xlsx"))
    selected = list(bundle.metrics["Country Code"].drop_duplicates().head(30))
    assert _layout(1) == (1, 1)
    assert _layout(4) == (2, 2)
    assert _layout(6) == (2, 3)
    assert _layout(12) == (3, 4)
    assert _layout(20) == (4, 5)
    assert _layout(30) == (5, 6)
    data = build_representative_index_data(bundle.metrics, selected, 2018, 2022)
    fig = plot_f05(data, replace(DEFAULT_CONFIG, representative_countries=tuple(selected)))
    assert len(fig.axes) == 30
    fig.clear()
    dynamic, _ = build_interval_dynamic_data(bundle.metrics, 2018, 2022)
    fig = plot_f06(dynamic, highlight_codes=selected)
    assert fig.axes
    fig.clear()


def test_direction_uses_auto_extremes_and_bottom_title(workbook):
    payload, _ = workbook
    bundle = build_analysis(load_data(payload, "World_Development_Indicators.xlsx"))
    fig = plot_f07(bundle.direction_low, bundle.direction_high)
    assert len(bundle.direction_low) == 9 and len(bundle.direction_high) == 9
    assert any(text.get_text() == "图7 ASK_out与ASK_in方向不对称国家比较" for text in fig.texts)
    fig.clear()
