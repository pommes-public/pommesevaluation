﻿"""
Module for power price validation
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from math import sqrt


def read_and_reshape_historical_prices(year, file_name):
    """Read and reshape historical prices for given year

    Parameters
    ----------
    year : int
        Year to consider

    file_name : str or list
        Name of the file(s) with the prices

    Returns
    -------
    power_prices : pd.DataFrame
        Power prices for given year
    """
    # Concat elements of recursive function call (2018 only)
    if isinstance(file_name, list):
        to_concat = [
            read_and_reshape_historical_prices(year, file)
            for file in file_name
        ]

        power_prices = pd.concat(to_concat)
        set_new_index(power_prices)

    else:
        # Read and slice
        power_prices = pd.read_csv(
            file_name,
            header=1,
            index_col=0,
            parse_dates=True,
            infer_datetime_format=True,
        )
        power_prices = power_prices.iloc[:, :25].loc[
            power_prices.index.year == year
        ]

        # Change columns
        hours = [1, 2, 3, 3.1, *list(range(4, 25))]
        power_prices.columns = hours
        power_prices = power_prices.sort_index().reset_index(drop=False)

        # Reshape
        power_prices = (
            pd.melt(
                power_prices,
                id_vars="Delivery day",
                value_vars=[
                    col
                    for col in power_prices.columns
                    if col != "Delivery day"
                ],
            )
            .sort_values(by=["Delivery day", "variable"])
            .dropna(how="any")
        )

        # Create date stamp
        power_prices["variable"] = power_prices["variable"].astype(int)
        power_prices["Delivery day"] = power_prices["Delivery day"].astype(str)
        power_prices["date"] = power_prices.apply(create_datestamps, axis=1)
        power_prices.set_index("date", inplace=True)

        set_new_index(power_prices)
        power_prices = power_prices[["value"]].rename(
            columns={"value": "historical_price"}
        )

    return power_prices


def set_new_index(power_prices):
    """Set a new UTC date index for power price time series"""
    power_prices["date_index"] = pd.date_range(
        start=power_prices.index[0], freq="H", periods=len(power_prices)
    )
    power_prices.set_index("date_index", inplace=True)


def create_datestamps(x):
    """Create datestamp from delivery day and hour information"""
    return pd.to_datetime(
        x["Delivery day"] + " " + f"{x['variable'] - 1}:00:00"
    )


def read_and_reshape_smard_prices(year: int, file_name: str):
    """Read in prices from SMARD in Excel format and reshape them"""
    power_prices = pd.read_excel(
        file_name, sheet_name="Großhandelspreise", skiprows=9, index_col=0
    )
    power_prices["new_idx"] = power_prices.index + " " + power_prices["Anfang"]
    set_new_index(power_prices)
    power_prices = power_prices.loc[
        power_prices.index.year == year, ["Deutschland/Luxemburg [€/MWh]"]
    ]
    power_prices.rename(
        columns={"Deutschland/Luxemburg [€/MWh]": "historical_price"},
        inplace=True,
    )

    return power_prices


def compare_or_show_price_distribution(
    model_prices,
    historical_prices=None,
    figsize=(15, 5),
    bins=30,
    save=True,
    path_plots="./plots/",
    xlabel="power prices",
    content="negative price distribution",
    file_name="negative_price_distribution",
):
    """Draw a histogram comparing (negative) prices of model to historical"""
    fig, ax = plt.subplots(figsize=figsize)
    model_prices.plot(kind="hist", bins=bins, color="r", alpha=0.3, ax=ax)
    if historical_prices is not None:
        historical_prices.plot(kind="hist", bins=bins, alpha=0.3, ax=ax)
        title = f"Comparison of {content}"
    else:
        title = content
    plt.title(title)
    plt.xlabel(xlabel)
    plt.legend()

    _ = plt.tight_layout()

    if save:
        plt.savefig(f"{path_plots}{file_name}.png", dpi=300)

    plt.show()
    plt.close()


def draw_price_plot(
    power_prices,
    color,
    title,
    y_min_max=False,
    ylim=None,
    show=False,
    save=True,
    path_plots="./plots/",
    file_name="power_prices",
    figsize=(20, 10),
    language="English",
):
    """Plot power price results of model against historical prices

    Parameters
    ----------
    power_prices : pd.DataFrame
        DataFrame containing power prices to be plotted

    color : list
        Colors to be used

    title : str
        Title of the plot

    y_min_max : boolean
        If True, use -100 and +200 as price limits if not specified otherwise

    ylim : list
        y axis limits (lower, upper)

    show : boolean
        If True, show the plot

    save : boolean
        If True, save the plot to disk

    path_plots : str
        Path to store plot at

    file_name : str
        File name for saving the plot

    figsize : tuple
        Control the size of the figure created

    language: str
        Language to use, one of "German" and "English"
    """
    axes_labels = {
        "German": {"x": "Zeit", "y": "Strompreis in €/MWh"},
        "English": {"x": "time", "y": "power price in €/MWh"}
    }

    fig, ax = plt.subplots(figsize=figsize)
    ax = power_prices.plot(color=color, ax=ax)
    _ = plt.ylabel(axes_labels[language]["y"])
    _ = plt.title(title)
    _ = ax.legend(loc="upper right")
    _ = plt.xlabel(axes_labels[language]["x"])
    _ = plt.xticks(rotation=45)

    if y_min_max:
        if ylim is not None:
            _ = plt.axis(ymin=ylim[0], ymax=ylim[1])
        else:
            _ = plt.axis(ymin=-100, ymax=200)

    _ = plt.tight_layout()

    if save:
        plt.savefig(f"{path_plots}{file_name}.png", dpi=300)
    if show:
        plt.show()

    plt.close()


def draw_weekly_plot(
    power_prices,
    simulation_year,
    color=["b", "r"],
    comparison=True,
    ylim=[-100, 200],
):
    """Draw weekly price plots

    Parameters
    ----------
    power_prices : pd.DataFrame
        Power price time series; either only model outcomes or model outcomes + historical

    simulation_year : int
        Year simulated

    color : list or str
        Color(s) to be used

    comparison : bool
        If True, plot against historical prices, else show model outcome only
    """
    for week in range(52):
        if comparison:
            title = (
                f"Power price time series comparison for {simulation_year};"
                + f"week: {week + 1}"
            )
        else:
            title = f"Power price pattern for {simulation_year} in week: {week + 1}"

        draw_price_plot(
            power_prices=power_prices.iloc[week * 168 : (week + 1) * 168 + 1],
            color=color,
            title=title,
            y_min_max=True,
            ylim=ylim,
            show=False,
            save=True,
            file_name=f"power_prices_{simulation_year}_week_{week + 1}",
        )


def draw_price_duration_plot(
    model_prices,
    historical_prices,
    show=True,
    save=False,
    y_min_max=True,
    ylim=None,
    file_name="power_price_duration_curve",
    figsize=(20, 10),
):
    """Plot price duration curves in comparison"""
    model_prices_sorted = model_prices.sort_values(
        by="model_price", ascending=False
    ).reset_index(drop=True)

    historical_prices_sorted = historical_prices.sort_values(
        by="historical_price", ascending=False
    ).reset_index(drop=True)

    sorted_prices = pd.concat(
        [historical_prices_sorted, model_prices_sorted], axis=1
    )
    draw_price_plot(
        power_prices=sorted_prices,
        color=["b", "r"],
        title="Power price duration curve comparison",
        y_min_max=y_min_max,
        ylim=ylim,
        show=show,
        save=save,
        file_name=file_name,
        figsize=figsize,
    )


def calculate_error_metrics(historical_prices, model_prices):
    """Calculate and return MAE, RMSE, NRMSE in a dict structure"""
    RMSE = sqrt(mean_squared_error(historical_prices, model_prices))

    return {
        "MAE": mean_absolute_error(historical_prices, model_prices),
        "RMSE": RMSE,
        "NRMSE": RMSE
        / (
            np.max(historical_prices.historical_price)
            - np.min(historical_prices.historical_price)
        ),
    }
