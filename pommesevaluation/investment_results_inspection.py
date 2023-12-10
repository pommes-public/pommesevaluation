"""
Routines used for investment results inspection for both, analyses of
investments taken as well as the resulting dispatch of units resp. clusters.
"""
import warnings

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter


def preprocess_raw_results(results_raw, investments=True, multi_header=False):
    """Preprocess raw investment results - both, investments and dispatch

    Parameters
    ----------
    results_raw : pd.DataFrame
        Raw investment results

    investments : bool
        If True, analyse volumes invested into (MW);
        if False, analyse resulting production (MWh)

    multi_header : bool
        It True, extract dispatch data that has a multi-index header
        with two levels

    Returns
    -------
    processed_results : pd.DataFrame
        Preprocessed investment results
    """
    processed_results = results_raw.copy()
    if not multi_header:
        processed_results.index = processed_results.index.str.split(
            expand=True
        )
    else:
        processed_results = processed_results.reset_index(level=1, drop=False)
        processed_results.index = processed_results.index.get_level_values(
            0
        ).str.split(expand=True)
        processed_results = processed_results.set_index("level_1", append=True)
    processed_results.index.names = ["from", "to", "year"]
    processed_results.reset_index(inplace=True)
    if multi_header:
        processed_results["to"] = np.where(
            processed_results["to"].isna(),
            processed_results["year"],
            processed_results["to"],
        )
    processed_results["from"] = processed_results["from"].str.strip("(',")
    processed_results["to"] = processed_results["to"].str.strip(")',")
    processed_results["year"] = processed_results["year"].str.strip(")")

    # Adjust storage labels
    processed_results.loc[
        (processed_results["from"].str.contains("storage"))
        & (processed_results["to"].str.contains("None")),
        "from",
    ] = (
        processed_results["from"] + "_capacity"
    )

    processed_results.loc[
        (processed_results["from"].str.contains("storage"))
        & (
            (processed_results["to"].str.contains("DE_bus_el"))
            | (processed_results["to"].str.contains("DE_bus_ev"))
        ),
        "from",
    ] = (
        processed_results["from"] + "_inflow"
    )

    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (processed_results["to"].str.contains("storage")),
        "from",
    ] = (
        processed_results["to"] + "_outflow"
    )

    # Adjust sink labels
    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (processed_results["to"].str.contains("DE_sink_el")),
        "from",
    ] = processed_results["to"]

    # Adjust electrolyzer labels
    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (
            processed_results["to"].str.contains(
                "DE_transformer_hydrogen_electrolyzer"
            )
        ),
        "from",
    ] = processed_results["to"]

    # Adjust links to foreign market areas
    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (processed_results["to"].str.contains("DE_link_")),
        "from",
    ] = processed_results["to"]

    # Adjust demand response inflows
    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (processed_results["to"].str.contains("cluster_")),
        "from",
    ] = (
        processed_results["to"] + "_demand_after"
    )

    # Separate demand response variables
    processed_results.loc[
        processed_results["to"].isin(
            ["dsm_up", "dsm_do_shift", "dsm_do_shed", "dsm_storage_level"]
        ),
        "from",
    ] = (
        processed_results["from"] + "_" + processed_results["to"]
    )

    processed_results = processed_results.rename(
        columns={"from": "unit"}
    ).drop(columns="to")
    string_to_drop = ["DE_storage_el_", "DE_transformer_"]
    if investments:
        string_to_drop.append("_new_built")
    for string in string_to_drop:
        processed_results["unit"] = processed_results["unit"].str.replace(
            string, ""
        )

    return processed_results


