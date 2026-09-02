"""Static HTML renderers that avoid Streamlit's dynamically imported result widgets."""
from __future__ import annotations

import base64
from html import escape
from io import BytesIO
from typing import Iterable, Mapping

import pandas as pd
import streamlit as st

from plots.registry import PLOT_LOCK


def render_kpi_cards(cards: Iterable[tuple[str, object] | tuple[str, object, str]]) -> None:
    """Render result KPIs as ordinary HTML, never ``st.metric``."""
    blocks = []
    for item in cards:
        label, value, *rest = item
        note = rest[0] if rest else ""
        blocks.append(
            '<div class="safe-kpi-card">'
            f'<div class="safe-kpi-label">{escape(str(label))}</div>'
            f'<div class="safe-kpi-value">{escape(str(value))}</div>'
            f'<div class="safe-kpi-note">{escape(str(note))}</div>'
            '</div>'
        )
    st.markdown('<div class="safe-kpi-grid">' + ''.join(blocks) + '</div>', unsafe_allow_html=True)


def figure_png_bytes(fig, dpi: int = 170) -> bytes:
    output = BytesIO()
    with PLOT_LOCK:
        fig.savefig(output, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    return output.getvalue()


def render_figure_html(fig, alt_text: str, dpi: int = 170) -> None:
    """Embed a Matplotlib figure as a static base64 PNG preview."""
    encoded = base64.b64encode(figure_png_bytes(fig, dpi=dpi)).decode("ascii")
    st.markdown(
        '<div class="safe-figure">'
        f'<img src="data:image/png;base64,{encoded}" alt="{escape(alt_text)}">'
        '</div>',
        unsafe_allow_html=True,
    )


def _format_value(value: object, decimals: int) -> object:
    if pd.isna(value):
        return "—"
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    if isinstance(value, int):
        return f"{value:,}"
    return value


def render_table_html(
    frame: pd.DataFrame,
    *,
    max_rows: int = 30,
    decimals: int = 3,
    caption: str | None = None,
    formats: Mapping[str, str] | None = None,
) -> None:
    """Render an escaped, locally scrollable HTML table."""
    shown = frame.head(max_rows).copy()
    for column in shown.columns:
        if formats and column in formats:
            fmt = formats[column]
            shown[column] = shown[column].map(
                lambda value: "—" if pd.isna(value) else fmt.format(value)
            )
        else:
            shown[column] = shown[column].map(lambda value: _format_value(value, decimals))
    table = shown.to_html(index=False, escape=True, border=0, classes="safe-result-table")
    cap = f'<div class="safe-table-caption">{escape(caption)}</div>' if caption else ""
    st.markdown(cap + '<div class="safe-table-scroll">' + table + '</div>', unsafe_allow_html=True)


def render_message(message: str, kind: str = "info") -> None:
    """Static status box for non-fatal result messages."""
    safe_kind = kind if kind in {"info", "success", "warning"} else "info"
    st.markdown(
        f'<div class="safe-message safe-message-{safe_kind}">{escape(message)}</div>',
        unsafe_allow_html=True,
    )
