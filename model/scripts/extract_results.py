import dill
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from common import (
    params_names,
    extract_jobid,
    make_measures_codes,
    get_dates,
    make_periods,
    get_exp_codes,
    rebuild_params,
    save_dataframe,
)


def read_results_file(path, m_code):
    with open(path, "rb") as file:
        results = dill.load(file)

        X = pd.DataFrame(
            data=(
                results["X"]
                if isinstance(results["X"][0], np.ndarray)
                else np.array([results["X"]])
            ),
            columns=params_names(),
        )

        columns = [m for m in m_code]

        F = pd.DataFrame(
            data=results["F"],
            columns=columns,
        )

        history = pd.DataFrame(
            data=[e.opt[0].F for e in results["history"]],
            columns=columns,
            index=[e.evaluator.n_eval for e in results["history"]],
        )

        del results

    return {"X": X, "F": F, "history": history}


def extract_data(basepath, exp_codes, extract_dir=Path("extract")):
    if not extract_dir.exists():
        extract_dir.mkdir()

    for e in tqdm(exp_codes):
        current_path = Path(f"{basepath}/{e}/")
        if current_path.exists():
            # Extract raw data
            res = {
                extract_jobid(path.name): read_results_file(path, e[:-4])
                for path in current_path.iterdir()
                if path.is_file()
            }
            # Prepare extract directory
            extract_exp = Path(f"{extract_dir}/{e}/")
            if not extract_exp.exists():
                extract_exp.mkdir()
            # Save as parquet files
            for jobid, r in tqdm(res.items(), e):
                extract_job = extract_exp.joinpath(f"{jobid}/")
                if not extract_job.exists():
                    extract_job.mkdir()

                save_dataframe(
                    rebuild_params(r["X"]), extract_job.joinpath("X.parquet")
                )
                save_dataframe(r["F"], extract_job.joinpath("F.parquet"))
                save_dataframe(r["history"], extract_job.joinpath("history.parquet"))


if __name__ == "__main__":
    dates = get_dates()
    periods = make_periods(dates)
    measures_combs = make_measures_codes("KCD")
    exp_codes = get_exp_codes(measures_combs, periods)
    extract_data("./results/dumps", exp_codes, Path("results/extracts"))
