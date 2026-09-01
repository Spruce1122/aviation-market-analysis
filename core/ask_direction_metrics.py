"""Shared ASK_out / ASK_in country-period calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DEFAULT_CONFIG, ASK_DIRECTION_END, ASK_DIRECTION_START, TOP_DIRECTION_N


def build_direction_metrics(direction: pd.DataFrame, config=DEFAULT_CONFIG) -> pd.DataFrame:
    """Use pairwise-valid years so outbound and inbound means share the same years."""
    sample = direction.loc[
        direction["year"].between(config.direction_start, config.direction_end)
        & direction["ASK_out"].notna()
        & direction["ASK_in"].notna()
    ].copy()
    result = (
        sample.groupby(["country_code", "country_name"], as_index=False)
        .agg(
            mean_ASK_out=("ASK_out", "mean"),
            mean_ASK_in=("ASK_in", "mean"),
            n_years=("year", "nunique"),
        )
    )
    result = result.loc[
        result["mean_ASK_out"].gt(0) & result["mean_ASK_in"].gt(0)
    ].copy()
    result["R"] = result["mean_ASK_out"].div(result["mean_ASK_in"])
    result["ln_R"] = np.log(result["R"])
    return result.sort_values(["ln_R", "country_code"]).reset_index(drop=True)


def select_direction_extremes(direction_metrics: pd.DataFrame, config=DEFAULT_CONFIG) -> tuple[pd.DataFrame, pd.DataFrame]:
    low = (
        direction_metrics.sort_values(["ln_R", "country_code"], ascending=[True, True])
        .head(config.top_direction_n)
        .copy()
    )
    high = (
        direction_metrics.sort_values(["ln_R", "country_code"], ascending=[False, True])
        .head(config.top_direction_n)
        .copy()
    )
    low["extreme_group"] = "ASK_in相对占优"
    high["extreme_group"] = "ASK_out相对占优"
    return low, high
