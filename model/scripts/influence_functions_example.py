#!/usr/bin/env python3
import numpy as np
from matplotlib import pyplot as plt

from multiants.influences.functions.utils import tanh_y
from multiants.influences.functions import (
    make_attraction_repulsion,
    make_open_distance,
    make_close_distance,
    make_balance,
)


def plot_attraction_repulsion(l_min, l_zero, l_max, ax):
    fn = make_attraction_repulsion(l_min, l_zero, l_max)

    x1 = np.linspace(0, l_min, 100)
    y1 = [fn(i) for i in x1]
    ax.plot(x1, y1, color="black")
    x2 = np.linspace(l_min, l_zero, 100)
    y2 = [fn(i) for i in x2]
    ax.plot(x2, y2, color="blue")
    x3 = np.linspace(l_zero, l_max, 100)
    y3 = [fn(i) for i in x3]
    ax.plot(x3, y3, color="green")
    x4 = np.linspace(l_zero, 100, 100)
    y4 = [fn(i) for i in x4]
    ax.plot(x4, y4, color="red")

    plot_l_min(l_min, fn(l_min), ax, (14, 0))
    plot_l_zero(l_zero, fn(l_zero), ax, (0, -0.2))
    plot_l_max(l_max, fn(l_max), ax, (0, -0.2))

    ax.set_title("Attraction Repulsion")


def plot_open_distance(l_min, l_max, ax):
    fn = make_open_distance(l_min, l_max)

    x1 = np.linspace(0, l_min, 100)
    y1 = [fn(i) for i in x1]
    ax.plot(x1, y1, color="black")
    x2 = np.linspace(l_min, l_max, 100)
    y2 = [fn(i) for i in x2]
    ax.plot(x2, y2, color="green")
    x3 = np.linspace(l_min, 100, 100)
    y3 = [fn(i) for i in x3]
    ax.plot(x3, y3, color="red")

    plot_l_min(l_min, fn(l_min), ax, (0, -0.2))
    plot_l_max(l_max, fn(l_max), ax, (0, +0.2))

    ax.set_title("Open Distance")


def plot_close_distance(l_min, l_max, ax):
    fn = make_close_distance(l_min, l_max)

    x1 = np.linspace(0, l_min, 100)
    y1 = [fn(i) for i in x1]
    ax.plot(x1, y1, color="black")
    x2 = np.linspace(l_min, l_max, 100)
    y2 = [fn(i) for i in x2]
    ax.plot(x2, y2, color="green")
    x3 = np.linspace(l_min, 100, 100)
    y3 = [fn(i) for i in x3]
    ax.plot(x3, y3, color="red")

    plot_l_min(l_min, fn(l_min), ax, (-14, 0))
    plot_l_max(l_max, fn(l_max), ax, (0, 0.2))

    ax.set_title("Close Distance")


def plot_l_min(x, y, ax, label_offset=(0, 0)):
    ax.plot(x, y, color="blue", marker="o")
    ax.text(
        x + label_offset[0],
        y + label_offset[1],
        r"$\lambda_\text{min}$",
        horizontalalignment="center",
        verticalalignment="center",
        size="large",
    )


def plot_l_zero(x, y, ax, label_offset=(0, 0)):
    ax.plot(x, y, color="green", marker="o")
    ax.text(
        x + label_offset[0],
        y + label_offset[1],
        r"$\lambda_0$",
        horizontalalignment="center",
        verticalalignment="center",
        size="large",
    )


def plot_l_max(x, y, ax, label_offset=(0, 0)):
    ax.plot(x, y, color="red", marker="o")
    ax.text(
        x + label_offset[0],
        y + label_offset[1],
        r"$\lambda_\text{max}$",
        horizontalalignment="center",
        verticalalignment="center",
        size="large",
    )


def plot_balance(l_min, l_zero, l_max, ax):
    fn = make_balance(l_min, l_zero, l_max)
    x1 = np.linspace(0, l_min, 100)
    y1 = [fn(i) for i in x1]
    ax.plot(x1, y1, color="black")
    x2 = np.linspace(l_min, l_zero, 100)
    y2 = [fn(i) for i in x2]
    ax.plot(x2, y2, color="blue")
    x3 = np.linspace(l_zero, l_max, 100)
    y3 = [fn(i) for i in x3]
    ax.plot(x3, y3, color="green")
    x4 = np.linspace(l_zero, 100, 100)
    y4 = [fn(i) for i in x4]
    ax.plot(x4, y4, color="red")

    # plot l_min, l_zero, l_max
    plot_l_min(l_min, fn(l_min), ax, (-5, 0.2))
    plot_l_zero(l_zero, fn(l_zero), ax, (0, -0.2))
    plot_l_max(l_max, fn(l_max), ax, (5, 0.2))

    ax.set_title("Balance")


if __name__ == "__main__":
    fig, ax = plt.subplots(1, 4, figsize=(10, 3), dpi=300)
    # share y axis and turn off ticks for all but one plot
    ax[1].sharey(ax[0])
    ax[2].sharey(ax[0])
    ax[3].sharey(ax[0])
    ax[1].get_yaxis().set_visible(False)
    ax[2].get_yaxis().set_visible(False)
    ax[3].get_yaxis().set_visible(False)
    ax[0].get_xaxis().set_visible(False)
    ax[1].get_xaxis().set_visible(False)
    ax[2].get_xaxis().set_visible(False)
    ax[3].get_xaxis().set_visible(False)
    plot_attraction_repulsion(20, 50, 80, ax[0])
    plot_open_distance(20, 80, ax[1])
    plot_close_distance(20, 80, ax[2])
    plot_balance(20, 50, 80, ax[3])
    plt.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.show()
