from typing import Dict

import pandas as pd
from pandas.tseries.frequencies import to_offset


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
        fuel_cost_pathway,
        emissions_cost_pathway,
        flexibility_options_scenario,
        activate_emissions_pathway_limit,
        activate_emissions_budget_limit,
        activate_demand_response,
        demand_response_scenario,
    ):
        """Initialize a data container"""
        self.path_folder_input = path_folder_input
        self.countries = countries
        self.start_time = start_time
        self.end_time = end_time
        self.overlap_in_time_steps = overlap_in_time_steps
        self.freq = freq
        self.fuel_cost_pathway = fuel_cost_pathway
        self.emissions_cost_pathway = emissions_cost_pathway
        self.flexibility_options_scenario = flexibility_options_scenario
        self.activate_emissions_pathway_limit = (
            activate_emissions_pathway_limit
        )
        self.activate_emissions_budget_limit = activate_emissions_budget_limit
        self.activate_demand_response = activate_demand_response
        self.demand_response_scenario = demand_response_scenario

    def add_demand_response_clusters(self, demand_response_clusters):
        """Append the information on demand response clusters to the model

        Parameters
        ----------
        demand_response_clusters : list
            Demand response clusters to be considered
        """
        setattr(self, "demand_response_clusters", demand_response_clusters)


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


def process_input_data(im: InvestmentModelDummy) -> Dict[str, pd.DataFrame]:
    """Process and return input data

    Parameters
    ----------
    im : InvestmentModelDummy
        investment model (attributes)

    Returns
    -------
    input_data : dict
        Input data stored in a dict of pd.DataFrame
    """
    buses = {"buses": "buses"}

    components = {
        "sinks_excess": "sinks_excess",
        "sinks_demand_el": "sinks_demand_el",
        "sources_shortage": "sources_shortage",
        "sources_commodity": "sources_commodity",
        "sources_renewables": "sources_renewables_investment_model",
        "exogenous_storages_el": "storages_el_exogenous",
        "new_built_storages_el": "storages_el_investment_options",
        "exogenous_transformers": "transformers_exogenous",
        "new_built_transformers": "transformers_investment_options",
    }

    hourly_time_series = {
        "sinks_demand_el_ts": "sinks_demand_el_ts_hourly",
        "sources_renewables_ts": "sources_renewables_ts_hourly",
        "transformers_minload_ts": "transformers_minload_ts_hourly",
        "transformers_availability_ts": "transformers_availability_ts_hourly",
        "linking_transformers_ts": "linking_transformers_ts",
    }

    annual_time_series = {
        "transformers_exogenous_max_ts": "transformers_exogenous_max_ts",
        "costs_fuel_ts": (
            f"costs_fuel_{im.fuel_cost_pathway}_nominal_indexed_ts"
        ),
        "costs_emissions_ts": (
            f"costs_emissions_{im.emissions_cost_pathway}_nominal_indexed_ts"
        ),
        "costs_operation_ts": (
            f"variable_costs_{im.flexibility_options_scenario}%_nominal"
        ),
        "costs_operation_storages_ts": (
            f"variable_costs_storages_"
            f"{im.flexibility_options_scenario}%_nominal"
        ),
        "costs_investment": (
            f"investment_expenses_{im.flexibility_options_scenario}%_nominal"
        ),
        "costs_storages_investment_capacity": (
            f"investment_expenses_storages_capacity_"
            f"{im.flexibility_options_scenario}%_nominal"
        ),
        "costs_storages_investment_power": (
            f"investment_expenses_storages_power_"
            f"{im.flexibility_options_scenario}%_nominal"
        ),
        "linking_transformers_annual_ts": "linking_transformers_annual_ts",
        "storages_el_exogenous_max_ts": "storages_el_exogenous_max_ts",
    }

    # Time-invariant data sets
    other_files = {
        "emission_limits": "emission_limits",
        "wacc": "wacc",
        "interest_rate": "interest_rate",
        "fixed_costs": (
            f"fixed_costs_{im.flexibility_options_scenario}%_nominal"
        ),
        "fixed_costs_storages": (
            f"fixed_costs_storages_{im.flexibility_options_scenario}%_nominal"
        ),
        "hydrogen_investment_maxima": "hydrogen_investment_maxima",
        "linking_transformers": "linking_transformers",
    }

    # Development factors for emissions; used for scaling minimum loads
    if (
        im.activate_emissions_pathway_limit
        or im.activate_emissions_budget_limit
    ):
        other_files[
            "emission_development_factors"
        ] = "emission_development_factors"

    # Add demand response units
    if im.activate_demand_response:
        # Overall demand = overall demand excluding demand response baseline
        hourly_time_series["sinks_demand_el_ts"] = (
            f"sinks_demand_el_excl_demand_response_ts_"
            f"{im.demand_response_scenario}_hourly"
        )
        components[
            "sinks_demand_el"
        ] = f"sinks_demand_el_excl_demand_response_{im.demand_response_scenario}"

        # Obtain demand response clusters from file to avoid hard-coding
        components[
            "demand_response_clusters_eligibility"
        ] = "demand_response_clusters_eligibility"
        dr_clusters = load_input_data(
            filename="demand_response_clusters_eligibility", im=im
        )
        # Add demand response clusters information to the model itself
        im.add_demand_response_clusters(list(dr_clusters.index))
        for dr_cluster in dr_clusters.index:
            components[
                f"sinks_dr_el_{dr_cluster}"
            ] = f"{dr_cluster}_potential_parameters_{im.demand_response_scenario}%"
            annual_time_series[
                f"sinks_dr_el_{dr_cluster}_variable_costs"
            ] = f"{dr_cluster}_variable_costs_parameters_{im.demand_response_scenario}%"
            annual_time_series[
                f"sinks_dr_el_{dr_cluster}_fixed_costs_and_investments"
            ] = (
                f"{dr_cluster}_fixed_costs_and_investments_parameters_"
                f"{im.demand_response_scenario}%"
            )

        hourly_time_series[
            "sinks_dr_el_ts"
        ] = f"sinks_demand_response_el_ts_{im.demand_response_scenario}"

        hourly_time_series[
            "sinks_dr_el_ava_pos_ts"
        ] = f"sinks_demand_response_el_ava_pos_ts_{im.demand_response_scenario}"
        hourly_time_series[
            "sinks_dr_el_ava_neg_ts"
        ] = f"sinks_demand_response_el_ava_neg_ts_{im.demand_response_scenario}"

    # Combine all files
    input_files = {
        **buses,
        **components,
        **annual_time_series,
        **hourly_time_series,
    }
    input_files = {**input_files, **other_files}

    input_data = {
        key: load_input_data(filename=name, im=im)
        for key, name in input_files.items()
    }

    return input_data


