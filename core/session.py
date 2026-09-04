"""Testable per-session cache. New bytes invalidate results BEFORE validation."""
import hashlib
import json
from .data_loader import load_data
from .pipeline import build_analysis

def sync_analysis(state, payload, filename, config):
    digest = hashlib.sha256(payload).hexdigest()
    source_key = (digest, filename)
    config_key = json.dumps(config.to_dict(), sort_keys=True)
    key = (source_key, config_key)
    if state.get('analysis_key') == key and state.get('bundle') is not None:
        return state['bundle']
    state['bundle'] = None
    state['analysis_key'] = None
    state['figure_cache'] = {}
    state.pop('results_zip', None)
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
