from dataclasses import replace
from io import BytesIO
import zipfile

import pandas as pd

from core.catalog import CHARTS
from core.config import DEFAULT_CONFIG
from core.data_loader import DataInputError, load_data
from core.pipeline import build_analysis
from core.session import release_session_data, sync_analysis
from plots.registry import render_chart
from utils.export import results_zip
from .conftest import make_workbook


def config_for(codes):
    return replace(DEFAULT_CONFIG, representative_countries=codes)


def test_all_report_charts_and_tables_render_in_memory(workbook):
    payload, codes = workbook
    bundle = build_analysis(load_data(payload, 'World_Development_Indicators.xlsx'), config_for(codes))
    assert set(bundle.tables) == {'T01', 'T02', 'T03', 'T04'}
    assert set(CHARTS) == {'F01','F02','F03','F04','F05','F06','F07','A01','A02','A03'}
    for code in CHARTS:
        figure = render_chart(bundle, code)
        assert figure.axes
        figure.clear()
    archive_bytes = results_zip(bundle)
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
        assert len([name for name in names if name.endswith('.png')]) == 10
        assert len([name for name in names if name.startswith('tables/') and name.endswith('.xlsx')]) == 4
        assert 'validation_report.txt' in names
        assert 'analysis_manifest.json' in names


def test_same_filename_changed_content_recomputes_without_cross_session_reuse(workbook):
    first_payload, codes = workbook
    second_payload, _ = make_workbook(scale=1.35)
    first_state, second_state = {}, {}
    first = sync_analysis(first_state, first_payload, 'World_Development_Indicators.xlsx', config_for(codes))
    second = sync_analysis(second_state, second_payload, 'World_Development_Indicators.xlsx', config_for(codes))
    assert first.loaded.digest != second.loaded.digest
    assert first.metrics.ASKs.sum() != second.metrics.ASKs.sum()
    assert first_state['loaded'] is not second_state['loaded']

    updated = sync_analysis(first_state, second_payload, 'World_Development_Indicators.xlsx', config_for(codes))
    assert updated.loaded.digest == second.loaded.digest
    assert first_state['load_count'] == 2
    assert first_state['compute_count'] == 2
    release_session_data(first_state)
    assert 'loaded' not in first_state and 'bundle' not in first_state and 'results_zip' not in first_state


def test_missing_direction_is_partial_and_never_fabricated():
    payload, codes = make_workbook(include_direction=False)
    bundle = build_analysis(load_data(payload, 'World_Development_Indicators.xlsx'), config_for(codes))
    assert bundle.loaded.direction is None
    assert bundle.direction.empty
    assert set(bundle.tables) == {'T01', 'T02'}
    assert 'PARTIAL' in bundle.loaded.report


def test_duplicate_country_year_is_rejected(workbook):
    payload, _ = workbook
    book = pd.ExcelFile(BytesIO(payload), engine='openpyxl')
    data = pd.read_excel(book, sheet_name='Data')
    direction = pd.read_excel(book, sheet_name='country_year_ask_capacity')
    duplicate = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        duplicate.to_excel(writer, sheet_name='Data', index=False)
        direction.to_excel(writer, sheet_name='country_year_ask_capacity', index=False)
    try:
        load_data(output.getvalue(), 'World_Development_Indicators.xlsx')
    except DataInputError as exc:
        assert '重复' in str(exc)
    else:
        raise AssertionError('重复国家—年份未被拒绝')


def test_analysis_creates_no_user_data_files(tmp_path, monkeypatch, workbook):
    payload, codes = workbook
    monkeypatch.chdir(tmp_path)
    before = set(tmp_path.rglob('*'))
    bundle = build_analysis(load_data(payload, 'World_Development_Indicators.xlsx'), config_for(codes))
    results_zip(bundle)
    after = set(tmp_path.rglob('*'))
    assert after == before
