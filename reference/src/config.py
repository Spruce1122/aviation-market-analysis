"""Project-wide configuration.

All research choices that a future user may reasonably change are kept here.
No current-result values or country classifications are hard-coded.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
CORE_FIGURE_DIR = OUTPUT_DIR / "figures" / "core"
ADDITIONAL_FIGURE_DIR = OUTPUT_DIR / "figures" / "additional"
VECTOR_FIGURE_DIR = OUTPUT_DIR / "figures" / "vector"
TABLE_DIR = OUTPUT_DIR / "tables"
PROCESSED_DATA_DIR = OUTPUT_DIR / "processed_data"
LOG_DIR = OUTPUT_DIR / "logs"
MPL_CONFIG_DIR = PROJECT_ROOT / ".mplconfig"

INPUT_FILENAME = "World_Development_Indicators(4).xlsx"
INPUT_FILE = INPUT_DIR / INPUT_FILENAME

DATA_SHEET = "Data"
DIRECTION_SHEET = "country_year_ask_capacity"
DATA_COLUMNS = ["Country Name", "Country Code", "Time", "ASKs", "RPKs"]
DIRECTION_COLUMNS = ["country_code", "country_name", "year", "ASK_out", "ASK_in"]

# Market-size definition
N_LARGE = 40
N_SMALL = 40

# Robust display limits for scatter plots. These affect display only.
SCATTER_QUANTILE_LOW = 0.01
SCATTER_QUANTILE_HIGH = 0.99
SCATTER_LIMIT_MARGIN = 0.06

# F05 representative countries. Order is intentionally fixed.
REPRESENTATIVE_COUNTRIES = [
    "CHN", "USA", "IND", "JPN", "GBR", "DEU",
    "FRA", "RUS", "BRA", "CAN", "AUS", "ZMB",
]

# Labels used in selected scatter plots.
SCATTER_LABEL_COUNTRIES = ["CHN", "USA", "ZMB"]
F06_FIXED_LABEL_COUNTRIES = ["CHN", "USA", "ZMB"]
F06_AUTO_LABEL_EACH_TAIL = 2

# F06 dynamic classification: quartiles are recomputed from the current sample.
MIN_DYNAMIC_VALID_YEARS = 4
DYNAMIC_QUANTILE_LOW = 0.25
DYNAMIC_QUANTILE_HIGH = 0.75

# ASK_out / ASK_in direction analysis
ASK_DIRECTION_START = 2000
ASK_DIRECTION_END = 2019
TOP_DIRECTION_N = 9
DIRECTION_RANK_TOP_N = 10

# A01
MIN_VALID_GROWTH_YEARS = 4
N_GROWTH_GAP_EXTREMES = 10

# Pandemic periods used only in explicitly fixed pandemic comparisons.
PANDEMIC_PRE_START = 2016
PANDEMIC_PRE_END = 2019
PANDEMIC_SHOCK_YEAR = 2020
PANDEMIC_RECOVERY_YEAR = 2021
PANDEMIC_PRE_MIN_OBS = 2

# T01 fixed comparison window
RANKING_START_YEAR = 2016
RANKING_END_YEAR = 2021
RANKING_MIN_COMMON_YEARS = 5
RANKING_TOP_N = 10

# Output quality
DPI = 350
BASE_FONT_SIZE = 10.0
PANEL_TITLE_SIZE = 11.0
BOTTOM_TITLE_SIZE = 12.0


def ensure_output_directories() -> None:
    """Create all deterministic output directories."""
    for path in [
        CORE_FIGURE_DIR,
        ADDITIONAL_FIGURE_DIR,
        VECTOR_FIGURE_DIR,
        TABLE_DIR,
        PROCESSED_DATA_DIR,
        LOG_DIR,
        MPL_CONFIG_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