def resample_timeseries(
    timeseries, freq, aggregation_rule="sum", interpolation_rule="linear"
):
    """Resample a timeseries to the frequency provided

    The frequency of the given timeseries is determined at first and upsampling
    resp. downsampling are carried out afterwards. For upsampling linear
    interpolation (default) is used, but another method may be chosen.

    Time series indices ignore time shifts and can be interpreted as UTC time.
    Since they aren't localized, this cannot be detected by pandas and the
    correct frequency cannot be inferred. As a hack, only the first couple of
    time steps are checked, for which no problems should occur.

    Parameters
    ----------
    timeseries : :obj:`pd.DataFrame`
        The timeseries to be resampled stored in a pd.DataFrame

    freq : :obj:`str`
        The target frequency

    interpolation_rule : :obj:`str`
        Method used for interpolation in upsampling

    Returns
    -------
    resampled_timeseries : :obj:`pd.DataFrame`
        The resampled timeseries stored in a pd.DataFrame

    """
    # Ensure a datetime index
    try:
        timeseries.index = pd.DatetimeIndex(timeseries.index)
    except ValueError:
        raise ValueError(
            "Time series has an invalid index. "
            "A pd.DatetimeIndex is required."
        )

    try:
        original_freq = pd.infer_freq(timeseries.index, warn=True)
    except ValueError:
        original_freq = "AS"

    # Hack for problems with recognizing abolishing the time shift
    if not original_freq:
        try:
            original_freq = pd.infer_freq(timeseries.index[:5], warn=True)
        except ValueError:
            raise ValueError("Cannot detect frequency of time series!")

    # Introduce common timestamp to be able to compare different frequencies
    common_dt = pd.to_datetime("2000-01-01")

    if common_dt + to_offset(freq) > common_dt + to_offset(original_freq):
        # do downsampling
        resampled_timeseries = timeseries.resample(freq).agg(aggregation_rule)

    else:
        # do upsampling
        resampled_timeseries = timeseries.resample(freq).interpolate(
            method=interpolation_rule
        )

    cut_leap_days(resampled_timeseries)

    return resampled_timeseries


def cut_leap_days(time_series):
    """Take a time series index with real dates and cut the leap days out

    Actual time stamps cannot be interpreted. Instead consider 8760 hours
    of a synthetical year

    Parameters
    ----------
    time_series : pd.Series or pd.DataFrame
        original time series with real life time index

    Returns
    -------
    time_series : pd.Series or pd.DataFrame
        Time series, simply cutted down to 8 760 hours per year
    """
    years = sorted(list(set(getattr(time_series.index, "year"))))
    for year in years:
        if is_leap_year(year):
            try:
                time_series.drop(
                    time_series.loc[
                        (time_series.index.year == year)
                        & (time_series.index.month == 12)
                        & (time_series.index.day == 31)
                    ].index,
                    inplace=True,
                )
            except KeyError:
                continue

    return time_series


def is_leap_year(year):
    """Check whether given year is a leap year or not

    Parameters:
    -----------
    year: :obj:`int`
        year which shall be checked

    Returns:
    --------
    leap_year: :obj:`boolean`
        True if year is a leap year and False else
    """
    leap_year = False

    if year % 4 == 0:
        leap_year = True
    if year % 100 == 0:
        leap_year = False
    if year % 400 == 0:
        leap_year = True

    return leap_year
