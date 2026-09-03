"""Period-aware derived views. Raw units are preserved until display columns are built."""
from __future__ import annotations

import numpy as np
import pandas as pd


UNIT_SCALE = 1e8


def period_growth_rows(metrics: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Filter growth after full-series growth has already been computed."""
    return metrics.loc[metrics["Time"].between(start_year, end_year)].copy()


def country_mean_growth(metrics: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    part = period_growth_rows(metrics, start_year, end_year)
    identity = part.sort_values("Time").drop_duplicates("Country Code", keep="last")[["Country Name", "Country Code", "market_size_group"]]
    counts = part.groupby("Country Code", as_index=False).agg(
        n_ASK_growth=("ASK_growth", "count"), n_RPK_growth=("RPK_growth", "count"),
    )
    common = part.loc[part.common_growth_sample]
    agg = common.groupby("Country Code", as_index=False).agg(
        ASK_growth=("ASK_growth", "mean"), RPK_growth=("RPK_growth", "mean"),
        n_valid_growth_years=("Time", "nunique"),
    )
    result = identity.merge(counts, on="Country Code", how="left").merge(agg, on="Country Code", how="left")
    result["common_growth_sample"] = result[["ASK_growth", "RPK_growth"]].notna().all(axis=1)
    result["growth_gap"] = result["RPK_growth"] - result["ASK_growth"]
    result["abs_growth_gap"] = result["growth_gap"].abs()
    result["opposite_direction"] = result["common_growth_sample"] & (np.sign(result["ASK_growth"]) != np.sign(result["RPK_growth"]))
    return result


def market_sync_summary(metrics: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    common = period_growth_rows(metrics, start_year, end_year)
    common = common.loc[common.common_growth_sample & common.market_size_group.notna()]
    rows=[]
    for group in ["Large","Medium","Small"]:
        p=common.loc[common.market_size_group.eq(group)]
        rows.append({"group":group,"corr":p.ASK_growth.corr(p.RPK_growth) if len(p)>1 else np.nan,
            "mean_abs_gap_pp":p.abs_growth_gap.mean()*100,"opposite_share_pct":p.opposite_direction.mean()*100,
            "countries":p["Country Code"].nunique(),"N":len(p)})
    return pd.DataFrame(rows)


def level_summary(metrics: pd.DataFrame, start_year: int, end_year: int, countries=None) -> pd.DataFrame:
    part = metrics.loc[metrics["Time"].between(start_year, end_year)].copy()
    if countries is not None:
        part = part.loc[part["Country Code"].isin(countries)]
    total = end_year - start_year + 1
    rows = []
    for (name, code), group in part.groupby(["Country Name", "Country Code"], sort=False):
        ask = group.loc[group.ASKs.gt(0), "ASKs"]
        rpk = group.loc[group.RPKs.gt(0), "RPKs"]
        pair = group.loc[group.ASKs.gt(0) & group.RPKs.gt(0)]
        rows.append({
            "Country Name": name, "Country Code": code,
            "ASK": ask.mean(), "RPK": rpk.mean(),
            "ASK_valid_years": int(ask.count()), "RPK_valid_years": int(rpk.count()),
            "pair_valid_years": int(len(pair)), "period_years": total,
            "period_PLF": pair.RPKs.sum() / pair.ASKs.sum() * 100 if len(pair) and pair.ASKs.sum() > 0 else np.nan,
        })
    return pd.DataFrame(rows)


def ranking_for_period(metrics: pd.DataFrame, start_year: int, end_year: int, metric: str) -> pd.DataFrame:
    result = level_summary(metrics, start_year, end_year)
    value = metric
    result = result.loc[result[value].gt(0)].copy()
    result[f"{metric}_rank"] = result[value].rank(method="min", ascending=False).astype(int)
    result = result.sort_values([f"{metric}_rank", "Country Code"]).reset_index(drop=True)
    result["有效年份"] = result[f"{metric}_valid_years"].astype(str) + " / " + result["period_years"].astype(str)
    result["ASK（亿座公里）"] = result["ASK"] / UNIT_SCALE
    result["RPK（亿客公里）"] = result["RPK"] / UNIT_SCALE
    result["区间PLF（%）"] = result["period_PLF"]
    return result


def annual_country_detail(metrics: pd.DataFrame, code: str, year: int) -> dict:
    row = metrics.loc[metrics["Country Code"].eq(code) & metrics.Time.eq(year)]
    if row.empty:
        return {"Country Code": code, "Time": year}
    row = row.iloc[0]
    ask_pool = metrics.loc[metrics.Time.eq(year) & metrics.ASKs.gt(0), ["Country Code", "ASKs"]].copy()
    rpk_pool = metrics.loc[metrics.Time.eq(year) & metrics.RPKs.gt(0), ["Country Code", "RPKs"]].copy()
    ask_pool["rank"] = ask_pool.ASKs.rank(method="min", ascending=False).astype(int)
    rpk_pool["rank"] = rpk_pool.RPKs.rank(method="min", ascending=False).astype(int)
    ask_match = ask_pool.loc[ask_pool["Country Code"].eq(code)]
    rpk_match = rpk_pool.loc[rpk_pool["Country Code"].eq(code)]
    ask_rank = int(ask_match.iloc[0]["rank"]) if not ask_match.empty else None
    rpk_rank = int(rpk_match.iloc[0]["rank"]) if not rpk_match.empty else None
    return {
        "Country Name": row["Country Name"], "Country Code": code, "Time": year,
        "ASK": row.ASKs if row.ASKs > 0 else np.nan, "RPK": row.RPKs if row.RPKs > 0 else np.nan,
        "ASK_rank": ask_rank, "ASK_N": len(ask_pool), "RPK_rank": rpk_rank, "RPK_N": len(rpk_pool),
        "ASK_growth": row.ASK_growth, "RPK_growth": row.RPK_growth,
        "PLF": row.RPKs / row.ASKs * 100 if row.ASKs > 0 and pd.notna(row.RPKs) else np.nan,
    }


def direction_for_period(direction: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    sample = direction.loc[direction.year.between(start_year, end_year) & direction.ASK_out.notna() & direction.ASK_in.notna()].copy()
    result = sample.groupby(["country_code", "country_name"], as_index=False).agg(
        mean_ASK_out=("ASK_out", "mean"), mean_ASK_in=("ASK_in", "mean"), n_years=("year", "nunique"))
    result = result.loc[result.mean_ASK_out.gt(0) & result.mean_ASK_in.gt(0)].copy()
    result["R"] = result.mean_ASK_out / result.mean_ASK_in
    result["ln_R"] = np.log(result.R)
    return result


def direction_display(frame: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    result = frame.copy()
    single = start_year == end_year
    result = result.rename(columns={"country_name":"国家", "country_code":"ISO", "n_years":"有效年份数",
        "mean_ASK_out": "ASK_out（亿座公里）" if single else "平均ASK_out（亿座公里）",
        "mean_ASK_in": "ASK_in（亿座公里）" if single else "平均ASK_in（亿座公里）"})
    for col in [c for c in result.columns if "ASK_out（" in c or "ASK_in（" in c]:
        result[col] = result[col] / UNIT_SCALE
    result.insert(2, "时期", str(start_year) if single else f"{start_year}—{end_year}")
    return result


def direction_extremes(frame: pd.DataFrame, n_each: int) -> pd.DataFrame:
    n = min(n_each, len(frame))
    low = frame.sort_values(["ln_R", "country_code"]).head(n).assign(方向="ASK_in相对占优")
    high = frame.sort_values(["ln_R", "country_code"], ascending=[False, True]).head(n).assign(方向="ASK_out相对占优")
    return pd.concat([low, high], ignore_index=True).drop_duplicates("country_code")


def t02_for_period(metrics: pd.DataFrame, start_year: int, end_year: int):
    common = period_growth_rows(metrics, start_year, end_year)
    common = common.loc[common.common_growth_sample].copy()
    total = len(common)
    cats = [("同时增长","both_up"),("同时下降","both_down"),("ASK增长、RPK下降","ASK_up_RPK_down"),("ASK下降、RPK增长","ASK_down_RPK_up"),("同方向","same_direction"),("反方向","opposite_direction")]
    summary = pd.DataFrame([{"变化方向":label,"国家—年份观测数":int(common[col].sum()),"比例（%）":int(common[col].sum())/total*100 if total else np.nan} for label,col in cats])
    detail = common[["Country Name","Country Code","Time","ASK_growth","RPK_growth","growth_gap"]].copy()
    def label(row):
        if row.ASK_growth > 0 and row.RPK_growth > 0:return "同时增长"
        if row.ASK_growth < 0 and row.RPK_growth < 0:return "同时下降"
        if row.ASK_growth > 0 and row.RPK_growth < 0:return "ASK增长、RPK下降"
        if row.ASK_growth < 0 and row.RPK_growth > 0:return "ASK下降、RPK增长"
        return "含零增长"
    detail["方向类型"] = detail.apply(label, axis=1)
    for c in ["ASK_growth","RPK_growth","growth_gap"]:detail[c] *= 100
    detail = detail.rename(columns={"Country Name":"国家","Country Code":"ISO","Time":"年份","ASK_growth":"ASK同比（%）","RPK_growth":"RPK同比（%）","growth_gap":"增长差（百分点）"})
    return summary, detail


def plf_year_summary(metrics: pd.DataFrame, start_year: int, end_year: int):
    part = metrics.loc[metrics.Time.between(start_year,end_year) & metrics.PLF.gt(0) & metrics.PLF.le(100)].copy()
    overall = part.groupby("Time").PLF.agg(median="median", q25=lambda s:s.quantile(.25), q75=lambda s:s.quantile(.75), N="count").reset_index()
    by_group = part.groupby(["market_size_group","Time"]).PLF.agg(median="median",N="count").reset_index()
    return overall, by_group, part
