"""Auditable chart inputs and country-level views of shared processed DataFrames."""
import numpy as np
import pandas as pd
from .config import *

def trend_metrics(bundle):
    m = bundle.metrics
    c = bundle.config
    if c.trend_year_start is not None:
        m = m.loc[m.Time.ge(c.trend_year_start)]
    if c.trend_year_end is not None:
        m = m.loc[m.Time.le(c.trend_year_end)]
    return m

def chart_data(bundle, chart):
    m = bundle.metrics
    common = m.loc[m.common_growth_sample].copy()
    if chart == 'F01':
        common = common.loc[common.market_size_group.notna()].copy()
        common['x'] = common.ASK_growth * 100
        common['y'] = common.RPK_growth * 100
        return common
    if chart in ('F02', 'F03'):
        m = trend_metrics(bundle)
        keys = ['Time'] if chart == 'F02' else ['market_size_group','Time']
        return m.groupby(keys).agg(ASK_growth=('ASK_growth','median'), RPK_growth=('RPK_growth','median'),
                                  ASK_N=('ASK_growth','count'),RPK_N=('RPK_growth','count')).reset_index()
    if chart == 'F04':
        rows = []
        for group in ['Large','Medium','Small']:
            p = common.loc[common.market_size_group.eq(group)]
            rows.append(dict(group=group, corr=p.ASK_growth.corr(p.RPK_growth) if len(p)>1 else np.nan,
                mean_abs_gap_pp=p.abs_growth_gap.mean()*100,
                opposite_share_pct=p.opposite_direction.mean()*100, N=len(p)))
        return pd.DataFrame(rows)
    if chart == 'F05':
        return bundle.indices
    if chart == 'F06':
        p = bundle.dynamic.dropna(subset=['corr_ask_rpk','mean_abs_growth_gap']).copy()
        p['gap_pp'] = p.mean_abs_growth_gap * 100
        p['point_size'] = 55 + 95 * (p.n_valid - p.n_valid.min()) / max(float(p.n_valid.max()-p.n_valid.min()),1.0)
        return p
    if chart == 'F07':
        return pd.concat([bundle.direction_low,bundle.direction_high],ignore_index=True).drop_duplicates('country_code').sort_values(['ln_R','country_code'])
    if chart == 'A01':
        return bundle.indices
    if chart == 'A02':
        return bundle.balanced
    if chart == 'A03':
        c = bundle.config
        wanted = common.Time.between(c.period_pre_start,c.period_pre_end) | common.Time.isin([c.period_shock_year,c.period_recovery_year])
        p = common.loc[wanted].copy()
        p['period'] = np.where(p.Time.between(c.period_pre_start,c.period_pre_end),
                               f'{c.period_pre_start}—{c.period_pre_end}',p.Time.astype(str))
        p['x'],p['y'] = p.ASK_growth*100,p.RPK_growth*100
        return p
    raise KeyError(chart)

def country_summary(bundle, codes):
    m = bundle.metrics
    identity = m.sort_values('Time').drop_duplicates('Country Code',keep='last')
    identity = identity.set_index('Country Code')[['Country Name','mean_ASK','market_size_group']]
    identity['mean_RPK'] = m.groupby('Country Code').RPKs.mean()
    valid_plf = m.loc[m.PLF.gt(0)&m.PLF.le(100)]
    identity['median_valid_PLF'] = valid_plf.groupby('Country Code').PLF.median()
    identity['n_valid_PLF'] = valid_plf.groupby('Country Code').PLF.count()
    dynamic = bundle.dynamic.drop(columns=['Country Name']).set_index('Country Code')
    identity = identity.join(dynamic)
    direction = bundle.direction.drop(columns=['country_name']).set_index('country_code')
    identity = identity.join(direction)
    return identity.reindex(codes).reset_index()