def aggregate_investment_results(
    processed_results,
    energy_carriers,
    by="energy_carrier",
    investments=True,
    include_chp_information=False,
):
    """Aggregate preprocessed investment results by energy carrier / technology

    Parameters
    ----------
    processed_results : pd.DataFrame
        Preprocessed investment results

    energy_carriers : iterable
        Feasible energy carriers

    by : str or list of str
        Rule to group by; either `energy_carrier` or `technology`
        or `["energy_carrier", "technology"]` for both

    investments : bool
        If True, analyse volumes invested into (MW);
        if False, analyse resulting production (MWh)

    include_chp_information : bool
        If True, distinct whether CHP is used or not for technology

    Returns
    -------
    aggregated_results : pd.DataFrame
        Aggregated results incl. investments in storage inflow for investments
        consideration; aggregated dispatch for dispatch consideration

    other_storages_results : pd.DataFrame
        Results for investments in storage capacity and storage outflow;
        only for investments consideration
    """
    aggregated_results = processed_results.copy()
    aggregated_results[["fuel", "tech"]] = aggregated_results[
        "unit"
    ].str.split("_", 1, expand=True)

    # Account for electrolyzers
    aggregated_results.loc[
        (aggregated_results["fuel"] == "hydrogen")
        & (aggregated_results["tech"].str.contains("electrolyzer")),
        "fuel",
    ] = (
        aggregated_results["fuel"] + "_" + aggregated_results["tech"]
    )

    storage_technologies = ["PHS", "battery"]
    if not investments:
        storage_technologies.extend(
            [tech + "_new_built" for tech in storage_technologies]
        )

    storage_elements = ["_capacity", "_outflow"]
    storages = [a + b for a in storage_technologies for b in storage_elements]

    technologies = r"GT|ST|CC|FC"

    grouping_col = by
    aggregated_results["energy_carrier"] = np.where(
        aggregated_results["fuel"].isin(energy_carriers),
        aggregated_results["fuel"],
        aggregated_results["unit"],
    )
    aggregated_results["technology"] = np.where(
        aggregated_results["tech"].str.contains(technologies),
        aggregated_results["tech"].str.split("_", expand=True).iloc[:, 0],
        aggregated_results["unit"],
    )
    if include_chp_information:
        aggregated_results["technology"] = np.where(
            aggregated_results["tech"].str.contains(technologies),
            aggregated_results["tech"],
            aggregated_results["unit"],
        )

    if by not in [
        "energy_carrier",
        "technology",
        ["energy_carrier", "technology"],
    ]:
        raise ValueError(
            f"Aggregation mode {by} not defined; "
            f"must be either `energy_carrier` or `technology` "
            f"or `['energy_carrier', 'technology']`."
        )

    if not isinstance(grouping_col, list):
        grouping_cols = [grouping_col]
    else:
        grouping_cols = grouping_col
    if investments:
        grouping_cols.append("year")

    aggregated_results = aggregated_results.groupby(grouping_cols).sum()

    if investments:
        other_storages_results = aggregated_results.loc[
            [idx for idx in storages]
        ]
        aggregated_results.drop(
            index=other_storages_results.index, inplace=True
        )

        return aggregated_results, other_storages_results

    else:
        return aggregated_results


def plot_single_investment_variable(
    results,
    variable_name,
    colors=None,
    aggregation="energy_carrier",
    storage=False,
    group=True,
    save=False,
    filename="results",
    dr_scenario="none",
    path_plots="./plots/",
    path_data_out="./data_out/",
    ylim=None,
    format_axis=True,
    draw_xlabel=True,
):
    """Plot a single investment-related variable from results data set

    Parameters
    ----------
    results : pd.DataFrame
        Data set containing all investment results

    variable_name : str
        Particular variable to plot;
        one of ['invest', 'old', 'old_end', 'old_exo', 'total', 'all']

    colors : dict or None
        Colors to use if given

    aggregation : str or None
        Determines which kind of aggregation has been made;
        aggregation by `energy_carrier` or by `technology`

    storage : bool
        If True, modify plot such that storage investments can be depicted;
        introduces secondary y axis for storage energy content

    group : bool
        If True, group data by given aggregation type (default);
        else plot data as it has been given

    save : bool
        If True, save to file (defaults to False)

    filename : str
        File name to use for saving to file

    dr_scenario : str
        Scenario for demand response that has been considered

    path_plots : str
        Path for storing the generated plot

    path_data_out : str
        Path for storing the aggregated results data

    ylim : list
        y axis limits

    format_axis : boolean
        If True, format the yaxis to int values

    draw_xlabel : boolean
        If True, add xaxis label to plot
    """
    ylabels = {
        "invest": "newly invested capacity",
        "old": "total decommissioned capacity",
        "old_end": "capacity decommissioned because of lifetime",
        "old_exo": "capacity decommissioned because after initial age",
        "total": "total installed capacity",
        "all": "overall installed capacity",
        "potential": "potential vs. realised capacity",
    }
    if group:
        plot_data = group_results(results, variable_name, aggregation)
    else:
        plot_data = results.copy()

    fig, ax = plt.subplots(figsize=(12, 5))
    create_single_plot(
        plot_data,
        variable_name,
        colors,
        storage,
        ax,
        ylabels,
        ylim=ylim,
        format_axis=format_axis,
        draw_xlabel=draw_xlabel,
    )

    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(f"{path_plots}{filename}_{dr_scenario}.png", dpi=300)
        plot_data.T.to_csv(f"{path_data_out}{filename}_{dr_scenario}.csv")

    _ = plt.show()
    plt.close()


