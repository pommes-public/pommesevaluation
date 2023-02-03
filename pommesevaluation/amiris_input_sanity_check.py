import pandas as pd
from matplotlib import pyplot as plt
import os


def check_time_series(path_folder, file_name, plot=True):
    """Routine to check time series data

    Parameters
    ----------
    path_folder: str
        Path where file is located
    file_name: str
        File name of time series to be checked
    plot: bool
        If True, show a plot

    Returns
    -------
    stats: pd.DataFrame
        Parameter statistics from describe method
    """
    time_series = pd.read_csv(
        f"{path_folder}{file_name}", sep=";", header=None, index_col=0
    ).astype("float64")
    stats = time_series.describe()
    if plot:
        fig, ax = plt.subplots(figsize=(15, 5))
        time_series.plot(ax=ax)
        plt.legend(labels=[file_name])
        plt.tight_layout()
        plt.show()

    return stats


def check_time_series_chunks(
    path_folder, file_name, chunks="annual", plot=True
):
    """Routine to check time series data chunks

    Parameters
    ----------
    path_folder: str
        Path where file is located
    file_name: str
        File name of time series to be checked
    chunks: str
        Chunks of data to be checked (only "annual" is allowed)
    plot: bool
        If True, show a plot of data
    """
    time_series = pd.read_csv(
        f"{path_folder}{file_name}", sep=";", header=None, index_col=0
    )
    years = time_series.index.str.slice(start=0, stop=4).unique()
    annual_data = {}
    if chunks == "annual":
        for iter_year in years:
            annual_data[iter_year] = {}
            annual_data[iter_year]["data"] = time_series.loc[
                time_series.index.str.slice(start=0, stop=4) == iter_year
            ]
            annual_data[iter_year]["stats"] = annual_data[iter_year][
                "data"
            ].describe()
    if plot:
        plot_time_series(annual_data)
    else:
        raise ValueError("Chunks other than annual are not implemented, yet.")

    return annual_data


def plot_time_series(data):
    """Plot given time series"

    Parameters
    ----------
    data: dict
        Dictionary holding annual data
    """
    fig, axs = plt.subplots(
        nrows=len(data), ncols=1, figsize=(10, 5 * len(data))
    )
    for no, data_entries in enumerate(data.items()):
        iter_year = data_entries[0]
        time_series = data_entries[1]["data"]
        time_series.plot(ax=axs[no])
        axs[no].title.set_text(iter_year)

    plt.tight_layout()
    plt.show()


def get_all_csv_files_in_folder_except(path_folder, exception=None):
    """Return a list of all csv files in folder except list of exceptions

    Parameters
    ----------
    path_folder: str
        Folder where csv files are stored
    exception: list of str
        Files to ignore

    Returns
    -------
    list:
        List of all csv files in given folder
    """
    if not exception:
        exception = []
    return [
        file
        for file in os.listdir(path_folder)
        if file.endswith(".csv") and file not in exception
    ]
