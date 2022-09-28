import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter


def preprocess_raw_results(results_raw):
    """Preprocess raw investment results

    Parameters
    ----------
    results_raw : pd.DataFrame
        Raw investment results

    Returns
    -------
    processed_results : pd.DataFrame
        Preprocessed investment results
    """
    processed_results = results_raw.copy()
    processed_results.index = processed_results.index.str.split(expand=True)
    processed_results.index.names = ["from", "to", "year"]
    processed_results.reset_index(inplace=True)
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
        & (processed_results["to"].str.contains("DE_bus_el")),
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

    processed_results = processed_results.rename(
        columns={"from": "unit"}
    ).drop(columns="to")
    string_to_drop = ["DE_storage_el_", "DE_transformer_", "_new_built"]
    for string in string_to_drop:
        processed_results["unit"] = processed_results["unit"].str.replace(
            string, ""
        )

    return processed_results


def aggregate_investment_decision_results(
    processed_results, energy_carriers, by="energy_carrier"
):
    """Aggregate preprocesed investment results by energy carrier or technology

    Parameters
    ----------
    processed_results : pd.DataFrame
        Preprocessed investment results

    energy_carriers : list
        List of feasible energy carriers

    by : str
        Rule to group by; either `energy_carrier` or `technologies`

    Returns
    -------
    aggregated_results : pd.DataFrame
        Aggregated results incl. investments in storage inflow

    other_storages_results : pd.DataFrame
        Results for investments in storage capacity and storage outflow
    """
    aggregated_results = processed_results.copy()
    aggregated_results[["fuel", "tech"]] = aggregated_results[
        "unit"
    ].str.split("_", 1, expand=True)

    storage_technologies = ["PHS", "battery"]
    storage_elements = ["_capacity", "_outflow"]
    storages = [a + b for a in storage_technologies for b in storage_elements]

    technologies = r"GT|ST|CC|FC"

    grouping_col = by
    if by == "energy_carrier":
        aggregated_results["energy_carrier"] = np.where(
            aggregated_results["fuel"].isin(energy_carriers),
            aggregated_results["fuel"],
            aggregated_results["unit"],
        )

    elif by == "technology":
        aggregated_results["technology"] = np.where(
            aggregated_results["tech"].str.contains(technologies),
            aggregated_results["tech"].str.split("_", expand=True).iloc[:, 0],
            aggregated_results["unit"],
        )
    else:
        raise ValueError(
            f"Aggregation mode {by} not defined; "
            f"must be `energy_carrier` or `technologies`."
        )

    aggregated_results = aggregated_results.groupby(
        [grouping_col, "year"]
    ).sum()

    other_storages_results = aggregated_results.loc[[idx for idx in storages]]
    aggregated_results.drop(index=other_storages_results.index, inplace=True)

    return aggregated_results, other_storages_results


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
    """
    ylabels = {
        "invest": "newly invested capacity",
        "old": "total decommissioned capacity",
        "old_end": "capacity decommissioned because of lifetime",
        "old_exo": "capacity decommissioned because after initial age",
        "total": "total installed capacity",
        "all": "overall installed capacity",
    }
    if group:
        plot_data = group_results(results, variable_name, aggregation)
    else:
        plot_data = results.copy()

    fig, ax = plt.subplots(figsize=(12, 5))
    create_single_plot(plot_data, variable_name, colors, storage, ax, ylabels)

    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(f"{path_plots}{filename}_{dr_scenario}.png", dpi=300)
        plot_data.to_csv(f"{path_data_out}{filename}_{dr_scenario}.csv")

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
    """
    plot_data = results[[variable_name]].reset_index()
    plot_data = plot_data.pivot(
        index=aggregation, columns="year", values=variable_name
    )

    return plot_data


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

        if not hide_axis:
            _ = ax2.set_ylabel(f"{ylabels[variable_name]} in MWh")

    if title:
        _ = ax.set_title(title)
    if legend:
        _ = plt.legend(bbox_to_anchor=[1.1, 1.02])

    if hide_axis:
        _ = ax.get_xaxis().set_visible(False)
    else:
        _ = plt.xlabel("year")
        _ = ax.set_ylabel(f"{ylabels[variable_name]} in MW")

    if ylim:
        _ = ax.set_ylim(ylim)
    # current_values = plt.gca().get_yticks()
    # _ = plt.gca().set_yticklabels(
    #     ["{:,.0f}".format(x) for x in current_values]
    # )
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
    """
    ylabels = {
        "invest": "newly invested capacity",
        "old": "total decommissioned capacity",
        "old_end": "capacity decommissioned because of lifetime",
        "old_exo": "capacity decommissioned because after initial age",
        "total": "total installed capacity",
        "all": "overall installed capacity",
    }

    fig, axs = plt.subplots(
        len(results_dict), 1, figsize=(12, 3 * len(results_dict))
    )
    hide_axis = True
    for number, item in enumerate(results_dict.items()):
        if number == len(results_dict) - 1:
            hide_axis = False

        dr_scenario = item[0]
        results = item[1]

        colors_copy = colors.copy()
        if dr_scenario is "none":
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
            title=f"Demand Response scenario {dr_scenario}",
            legend=False,
            hide_axis=hide_axis,
            ylim=ylim,
        )

    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(f"{path_plots}{filename}_all_scenarios.png", dpi=300)

    _ = plt.show()
    plt.close()
