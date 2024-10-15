import sys
import pandas as pd
from pathlib import Path

sys.path.append("./learn-influences")

from scripts.read_results import read_results
from scripts.common import (
    get_dates,
    get_exp_codes,
    make_measures_codes,
    make_periods,
    save_dataframe,
)


def make_results_dataframe():
    DATE2_to_DATE4 = {
        "94": "1994",
        "02": "2002",
        "09": "2009",
        "19": "2019",
    }
    exp_codes = get_exp_codes(
        make_measures_codes("KCD"),
        make_periods(get_dates()),
    )
    results = read_results(Path("results/extracts"), exp_codes, "X")
    combined_results = pd.DataFrame()
    for m_code, exps in results.items():
        exps_m, exps_begin, exps_end = (
            m_code[:-4],
            m_code[-4:-2],
            m_code[-2:],
        )
        for exp_id, exp in exps.items():
            meta = pd.DataFrame(
                {
                    "measures": [exps_m],
                    "start": [DATE2_to_DATE4[exps_begin]],
                    "end": [DATE2_to_DATE4[exps_end]],
                    "jobid": [exp_id],
                }
            )
            exp_data = pd.concat((exp["X"], meta), axis="columns").ffill()
            combined_results = pd.concat(
                (combined_results, exp_data), ignore_index=True
            )
    return combined_results


if __name__ == "__main__":
    save_dataframe(
        make_results_dataframe(),
        Path("results/results.parquet"),
    )