def group_results(
    results,
    variable_name,
    aggregation="energy_carrier",
):
    """Group investment decision results by given aggregation column

    Parameters
    ----------
    results : pd.DataFrame
        Data set containing all investment results

    variable_name : str
        Particular variable to plot;
        one of ['invest', 'old', 'old_end', 'old_exo', 'total']

    aggregation : str or None
        Determines which kind of aggregation has been made;
        aggregation by `energy_carrier` or by `technology`

    Returns
    -------
    grouped_data : pd.DataFrame
        Grouped data set
    """
    grouped_data = results[[variable_name]].reset_index()
    grouped_data = grouped_data.pivot(
        index=aggregation, columns="year", values=variable_name
    )

    return grouped_data


def extract_data_and_save(
    results,
    variable_name,
    aggregation="energy_carrier",
    group=True,
    filename="results",
    dr_scenario="none",
    path_data_out="./data_out/",
):
    """Extract and group data from results data set

    Parameters
    ----------
    results : pd.DataFrame
        Data set containing all investment results

    variable_name : str
        Particular variable to plot;
        one of ['invest', 'old', 'old_end', 'old_exo', 'total', 'all']

    aggregation : str or None
        Determines which kind of aggregation has been made;
        aggregation by `energy_carrier` or by `technology`

    group : bool
        If True, group data by given aggregation type (default);
        else use data as it has been given

    filename : str
        File name to use for saving to file

    dr_scenario : str
        Scenario for demand response that has been considered

    path_data_out : str
        Path for storing the aggregated results data
    """
    if group:
        extracted_data = group_results(results, variable_name, aggregation)
    else:
        extracted_data = results.copy()

    extracted_data.T.to_csv(f"{path_data_out}{filename}_{dr_scenario}.csv")


def create_single_plot(
    plot_data,
    variable_name,
    colors,
    storage,
    ax,
    ylabels,
    title=None,
    legend=True,
    hide_axis=False,
    ylim=None,
    format_axis=True,
    draw_xlabel=True,
    draw_ylabel=True,
):
    """Create one single investment results plot"""
    if not storage:
        if colors:
            plot_data = plot_data.loc[[col for col in colors]]
            if legend:
                _ = plot_data.T.plot(
                    kind="bar", stacked=True, ax=ax, color=colors
                )
            else:
                _ = plot_data.T.plot(
                    kind="bar", stacked=True, ax=ax, color=colors, legend=False
                )
        else:
            if legend:
                _ = plot_data.T.plot(kind="bar", stacked=True, ax=ax)
            else:
                _ = plot_data.T.plot(
                    kind="bar", stacked=True, ax=ax, legend=False
                )

    else:
        ax2 = ax.twinx()
        energy_results = plot_data.loc[
            plot_data.index.get_level_values(0).isin(
                ["PHS_capacity", "battery_capacity"]
            )
        ]
        power_results = plot_data.drop(index=energy_results.index)

        if colors:
            energy_results = energy_results.loc[
                [col for col in colors if col in energy_results.index]
            ]
            energy_colors = {
                col: val
                for col, val in colors.items()
                if col in energy_results.index
            }
            _ = energy_results.T.plot(
                kind="bar",
                stacked=True,
                ax=ax2,
                alpha=0.3,
                color=energy_colors,
                legend=False,
            )

            power_results = power_results.loc[
                [col for col in colors if col in power_results.index]
            ]
            power_colors = {
                col: val
                for col, val in colors.items()
                if col in power_results.index
            }
            _ = power_results.T.plot(
                kind="bar",
                stacked=True,
                ax=ax,
                color=power_colors,
                legend=False,
            )
        else:
            _ = energy_results.T.plot(kind="bar", stacked=True, ax=ax)
            _ = power_results.T.plot(kind="bar", stacked=True, ax=ax)

        if draw_ylabel:
            _ = ax2.set_ylabel(f"{ylabels[variable_name]} in MWh")

    if title:
        _ = ax.set_title(title)
    if legend:
        _ = plt.legend(bbox_to_anchor=[1.1, 1.02])

    if hide_axis:
        _ = ax.get_xaxis().set_visible(False)
    else:
        if draw_xlabel:
            _ = plt.xlabel("year")
        else:
            ax.get_xaxis().label.set_visible(False)
        if draw_ylabel:
            _ = ax.set_ylabel(f"{ylabels[variable_name]} in MW")

    if ylim:
        _ = ax.set_ylim(ylim)
    # current_values = plt.gca().get_yticks()
    # _ = plt.gca().set_yticklabels(
    #     ["{:,.0f}".format(x) for x in current_values]
    # )
    if format_axis:
        _ = ax.get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, p: format(int(x), ","))
        )


