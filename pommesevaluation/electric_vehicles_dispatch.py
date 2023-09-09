import matplotlib.pyplot as plt


def draw_ev_dispatch_plot(
    data,
    color,
    title,
    ylim=None,
    show=False,
    save=True,
    path_plots="./plots/",
    file_name="ev_dispatch",
    figsize=(20, 10),
):
    """Plot dispatch pattern

    Parameters
    ----------
    data : pd.DataFrame
        dispatch data to be plotted

    color : list
        Colors to be used

    title : str
        Title of the plot

    ylim : list
        y axis limits (lower, upper)

    show : boolean
        If True, show the plot

    save : boolean
        If True, save the plot to disk

    file_name : str
        File name for saving the plot

    figsize : tuple
        Control the size of the figure created
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax = data.plot(color=color, ax=ax)
    _ = plt.ylabel("Dispatch in MWh/h")
    _ = plt.title(title)
    _ = ax.legend(loc="upper right")
    _ = plt.xlabel("time")
    _ = plt.xticks(rotation=45)

    if ylim is not None:
        _ = plt.axis(ymin=ylim[0], ymax=ylim[1])

    _ = plt.tight_layout()

    if save:
        plt.savefig(f"{path_plots}{file_name}.png", dpi=300)
    if show:
        plt.show()

    plt.close()


def draw_weekly_plot(
    data,
    simulation_year,
    color=None,
    ylim=None,
    file_name=None,
):
    """Draw weekly ev dispatch plots

    Parameters
    ----------
    simulation_year : int
        Year simulated

    data : pd.DataFrame
        data to be plotted

    color : list or str
        Color(s) to be used

    ylim: list
        y axis limits

    file_name: str or none
        File name pattern to apply for weekly plots
    """
    if not file_name:
        file_name = "dispatch"

    for week in range(52):
        title = f"Dispatch pattern for {simulation_year} in week: {week + 1}"

        draw_ev_dispatch_plot(
            data=data.iloc[week * 168 : (week + 1) * 168 + 1],
            color=color,
            title=title,
            ylim=ylim,
            show=False,
            save=True,
            file_name=f"{file_name}_{simulation_year}_week_{week + 1}",
        )
