# -*- coding: utf-8 -*-
import pandas as pd
import pyarrow.parquet as pq
import seaborn as sns
import matplotlib.pyplot as plt
import sys

sys.path.append("./learn-influences")

from scripts.common import VALIDATION_DATE


def create_simulation_error_column(error: pd.DataFrame, agg="mean"):
    col = error.groupby(["jobid", "result_index"]).agg([agg])
    col = col.droplevel("jobid").reset_index()
    col["result_index"] = col["result_index"].astype(int)
    col = col.set_index("result_index").sort_index()
    return col["error"][agg].rename(f"simulation_error_{agg}")


def error_by_measures_and_periods(
    results: pd.DataFrame,
    error_cols=[
        "simulation_error_mean",
        "simulation_error_std",
        "influence_error",
    ],
    sort_by="simulation_error_mean",
):
    return (
        results[["measures", "start", "end", *error_cols]]
        .groupby(["measures", "start", "end"])
        .agg(["mean", "std"])
        .sort_values(by=[(sort_by, "mean")], ascending=True)
    )


def plot_error_by_measures_and_periods(
    results: pd.DataFrame,
    baselines: pd.DataFrame,
    error_type="simulation_error_mean",
):
    fig = sns.stripplot(
        data=results,
        x="measures",
        y=error_type,
        hue="start",
        dodge=True,
        alpha=0.4,
        # legend=False,
    )

    # Rename start dates
    legend = fig.legend(
        title="Learning Periods",
        labels=[
            f"{start_date} - {VALIDATION_DATE[int(start_date)]}"
            for start_date in results["start"].unique()
        ],
        loc="upper right",
        fontsize="large",
    )

    legend.get_title().set_fontsize("large")

    # Describe x axis
    fig.set_xlabel("Learning Measures Combinations", size="large")
    fig.set_ylabel(
        " ".join([w.capitalize() for w in error_type.split("_")]), size="large"
    )
    # set tick labels font to large
    fig.tick_params(labelsize="large")
    # fig.set_xticklabels(fig.get_xticklabels(), rotation=45, ha="right")

    # Add baseline values
    # for i, start_date in enumerate(results["start"].unique()):
    #     mean = baselines.loc[int(start_date)]["mean"]

    #     fig.hlines(
    #         mean,
    #         colors=sns.color_palette()[i],
    #         xmin=-0.4,
    #         xmax=results["measures"].nunique() - 1 + 0.4,
    #         linestyles="dashed",
    #         # change line width size
    #         linewidth=2,
    #     )

    # fig.text(
    #     results["measures"].nunique() - 1 + 0.5,
    #     mean,
    #     f"{start_date}\n{VALIDATION_DATE[int(start_date)]}",
    #     verticalalignment="center",
    #     color=sns.color_palette()[i],
    #     size="medium",
    # )

    # Add horizontal segments to indicate the mean values (for each start date / measure combination)
    for j, measure in enumerate(results["measures"].unique()):
        for i, start_date in enumerate(results["start"].unique()):
            error = results[
                (results["start"] == start_date) & (results["measures"] == measure)
            ][error_type]

            mean = error.mean()
            min = error.min()
            # max = error.max()

            # Display start date below the x axis
            # fig.text(
            #     j - 0.27 + i * 0.27,
            #     max + 0.1,
            #     f"{start_date}\n{VALIDATION_DATE[int(start_date)]}",
            #     horizontalalignment="center",
            #     color=sns.color_palette()[i],
            #     size="medium",
            #     # rotation=45,
            # )

            # fig.hlines(
            #     mean,
            #     xmin=j - 0.4 + i * 0.27,
            #     xmax=j - 0.4 + (i + 1) * 0.27,
            #     colors=sns.color_palette()[i],
            #     # linestyles="dashed",
            #     linewidth=2,
            # )

            # add baseline value
            fig.hlines(
                baselines.loc[int(start_date)]["mean"],
                xmin=j - 0.4 + i * 0.27,
                xmax=j - 0.4 + (i + 1) * 0.27,
                colors="red",
                linestyles="dashed",
                linewidth=2,
            )

            # add percentage of improvement
            percentage = (
                (baselines.loc[int(start_date)]["mean"] - mean)
                / baselines.loc[int(start_date)]["mean"]
                * 100
            )
            fig.text(
                j - 0.27 + i * 0.27,
                min - 0.01,
                f"{percentage:.0f}%",
                horizontalalignment="center",
                color="blue"
                if percentage > 10
                else "black"
                if percentage > 0
                else "red",
                size="large",
                # rotation=45,
            )

    return fig


