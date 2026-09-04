import logging
from io import BytesIO
from pathlib import Path
import warnings

import pytest

from core.catalog import CHARTS
from core.config import SAMPLE_FILE
from core.data_loader import load_data
from core.pipeline import build_analysis
from plots.registry import render_chart
from plots.style import CJK_SEARCH_PATTERNS, setup_plotting_style, validate_matplotlib_fonts


LOGGER = logging.getLogger("font_rendering_test")


@pytest.fixture(scope="module")
def analysis_bundle():
    return build_analysis(load_data(SAMPLE_FILE.read_bytes(), SAMPLE_FILE.name))


def test_cloud_font_search_supports_noto_ttf_otf_and_ttc():
    patterns = "\n".join(CJK_SEARCH_PATTERNS)
    assert "/usr/share/fonts/opentype/noto/" in patterns
    assert "/usr/share/fonts/truetype/noto/" in patterns
    assert "/usr/share/fonts/**/NotoSerifCJK" in patterns
    assert "/usr/share/fonts/**/NotoSansCJK" in patterns
    assert all(extension in patterns for extension in (".ttf", ".otf", ".ttc"))
    packages = (Path(__file__).resolve().parents[1] / "packages.txt").read_text(encoding="utf-8")
    assert "fonts-noto-cjk" in packages
    assert "fonts-liberation" in packages


def test_matplotlib_chinese_font_self_check_passes():
    status = setup_plotting_style(LOGGER, require_cjk=True)
    checked = validate_matplotlib_fonts(LOGGER, status)
    assert checked["cjk_available"]
    assert checked["cjk_path"]
    assert checked["cjk_family"]
    assert checked["font_validation_ok"], checked["font_validation_message"]
    assert checked["font_test_png"].startswith(b"\x89PNG")


def test_all_chart_png_and_pdf_exports_have_no_missing_glyphs(analysis_bundle):
    missing = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for code in CHARTS:
            figure = render_chart(analysis_bundle, code)
            for output_format, signature in (("png", b"\x89PNG"), ("pdf", b"%PDF")):
                output = BytesIO()
                figure.savefig(output, format=output_format, dpi=120, bbox_inches="tight")
                assert output.getvalue().startswith(signature), f"{code} {output_format} export failed"
        missing = [
            str(item.message)
            for item in caught
            if "Glyph" in str(item.message) and "missing" in str(item.message)
        ]
    assert not missing, "；".join(missing)
