"""Single shared analysis entry point for Streamlit, batch export and tests."""
from dataclasses import dataclass
import pandas as pd
from .config import DEFAULT_CONFIG, AnalysisConfig
from .data_loader import LoadedWorkbook, DataInputError
from .ask_rpk_metrics import build_country_year_metrics, build_representative_index_data, build_country_dynamic_metrics
from .ask_direction_metrics import build_direction_metrics, select_direction_extremes
from .pandemic import build_balanced_pandemic_plf
from tables.build_tables import make_t01, make_t02, make_t03, make_t04

@dataclass
class AnalysisBundle:
    loaded: LoadedWorkbook
    config: AnalysisConfig
    metrics: pd.DataFrame
    indices: pd.DataFrame
    all_indices: pd.DataFrame
    dynamic: pd.DataFrame
    thresholds: pd.DataFrame
    direction: pd.DataFrame
    direction_low: pd.DataFrame
    direction_high: pd.DataFrame
    balanced: pd.DataFrame
    ranking: pd.DataFrame
    tables: dict
    warnings: list[str]

    def processed(self):
        return {
            'country_year_ask_rpk_metrics.csv': self.metrics,
            'representative_country_indices.csv': self.indices,
            'country_dynamic_metrics.csv': self.dynamic,
            'dynamic_type_thresholds.csv': self.thresholds,
            'country_ask_direction_metrics.csv': self.direction,
            'ask_direction_extreme_countries.csv': pd.concat([self.direction_low, self.direction_high], ignore_index=True),
            'pandemic_plf_balanced_sample.csv': self.balanced,
            't01_market_ranking_eligible_countries.csv': self.ranking,
        }

def build_analysis(loaded: LoadedWorkbook, config=DEFAULT_CONFIG):
    config.validate()
    notes = list(loaded.warnings)
    try:
        metrics = build_country_year_metrics(loaded.data, config)
    except ValueError as exc:
        raise DataInputError(str(exc) + ' 请在左侧参数中减小大型/小型市场数量后应用。', loaded.report) from exc
    all_indices = build_representative_index_data(metrics, sorted(metrics['Country Code'].unique()))
    indices = build_representative_index_data(metrics, config.representative_countries)
    try:
        dynamic, thresholds = build_country_dynamic_metrics(metrics, config)
    except ValueError as exc:
        notes.append(str(exc))
        dynamic = pd.DataFrame(columns=['Country Name','Country Code','corr_ask_rpk','median_growth_gap',
                      'mean_abs_growth_gap','opposite_share','growth_gap_std','n_valid','dynamic_type'])
        thresholds = pd.DataFrame(columns=['parameter','value'])
    if loaded.direction is not None:
        direction = build_direction_metrics(loaded.direction, config)
    else:
        direction = pd.DataFrame(columns=['country_code','country_name','mean_ASK_out','mean_ASK_in','n_years','R','ln_R'])
    low, high = select_direction_extremes(direction, config)
    if direction.empty:
        notes.append('当前方向分析区间没有可用国家，方向不对称图和相关统计表暂不可用。')
    balanced = build_balanced_pandemic_plf(metrics, config)
    t01, ranking = make_t01(metrics, config=config)
    tables = {'T01': t01, 'T02': make_t02(metrics, config=config)}
    if not direction.empty:
        tables['T03'] = make_t03(low, high, config=config)
        tables['T04'] = make_t04(direction, config=config)
    return AnalysisBundle(loaded, config, metrics, indices, all_indices, dynamic, thresholds,
                          direction, low, high, balanced, ranking, tables, notes)
