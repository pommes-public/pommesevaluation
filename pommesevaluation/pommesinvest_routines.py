import pandas as pd


class InvestmentModelDummy:
    """Container object holding attributes, an InvestmentModel usually has"""

    def __init__(
        self,
        path_folder_input,
        countries,
        start_time,
        end_time,
        overlap_in_time_steps,
        freq,
    ):
        """Initialize a data container"""
        self.path_folder_input = path_folder_input
        self.countries = countries
        self.start_time = start_time
        self.end_time = end_time
        self.overlap_in_time_steps = overlap_in_time_steps
        self.freq = freq


def load_input_data(filename=None, im=None):
    r"""Load input data from csv files.

    Parameters
    ----------
    filename : :obj:`str`
        Name of CSV file containing data

    im : :class:`InvestmentModel`
        The investment model that is considered

    Returns
    -------
    df : :class:`pandas.DataFrame`
        DataFrame containing information about nodes or time series.
    """
    if "ts_hourly" not in filename:
        df = pd.read_csv(im.path_folder_input + filename + ".csv", index_col=0)
    # Load slices for hourly data to reduce computational overhead
    else:
        df = load_time_series_data_slice(filename + ".csv", im)

    if "country" in df.columns and im.countries is not None:
        df = df[df["country"].isin(im.countries)]

    if df.isna().any().any() and "_ts" in filename:
        print(
            f"Attention! Time series input data file {filename} contains NaNs."
        )
        print(df.loc[df.isna().any(axis=1)])

    return df


def load_time_series_data_slice(filename=None, im=None):
    """Load slice of input time series data from csv files.

    Determine index range to read in from reading in index
    separately.

    Parameters
    ----------
    filename : :obj:`str`
        Name of CSV file containing data

    im : :class:`InvestmentModel`
        The investment model that is considered

    Returns
    -------
    df : :class:`pandas.DataFrame`
        DataFrame containing sliced time series.
    """
    time_series_start = pd.read_csv(
        im.path_folder_input + filename,
        parse_dates=True,
        index_col=0,
        usecols=[0],
    )
    start_index = pd.Index(time_series_start.index).get_loc(im.start_time)
    time_series_end = pd.Timestamp(im.end_time)
    end_index = pd.Index(time_series_start.index).get_loc(
        (
            time_series_end
            + im.overlap_in_time_steps
            * pd.Timedelta(hours=int(im.freq.split("H")[0]))
        ).strftime("%Y-%m-%d %H:%M:%S")
    )

    return pd.read_csv(
        im.path_folder_input + filename,
        parse_dates=True,
        index_col=0,
        skiprows=range(1, start_index),
        nrows=end_index - start_index + 1,
    )
