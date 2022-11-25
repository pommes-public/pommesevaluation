from matplotlib import pyplot as plt


def plot_combined_dispatch_and_price_plot(
    start_time_step,
    end_time_step,
    simulation_year,
    dispatch_df,
    prices_df,
    color,
    figsize=(15, 10),
    dispatch_limits=None,
    price_limits=None,
    path_plots="./plots/",
    file_name_suffix="",
):
    """Draw a combined dispatch and price plot"""
    fig, ax = plt.subplots(figsize=figsize)

    if not dispatch_limits:
        dispatch_limits = {"bottom": -20000, "top": 100000}

    if not price_limits:
        price_limits = {"bottom": -100, "top": 40}

    _ = dispatch_df.plot(
        ax=ax, kind="area", color=color["dispatch"], alpha=0.5, legend=False
    )
    _ = ax.set_xlabel("Time")
    _ = ax.set_ylabel("Energy [MWh/h]")
    _ = ax.set_ylim(
        bottom=dispatch_limits["bottom"], top=dispatch_limits["top"]
    )
    current_values = plt.gca().get_yticks()
    plt.gca().set_yticklabels(["{:,.0f}".format(x) for x in current_values])

    _ = prices_df.plot(
        secondary_y=True,
        ax=ax,
        color=color["power_prices"],
        linewidth=3,
        legend=False,
    )
    _ = ax.right_ax.set_ylim(
        bottom=price_limits["bottom"], top=price_limits["top"]
    )
    _ = ax.right_ax.set_ylabel("Power price [€/MWh]")

    _ = plt.title(
        f"Dispatch and price situation between {start_time_step} and {end_time_step}"
    )

    # Create the legend
    fig.legend(
        loc="upper right",
        bbox_to_anchor=[1, 0.88],
        borderaxespad=0.1,
    )

    _ = plt.subplots_adjust(right=0.75)
    # _ = plt.tight_layout(rect=[0, 0, 0.75, 1])
    _ = plt.savefig(
        f"{path_plots}excess_situation_{simulation_year}{file_name_suffix}.png", dpi=300
    )

    plt.show()
    plt.close()
