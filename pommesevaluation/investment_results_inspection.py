"""
Routines used for investment results inspection for both, analyses of
investments taken as well as the resulting dispatch of units resp. clusters.
"""
import warnings
from typing import Dict

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from pommesevaluation.global_vars import (
    STORAGES_OTHER_RENAMED,
)


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
        processed_results["from"] + "_outflow"
    )

    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (processed_results["to"].str.contains("storage")),
        "from",
    ] = (
        processed_results["to"] + "_inflow"
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

    # Adjust label for uncontrolled EV charging
    processed_results.loc[
        (processed_results["from"].str.contains("DE_bus_el"))
        & (processed_results["to"].str.contains("transformer_ev_uc")),
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
    figsize=(14, 9),
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
    place_legend_below=True,
    bbox_params=(0.5, -0.15),
    ncol=4,
    language="German",
    exclude_unit=False,
):
    """Plot a single investment-related variable from results data set

    Parameters
    ----------
    results : pd.DataFrame
        Data set containing all investment results

    variable_name : str
        Particular variable to plot;
        one of ['invest', 'old', 'old_end', 'old_exo', 'total', 'all']

    figsize: tuple or list
        Size of the figure to be plotted

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

    place_legend_below : boolean
        If True, plot legend under plot, else right next to it

    bbox_params : tuple or list
        Define bbox_to_anchor content (for legend placed below)

    ncol : int
        Control the number of columns for the legend labels

    language : str
        Language to use (one of "German" and "English")

    exclude_unit : boolean
        If True, exclude the default unit (MW)
    """
    ylabels = {
        "German": {
            "invest": "neu installierte Kapazität",
            "old": "insgesamt stillgelegte Kapazität",
            "old_end": "wegen Lebensdauer stillgelegte Kapazität",
            "old_exo": "unter Berücksichtigung des Anlagenalters stillgelegte Kapazität",  # noqa: E501
            "total": "insgesamt installierte Kapazität",
            "all": "insgesamt vorhandene Kapazität",
            "potential": "Potenzial vs. investierte Kapazität",
            "generation": "Stromerzeugung in GWh/a",
        },
        "English": {
            "invest": "newly invested capacity",
            "old": "total decommissioned capacity",
            "old_end": "capacity decommissioned because of lifetime",
            "old_exo": "capacity decommissioned considering initial age",
            "total": "total installed capacity",
            "all": "overall installed capacity",
            "potential": "potential vs. realised capacity",
            "generation": "power generation in GWh/a",
        },
    }
    if group:
        plot_data = group_results(results, variable_name, aggregation)
    else:
        plot_data = results.copy()

    fig, ax = plt.subplots(figsize=figsize)
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
        place_legend_below=place_legend_below,
        bbox_params=bbox_params,
        ncol=ncol,
        language=language,
        exclude_unit=exclude_unit,
    )

    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(
            f"{path_plots}{filename}_{dr_scenario}.png",
            dpi=300,
            bbox_inches="tight",
        )
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
    place_legend_below=True,
    bbox_params=(0.5, -0.15),
    ncol=4,
    language="German",
    exclude_unit=False,
):
    """Create one single investment results plot"""
    x_label = {"German": "Jahr", "English": "year"}
    if not storage:
        if colors:
            plot_data = plot_data.loc[
                [col for col in colors if col in plot_data.index]
            ]
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
        handles, labels = ax.get_legend_handles_labels()

    else:
        options = [
            STORAGES_OTHER_RENAMED[language]["PHS_capacity"],
            STORAGES_OTHER_RENAMED[language]["battery_capacity"],
        ]
        ax2 = ax.twinx()
        energy_results = plot_data.loc[
            plot_data.index.get_level_values(0).isin(options)
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

        if draw_xlabel:
            ax.set_xlabel(x_label[language], labelpad=10)
        if draw_ylabel:
            _ = ax2.set_ylabel(
                f"{ylabels[language][variable_name]} in MWh", labelpad=10
            )

        handles, labels = [], []
        for ax_object in [ax, ax2]:
            h, l = ax_object.get_legend_handles_labels()
            handles.extend(h)
            labels.extend(l)

    if title:
        _ = ax.set_title(title)
    if legend:
        if place_legend_below:
            _ = plt.legend(
                handles,
                labels,
                loc="upper center",
                bbox_to_anchor=bbox_params,
                fancybox=True,
                shadow=False,
                ncol=ncol,
            )
        else:
            _ = plt.legend(handles, labels, bbox_to_anchor=bbox_params)

    if hide_axis:
        # _ = ax.get_xaxis().set_visible(False)  # show nothing
        _ = ax.set_xticklabels([])
        _ = ax.set_xlabel("")
    else:
        if draw_xlabel:
            _ = plt.xlabel(x_label[language], labelpad=10)
        else:
            ax.get_xaxis().label.set_visible(False)
        if draw_ylabel:
            if exclude_unit:
                _ = ax.set_ylabel(
                    f"{ylabels[language][variable_name]}", labelpad=10
                )
            else:
                _ = ax.set_ylabel(
                    f"{ylabels[language][variable_name]} in MW", labelpad=10
                )

    if ylim:
        _ = ax.set_ylim(ylim)
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
    dr_color_codes=None,
    save=False,
    filename="results",
    path_plots="./plots/",
    ylim=None,
    title="Demand Response scenario",
    format_axis=True,
    draw_ylabel=False,
    include_common_xlabel=True,
    fig_width=13,
    subplot_height=3,
    place_legend_below=True,
    bbox_params=(0.5, -0.45),
    ncol=4,
    language="German",
    include_common_legend=True,
    fig_position=0.13,
    exclude_unit=False,
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

    dr_color_codes : dict or None
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

    draw_ylabel : boolean
        If True, add ylabel to last subplot

    include_common_xlabel : boolean
        If True, draw a common xlabel

    fig_width : int
        Width of figure

    subplot_height : int
        height of a subplot

    place_legend_below : boolean
        If True, plot legend under plot, else right next to it

    bbox_params : tuple or list
        Define bbox_to_anchor content (for legend placed below)

    ncol : int
        Control the number of columns for the legend labels

    language : str
        Language to use (one of "German" and "English")

    include_common_legend : boolean
        If True, include a common x and y legend

    fig_position : float
        Location for x label

    exclude_unit : boolean
        If True, exclude the default unit (MW)
    """
    x_label = {"German": "Jahr", "English": "year"}
    ylabels = {
        "German": {
            "invest": "neu installierte Kapazität",
            "old": "insgesamt stillgelegte Kapazität",
            "old_end": "wegen Lebensdauer stillgelegte Kapazität",
            "old_exo": "unter Berücksichtigung des Anlagenalters stillgelegte Kapazität",
            "total": "insgesamt installierte Kapazität",
            "all": "insgesamt vorhandene Kapazität",
            "potential": "Potenzial vs. investierte Kapazität",
        },
        "English": {
            "invest": "newly invested capacity",
            "old": "total decommissioned capacity",
            "old_end": "capacity decommissioned because of lifetime",
            "old_exo": "capacity decommissioned considering initial age",
            "total": "total installed capacity",
            "all": "overall installed capacity",
            "potential": "potential vs. realised capacity",
        },
    }

    fig, axs = plt.subplots(
        len(results_dict),
        1,
        figsize=(fig_width, subplot_height * len(results_dict)),
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
            place_legend_below=place_legend_below,
            bbox_params=bbox_params,
            ncol=ncol,
            language=language,
            exclude_unit=exclude_unit,
        )

    # Use common axes across plot
    if storage:
        fig.text(
            1.01,
            0.55,
            f"{ylabels[language][variable_name]} in MWh",
            va="center",
            rotation="vertical",
        )
    xaxis_label_pos = 0.5
    if include_common_xlabel:
        if include_common_legend:
            fig.text(
                xaxis_label_pos, fig_position, x_label[language], ha="center"
            )
        else:
            fig.text(xaxis_label_pos, -0.01, x_label[language], ha="center")
    if include_common_legend:
        _ = plt.legend(
            loc="upper center",
            bbox_to_anchor=bbox_params,
            fancybox=True,
            shadow=False,
            ncol=ncol,
        )
    fig.text(
        -0.01,
        0.55,
        f"{ylabels[language][variable_name]} in MW",
        va="center",
        rotation="vertical",
    )

    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(
            f"{path_plots}{filename}_all_scenarios.png",
            dpi=300,
            bbox_inches="tight",
        )

    _ = plt.show()
    plt.close()


def plot_single_dispatch_pattern(
    dispatch_pattern,
    start_time_step,
    amount_of_time_steps,
    colors,
    title,
    save=True,
    path_plots="./plots/",
    filename="dispatch_pattern",
    kind="area",
    stacked=None,
    figsize=(15, 10),
    ylabel=None,
    linestyle=None,
    return_plot=False,
    place_legend_below=True,
    ncol=4,
    bbox_params=(0.5, -0.45),
    language="German",
    xtick_frequency=12,
    format_axis=True,
    dr_scenario=None,
    hide_legend_and_xlabel=False,
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

    title : str
        String to display in plot title

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

    ylabel : str
        String to use for labelling y label

    linestyle : dict
        Linestyles to use in case of a line plot

    return_plot : boolean
        If True, return plot before showing / saving

    place_legend_below : boolean
        If True, plot legend under plot, else right next to it

    ncol : int
        Control the number of columns for the legend labels

    bbox_params : tuple or list
        Define bbox_to_anchor content (for legend placed below)

    language : str
        Language for plot labels (one of "German" and "English")

    xtick_frequency : int
        Determine frequency of x ticks (12: plot every 12th x tick)

    format_axis : boolean
        If True, format thousands in y axis

    dr_scenario : str
        Demand response scenario considered

    hide_legend_and_xlabel : boolean
        Don't show legend and x label if True
    """
    index_start = int(dispatch_pattern.index.get_loc(start_time_step))
    index_end = int(index_start + amount_of_time_steps)
    end_time_step = dispatch_pattern.iloc[index_end].name

    to_plot = dispatch_pattern.iloc[index_start : index_end + 1]
    plot_labels = {
        "German": {
            "x_label": "Zeit",
            "y_label": "Energie in MWh/h",
            "title": f"{title} von {start_time_step} bis {end_time_step}",
        },
        "English": {
            "x_label": "time",
            "y_label": "energy in MWh/h",
            "title": f"{title} from {start_time_step} to {end_time_step}",
        },
    }

    fig, ax = plt.subplots(figsize=figsize)
    if kind == "bar" and stacked:
        _ = to_plot.plot(
            ax=ax, kind=kind, color=colors, stacked=stacked, legend=False
        )
    elif linestyle:
        for col in to_plot.columns:
            _ = to_plot[col].plot(
                ax=ax,
                kind=kind,
                color=colors[col],
                linestyle=linestyle[col],
                legend=False,
            )
    else:
        _ = to_plot.plot(ax=ax, kind=kind, color=colors, legend=False)
    if not hide_legend_and_xlabel:
        _ = ax.set_xlabel(plot_labels[language]["x_label"], labelpad=10)
    if not ylabel:
        ylabel = plot_labels[language]["y_label"]
    _ = ax.set_ylabel(ylabel, labelpad=10)
    _ = plt.title(plot_labels[language]["title"])
    if not hide_legend_and_xlabel:
        if place_legend_below:
            _ = plt.legend(
                loc="upper center",
                bbox_to_anchor=bbox_params,
                fancybox=True,
                shadow=False,
                ncol=ncol,
            )
        else:
            _ = plt.legend(bbox_to_anchor=[1.02, 1.05])

    _ = ax.set_xticks(range(0, len(to_plot.index), xtick_frequency))
    _ = ax.set_xticklabels(
        [label[:16] for label in to_plot.index[::xtick_frequency]],
        rotation=90,
        ha="center",
    )
    _ = plt.margins(0, 0.05)
    if return_plot:
        if save:
            print("Did not save, but return plot.")
        return fig, ax

    if format_axis:
        _ = ax.get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, p: format(int(x), ","))
        )

    _ = plt.tight_layout()

    if save:
        file_name_out = (
            f"{path_plots}{filename}_{dr_scenario}_"
            f"{start_time_step}-{end_time_step}.png"
        )
        file_name_out = file_name_out.replace(":", "-").replace(" ", "_")
        file_name_out.replace(":", "-")
        _ = plt.savefig(file_name_out, dpi=300, bbox_inches="tight")

    _ = plt.show()
    plt.close()


