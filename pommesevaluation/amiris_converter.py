import os
from typing import Dict

import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from pommesevaluation.pommesinvest_routines import cut_leap_days


def convert_annual_data_to_fame_time(
    df: pd.DataFrame,
    orient: str = "rows",
    save: bool = False,
    path: str = "./data_out/amiris/",
    filename: str = "time_series",
    rounding_precision: int = 3,
) -> pd.DataFrame:
    """Converts a given annual DataFrame to FAME time format

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame to be converted

    orient: str
        Defines whether orientation of time series data in
        DataFrame is column- or row-wise ("columns" or "rows")

    save: boolean
        If True, save converted data to disk

    path: str
        Path to store the data

    filename: str
        File name of the data

    rounding_precision: int
        Decimal digits to use for rounding

    Returns
    -------
    reindexed_df: pd.DataFrame
        Reindexed DataFrame with FAME time stamps
    """
    if orient == "columns":
        reindexed_df = df.T.copy()
    elif orient == "rows":
        reindexed_df = df.copy()
    else:
        raise ValueError("orient must be either 'columns' or 'rows'!")
    reindexed_df.index = reindexed_df.index.astype(str)

    reindexed_df["fame_time_index"] = [
        f"{idx}-01-01_00:00:00" for idx in reindexed_df.index
    ]
    reindexed_df.set_index("fame_time_index", drop=True, inplace=True)
    reindexed_df = reindexed_df.round(rounding_precision)

    if save:
        save_given_data_set_for_fame(reindexed_df, path, filename)

    return reindexed_df


def save_given_data_set_for_fame(
    data_set: pd.DataFrame or pd.Series, path: str, filename: str
):
    """Save a given data set using FAME time and formatting

    Parameters
    ----------
    data_set: pd.DataFrame or pd.Series
        Data set to be saved (column-wise)

    path: str
        Path to store the data

    filename: str
        File name for storing
    """
    make_directory_if_missing(path)
    if isinstance(data_set, pd.DataFrame):
        if not isinstance(data_set.columns, pd.MultiIndex):
            for col in data_set.columns:
                data_set[col].to_csv(
                    f"{path}{filename}_{col}.csv", header=False, sep=";"
                )
        else:
            for col in data_set.columns:
                data_set[col].to_csv(
                    f"{path}{filename}_{col[0]}_{col[1]}.csv",
                    header=False,
                    sep=";",
                )
    elif isinstance(data_set, pd.Series):
        data_set.to_csv(f"{path}{filename}.csv", header=False, sep=";")
    else:
        raise ValueError("Data set must be of type pd.DataFrame or pd.Series.")


def make_directory_if_missing(folder: str) -> None:
    """Add directories if missing; works with at maximum 2 sub-levels"""
    if os.path.exists(folder):
        pass
    else:
        if os.path.exists(folder.rsplit("/", 2)[0]):
            path = "./" + folder
            os.mkdir(path)
        else:
            path = "./" + folder.rsplit("/", 2)[0]
            os.mkdir(path)
            subpath = folder
            os.mkdir(subpath)


def convert_time_series_index_to_fame_time(
    time_series: pd.DataFrame,
    save: bool = False,
    path: str = "./data_out/amiris/",
    filename: str = "time_series",
    rounding_precision: int = 3,
) -> pd.DataFrame:
    """Convert index of given time series to FAME time format

    Parameters
    ----------
    time_series: pd.DataFrame
        DataFrame to be converted

    save: boolean
        If True, save converted data to disk

    path: str
        Path to store the data

    filename: str
        File name of the data

    rounding_precision: int
        Decimal digits to use for rounding

    Returns
    -------
    time_series_reindexed: pd.DataFrame
        manipulated DataFrame with FAME time stamps
    """
    time_series_reindexed = time_series.copy()
    time_series_reindexed.index = time_series_reindexed.index.astype(str)
    time_series_reindexed.index = time_series_reindexed.index.str.replace(
        " ", "_"
    )
    time_series_reindexed = time_series_reindexed.round(rounding_precision)

    if save:
        save_given_data_set_for_fame(time_series_reindexed, path, filename)

    return time_series_reindexed


