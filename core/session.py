"""Testable per-session cache. New bytes invalidate results BEFORE validation."""
import hashlib
import json
import gc
from .data_loader import load_data
from .pipeline import build_analysis

SESSION_DATA_KEYS = (
    'bundle', 'analysis_key', 'figure_cache', 'results_zip', 'loaded',
    'source_key', 'source_label', 'font_status',
)

def _clear_figures(state):
    figures = state.get('figure_cache') or {}
    for figure in figures.values():
        try:
            figure.clear()
        except Exception:
            pass

def release_session_data(state):
    """Release figures and uploaded-workbook derivatives owned by one session."""
    _clear_figures(state)
    for key in SESSION_DATA_KEYS:
        state.pop(key, None)
    gc.collect()

def sync_analysis(state, payload, filename, config):
    digest = hashlib.sha256(payload).hexdigest()
    source_key = (digest, filename)
    config_key = json.dumps(config.to_dict(), sort_keys=True)
    key = (source_key, config_key)
    if state.get('analysis_key') == key and state.get('bundle') is not None:
        return state['bundle']
    if state.get('source_key') != source_key:
        release_session_data(state)
    else:
        _clear_figures(state)
        for derived_key in ('bundle','analysis_key','figure_cache','results_zip'):
            state.pop(derived_key, None)
    if state.get('source_key') != source_key:
        state['loaded'] = None
        state['source_key'] = None
        loaded = load_data(payload, filename)
        state['loaded'], state['source_key'] = loaded, source_key
        state['load_count'] = state.get('load_count', 0) + 1
    bundle = build_analysis(state['loaded'], config)
    state['bundle'], state['analysis_key'] = bundle, key
    state['compute_count'] = state.get('compute_count',0) + 1
    return bundle