def add_area_to_existing_plot(
    data,
    start_time_step,
    amount_of_time_steps,
    colors,
    ax,
    save=True,
    path_plots="./plots/",
    filename="area_plot",
    place_legend_below=True,
    ncol=4,
    bbox_params=(0.5, -0.45),
):
    """Add a stacked area to plot

    Parameters
    ----------
    data : pd.DataFrame
        Data to plot

    start_time_step : str
        First time step of excerpt displayed

    amount_of_time_steps : int or float
        Number of time steps to be displayed

    colors : Dict
        Colors to use

    ax : matplotlib.axes.Axes
        matplotlib axes object

    save : bool
        Indicates whether to save the plot

    path_plots : str
        Path to use for storing the plot

    filename : str
        File name to use for the plot

    place_legend_below : boolean
        If True, plot legend under plot, else right next to it

    ncol : int
        Control the number of columns for the legend labels

    bbox_params : tuple or list
        Define bbox_to_anchor content (for legend placed below)
    """
    index_start = int(data.index.get_loc(start_time_step))
    index_end = int(index_start + amount_of_time_steps)
    end_time_step = data.iloc[index_end].name

    to_plot = data.rename(columns=lambda x: "_" + x).iloc[
        index_start : index_end + 1
    ]
    _ = to_plot.plot(
        kind="area",
        color={"_" + x: color for x, color in colors.items()},
        alpha=0.3,
        ax=ax,
        legend=False,
    )
    _ = ax.set_xticks(range(0, len(to_plot.index), 12))
    _ = ax.set_xticklabels(
        [label[:16] for label in to_plot.index[::12]], rotation=90, ha="center"
    )
    if place_legend_below:
        _ = plt.legend(
            loc="upper center",
            bbox_to_anchor=bbox_params,
            fancybox=True,
            shadow=False,
            ncol=ncol,
        )
    else:
        _ = plt.legend(bbox_to_anchor=[1.02, 1.05])
    _ = plt.tight_layout()

    if save:
        file_name_out = (
            f"{path_plots}{filename}_{start_time_step}-{end_time_step}.png"
        )
        file_name_out = file_name_out.replace(":", "-").replace(" ", "_")
        file_name_out.replace(":", "-")
        _ = plt.savefig(file_name_out, dpi=300, bbox_inches="tight")

    _ = plt.show()
    plt.close()


