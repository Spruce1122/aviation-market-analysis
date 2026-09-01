"""Original T01–T04 calculations, returning DataFrames instead of writing files."""
import pandas as pd
import logging
from core.config import *
LOGGER = logging.getLogger("aviation_dashboard")

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


