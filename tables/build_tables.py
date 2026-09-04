"""Original T01–T04 calculations, returning DataFrames instead of writing files."""
import pandas as pd
import logging
from core.config import *
LOGGER = logging.getLogger("aviation_dashboard")


def ranking_for_period(metrics: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """Rank countries using pairwise-positive ASK/RPK observations in a chosen period."""
    sample = metrics.loc[
        metrics["Time"].between(start, end) & metrics["ASKs"].gt(0) & metrics["RPKs"].gt(0)
    ].copy()
    ranking = sample.groupby(["Country Name", "Country Code"], as_index=False).agg(
        有效年份=("Time", "nunique"), ASK=("ASKs", "mean"), RPK=("RPKs", "mean"),
        sum_ASK=("ASKs", "sum"), sum_RPK=("RPKs", "sum"),
        ASK增长率=("ASK_growth", "median"), RPK增长率=("RPK_growth", "median"),
    )
    if ranking.empty:
        return ranking
    ranking["ASK排名"] = ranking["ASK"].rank(method="min", ascending=False).astype(int)
    ranking["RPK排名"] = ranking["RPK"].rank(method="min", ascending=False).astype(int)
    ranking["加权PLF（%）"] = ranking["sum_RPK"].div(ranking["sum_ASK"]).mul(100)
    ranking["ASK增长率（%）"] = ranking.pop("ASK增长率").mul(100)
    ranking["RPK增长率（%）"] = ranking.pop("RPK增长率").mul(100)
    return ranking.drop(columns=["sum_ASK", "sum_RPK"])


def direction_counts_for_period(metrics: pd.DataFrame, start: int, end: int):
    common = metrics.loc[metrics["common_growth_sample"] & metrics["Time"].between(start, end)].copy()
    categories = [
        ("同时增长", "both_up"), ("同时下降", "both_down"),
        ("ASK增长、RPK下降", "ASK_up_RPK_down"), ("ASK下降、RPK增长", "ASK_down_RPK_up"),
        ("同方向合计", "same_direction"), ("反方向合计", "opposite_direction"),
    ]
    total = len(common)
    summary = pd.DataFrame([
        {"变化方向": label, "观测数": int(common[col].sum()),
         "占有效样本比例（%）": int(common[col].sum()) / total * 100 if total else float("nan")}
        for label, col in categories
    ])
    detail_cols = ["Country Name", "Country Code", "Time", "ASK_growth", "RPK_growth",
                   "both_up", "both_down", "ASK_up_RPK_down", "ASK_down_RPK_up",
                   "same_direction", "opposite_direction"]
    detail = common[detail_cols].copy()
    detail["ASK_growth"] *= 100
    detail["RPK_growth"] *= 100
    return summary, detail


def direction_ranking_for_period(direction_metrics: pd.DataFrame, metric: str, top_n: int) -> pd.DataFrame:
    label = "mean_ASK_out" if metric == "ASK_out" else "mean_ASK_in"
    columns = ["country_name", "country_code", "mean_ASK_out", "mean_ASK_in", "R", "ln_R", "n_years"]
    return direction_metrics.sort_values([label, "country_code"], ascending=[False, True])[columns].head(top_n)

def make_t01(metrics: pd.DataFrame, logger=LOGGER, config=DEFAULT_CONFIG) :
    sample = metrics.loc[
        metrics["Time"].between(RANKING_START_YEAR, RANKING_END_YEAR)
        & metrics["ASKs"].gt(0)
        & metrics["RPKs"].gt(0)
    ].copy()
    ranking = (
        sample.groupby(["Country Name", "Country Code"], as_index=False)
        .agg(
            n_common_years=("Time", "nunique"),
            mean_ASK=("ASKs", "mean"),
            mean_RPK=("RPKs", "mean"),
            sum_ASK=("ASKs", "sum"),
            sum_RPK=("RPKs", "sum"),
        )
    )
    ranking = ranking.loc[ranking["n_common_years"].ge(RANKING_MIN_COMMON_YEARS)].copy()
    ranking["ASK_rank"] = ranking["mean_ASK"].rank(method="min", ascending=False).astype(int)
    ranking["RPK_rank"] = ranking["mean_RPK"].rank(method="min", ascending=False).astype(int)
    ranking["weighted_PLF"] = ranking["sum_RPK"].div(ranking["sum_ASK"]).mul(100)
    output_columns = [
        "Country Name", "Country Code", "n_common_years", "mean_ASK", "mean_RPK",
        "ASK_rank", "RPK_rank", "weighted_PLF",
    ]
    ask_top = ranking.sort_values(["ASK_rank", "Country Code"])[output_columns].head(RANKING_TOP_N)
    rpk_top = ranking.sort_values(["RPK_rank", "Country Code"])[output_columns].head(RANKING_TOP_N)

    return {"ASK_Top10": ask_top, "RPK_Top10": rpk_top}, ranking


def make_t02(metrics: pd.DataFrame, logger=LOGGER, config=DEFAULT_CONFIG) :
    common = metrics.loc[metrics["common_growth_sample"]].copy()
    total = len(common)
    categories = [
        ("同时增长", "both_up"),
        ("同时下降", "both_down"),
        ("ASK增长、RPK下降", "ASK_up_RPK_down"),
        ("ASK下降、RPK增长", "ASK_down_RPK_up"),
        ("同方向合计", "same_direction"),
        ("反方向合计", "opposite_direction"),
    ]
    rows = []
    for label, column in categories:
        count = int(common[column].sum())
        rows.append(
            {"变化方向": label, "观测数": count, "占有效样本比例（%）": count / total * 100 if total else float("nan")}
        )
    summary = pd.DataFrame(rows)
    check = pd.DataFrame(
        [
            {"校验项目": "共同增长有效样本总数", "数值": total},
            {"校验项目": "增长率等于0且未进入严格增减类别", "数值": int(common["zero_growth_unclassified"].sum())},
            {"校验项目": "四个互斥基本类别合计", "数值": int(
                common[["both_up", "both_down", "ASK_up_RPK_down", "ASK_down_RPK_up"]].sum().sum()
            )},
        ]
    )
    return {"方向统计": summary, "校验": check}


def make_t03(direction_low: pd.DataFrame, direction_high: pd.DataFrame, logger=LOGGER, config=DEFAULT_CONFIG) :
    columns = ["country_name", "country_code", "mean_ASK_out", "mean_ASK_in", "R", "ln_R", "n_years"]
    low = direction_low[columns].sort_values(["ln_R", "country_code"])
    high = direction_high[columns].sort_values(["ln_R", "country_code"], ascending=[False, True])
    return {f"ln_R最低{config.top_direction_n}国": low, f"ln_R最高{config.top_direction_n}国": high}


def make_t04(direction_metrics: pd.DataFrame, logger=LOGGER, config=DEFAULT_CONFIG) :
    columns = ["country_name", "country_code", "mean_ASK_out", "mean_ASK_in", "R", "ln_R", "n_years"]
    rename = {
        "country_name": "国家",
        "country_code": "ISO",
        "n_years": "有效年份数",
    }
    out_top = (
        direction_metrics.nlargest(DIRECTION_RANK_TOP_N, ["mean_ASK_out", "mean_ASK_in"])[columns]
        .rename(columns=rename)
    )
    in_top = (
        direction_metrics.nlargest(DIRECTION_RANK_TOP_N, ["mean_ASK_in", "mean_ASK_out"])[columns]
        .rename(columns=rename)
    )
    return {"ASK_out_top10": out_top, "ASK_in_top10": in_top}