def plot_generation_and_comsumption_pattern(
    data,
    start_time_step,
    amount_of_time_steps,
    colors,
    title,
    figsize=(15, 10),
    kind="area",
    ylabel=None,
    save=True,
    single_hour=False,
    path_plots="./plots/",
    filename="dispatch_pattern",
    place_legend_below=True,
    ncol=4,
    bbox_params=(0.5, -0.25),
    language="German",
    xtick_frequency=12,
    format_axis=True,
    dr_scenario=None,
    hide_legend_and_xlabel=False,
):
    """Plot combined generation and consumption pattern as stacked are chart

    Generation is depicted in the positive range;
    consumption in the negative range

    Solution taken from this stackoverflow issue:
    https://stackoverflow.com/questions/52872938/stacked-area-plot-in-python-with-positive-and-negative-values,
    accessed 11.12.2023

    Parameters
    ----------
    data : pd.DataFrame
        Data for plotting

    start_time_step : str
        First time step of excerpt displayed

    amount_of_time_steps : int or float
        Number of time steps to be displayed

    colors : dict
        Colors to use for the plot

    title : str
        String to display in plot title

    figsize : tuple of int
        Size of plot

    kind : str
        Kind of plot to generate (area or bar)

    ylabel : str
        String to use for labelling y label

    save : bool
        Indicates whether to save the plot

    single_hour : bool
        If True, adapt title to relect single hour dispatch situation

    path_plots : str
        Path to use for storing the plot

    filename : str
        File name to use for the plot

    place_legend_below : boolean
        If True, plot legend under plot, else right next to it

    ncol : int
        Control the number of columns for the legend labels

    bbox_params : tuple or list
        Define bbox_to_anchor content (for legend placed below)

    language : str
        Language for plot labels (one of "German" and "English")

    xtick_frequency : int
        Determine frequency of x ticks (12: plot every 12th x tick)

    format_axis : boolean
        If True, format thousands in y axis

    dr_scenario: str
        Demand response scenario considered

    hide_legend_and_xlabel : boolean
        Don't show legend and x label if True
    """
    index_start = int(data.index.get_loc(start_time_step))
    index_end = int(index_start + amount_of_time_steps)
    end_time_step = data.iloc[index_end].name
    data = data.iloc[index_start : index_end + 1]
    plot_labels = {
        "German": {
            "x_label": "Zeit",
            "y_label": "Energie in MWh/h",
            "title_span": f"{title} von {start_time_step} bis {end_time_step}",
            "title_step": f"{title} für {start_time_step}",
        },
        "English": {
            "x_label": "time",
            "y_label": "energy in MWh/h",
            "title_span": f"{title} from {start_time_step} to {end_time_step}",
            "title_step": f"{title} for {start_time_step}",
        },
    }

    fig, ax = plt.subplots(figsize=figsize)
    df_neg, df_pos = data.clip(upper=0), data.clip(lower=0)
    _ = df_pos.plot(
        kind=kind,
        ax=ax,
        stacked=True,
        linewidth=0.0,
        color=colors,
        legend=False,
    )
    _ = ax.set_prop_cycle(None)
    _ = df_neg.rename(columns=lambda x: "_" + x).plot(
        kind=kind,
        ax=ax,
        stacked=True,
        linewidth=0.0,
        color={"_" + k: v for k, v in colors.items()},
        legend=False,
    )
    _ = ax.set_ylim(
        [df_neg.sum(axis=1).min() * 1.05, df_pos.sum(axis=1).max() * 1.05]
    )
    _ = ax.set_xticks(range(0, len(data.index), xtick_frequency))
    _ = ax.set_xticklabels(
        [label[:16] for label in data.index[::xtick_frequency]],
        rotation=90,
        ha="center",
    )
    if not hide_legend_and_xlabel:
        _ = ax.set_xlabel(plot_labels[language]["x_label"], labelpad=10)
    if not ylabel:
        ylabel = plot_labels[language]["y_label"]
    _ = ax.set_ylabel(ylabel, labelpad=10)
    if single_hour:
        title = plot_labels[language]["title_step"]
    else:
        title = plot_labels[language]["title_span"]
    _ = plt.title(title)
    _ = plt.xticks(rotation=90)
    _ = plt.margins(0)

    if not hide_legend_and_xlabel:
        if place_legend_below:
            _ = plt.legend(
                loc="upper center",
                bbox_to_anchor=bbox_params,
                fancybox=True,
                shadow=False,
                ncol=ncol,
            )
        else:
            _ = plt.legend(bbox_to_anchor=bbox_params)

    if format_axis:
        _ = ax.get_yaxis().set_major_formatter(
            FuncFormatter(lambda x, p: format(int(x), ","))
        )

    _ = plt.tight_layout()

    if save:
        file_name_out = (
            f"{path_plots}{filename}_{dr_scenario}_"
            f"{start_time_step}-{end_time_step}.png"
        )
        file_name_out = file_name_out.replace(":", "-").replace(" ", "_")
        file_name_out.replace(":", "-")
        _ = plt.savefig(file_name_out, dpi=300, bbox_inches="tight")

    _ = plt.show()
    plt.close()


