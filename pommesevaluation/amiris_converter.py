import pandas as pd
import os

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
                    f"{path}{filename}_{col[0]}_{col[1]}.csv", header=False, sep=";"
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

    Returns
    -------
    pd.Series
    """
    filtered_df = df[[col for col in df.columns if column_str in col]].copy()
    outflows = [col for col in filtered_df if outflow_column_str in col]
    inflows = [col for col in filtered_df if inflow_column_str in col]
    filtered_df["outflows"] = filtered_df[outflows].sum(axis=1)
    filtered_df["inflows"] = -filtered_df[inflows].sum(axis=1)
    filtered_df["net_flows"] = filtered_df["outflows"] + filtered_df["inflows"]

    return filtered_df["net_flows"]


def resample_to_hourly_frequency(
    data: pd.Series or pd.DataFrame, multiplier: int
) -> pd.Series or pd.DataFrame:
    """Resamples a given time series to hourly frequency

    Parameters
    ----------
    data: pd.Series or pd.DataFrame
        Data to be resampled

    multiplier: int
        Multiplier for frequency conversion

    Returns
    -------
    resampled_data: pd.Series or pd.DataFrame
        Data in hourly resolution
    """
    resampled_data = data.copy()
    resampled_data.loc["2051-01-01 00:00:00"] = resampled_data.iloc[-1]
    resampled_data.index = pd.to_datetime(pd.Series(resampled_data.index))
    resampled_data = resampled_data.div(multiplier)
    resampled_data = resampled_data.resample("H").interpolate("ffill")[:-1]
    resampled_data = cut_leap_days(resampled_data)

    return resampled_data