import numpy as np

from core.ask_rpk_metrics import build_country_dynamic_metrics, build_representative_index_data
from core.data_loader import load_data
from core.period_analysis import (annual_country_detail, country_mean_growth, direction_extremes,
    direction_for_period, level_summary, market_sync_summary, period_growth_rows,
    plf_year_summary, ranking_for_period, t02_for_period)
from core.pipeline import build_analysis


def _bundle(workbook):
    payload, _ = workbook
    return build_analysis(load_data(payload, "World_Development_Indicators.xlsx"))


def test_f01_multi_has_one_point_per_country_and_periods_change(workbook):
    bundle=_bundle(workbook)
    multi=country_mean_growth(bundle.metrics,2018,2021)
    single=country_mean_growth(bundle.metrics,2020,2020)
    assert multi["Country Code"].is_unique and single["Country Code"].is_unique
    assert len(multi)==bundle.metrics["Country Code"].nunique()
    assert not np.allclose(multi.ASK_growth.fillna(0),single.ASK_growth.fillna(0))
    assert int(period_growth_rows(bundle.metrics,2020,2020).Time.nunique())==1


def test_levels_ranking_and_annual_query_follow_selected_period(workbook):
    bundle=_bundle(workbook);codes=list(bundle.metrics["Country Code"].unique()[:6])
    single=level_summary(bundle.metrics,2020,2020,codes)
    multi=level_summary(bundle.metrics,2018,2021,codes)
    assert single.period_years.eq(1).all() and multi.period_years.eq(4).all()
    ask2020=ranking_for_period(bundle.metrics,2020,2020,"ASK")
    askmulti=ranking_for_period(bundle.metrics,2018,2021,"ASK")
    assert ask2020.ASK_rank.min()==1 and askmulti.ASK_rank.min()==1
    assert not ask2020[["Country Code","ASK_rank"]].equals(askmulti[["Country Code","ASK_rank"]]) or not np.allclose(ask2020.ASK,askmulti.ASK)
    detail=annual_country_detail(bundle.metrics,codes[0],2020)
    row=bundle.metrics.loc[bundle.metrics["Country Code"].eq(codes[0])&bundle.metrics.Time.eq(2020)].iloc[0]
    assert np.isclose(detail["ASK_growth"],row.ASK_growth,equal_nan=True)
    assert np.isclose(detail["PLF"],row.RPKs/row.ASKs*100)
    assert 1<=detail["ASK_rank"]<=detail["ASK_N"]


def test_direction_single_and_multi_use_ratio_of_means(workbook):
    bundle=_bundle(workbook);raw=bundle.loaded.direction
    single=direction_for_period(raw,2019,2019);multi=direction_for_period(raw,2017,2019)
    assert single.n_years.eq(1).all() and multi.n_years.le(3).all()
    assert np.allclose(multi.R,multi.mean_ASK_out/multi.mean_ASK_in)
    assert len(direction_extremes(multi,5))==10


def test_f04_f06_t02_and_plf_recompute_by_period(workbook):
    bundle=_bundle(workbook)
    f04a=market_sync_summary(bundle.metrics,2020,2020);f04b=market_sync_summary(bundle.metrics,2018,2021)
    assert not np.allclose(f04a.mean_abs_gap_pp,f04b.mean_abs_gap_pp)
    period=period_growth_rows(bundle.metrics,2018,2021)
    dynamic,thresholds=build_country_dynamic_metrics(period)
    assert not dynamic.empty and len(thresholds)==7
    s1,d1=t02_for_period(bundle.metrics,2020,2020);s2,d2=t02_for_period(bundle.metrics,2018,2021)
    assert len(d1)<len(d2) and int(s1.iloc[0]["国家—年份观测数"])!=int(s2.iloc[0]["国家—年份观测数"])
    overall,groups,raw=plf_year_summary(bundle.metrics,2018,2021)
    assert set(overall.Time)=={2018,2019,2020,2021} and not groups.empty and raw.PLF.between(0,100,inclusive="both").all()


def test_indices_reset_inside_selected_period(workbook):
    bundle=_bundle(workbook);codes=list(bundle.metrics["Country Code"].unique()[:4])
    index=build_representative_index_data(bundle.metrics,codes,2018,2021)
    bases=index.loc[index.Time.eq(index.base_year)]
    assert bases.base_year.eq(2018).all()
    assert bases.ASK_index.eq(100).all() and bases.RPK_index.eq(100).all()
