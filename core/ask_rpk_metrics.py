"""Shared ASK/RPK calculations used by every downstream figure and table."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    DEFAULT_CONFIG,
    DYNAMIC_QUANTILE_HIGH,
    DYNAMIC_QUANTILE_LOW,
    MIN_DYNAMIC_VALID_YEARS,
    N_LARGE,
    N_SMALL,
    REPRESENTATIVE_COUNTRIES,
)


def build_country_year_metrics(data: pd.DataFrame, config=DEFAULT_CONFIG) -> pd.DataFrame:
    """Create all common country-year ASK/RPK variables exactly once."""
    N_LARGE, N_SMALL = config.n_large, config.n_small
    frame = data.copy().sort_values(["Country Code", "Time"]).reset_index(drop=True)
    grouped = frame.groupby("Country Code", sort=False)
    frame["prev_Time"] = grouped["Time"].shift(1)
    frame["prev_ASKs"] = grouped["ASKs"].shift(1)
    frame["prev_RPKs"] = grouped["RPKs"].shift(1)
    frame["is_consecutive_year"] = frame["Time"].sub(frame["prev_Time"]).eq(1)

    ask_valid = (
        frame["is_consecutive_year"]
        & frame["ASKs"].gt(0)
        & frame["prev_ASKs"].gt(0)
    )
    rpk_valid = (
        frame["is_consecutive_year"]
        & frame["RPKs"].gt(0)
        & frame["prev_RPKs"].gt(0)
    )
    frame["ASK_growth"] = np.where(
        ask_valid, frame["ASKs"].div(frame["prev_ASKs"]).sub(1), np.nan
    )
    frame["RPK_growth"] = np.where(
        rpk_valid, frame["RPKs"].div(frame["prev_RPKs"]).sub(1), np.nan
    )
    frame["common_growth_sample"] = frame["ASK_growth"].notna() & frame["RPK_growth"].notna()
    frame["growth_gap"] = np.where(
        frame["common_growth_sample"],
        frame["RPK_growth"] - frame["ASK_growth"],
        np.nan,
    )
    frame["abs_growth_gap"] = frame["growth_gap"].abs()

    common = frame["common_growth_sample"]
    frame["both_up"] = common & frame["ASK_growth"].gt(0) & frame["RPK_growth"].gt(0)
    frame["both_down"] = common & frame["ASK_growth"].lt(0) & frame["RPK_growth"].lt(0)
    frame["ASK_up_RPK_down"] = common & frame["ASK_growth"].gt(0) & frame["RPK_growth"].lt(0)
    frame["ASK_down_RPK_up"] = common & frame["ASK_growth"].lt(0) & frame["RPK_growth"].gt(0)
    frame["same_direction"] = frame["both_up"] | frame["both_down"]
    frame["opposite_direction"] = frame["ASK_up_RPK_down"] | frame["ASK_down_RPK_up"]
    frame["zero_growth_unclassified"] = common & ~(
        frame["same_direction"] | frame["opposite_direction"]
    )

    plf_valid = frame["ASKs"].gt(0) & frame["RPKs"].notna()
    frame["PLF"] = np.where(plf_valid, frame["RPKs"].div(frame["ASKs"]).mul(100), np.nan)

    mean_ask = frame.groupby("Country Code")["ASKs"].mean().rename("mean_ASK")
    frame = frame.join(mean_ask, on="Country Code")
    eligible = mean_ask[mean_ask.gt(0)].reset_index()
    eligible = eligible.sort_values(["mean_ASK", "Country Code"], ascending=[False, True])
    if len(eligible) < N_LARGE + N_SMALL:
        raise ValueError(
            f"可分组国家仅{len(eligible)}个，少于N_LARGE+N_SMALL={N_LARGE + N_SMALL}。"
        )
    eligible["market_size_group"] = "Medium"
    eligible.loc[eligible.index[:N_LARGE], "market_size_group"] = "Large"
    eligible.loc[eligible.index[-N_SMALL:], "market_size_group"] = "Small"
    group_map = eligible.set_index("Country Code")["market_size_group"]
    frame["market_size_group"] = frame["Country Code"].map(group_map)
    return frame.sort_values(["Country Code", "Time"]).reset_index(drop=True)


def build_representative_index_data(
    metrics: pd.DataFrame, countries=None, start_year: int | None = None, end_year: int | None = None
) -> pd.DataFrame:
    """Create country-specific ASK/RPK indices with each country's own base year."""
    rows: list[pd.DataFrame] = []
    for code in (REPRESENTATIVE_COUNTRIES if countries is None else countries):
        country = metrics.loc[metrics["Country Code"].eq(code)].sort_values("Time").copy()
        if start_year is not None:
            country = country.loc[country["Time"].ge(start_year)]
        if end_year is not None:
            country = country.loc[country["Time"].le(end_year)]
        common_positive = country["ASKs"].gt(0) & country["RPKs"].gt(0)
        if not common_positive.any():
            continue
        base_row = country.loc[common_positive].iloc[0]
        base_year = int(base_row["Time"])
        base_ask = float(base_row["ASKs"])
        base_rpk = float(base_row["RPKs"])
        country = country.loc[country["Time"].ge(base_year)].copy()
        country["base_year"] = base_year
        country["ASK_index"] = np.where(
            country["ASKs"].gt(0), country["ASKs"].div(base_ask).mul(100), np.nan
        )
        country["RPK_index"] = np.where(
            country["RPKs"].gt(0), country["RPKs"].div(base_rpk).mul(100), np.nan
        )
        rows.append(
            country[
                [
                    "Country Name",
                    "Country Code",
                    "Time",
                    "ASKs",
                    "RPKs",
                    "base_year",
                    "ASK_index",
                    "RPK_index",
                ]
            ]
        )
    if not rows:
        return pd.DataFrame(columns=['Country Name','Country Code','Time','ASKs','RPKs','base_year','ASK_index','RPK_index'])
    return pd.concat(rows, ignore_index=True)


