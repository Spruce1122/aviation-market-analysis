"""Single source of truth for all figure styling and saving."""

from __future__ import annotations

import glob
import logging
import os
import warnings
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager, pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from PIL import Image

from core.config import (
    BASE_FONT_SIZE,
    BOTTOM_TITLE_SIZE,
    DPI,
    PANEL_TITLE_SIZE,
    VECTOR_FIGURE_DIR,
)


COLORS = {
    "ASK": "#1F4E79",
    "RPK": "#E67E22",
    "Large": "#1F4E79",
    "Medium": "#71879B",
    "Small": "#C8543D",
    "reference": "#B8BEC5",
    "grid": "#D9DEE3",
    "长期高同步型": "#1F4E79",
    "ASK相对领先型": "#507A9E",
    "RPK相对领先型": "#E67E22",
    "高波动型": "#B44C43",
    "过渡型": "#8B8F94",
    "ASK_in相对占优": "#E67E22",
    "ASK_out相对占优": "#1F4E79",
}

MARKET_LABELS = {"Large": "大型市场", "Medium": "中型市场", "Small": "小型市场"}


def _font_family_exists(family: str) -> bool:
    try:
        font_manager.findfont(family, fallback_to_default=False)
        return True
    except ValueError:
        return False


def _register_font_file(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        font_manager.fontManager.addfont(str(path))
        return font_manager.FontProperties(fname=str(path)).get_name()
    except Exception:
        return None


FONT_TEST_TEXT = "年份 年度增长率中位数 大型市场 ASK与RPK 中国"
CJK_SEARCH_PATTERNS = (
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simsun.ttf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK*.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK*.otf",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK*.ttf",
    "/usr/share/fonts/**/NotoSerifCJK*.ttc",
    "/usr/share/fonts/**/NotoSerifCJK*.otf",
    "/usr/share/fonts/**/NotoSerifCJK*.ttf",
    "/usr/share/fonts/**/NotoSerifSC*.ttc",
    "/usr/share/fonts/**/NotoSerifSC*.otf",
    "/usr/share/fonts/**/NotoSerifSC*.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK*.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK*.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK*.ttf",
    "/usr/share/fonts/**/NotoSansCJK*.ttc",
    "/usr/share/fonts/**/NotoSansCJK*.otf",
    "/usr/share/fonts/**/NotoSansCJK*.ttf",
    "/usr/share/fonts/**/NotoSansSC*.ttc",
    "/usr/share/fonts/**/NotoSansSC*.otf",
    "/usr/share/fonts/**/NotoSansSC*.ttf",
    # Development/verification fallback; production uses packages.txt paths above.
    "/workspace/scratch/*/qa_fonts/noto-serif-sc-*.ttf",
    "/workspace/scratch/*/qa_fonts/noto-sans-sc-*.ttf",
)


def _font_supports_text(path: Path, text: str = FONT_TEST_TEXT) -> bool:
    """Verify that the face Matplotlib will load contains every requested glyph."""
    try:
        charmap = font_manager.get_font(str(path)).get_charmap()
        return all(ord(char) in charmap for char in set(text) if not char.isspace())
    except Exception:
        return False


def _expand_patterns(patterns) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for pattern in patterns:
        for item in sorted(glob.glob(pattern, recursive=True)):
            suffix = Path(item).suffix.lower()
            if suffix not in {".ttf", ".otf", ".ttc"} or item in seen:
                continue
            found.append(Path(item))
            seen.add(item)
    return found


@lru_cache(maxsize=1)
def _discover_fonts() -> dict:
    searched = list(CJK_SEARCH_PATTERNS)
    explicit = os.environ.get("AVIATION_CJK_FONT")
    candidates = ([Path(explicit)] if explicit else []) + _expand_patterns(CJK_SEARCH_PATTERNS)
    cjk_path = None
    cjk_family = None
    for candidate in candidates:
        if not candidate.is_file() or not _font_supports_text(candidate):
            continue
        family = _register_font_file(candidate)
        if family:
            cjk_path, cjk_family = str(candidate), family
            break

    windows_times = [Path("C:/Windows/Fonts/times.ttf"), Path("C:/Windows/Fonts/timesbd.ttf")]
    for path in windows_times:
        _register_font_file(path)
    times_ok = _font_family_exists("Times New Roman")

    liberation_candidates = _expand_patterns((
        "/usr/share/fonts/**/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/**/LiberationSerif-Regular.otf",
        "/usr/share/fonts/**/LiberationSerif*.ttc",
    ))
    liberation_family = None
    for candidate in liberation_candidates:
        liberation_family = _register_font_file(candidate)
        if liberation_family:
            break
    if not liberation_family and _font_family_exists("Liberation Serif"):
        liberation_family = "Liberation Serif"

    latin_family = (
        "Times New Roman" if times_ok else
        liberation_family or
        ("Nimbus Roman" if _font_family_exists("Nimbus Roman") else "DejaVu Serif")
    )
    return {
        "times_new_roman": times_ok,
        "simsun": bool(cjk_family and "SimSun" in cjk_family),
        "latin_family": latin_family,
        "cjk_family": cjk_family,
        "cjk_path": cjk_path,
        "cjk_available": cjk_family is not None,
        "searched_paths": searched,
    }


def setup_plotting_style(logger: logging.Logger, require_cjk: bool = False) -> dict:
    """Register real font files once and apply one style to preview, PNG and PDF."""
    status = dict(_discover_fonts())
    if not status["times_new_roman"]:
        logger.info("Times New Roman不可用；英文字体使用 %s。", status["latin_family"])
    if status["cjk_available"]:
        logger.info("图表中文字体：%s（%s）", status["cjk_family"], status["cjk_path"])
    else:
        logger.error("未找到支持中文的Matplotlib字体。已搜索：%s", " | ".join(status["searched_paths"]))
        if require_cjk:
            raise RuntimeError("服务器未找到支持中文的字体；请确认packages.txt已安装fonts-noto-cjk。")

    families = [status["latin_family"]]
    if status["cjk_family"]:
        families.append(status["cjk_family"])
    plt.rcParams.update(
        {
            "font.family": families,
            "font.size": BASE_FONT_SIZE,
            "axes.titlesize": PANEL_TITLE_SIZE,
            "axes.labelsize": BASE_FONT_SIZE + 0.5,
            "xtick.labelsize": BASE_FONT_SIZE,
            "ytick.labelsize": BASE_FONT_SIZE,
            "legend.fontsize": BASE_FONT_SIZE,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    return status


def validate_matplotlib_fonts(logger: logging.Logger, status: dict | None = None) -> dict:
    """Render representative Chinese labels to an in-memory PNG and capture glyph errors."""
    current = dict(status or setup_plotting_style(logger))
    if not current.get("cjk_available"):
        current.update(font_validation_ok=False, font_validation_message=(
            "未找到中文字体。已搜索：" + " | ".join(current.get("searched_paths", []))))
        return current
    output = BytesIO()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig, ax = plt.subplots(figsize=(6.4, 2.0))
        ax.plot([0, 1], [0, 1], label="大型市场")
        ax.set_xlabel("年份")
        ax.set_ylabel("年度增长率中位数")
        ax.set_title("ASK与RPK")
        ax.text(0.5, 0.45, "中国", ha="center")
        ax.legend(frameon=False)
        fig.savefig(output, format="png", dpi=120, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    missing = [str(item.message) for item in caught if "Glyph" in str(item.message) and "missing" in str(item.message)]
    ok = output.tell() > 0 and not missing
    message = "字体自检通过" if ok else "字体自检发现缺字：" + "；".join(missing)
    if ok:
        logger.info("%s：中文=%s；英文=%s", message, current["cjk_family"], current["latin_family"])
    else:
        logger.error(message)
    current.update(font_validation_ok=ok, font_validation_message=message,
                   font_test_png=output.getvalue() if ok else b"")
    return current


def style_axis(ax, grid_axis: str | None = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#8E969E")
    ax.spines["bottom"].set_color("#8E969E")
    ax.tick_params(colors="#30353A", width=0.8)
    if grid_axis:
        ax.grid(axis=grid_axis, color=COLORS["grid"], linewidth=0.7, alpha=0.55)
        ax.set_axisbelow(True)


def add_bottom_title(fig, title: str, y: float = 0.012) -> None:
    fig.text(0.5, y, title, ha="center", va="bottom", fontsize=BOTTOM_TITLE_SIZE)


def percent_formatter(decimals: int = 1) -> FuncFormatter:
    return FuncFormatter(lambda value, _: f"{value:.{decimals}f}%")


def save_figure(fig, png_path: Path) -> tuple[Path, Path]:
    """Save mandatory PNG and a same-name PDF vector version."""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    VECTOR_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = VECTOR_FIGURE_DIR / f"{png_path.stem}.pdf"
    png_temp = png_path.with_name(f".{png_path.stem}.tmp.png")
    pdf_temp = pdf_path.with_name(f".{pdf_path.stem}.tmp.pdf")
    fig.savefig(png_temp, dpi=DPI, bbox_inches="tight", facecolor="white")
    with Image.open(png_temp) as image:
        image.verify()
    png_temp.replace(png_path)
    fig.savefig(pdf_temp, bbox_inches="tight", facecolor="white")
    if pdf_temp.stat().st_size == 0:
        raise RuntimeError(f"矢量图保存失败: {pdf_temp}")
    pdf_temp.replace(pdf_path)
    plt.close(fig)
    return png_path, pdf_path


def robust_common_limits(values: Iterable[np.ndarray]) -> tuple[float, float]:
    from core.config import SCATTER_LIMIT_MARGIN, SCATTER_QUANTILE_HIGH, SCATTER_QUANTILE_LOW

    arrays = [np.asarray(value, dtype=float).ravel() for value in values]
    pooled = np.concatenate(arrays)
    pooled = pooled[np.isfinite(pooled)]
    if pooled.size == 0:
        return -1.0, 1.0
    low = float(np.quantile(pooled, SCATTER_QUANTILE_LOW))
    high = float(np.quantile(pooled, SCATTER_QUANTILE_HIGH))
    if np.isclose(low, high):
        low, high = float(pooled.min()), float(pooled.max())
    span = high - low
    margin = span * SCATTER_LIMIT_MARGIN if span > 0 else max(abs(high), 1.0) * 0.1
    return low - margin, high + margin


def adjust_text_labels(texts: list, ax, logger: logging.Logger | None = None) -> None:
    """Use adjustText when installed; otherwise apply deterministic vertical repulsion."""
    if not texts:
        return
    try:
        from adjustText import adjust_text

        adjust_text(
            texts,
            ax=ax,
            arrowprops={"arrowstyle": "-", "color": "#7D858C", "lw": 0.6},
            expand=(1.08, 1.18),
            force_text=(0.25, 0.45),
            force_points=(0.15, 0.25),
            iter_lim=150,
        )
        return
    except ImportError:
        if logger:
            logger.warning("adjustText未安装；使用内置确定性标签避让。")

    # Deterministic fallback in display coordinates for a small label set.
    fig = ax.figure
    for text in texts:
        text.set_clip_on(True)
    fig.canvas.draw()
    for _ in range(100):
        moved = False
        renderer = fig.canvas.get_renderer()
        boxes = [text.get_window_extent(renderer=renderer).expanded(1.05, 1.14) for text in texts]
        shifts = [np.zeros(2) for _ in texts]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                if not boxes[i].overlaps(boxes[j]):
                    continue
                center_i = np.array([(boxes[i].x0 + boxes[i].x1) / 2, (boxes[i].y0 + boxes[i].y1) / 2])
                center_j = np.array([(boxes[j].x0 + boxes[j].x1) / 2, (boxes[j].y0 + boxes[j].y1) / 2])
                delta = center_i - center_j
                if np.allclose(delta, 0):
                    delta = np.array([1.0 if i % 2 == 0 else -1.0, 1.0])
                direction = delta / max(np.linalg.norm(delta), 1.0)
                push = direction * np.array([2.0, 3.5])
                shifts[i] += push
                shifts[j] -= push
        axes_box = ax.get_window_extent(renderer=renderer)
        for i, (text, shift, box) in enumerate(zip(texts, shifts, boxes)):
            correction = shift.copy()
            if box.x0 + correction[0] < axes_box.x0 + 3:
                correction[0] += axes_box.x0 + 3 - (box.x0 + correction[0])
            if box.x1 + correction[0] > axes_box.x1 - 3:
                correction[0] -= box.x1 + correction[0] - (axes_box.x1 - 3)
            if box.y0 + correction[1] < axes_box.y0 + 3:
                correction[1] += axes_box.y0 + 3 - (box.y0 + correction[1])
            if box.y1 + correction[1] > axes_box.y1 - 3:
                correction[1] -= box.y1 + correction[1] - (axes_box.y1 - 3)
            if np.linalg.norm(correction) > 0.1:
                display = ax.transData.transform(text.get_position()) + correction
                text.set_position(ax.transData.inverted().transform(display))
                moved = True
        if not moved:
            break
        fig.canvas.draw()