def extract_net_operation(
    df: pd.DataFrame,
    column_str: str,
    outflow_column_str: str,
    inflow_column_str: str,
    multi_index: bool = True,
    add_outflow_str: str = "",
    add_inflow_str: str = "",
) -> pd.Series:
    """Extracts net storage resp. import and exports operation

    Parameters
    ----------
    df: pd.DataFrame
        Data for which to extract net operation

    column_str: str
        String to filter for

    outflow_column_str: str
        String for all outflows

    inflow_column_str: str
        String for all inflows

    multi_index: bool
        If True, assume df columns to be a pd.MultiIndex with two levels

    add_outflow_str: str
        Additional string value that needs to be matched for outflow columns

    add_inflow_str: str
        Additional string value that needs to be matched for inflow columns

    Returns
    -------
    pd.Series
    """
    if multi_index:
        filtered_df = df[
            [col for col in df.columns if column_str in col[0]]
        ].copy()
        outflows = [
            col
            for col in filtered_df
            if outflow_column_str in col[0] and add_outflow_str in col[0]
        ]
        inflows = [
            col
            for col in filtered_df
            if inflow_column_str in col[0] and add_inflow_str in col[0]
        ]
    else:
        filtered_df = df[
            [col for col in df.columns if column_str in col]
        ].copy()
        outflows = [
            col
            for col in filtered_df
            if outflow_column_str in col and add_outflow_str in col
        ]
        inflows = [
            col
            for col in filtered_df
            if inflow_column_str in col and add_inflow_str in col
        ]

    filtered_df["outflows"] = filtered_df[outflows].sum(axis=1)
    filtered_df["inflows"] = -filtered_df[inflows].sum(axis=1)
    filtered_df["net_flows"] = filtered_df["outflows"] + filtered_df["inflows"]

    return filtered_df["net_flows"]


def resample_to_hourly_frequency(
    data: pd.Series or pd.DataFrame,
    multiplier: int,
    end_year: int = 2045,
) -> pd.Series or pd.DataFrame:
    """Resamples a given time series to hourly frequency

    Parameters
    ----------
    data: pd.Series or pd.DataFrame
        Data to be resampled

    multiplier: int
        Multiplier for frequency conversion

    end_year: int
        Last year of time series

    Returns
    -------
    resampled_data: pd.Series or pd.DataFrame
        Data in hourly resolution
    """
    resampled_data = data.copy()
    resampled_data.loc[f"{end_year + 1}-01-01 00:00:00"] = resampled_data.iloc[
        -1
    ]
    resampled_data.index = pd.to_datetime(pd.Series(resampled_data.index))
    resampled_data = resampled_data.div(multiplier)
    resampled_data = resampled_data.resample("H").interpolate("ffill")[:-1]
    resampled_data = cut_leap_days(resampled_data)

    return resampled_data


def group_transformers_data(
    path: str,
    file_name_transformers: str,
    file_name_transformers_max: str = "transformers_exogenous_max_ts.csv",
    unclustered: bool = False,
) -> Dict[str, pd.DataFrame]:
    """Group transformers data by 'tech_fuel' and return grouped data set

    Parameters
    ----------
    path : str
        Path to input file(s)

    file_name_transformers : str
        Name of file holding transformers data

    file_name_transformers_max : str
        Name of file holding maximum output development factors
        (only for clustered data)

    unclustered : bool
        If True, use unclustered transformers data, else use clustered one

    Returns
    -------
    dict
        transformers data grouped by 'tech_fuel'
    """

    transformers = pd.read_csv(f"{path}{file_name_transformers}", index_col=0)
    transformers = transformers.loc[transformers["country"] == "DE"]
    if unclustered:
        transformers.columns = [
            col for col in transformers.columns if "20" not in col
        ] + [col[:4] for col in transformers.columns if "20" in col]
    else:
        transformers_max_ts = pd.read_csv(
            f"{path}{file_name_transformers_max}", index_col=0
        )
        transformers_capacity_ts = transformers_max_ts.mul(
            transformers["capacity"]
        )

        # Prepare for grouping
        transformers_capacity_ts.index = transformers_capacity_ts.index.str[:4]
        transformers_capacity_ts_transposed = transformers_capacity_ts.T
        transformers_capacity_ts_transposed[
            ["efficiency_el", "tech_fuel"]
        ] = transformers[["efficiency_el", "tech_fuel"]]
        transformers = transformers_capacity_ts_transposed

    return {
        tech_fuel: plants.sort_values(by="efficiency_el")
        for tech_fuel, plants in transformers.groupby("tech_fuel")
    }


