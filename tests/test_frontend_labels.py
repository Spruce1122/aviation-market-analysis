from io import BytesIO
import re
import zipfile

from core.catalog import CHARTS, HOW_TO_READ, MODULE_ITEMS, display_label
from core.config import SAMPLE_FILE
from core.data_loader import load_data
from core.pipeline import build_analysis
from plots.registry import render_chart
from utils.export import results_zip


VISIBLE_NUMBER = re.compile(r"(?:F|A|T)0[1-9]|附图\s*[0-9]+|图\s*[0-9]+")


def _all_figure_text(figure):
    text = [item.get_text() for item in figure.texts]
    for axis in figure.axes:
        text.extend([axis.get_title(), axis.get_xlabel(), axis.get_ylabel()])
        text.extend(item.get_text() for item in axis.texts)
        legend = axis.get_legend()
        if legend is not None:
            text.extend(item.get_text() for item in legend.get_texts())
    return [item for item in text if item]


def test_frontend_navigation_and_explanations_have_no_internal_numbers():
    frontend_codes = [code for codes in MODULE_ITEMS.values() for code in codes]
    for code in frontend_codes:
        assert not VISIBLE_NUMBER.search(display_label(code))
        assert not any(VISIBLE_NUMBER.search(line) for line in HOW_TO_READ[code])


def test_web_figures_have_semantic_titles_and_offline_titles_remain_numbered():
    bundle = build_analysis(load_data(SAMPLE_FILE.read_bytes(), SAMPLE_FILE.name))
    for code in CHARTS:
        figure = render_chart(bundle, code, numbered_title=False)
        figure_text = _all_figure_text(figure)
        assert CHARTS[code][0] in figure_text
        assert not any(VISIBLE_NUMBER.search(item) for item in figure_text), code

    offline = render_chart(bundle, "F02")
    assert "图2 ASK与RPK年度增长率中位数趋势" in _all_figure_text(offline)


def test_web_export_keeps_numbered_filenames_but_hides_codes_in_progress():
    bundle = build_analysis(load_data(SAMPLE_FILE.read_bytes(), SAMPLE_FILE.name))
    progress_messages = []
    payload = results_zip(
        bundle,
        lambda _, message: progress_messages.append(message),
        numbered_titles=False,
    )
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        names = set(archive.namelist())
    assert f"figures/core/{CHARTS['F01'][1]}.png" in names
    assert f"figures/additional/{CHARTS['A01'][1]}.png" in names
    assert "tables/T01_ASK_RPK国家排名与排名查询.xlsx" in names
    assert not any(VISIBLE_NUMBER.search(message) for message in progress_messages)