def plot_single_investment_variable_for_all_cases(
    results_dict,
    variable_name,
    colors=None,
    aggregation="energy_carrier",
    storage=False,
    group=True,
    dr_color_codes={},
    save=False,
    filename="results",
    path_plots="./plots/",
    ylim=None,
    title="Demand Response scenario",
    format_axis=True,
    draw_ylabel=False,
    include_common_xlabel=True,
    figwidth=12,
):
    """Plot investment variable; create subplots to compare among scenarios

    Parameters
    ----------
    results_dict : dict of pd.DataFrame
        Dict containing all investment results data sets

    variable_name : str
        Particular variable to plot;
        one of ['invest', 'old', 'old_end', 'old_exo', 'total', 'all']

    colors : dict or None
        Colors to use if given

    aggregation : str or None
        Determines which kind of aggregation has been made;
        aggregation by `energy_carrier` or by `technology`

    storage : bool
        If True, modify plot such that storage investments can be depicted;
        introduces secondary y axis for storage energy content

    group : bool
        If True, group data by given aggregation type (default);
        else plot data as it has been given

    dr_color_codes : dict
        Dict of demand response color codes

    save : bool
        If True, save to file (defaults to False)

    filename : str
        File name to use for saving to file

    path_plots : str
        Path for storing the generated plot

    ylim : list
        Common yaxis limit to share among the plots

    title : str
        Title of the plot

    format_axis : boolean
        If True, format the yaxis to int values

    draw_xlabel : boolean
        If True, add xaxis label to plot

    draw_ylabel : boolean
        If True, add ylabel to last subplot

    include_common_xlabel : boolean
        If True, draw a common xlabel

    figwidth : int
        Width of figure
    """
    ylabels = {
        "invest": "newly invested capacity",
        "old": "total decommissioned capacity",
        "old_end": "capacity decommissioned because of lifetime",
        "old_exo": "capacity decommissioned because after initial age",
        "total": "total installed capacity",
        "all": "overall installed capacity",
        "potential": "potential vs. realised capacity",
    }

    fig, axs = plt.subplots(
        len(results_dict), 1, figsize=(figwidth, 3 * len(results_dict))
    )
    hide_axis = True
    for number, item in enumerate(results_dict.items()):
        if number == len(results_dict) - 1:
            hide_axis = False

        dr_scenario = item[0]
        results = item[1]

        colors_copy = colors.copy()
        if dr_scenario == "none":
            for color in dr_color_codes:
                colors_copy.pop(color)

        if group:
            plot_data = group_results(results, variable_name, aggregation)
        else:
            plot_data = results.copy()

        create_single_plot(
            plot_data,
            variable_name,
            colors_copy,
            storage,
            axs[number],
            ylabels,
            title=f"{title} {dr_scenario}",
            legend=False,
            hide_axis=hide_axis,
            ylim=ylim,
            format_axis=format_axis,
            draw_xlabel=False,
            draw_ylabel=draw_ylabel,
        )

    # Use common axes across plot
    if storage:
        fig.text(
            1.01,
            0.52,
            f"{ylabels[variable_name]} in MWh",
            va="center",
            rotation="vertical",
        )
        xaxis_label_pos = 0.5
    else:
        xaxis_label_pos = 0.53
    if include_common_xlabel:
        fig.text(xaxis_label_pos, -0.01, "year", ha="center")
    fig.text(
        -0.01,
        0.52,
        f"{ylabels[variable_name]} in MW",
        va="center",
        rotation="vertical",
    )

    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(f"{path_plots}{filename}_all_scenarios.png", dpi=300)

    _ = plt.show()
    plt.close()