def plot_influence_error(results: pd.DataFrame, baseline: pd.DataFrame):
    fig = sns.barplot(
        data=results[["measures", "start", "influence_error"]],
        x="measures",
        y="influence_error",
        hue="start",
        errorbar=None,
    )
    fig.set_xlabel("Learning Measures Combinations", size="large")
    fig.set_ylabel("Mean Influence Error", size="large")
    fig.tick_params(labelsize="large")

    # add baselines
    baseline = baseline.set_index("start")
    for i, start_date in enumerate(results["start"].unique()):
        mean = baseline.loc[int(start_date)]["mean"]

        fig.hlines(
            mean,
            colors=sns.color_palette()[i],
            xmin=-0.4,
            xmax=results["measures"].nunique() - 1 + 0.4,
            linestyles="dashed",
            # change line width size
            linewidth=2,
        )

        fig.text(
            results["measures"].nunique() / 2 - 3 + i * 1.5,
            mean,
            f"{start_date} - {VALIDATION_DATE[int(start_date)]}",
            verticalalignment="center",
            color=sns.color_palette()[i],
            backgroundcolor="white",
            size="large",
        )
    # add baseline to legend
    # Rename start dates
    legend = fig.legend(
        title="Learning Periods",
        labels=[
            f"{start_date} - {VALIDATION_DATE[int(start_date)]}"
            for start_date in results["start"].unique()
        ]
        + ["Random"],
        loc="upper left",
        bbox_to_anchor=(1, 1),
        fontsize="large",
    )
    # change color of baseline in legend
    legend.legend_handles[-1].set_color("black")
    legend.get_title().set_fontsize("large")

    return fig


def error_by_periods(
    results: pd.DataFrame,
    error_cols=[
        "simulation_error_mean",
        "simulation_error_std",
        "influence_error",
    ],
    sort_by="simulation_error_mean",
):
    return (
        results[["start", "end", *error_cols]]
        .groupby(["start", "end"])
        .agg(["mean", "std"])
        .sort_values(by=[(sort_by, "mean")], ascending=True)
    )


def error_by_measures(
    results: pd.DataFrame,
    error_cols=[
        "simulation_error_mean",
        "simulation_error_std",
        "influence_error",
    ],
    sort_by="simulation_error_mean",
):
    return (
        results[["measures", *error_cols]]
        .groupby(["measures"])
        .agg(["mean", "std"])
        .sort_values(by=[(sort_by, "mean")], ascending=True)
    )


if __name__ == "__main__":
    results = pq.read_table("results/results.parquet").to_pandas()
    simulation_error = pq.read_table("results/results_w_error_ok.parquet").to_pandas()
    simulation_error_baselines = pq.read_table(
        "results/simulation_error_baselines.parquet"
    ).to_pandas()
    influence_error = pq.read_table("results/error_rate_good.parquet").to_pandas()
    influence_error_baselines = pq.read_table(
        "results/influence_error_baselines.parquet"
    ).to_pandas()

    # Add error columns
    results = pd.concat(
        (
            results,
            create_simulation_error_column(simulation_error, "mean"),
            create_simulation_error_column(simulation_error, "std"),
            influence_error["error"].rename("influence_error"),
        ),
        axis="columns",
    )

    # export results to csv
    results.to_csv("results/results_w_error.csv", index=False)
    influence_error_baselines.to_csv(
        "results/influence_error_baselines.csv", index=False
    )

    print("Error by measures and periods")
    print(error_by_measures_and_periods(results))
    print()

    print("Error by periods")
    print(error_by_measures(results))
    print()

    print("Error by measures")
    print(error_by_periods(results))
    print()

    print("Simulation error baselines")
    print(simulation_error_baselines)
    print()

    # plot_error_by_measures_and_periods(
    #     results, simulation_error_baselines, "simulation_error_mean"
    # )
    plot_influence_error(results, influence_error_baselines)
    plt.tight_layout()
    plt.show()
