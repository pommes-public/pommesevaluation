import pandas as pd
import os


def convert_annual_data_to_fame_time(
    df: pd.DataFrame,
    orient: str = "columns",
    save: bool = False,
    path: str = "./data_out/amiris/",
    filename: str = "time_series",
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

    if save:
        save_given_data_set_for_fame(reindexed_df, path, filename)

    return reindexed_df


def save_given_data_set_for_fame(
    data_set: pd.DataFrame, path: str, filename: str
):
    """Save a given data set using FAME time and formatting

    Parameters
    ----------
    data_set: pd.DataFrame
        Data set to be saved (column-wise)

    path: str
        Path to store the data

    filename: str
        File name for storing
    """
    make_directory_if_missing(path)
    for col in data_set.columns:
        data_set[col].to_csv(
            f"{path}{filename}_{col}.csv", header=None, sep=";"
        )


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

    if save:
        save_given_data_set_for_fame(time_series_reindexed, path, filename)

    return time_series_reindexed