def perform_efficiency_regression(
    grouped_plants: pd.DataFrame,
    plot: bool = False,
    path: str = "./data_out/amiris/",
    path_plots: str = "./plots_out/efficiency/",
    filename_suffix: str = "",
    colors: Dict or None = None,
    language: str = "German",
    fuels_renamed: Dict or None = None,
    techs_renamed: Dict or None = None,
):
    """Perform a linear regression to determine min and max efficiencies"""
    # Perform a regression analysis to derive efficiencies
    # and calculate installed capacities meanwhile
    for key, value in grouped_plants.items():
        power_plants_regression = pd.DataFrame(
            index=range(2020, 2051),
            columns=[
                "efficiency_min",
                "efficiency_max",
                "exogenous_installed_cap",
            ],
        )
        for iter_year in range(2020, 2051):
            value["cumulated_capacity"] = value[str(iter_year)].cumsum()

            X = grouped_plants[key].cumulated_capacity.values
            Y = grouped_plants[key].efficiency_el.values
            X = sm.add_constant(X)

            efficiency_regression = sm.OLS(Y, X).fit()

            x = np.linspace(0, X.max(), int(X.max()))

            # Multiple entries in group and different efficiency values
            if len(Y) > 1 and len(efficiency_regression.params) > 1:
                regression_function = (
                    efficiency_regression.params[0]
                    + efficiency_regression.params[1] * x
                )
                min_efficiency = max(0.1, round(regression_function[0], 4))
                max_efficiency = round(regression_function[-1], 4)

            # Only one entry in group or only one efficiency value;
            # thus no regression function
            else:
                min_efficiency = round(Y[0], 4)
                max_efficiency = round(Y[0], 4)
                regression_function = min_efficiency

            if plot:
                plot_regression_function(
                    grouped_plants,
                    str(key),
                    regression_function,
                    iter_year,
                    colors,
                    language,
                    fuels_renamed,
                    techs_renamed,
                    path_plots,
                )

            power_plants_regression.at[
                iter_year, "efficiency_min"
            ] = min_efficiency
            power_plants_regression.at[
                iter_year, "efficiency_max"
            ] = max_efficiency
            power_plants_regression.at[
                iter_year, "exogenous_installed_cap"
            ] = value["cumulated_capacity"].iloc[-1]

        _ = convert_annual_data_to_fame_time(
            power_plants_regression,
            save=True,
            path=f"{path}all_scenarios/",
            filename=f"{key}{filename_suffix}",
        )


def plot_regression_function(
    grouped_plants: pd.DataFrame,
    key: str,
    regression_function: float or np.array,
    iter_year: int,
    colors: Dict or None,
    language: str,
    fuels_renamed: Dict or None,
    techs_renamed: Dict or None,
    path_plots: str,
):
    """Show a combined scatter and line plot of efficiency estimate"""
    fig, ax = plt.subplots(figsize=(15, 6))

    plot_labels = {
        "German": {
            "cumulated_capacity": "kumulierte Kapazität in MW",
            "efficiency_el": "elektrischer Wirkungsgrad in %",
        },
        "English": {
            "cumulated_capacity": "cumulated capacity in MW",
            "efficiency_el": "electrical efficiency in %",
        },
    }

    to_plot = grouped_plants[key].copy()
    regression_function_plot = regression_function.copy()
    to_plot["efficiency_el"] = to_plot["efficiency_el"] * 100
    regression_function_plot = regression_function_plot * 100
    to_plot.rename(
        columns={
            "cumulated_capacity": plot_labels[language]["cumulated_capacity"],
            "efficiency_el": plot_labels[language]["efficiency_el"],
        },
        inplace=True,
    )
    if colors:
        color = colors[key]
    else:
        color = "blue"
    _ = to_plot.plot(
        kind="scatter",
        x=plot_labels[language]["cumulated_capacity"],
        y=plot_labels[language]["efficiency_el"],
        marker="D",
        color=color,
        ax=ax,
    )
    _ = ax.plot(
        regression_function_plot,
        linestyle="--",
        color="k",
    )
    if language == "English":
        _ = ax.get_xaxis().set_major_formatter(
            FuncFormatter(lambda x, p: format(int(x), ","))
        )
    elif language == "German":
        _ = ax.get_xaxis().set_major_formatter(
            FuncFormatter(lambda x, p: format(int(x), ",").replace(",", "."))
        )
        _ = ax.get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, p: "{:.1f}".format(x).replace(".", ","))
        )
    else:
        raise ValueError(f"Language not implemented: {language}.")

    title = (
        f"{fuels_renamed[language][key.split('_')[1]]} "
        f"{techs_renamed[language][key.split('_')[0]]} "
        f"{iter_year}"
    )

    ax.set_title(title)
    _ = plt.tight_layout()

    make_directory_if_missing(path_plots)
    file_name = f"{path_plots}{key}_{iter_year}_efficiency_regression.png"
    _ = plt.savefig(file_name, dpi=300, bbox_inches="tight")
    _ = plt.show()
    plt.close()
