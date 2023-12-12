import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pommesevaluation.pommesinvest_routines import resample_timeseries


def extract_costs_data_for_investment_model(
    file_name: str, frequency: str, time: str, col_name: str
):
    """Extract and filter costs information for investment model"""
    data = pd.read_csv(file_name, index_col=0)
    data = data[[col for col in data if "DE_" in col]]
    data.columns = [col.split("_")[-1] for col in data.columns]
    data.loc["2051-01-01"] = data.loc["2050-01-01"]
    data = resample_timeseries(
        data, freq=frequency, interpolation_rule="linear"
    )[:-1]
    data = data.loc[[time]].T
    data.columns = [col_name]
    return data


def prepare_market_values_from_results(costs_market_values, simulation_year):
    """Prepare market values obtained from results file (reindexing)

    Parameters
    ----------
    costs_market_values : pd.DataFrame
        Market values obtained from results, one value per month, int indexed

    simulation_year : int
        Year simulated

    Returns
    -------
    costs_market_values : pd.DataFrame
        Reshaped version of data
    """
    costs_market_values.index = [
        f"{simulation_year}-0{el}-01 00:00:00"
        if len(str(el)) == 1
        else f"{simulation_year}-{el}-01 00:00:00"
        for el in costs_market_values.index
    ]
    costs_market_values.loc[
        f"{simulation_year + 1}-01-01 00:00:00"
    ] = costs_market_values.iloc[-1]
    costs_market_values.index = pd.to_datetime(costs_market_values.index)
    costs_market_values = costs_market_values.resample("H").ffill()

    return costs_market_values


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
        data=merit_order,
        columns=["fuel", "costs_marginal", "capacity_cumulated"],
    )
    return merit_order.astype(
        {"capacity_cumulated": "float32", "costs_marginal": "float32"}
    )


def plot_merit_order(
    merit_order,
    colors,
    ylim=(-100, 200),
    set_ylim=True,
    interval=20,
    height=5,
    save=True,
    path_plots="./plots/",
    file_name="merit_order",
    place_legend_below=False,
):
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

    interval : int
        interval to use for horizontal grid lines

    height : int
        height of plot

    save : boolean
        If True, save to disk

    path_plots : str
        Path to store the plot

    file_name : str
        file name for the plot

    place_legend_below: boolean
        If True, place legend below outside the actual plot
    """
    fig, ax = plt.subplots(figsize=(12, height))
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
    _ = plt.yticks(np.arange(ylim[0], ylim[1] + 1, interval))
    current_values = plt.gca().get_xticks()
    plt.gca().set_xticklabels(["{:,.0f}".format(x) for x in current_values])
    _ = plt.xlabel("Cumulated power [MW]")
    _ = plt.ylabel("marginal costs resp. opportunity costs [€/MWh]")
    if not place_legend_below:
        _ = ax.legend(loc="lower right", ncol=4)
    else:
        _ = ax.legend(
            loc="lower left",
            bbox_to_anchor=[0, -0.15, 1, 1],
            ncol=4,
            fancybox=True,
            borderaxespad=0.0,
            mode="expand",
        )

    plt.tight_layout()

    if save:
        _ = plt.savefig(f"{path_plots}{file_name}.png", dpi=300)

    plt.show()
