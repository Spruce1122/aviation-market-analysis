from streamlit.testing.v1 import AppTest


F01_APP = '''
from tests.conftest import make_workbook
from core.data_loader import load_data
from core.pipeline import build_analysis
from components.pages import chart_page
payload, codes = make_workbook()
bundle = build_analysis(load_data(payload, "test.xlsx"))
chart_page(bundle, "ASK–RPK供需关系")
'''


DYNAMIC_APP = '''
from tests.conftest import make_workbook
from core.data_loader import load_data
from core.pipeline import build_analysis
from components.pages import dynamic_page
payload, codes = make_workbook()
bundle = build_analysis(load_data(payload, "test.xlsx"))
dynamic_page(bundle)
'''


def test_f01_page_switches_to_single_year_without_frontend_error():
    app = AppTest.from_string(F01_APP, default_timeout=60).run()
    app.selectbox(key="ask_rpk_start_year").select(2020)
    app.selectbox(key="ask_rpk_end_year").select(2020)
    app = app.run()
    assert not app.exception
    assert len(app.get("download_button")) == 3
    assert any("单年" in str(item.value) for item in app.markdown)


def test_f06_single_year_shows_method_warning_and_no_old_download():
    app = AppTest.from_string(DYNAMIC_APP, default_timeout=60).run()
    app.multiselect(key="dynamic_countries").set_value(["AAA", "AAB", "AAC"])
    app.selectbox(key="dynamic_chart").select("F06")
    app.selectbox(key="dynamic_start_year").select(2020)
    app.selectbox(key="dynamic_end_year").select(2020)
    app = app.run()
    assert not app.exception
    assert not app.get("download_button")
    assert any("至少3个有效年度增长观测" in str(item.value) for item in app.markdown)
