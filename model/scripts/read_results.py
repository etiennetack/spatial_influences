import os
import warnings
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import seaborn as sns
import matplotlib.pyplot as plt

from common import (
    make_measures_codes,
    get_dates,
    make_periods,
    get_exp_codes,
    save_dataframe,
)


def read_results(basepath, exp_codes, select="XFH"):
    results = {}
    for e in exp_codes:
        current_path = Path(f"{basepath}/{e}/")
        if current_path.exists():
            results[e] = {}
            for job in current_path.iterdir():
                job_data = {}
                if "X" in select:
                    X = pq.read_table(job.joinpath("X.parquet")).to_pandas()
                    job_data["X"] = X
                if "F" in select:
                    F = pq.read_table(job.joinpath("F.parquet")).to_pandas()
                    job_data["F"] = F
                if "H" in select:
                    history = pq.read_table(job.joinpath("history.parquet"))
                    history = history.to_pandas()
                    job_data["history"] = history
                results[e][job.name] = job_data
    return results


def compare_combinaisons(results, measures_codes):
    # combinations_colours = dict(zip(measures_codes, DISTINCT_COLOURS))

    for m in "KCD":
        plt.figure()
        data = pd.DataFrame()
        for m_code, exps in results.items():
            exp_measures = m_code[:-4]
            if m in exp_measures:
                for exp in exps.values():
                    d = exp["history"][m]
                    data = pd.concat(
                        (data, pd.DataFrame({m_code: d})),
                        axis="columns",
                    )
        data = data.ffill()
        sns.lineplot(data=data, errorbar="ci").set(yscale="log", title=m)
        plt.show()
        # plt.savefig(f"convergence/compare_combinations_{m}.png")


def ensure_directory(dir_path, sub_path=None):
    if sub_path:
        dir_path = dir_path.joinpath(sub_path)
    if not dir_path.exists():
        dir_path.mkdir()
    return dir_path


# def params_groups():
#     return [
#         ["neighbours_l_min", "neighbours_l_0", "neighbours_l_max"],
#         ["roads_l_min", "roads_l_0", "roads_l_max"],
#         ["paths_l_min", "paths_l_max"],
#         ["slope_l_min", "slope_l_max"],
#         ["neighbours_w", "roads_w", "paths_w", "slope_w"],
#     ]


def compare_results(results, save_path):
    local_save_path = ensure_directory(save_path, "compare_results/")
    META = ["period", "exp", "measures"]

    data = pd.DataFrame()

    for m_code, exps in results.items():
        exp_measures, period = m_code[:-4], m_code[-4:]

        for jobid, exp in exps.items():
            d = pd.concat(
                (exp["X"], exp["F"]),
                axis="columns",
            )

            d = rank(d, exp_measures)
            d = d[d["rank"] == d["rank"].min()]
            d = pd.DataFrame(d[exp["X"].columns])
            d["period"] = period
            d["exp"] = jobid
            d["measures"] = exp_measures

            data = pd.concat((data, d), ignore_index=True)

    for p in list(set(data.columns) - set(META)):
        plt.figure(figsize=(15, 5), dpi=300)
        plot = sns.violinplot(
            data, x="measures", y=p, hue="period", cut=0, fill=False
        )
        plot.set(title=p)
        plt.savefig(local_save_path.joinpath(f"{p}.png"))


def compare_results_2(results, save_path):
    local_save_path = ensure_directory(save_path, "compare_results/")
    META = ["period", "exp", "measures", "best"]

    data = pd.DataFrame()

    for m_code, exps in results.items():
        exp_measures, period = m_code[:-4], m_code[-4:]

        for jobid, exp in exps.items():
            d = pd.concat(
                (exp["X"], exp["F"]),
                axis="columns",
            )

            d = rank(d, exp_measures)
            d["best"] = d["rank"] == d["rank"].min()
            print(
                sum(d["rank"] == d["rank"].min()),
                sum(d["rank"] > d["rank"].min()),
                sum(d["best"] == True),
                sum(d["best"] == False),
            )
            d = pd.DataFrame(d[list(exp["X"].columns) + ["best"]])
            d["period"] = period
            d["exp"] = jobid
            d["measures"] = exp_measures

            data = pd.concat((data, d), ignore_index=True)

    for p in list(set(data.columns) - set(META)):
        plt.figure(figsize=(15, 5), dpi=300)
        plot = sns.violinplot(
            data, x="measures", y=p, hue="best", split=True, cut=0, fill=False
        )
        plot.set(title=p)
        plt.savefig(local_save_path.joinpath(f"{p}.png"))


