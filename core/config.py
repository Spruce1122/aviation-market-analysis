"""Report defaults and immutable, per-session dashboard parameters."""
from dataclasses import dataclass, asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_SHEET = 'Data'
DIRECTION_SHEET = 'country_year_ask_capacity'
DATA_COLUMNS = ['Country Name', 'Country Code', 'Time', 'ASKs', 'RPKs']
DIRECTION_COLUMNS = ['country_code', 'country_name', 'year', 'ASK_out', 'ASK_in']
N_LARGE = 40
N_SMALL = 40
ASK_DIRECTION_START = 2000
ASK_DIRECTION_END = 2019
TOP_DIRECTION_N = 9
DIRECTION_RANK_TOP_N = 10
REPRESENTATIVE_COUNTRIES = ['CHN','USA','IND','JPN','GBR','DEU','FRA','RUS','BRA','CAN','AUS','ZMB']
MIN_DYNAMIC_VALID_YEARS = 3
DYNAMIC_QUANTILE_LOW = 0.25
DYNAMIC_QUANTILE_HIGH = 0.75
MIN_VALID_GROWTH_YEARS = 4
N_GROWTH_GAP_EXTREMES = 10
PANDEMIC_PRE_START = 2016
PANDEMIC_PRE_END = 2019
PANDEMIC_SHOCK_YEAR = 2020
PANDEMIC_RECOVERY_YEAR = 2021
PANDEMIC_PRE_MIN_OBS = 2
RANKING_START_YEAR = 2016
RANKING_END_YEAR = 2021
RANKING_MIN_COMMON_YEARS = 5
RANKING_TOP_N = 10
SCATTER_QUANTILE_LOW = 0.01
SCATTER_QUANTILE_HIGH = 0.99
SCATTER_LIMIT_MARGIN = 0.06
SCATTER_LABEL_COUNTRIES = ['CHN','USA','ZMB']
F06_FIXED_LABEL_COUNTRIES = ['CHN','USA','ZMB']
F06_AUTO_LABEL_EACH_TAIL = 2
DPI = 350
BASE_FONT_SIZE = 10.0
PANEL_TITLE_SIZE = 11.0
BOTTOM_TITLE_SIZE = 12.0
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

@dataclass(frozen=True)
class AnalysisConfig:
    n_large: int = N_LARGE
    n_small: int = N_SMALL
    direction_start: int = ASK_DIRECTION_START
    direction_end: int = ASK_DIRECTION_END
    top_direction_n: int = TOP_DIRECTION_N
    min_dynamic_years: int = MIN_DYNAMIC_VALID_YEARS
    representative_countries: tuple[str, ...] = tuple(REPRESENTATIVE_COUNTRIES)
    trend_year_start: int | None = None
    trend_year_end: int | None = None

    def validate(self):
        if not (1 <= self.n_large <= 500 and 1 <= self.n_small <= 500):
            raise ValueError('大型、小型市场国家数均须为1—500的整数。')
        if self.direction_start > self.direction_end:
            raise ValueError('ASK方向分析的起始年份不能晚于结束年份。')
        if self.top_direction_n not in (5, 9, 10, 15):
            raise ValueError('方向极端国家每侧数量须为5、9、10或15。')
        if not 1 <= len(self.representative_countries) <= 12:
            raise ValueError('代表国家请选择1—12个。')
        if not 2 <= self.min_dynamic_years <= 50:
            raise ValueError('动态分析最低有效年份须为2—50年。')
        if (self.trend_year_start is not None and self.trend_year_end is not None
                and self.trend_year_start > self.trend_year_end):
            raise ValueError('趋势图起始年份不能晚于结束年份。')

    def to_dict(self):
        return asdict(self)

DEFAULT_CONFIG = AnalysisConfig()
