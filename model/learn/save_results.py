import dill
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def as_dump(res, filename: Path):
    with open(filename, "wb") as file:
        save = {
            "exec_time": res.exec_time,
            "X": res.X,
            "F": res.F,
            "history": res.history,
        }
        dill.dump(save, file)


def as_parquets(res, seed, psize, output_base: Path, model_cls, measures):
    output_base.mkdir(parents=True, exist_ok=True)
    output = output_base / str(seed)
    output.mkdir(exist_ok=True)

    if res.X is None:
        X_data = np.array([])
    elif not isinstance(res.X[0], np.ndarray):
        X_data = np.array([res.X])
    else:
        X_data = res.X

    X = pd.DataFrame(
        # build params from learning variables
        data=(
            np.apply_along_axis(model_cls.build_params, 1, X_data)
            if len(X_data) != 0
            else None
        ),
        columns=model_cls.params_names(),
    )
    save_dataframe(X, output / "X.parquet")

    F = pd.DataFrame(
        data=res.F,
        columns=measures,
    )
    save_dataframe(F, output / "F.parquet")

    history = pd.DataFrame(
        data=[e.opt[0].F for e in res.history],
        columns=measures,
        index=[e.evaluator.n_eval for e in res.history],
    )
    save_dataframe(history, output / "history.parquet")

    n_eval = history.index.max()
    n_gen = n_eval // psize
    meta = pd.DataFrame(
        [
            {
                "seed": seed,
                "exec_time": res.exec_time,
                "n_gen": n_gen,
                "n_eval": n_eval,
            }
        ]
    )
    save_dataframe(meta, output / "meta.parquet")


def save_dataframe(data: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(data)
    pq.write_table(table, path)
