import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def reshape_merit_order_data(blocks):
    """Reshape merit order data to facilitate plotting

    Parameters
    ----------
    blocks : pd.DataFrame
        Combined data set with all generators

    Returns
    -------
    merit_order : pd.DataFrame
        DataFrame with energy carrier, price and cumulated capacity
    """
    # Reshape data set
    matrix = blocks[["fuel", "costs_marginal", "capacity_cumulated"]].values
    merit_order = np.zeros((0, 3))

    for el in range(len(matrix) - 1):
        merit_order = np.append(
            merit_order,
            np.reshape(
                matrix[
                    el,
                ],
                (1, 3),
            ),
            axis=0,
        )
        if matrix[el, 0] != matrix[el + 1, 0]:
            obj = np.reshape(
                matrix[
                    el,
                ],
                (1, 3),
            )
            obj[0][0] = matrix[el + 1, 0]
            merit_order = np.append(merit_order, obj, axis=0)

    # Create a DataFrame out of array
    merit_order = pd.DataFrame(
        data=merit_order, columns=["fuel", "costs_marginal", "capacity_cumulated"]
    )
    return merit_order.astype(
        {"capacity_cumulated": "float32", "costs_marginal": "float32"}
    )


def plot_merit_order(merit_order, colors, ylim=(-100, 200), set_ylim=True):
    """Plot a merit order based on given data

    Parameters
    ----------
    merit_order : pd.DataFrame
        Merit order to plot

    colors : dict
        Mapping of energy carriers and colors

    ylim : tuple
        y limits to use if set_ylim is True

    set_ylim : boolean
        If False, use minima and maxima of data set plus margins
        to derive ylim
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    for fuel in merit_order["fuel"].unique():
        _ = ax.fill_between(
            x="capacity_cumulated",
            y1="costs_marginal",
            where=merit_order["fuel"] == fuel,
            facecolor=colors[fuel],
            step="pre",
            lw=15,
            data=merit_order,
            label=fuel,
        )
    if set_ylim:
        _ = ax.set(
            xlim=(-1000, merit_order["capacity_cumulated"].max() + 1000),
            ylim=ylim,
        )
    else:
        _ = ax.set(
            xlim=(-1000, merit_order["capacity_cumulated"].max() + 1000),
            ylim=(
                merit_order["costs_marginal"].min() - 10,
                merit_order["costs_marginal"].max() + 10,
            ),
        )
    _ = ax.grid(axis="y")
    _ = plt.yticks(np.arange(-100, 121, 10.0))
    _ = plt.xlabel("Kumulierte Leistung [MW]")
    _ = plt.ylabel("Grenzkosten [€/MWh]")
    _ = ax.legend(loc="lower right", ncol=4)

    plt.tight_layout()

    plt.show()
