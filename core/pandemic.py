"""Original strict balanced PLF calculation (pre-period country median)."""
import pandas as pd
from .config import *

def build_balanced_pandemic_plf(metrics: pd.DataFrame, config=DEFAULT_CONFIG) -> pd.DataFrame:
    """Construct one country-level PLF value per period for a balanced sample."""
    valid = metrics.loc[metrics["PLF"].gt(0) & metrics["PLF"].le(100)].copy()
    pre = valid.loc[valid["Time"].between(config.period_pre_start, config.period_pre_end)]
    pre_stats = (
        pre.groupby("Country Code")
        .agg(pre_plf=("PLF", "median"), pre_n=("PLF", "count"))
        .reset_index()
    )
    shock = valid.loc[valid["Time"].eq(config.period_shock_year), ["Country Code", "PLF"]].rename(
        columns={"PLF": "shock_plf"}
    )
    recovery = valid.loc[
        valid["Time"].eq(config.period_recovery_year), ["Country Code", "PLF"]
    ].rename(columns={"PLF": "recovery_plf"})
    identity = (
        metrics.sort_values("Time")
        .drop_duplicates("Country Code", keep="last")
        [["Country Code", "Country Name", "market_size_group"]]
    )
    balanced = pre_stats.merge(shock, on="Country Code", how="inner").merge(
        recovery, on="Country Code", how="inner"
    )
    minimum_pre = 1 if config.period_pre_start == config.period_pre_end else PANDEMIC_PRE_MIN_OBS
    balanced = balanced.loc[balanced["pre_n"].ge(minimum_pre)].merge(
        identity, on="Country Code", how="left"
    )
    return balanced