def plot_single_dispatch_pattern(
    dispatch_pattern,
    start_time_step,
    amount_of_time_steps,
    colors,
    save=True,
    path_plots="./plots/",
    filename="dispatch_pattern",
    kind="area",
    stacked=None,
    figsize=(15, 10),
    title=None,
    ylabel=None,
    linestyle=None,
):
    """Plot a single dispatch pattern for a given start and end time stamp

    Parameters
    ----------
    dispatch_pattern : pd.DataFrame
        Dispatch pattern to be plotted

    start_time_step : str
        First time step of excerpt displayed

    amount_of_time_steps : int or float
        Number of time steps to be displayed

    colors : dict
        Colors to use for the plot

    save : bool
        Indicates whether to save the plot

    path_plots : str
        Path to use for storing the plot

    filename : str
        File name to use for the plot

    kind : str
        Kind of plot to draw; defaults to "area"

    stacked : bool
        If True, draw a stacked (bar) chart

    figsize : tuple of int
        Size of plot

    title : str
        String to display in plot title

    ylabel : str
        String to use for labelling y label

    linestyle : dict
        Linestyles to use in case of a line plot
    """
    index_start = int(dispatch_pattern.index.get_loc(start_time_step))
    index_end = int(index_start + amount_of_time_steps)
    end_time_step = dispatch_pattern.iloc[index_end].name

    fig, ax = plt.subplots(figsize=figsize)
    if kind == "bar" and stacked:
        _ = dispatch_pattern.iloc[index_start : index_end + 1].plot(
            ax=ax, kind=kind, color=colors, stacked=stacked
        )
    elif linestyle:
        for col in dispatch_pattern.columns:
            _ = (
                dispatch_pattern[col]
                .iloc[index_start : index_end + 1]
                .plot(
                    ax=ax,
                    kind=kind,
                    color=colors[col],
                    linestyle=linestyle[col],
                )
            )
    else:
        _ = dispatch_pattern.iloc[index_start : index_end + 1].plot(
            ax=ax, kind=kind, color=colors
        )
    _ = ax.set_xlabel("Time")
    if not ylabel:
        ylabel = "Energy [MWh/h]"
    _ = ax.set_ylabel(ylabel)
    if not title:
        title = "Dispatch situation"
    _ = plt.title(f"{title} from {start_time_step} to {end_time_step}")
    _ = plt.legend(bbox_to_anchor=[1.02, 1.05])
    _ = plt.xticks(rotation=90)
    _ = plt.tight_layout()

    if save:
        file_name_out = (
            f"{path_plots}{filename}_{start_time_step}-{end_time_step}.png"
        )
        file_name_out = file_name_out.replace(":", "-").replace(" ", "_")
        file_name_out.replace(":", "-")
        _ = plt.savefig(
            file_name_out,
            dpi=300,
        )

    _ = plt.show()
    plt.close()


def plot_time_series_cols(df, size=(15, 5)):
    """Plot each column of a time series DataFrame in dedicated subplot

    Parameters
    ----------
    df: pd.DataFrame
        time series data to visualize

    size: tuple of int
        size of plot; first entry: width; second entry: height of single
        subplot
    """
    fig, axs = plt.subplots(
        len(df.columns), 1, figsize=(size[0], len(df.columns) * size[1])
    )

    for no, col in enumerate(df.columns):
        try:
            _ = df[col].plot(ax=axs[no])
            _ = axs[no].set_title(col)
        except TypeError:
            warnings.warn(
                f"No numeric data to plot for column: {col}", UserWarning
            )

    _ = plt.tight_layout()
    _ = plt.show()
    plt.close()


def create_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with datetime index"""
    df.loc[2051] = df.iloc[-1]
    df["new_index"] = df.index.astype(str) + "-01-01"
    df.index = pd.to_datetime(df["new_index"])
    df.drop(columns="new_index", inplace=True)

    return df
