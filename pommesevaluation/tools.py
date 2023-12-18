import matplotlib.pyplot as plt


def update_matplotlib_params(
    small_size: int, medium_size: int, large_size: int
):
    """Update matplotlib font size params according to given specification"""
    plt.rc("font", size=small_size)  # controls default text sizes
    plt.rc("axes", titlesize=large_size)  # fontsize of the axes title
    plt.rc("axes", labelsize=medium_size)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=small_size)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=small_size)  # fontsize of the tick labels
    plt.rc("legend", fontsize=small_size)  # legend fontsize
    plt.rc("figure", titlesize=large_size)  # fontsize of the figure title
