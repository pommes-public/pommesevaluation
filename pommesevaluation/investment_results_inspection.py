import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


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

    energy_carriers = energy_carriers
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
):
    """Plot a single investment-related variable from results data set

    Parameters
    ----------
    results : pd.DataFrame
        Data set containing all investment results

    variable_name : str
        Particular variable to plot;
        one of ['invest', 'old', 'old_end', 'old_exo', 'total']

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
        plot_data = results[[variable_name]].reset_index()
        plot_data = plot_data.pivot(
            index=aggregation, columns="year", values=variable_name
        )
    else:
        plot_data = results.copy()
    fig, ax = plt.subplots(figsize=(12, 5))
    if not storage:
        if colors:
            plot_data = plot_data.loc[[col for col in colors]]
            _ = plot_data.T.plot(kind="bar", stacked=True, ax=ax, color=colors)
        else:
            _ = plot_data.T.plot(kind="bar", stacked=True, ax=ax)

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

        _ = ax2.set_ylabel(f"{ylabels[variable_name]} in MWh")

    _ = plt.legend(bbox_to_anchor=[1.1, 1.02])
    _ = plt.xlabel("year")
    current_values = plt.gca().get_yticks()
    _ = plt.gca().set_yticklabels(
        ["{:,.0f}".format(x) for x in current_values]
    )
    _ = ax.set_ylabel(f"{ylabels[variable_name]} in MW")
    _ = plt.tight_layout()
    _ = plt.show()