def plot_generation_and_consumption_for_all_cases(
    data_dict,
    start_time_steps,
    amount_of_time_steps,
    colors,
    fig_height=15,
    subplot_width=4,
    save=True,
    path_plots="./plots/",
    filename="dispatch_pattern",
    place_legend_below=True,
    ncol=4,
    bbox_params=(0.5, -0.25),
    language="German",
    wspace=0.5,
    y_label_pos=(-0.01, 0.55),
    format_axis=True,
    dr_scenario=None,
    hide_legend_and_xlabel=False,
):
    """Plot bar plots for exemplary dispatch situation next to each other

    Parameters
    ----------
    data_dict : dict of pd.DataFrame
        Data for plotting (given per case)

    start_time_steps : dict of str
        First time step of excerpt displayed

    amount_of_time_steps : int or float
        Number of time steps to be displayed

    colors : dict
        Colors to use for the plot

    fig_height : int
        Overall height of the figure

    subplot_width : int
        Width of subplot element

    save : bool
        Indicates whether to save the plot

    path_plots : str
        Path to use for storing the plot

    filename : str
        File name to use for the plot

    place_legend_below : boolean
        If True, plot legend under plot, else right next to it

    ncol : int
        Control the number of columns for the legend labels

    bbox_params : tuple or list
        Define bbox_to_anchor content (for legend placed below)

    language : str
        Language for plot labels (one of "German" and "English")

    wspace : float
        Manually configure spacing between subplots

    y_label_pos : tuple
        Adjust position of common y axis label

    format_axis : boolean
        If True, format thousands in y axis

    dr_scenario: str
        Demand response scenario considered

    hide_legend_and_xlabel : boolean
        Don't show legend and x label if True
    """
    plot_labels = {
        "German": {
            "y_label": "Energie in MWh/h",
        },
        "English": {
            "y_label": "energy in MWh/h",
        },
    }

    fig, axs = plt.subplots(
        1,
        len(data_dict),
        figsize=(subplot_width * len(data_dict), fig_height),
        gridspec_kw={"wspace": wspace},
    )
    for number, item in enumerate(data_dict.items()):
        key = item[0]
        data = item[1]

        index_start = int(data.index.get_loc(start_time_steps[key]))
        index_end = int(index_start + amount_of_time_steps)
        data = data.iloc[index_start : index_end + 1]

        df_neg, df_pos = data.clip(upper=0), data.clip(lower=0)
        _ = df_pos.plot(
            kind="bar",
            ax=axs[number],
            stacked=True,
            linewidth=0.0,
            color=colors,
            legend=False,
        )
        _ = axs[number].set_prop_cycle(None)
        _ = df_neg.rename(columns=lambda x: "_" + x).plot(
            kind="bar",
            ax=axs[number],
            stacked=True,
            linewidth=0.0,
            color={"_" + k: v for k, v in colors.items()},
            legend=False,
        )
        _ = axs[number].set_xticklabels(
            [f"DR {key} -\n{label[:16]}" for label in data.index],
            rotation=90,
            ha="center",
        )

        _ = axs[number].set_ylim(
            [df_neg.sum(axis=1).min() * 1.05, df_pos.sum(axis=1).max() * 1.05]
        )
        _ = plt.margins(0)

        if format_axis:
            _ = (
                axs[number]
                .get_yaxis()
                .set_major_formatter(
                    FuncFormatter(lambda x, p: format(int(x), ","))
                )
            )

    if not hide_legend_and_xlabel:
        if place_legend_below:
            _ = plt.legend(
                loc="lower center",
                bbox_to_anchor=bbox_params,
                fancybox=True,
                shadow=False,
                ncol=ncol,
            )
        else:
            _ = plt.legend(bbox_to_anchor=bbox_params)

    fig.text(
        y_label_pos[0],
        y_label_pos[1],
        f"{plot_labels[language]['y_label']}",
        va="center",
        rotation="vertical",
    )

    _ = plt.tight_layout()

    if save:
        file_name_out = (
            f"{path_plots}{filename}_scenario_comparison.png"
        )
        file_name_out = file_name_out.replace(":", "-").replace(" ", "_")
        file_name_out.replace(":", "-")
        _ = plt.savefig(file_name_out, dpi=300, bbox_inches="tight")

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