def rank(df, measures):
    ranks = pd.DataFrame()
    rank_cols = []
    for m in measures:
        rank_name = f"rank_{m}"
        ranks[rank_name] = df[m].rank(ascending=True)
        rank_cols.append(rank_name)
    df["rank"] = sum((ranks[r] for r in ranks.columns))
    df["rank"] = df["rank"].rank(ascending=True)
    return df.sort_values(by=["rank"])


def find_best_2(results):
    bests = pd.DataFrame()
    for m_code, exps in results.items():
        data = pd.DataFrame()
        exp_measures, period = m_code[:-4], m_code[-4:]

        for jobid, exp in exps.items():
            d = pd.concat(
                (exp["X"], exp["F"]),
                axis="columns",
            )
            d["exp"] = jobid
            data = pd.concat((data, d), ignore_index=True)

        data = rank(data, exp_measures)
        data["period"] = period
        data["measures"] = exp_measures

        bests = pd.concat(
            (bests, data[data["rank"] == data["rank"].min()]),
            ignore_index=True,
        )

        # os.system('clear')
        # print(data)
        # print()
        # print("BEST\n")
        # print(data[data["rank"] == data["rank"].min()])
        # input("next?")
    bests.pop("rank")
    bests["K"], bests["C"], bests["D"] = (
        bests.pop("K"),
        bests.pop("C"),
        bests.pop("D"),
    )
    save_dataframe(bests, Path("results/bests.parquet"))
    print(bests)


def find_best(results):
    for m_code, exps in results.items():
        data = pd.DataFrame()

        exp_measures, period = m_code[:-4], m_code[-4:]

        for jobid, exp in exps.items():
            d = pd.concat(
                (exp["X"], exp["F"]),
                axis="columns",
            )

            d["exp"] = jobid

            data = pd.concat((data, d), ignore_index=True)

        print(f"{period}, {exp_measures}")

        data["rank"] = (
            data[[m for m in exp_measures]]
            .apply(tuple, axis="columns")
            .rank(method="dense", ascending=True)
            .astype(int)
        )
        data = data.sort_values(by=["rank"])
        r_cols = []
        for m in exp_measures:
            rank_name = f"rank_{m}"
            data[rank_name] = data[m].rank(ascending=True)
            r_cols.append(rank_name)
        # print(data[[m for m in exp_measures] + ["rank", "exp"]])

        data["g_rank"] = sum((data[r] for r in r_cols))
        data["g_rank"] = data["g_rank"].rank(ascending=True)
        d_cols = ["exp", "period", "rank", "g_rank"]

        data["period"] = period
        data["measures"] = exp_measures

        best = pd.DataFrame(data[data["g_rank"] == 1])
        worst = pd.DataFrame(data[data["g_rank"] == data["g_rank"].max()])

        print("BEST")
        print(best[[m for m in exp_measures] + d_cols + r_cols])
        print("WORST")
        print(worst[[m for m in exp_measures] + d_cols + r_cols])
        print("=====")
        input("next?")
        os.system("clear")


# def analyse_results(results, save_path):
#     local_save_path = ensure_directory(save_path, "analyse_results/")
#     pass


if __name__ == "__main__":
    sns.set_theme()
    dates = get_dates()
    periods = make_periods(dates)
    measures_combs = make_measures_codes("KCD")
    exp_codes = get_exp_codes(measures_combs, periods)
    results = read_results(Path("results/extracts"), exp_codes, "XFH")
    save_path = ensure_directory(Path("results/plots"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # compare_combinaisons(results, exp_codes)
        find_best_2(results)
        compare_results(results, save_path)