def build_interval_dynamic_data(
    metrics: pd.DataFrame, start_year: int, end_year: int, config=DEFAULT_CONFIG
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recompute country dynamic metrics using growth already calculated on full series."""
    interval = metrics.loc[metrics["Time"].between(start_year, end_year)].copy()
    return build_country_dynamic_metrics(interval, config)


def build_country_dynamic_metrics(
    metrics: pd.DataFrame, config=DEFAULT_CONFIG,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate common-growth observations and classify countries by sample quartiles.

    Exclusive precedence: long-run high synchronization, ASK lead, RPK lead,
    high volatility, transition. This makes overlapping quartile rules auditable.
    """
    common = metrics.loc[metrics["common_growth_sample"]].copy()
    records = []
    for code, group in common.groupby("Country Code"):
        ask = group["ASK_growth"]
        rpk = group["RPK_growth"]
        corr = ask.corr(rpk) if len(group) >= 2 else np.nan
        records.append(
            {
                "Country Name": group["Country Name"].iloc[0],
                "Country Code": code,
                "corr_ask_rpk": corr,
                "median_growth_gap": group["growth_gap"].median(),
                "mean_abs_growth_gap": group["abs_growth_gap"].mean(),
                "opposite_share": group["opposite_direction"].mean(),
                "growth_gap_std": group["growth_gap"].std(ddof=1),
                "n_valid": len(group),
            }
        )
    country = pd.DataFrame(records)
    if country.empty:
        raise ValueError("没有可用于国家动态指标的共同增长样本。")
    country = country.loc[country["n_valid"].ge(config.min_dynamic_years)].copy()
    if country.empty:
        raise ValueError("达到国家动态指标最低有效年份数的国家为0。")

    quantiles = {
        "corr_q75": country["corr_ask_rpk"].quantile(DYNAMIC_QUANTILE_HIGH),
        "median_gap_q25": country["median_growth_gap"].quantile(DYNAMIC_QUANTILE_LOW),
        "median_gap_q75": country["median_growth_gap"].quantile(DYNAMIC_QUANTILE_HIGH),
        "mean_abs_gap_q25": country["mean_abs_growth_gap"].quantile(DYNAMIC_QUANTILE_LOW),
        "mean_abs_gap_q75": country["mean_abs_growth_gap"].quantile(DYNAMIC_QUANTILE_HIGH),
        "opposite_share_q75": country["opposite_share"].quantile(DYNAMIC_QUANTILE_HIGH),
        "growth_gap_std_q75": country["growth_gap_std"].quantile(DYNAMIC_QUANTILE_HIGH),
    }
    q = quantiles

    def classify(row: pd.Series) -> str:
        if (
            pd.notna(row["corr_ask_rpk"])
            and row["corr_ask_rpk"] >= q["corr_q75"]
            and row["mean_abs_growth_gap"] <= q["mean_abs_gap_q25"]
        ):
            return "长期高同步型"
        if row["median_growth_gap"] <= q["median_gap_q25"]:
            return "ASK相对领先型"
        if row["median_growth_gap"] >= q["median_gap_q75"]:
            return "RPK相对领先型"
        if (
            row["mean_abs_growth_gap"] >= q["mean_abs_gap_q75"]
            or row["opposite_share"] >= q["opposite_share_q75"]
            or row["growth_gap_std"] >= q["growth_gap_std_q75"]
        ):
            return "高波动型"
        return "过渡型"

    country["dynamic_type"] = country.apply(classify, axis=1)
    country = country.sort_values(["dynamic_type", "Country Code"]).reset_index(drop=True)
    thresholds = pd.DataFrame(
        [{"parameter": key, "value": value} for key, value in quantiles.items()]
    )
    return country, thresholds
