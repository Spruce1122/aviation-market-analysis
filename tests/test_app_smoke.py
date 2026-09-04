from pathlib import Path
from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


def _loaded_app():
    app = AppTest.from_file(str(APP), default_timeout=180).run()
    next(button for button in app.button if button.label == "载入报告基准，开始分析").click().run(timeout=180)
    assert not app.exception
    return app


def test_app_has_exactly_five_modules_and_overview_loads():
    app = _loaded_app()
    nav = next(radio for radio in app.radio if radio.label == "分析模块")
    assert nav.options == [
        "数据概览", "全样本分析", "分国家ASK/RPK分析",
        "出发侧（ASK_out）与到达侧（ASK_in）分析", "数据与方法说明",
    ]
    assert not app.error


def test_all_three_analysis_modules_render_without_page_errors():
    for module in ["全样本分析", "分国家ASK/RPK分析", "出发侧（ASK_out）与到达侧（ASK_in）分析"]:
        app = _loaded_app()
        next(radio for radio in app.radio if radio.label == "分析模块").set_value(module).run(timeout=180)
        assert not app.exception
        assert not app.error
