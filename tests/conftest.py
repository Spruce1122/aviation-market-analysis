from io import BytesIO
from itertools import product
import string

import numpy as np
import pandas as pd
import pytest


def make_workbook(scale=1.0, include_direction=True):
    rng = np.random.default_rng(20260901)
    codes = [''.join(chars) for chars in product(string.ascii_uppercase, repeat=3)][:90]
    years = range(2015, 2023)
    rows = []
    direction = []
    for rank, code in enumerate(codes, start=1):
        ask = (2_000_000 + rank * 80_000) * scale
        plf = 0.48 + (rank % 35) / 100
        for year in years:
            shock = 0.52 if year == 2020 else 1.28 if year == 2021 else 1.0
            ask_growth = 1.03 + 0.018 * np.sin(rank + year) + rng.normal(0, 0.008)
            rpk_growth = 1.035 + 0.028 * np.cos(rank / 3 + year) + rng.normal(0, 0.012)
            ask *= ask_growth * shock
            plf = float(np.clip(plf * rpk_growth / ask_growth, 0.18, 0.94))
            rpk = ask * plf
            rows.append({
                'Country Name': f'Country {code}', 'Country Code': code,
                'Time': year, 'ASKs': ask, 'RPKs': rpk,
            })
            if include_direction:
                direction.append({
                    'country_code': code, 'country_name': f'Country {code}', 'year': year,
                    'ASK_out': ask * (0.48 + rank / 1000),
                    'ASK_in': ask * (0.52 - rank / 2000),
                })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name='Data', index=False)
        if include_direction:
            pd.DataFrame(direction).to_excel(writer, sheet_name='country_year_ask_capacity', index=False)
    return output.getvalue(), tuple(codes[:12])


@pytest.fixture(scope='session')
def workbook():
    return make_workbook()
