import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_entsoe_german_generation_data(path="./data/production/", year=2017):
    """Load generation for Germany, handle time shift and resample to hourly

    Parameters
    ----------
    path : str
        relative path to the input file

    year : int
        Year for which to evaluate generation
    """
    if year in range(2017, 2022):
        filename = f"entsoe_generation_DE_{year}0101-{year + 1}0101.csv"
    else:
        msg = f"year must be between 2017 and 2021. You specified {year}"
        raise ValueError(msg)

    generation = pd.read_csv(path + filename, index_col=1)
    generation.drop(columns="Area", inplace=True)
    # Columns for hour 2B are left empty; drop for time shift consideration
    generation = generation.dropna(how="all")

    generation.index = pd.date_range(
        start=f"{year}-01-01 00:00:00",
        end=f"{year}-12-31 23:45:00",
        freq="15min",
    )
    generation = generation.resample("H").mean()

    column_names = {
        "Biomass  - Actual Aggregated [MW]": "biomass",
        "Nuclear  - Actual Aggregated [MW]": "uranium",
        "Fossil Brown coal/Lignite  - Actual Aggregated [MW]": "lignite",
        "Fossil Hard coal  - Actual Aggregated [MW]": "hardcoal",
        "Fossil Gas  - Actual Aggregated [MW]": "natgas",
        "Fossil Coal-derived gas  - Actual Aggregated [MW]": "minegas",
        "Fossil Oil  - Actual Aggregated [MW]": "oil",
        "Fossil Oil shale  - Actual Aggregated [MW]": "shale_oil",
        "Fossil Peat  - Actual Aggregated [MW]": "peat",
        "Geothermal  - Actual Aggregated [MW]": "geothermal",
        "Hydro Pumped Storage  - Actual Aggregated [MW]": "storage_el_out",
        "Hydro Run-of-river and poundage  - Actual Aggregated [MW]": "ROR",
        "Hydro Water Reservoir  - Actual Aggregated [MW]": "reservoir",
        "Other  - Actual Aggregated [MW]": "otherfossil",
        "Other renewable  - Actual Aggregated [MW]": "otherrenewables",
        "Solar  - Actual Aggregated [MW]": "solarPV",
        "Waste  - Actual Aggregated [MW]": "waste",
        "Wind Offshore  - Actual Aggregated [MW]": "windoffshore",
        "Wind Onshore  - Actual Aggregated [MW]": "windonshore",
    }

    generation.rename(
        columns=column_names,
        inplace=True,
    )

    generation.drop(
        columns=[col for col in generation.columns if col not in column_names.values()],
        inplace=True,
    )

    return generation


def plot_imports_and_exports(im_ex_data, country_colors_im_ex, start, end, save=True, path_plots="./plots/", file_name="imports_and_exports"):
    """Plot an area plot of imports and exports

    Parameters
    ----------
    im_ex_data : pd.DataFrame
        Imports and exports DataFrame

    country_colors_im_ex : dict
        Dictionary assigning colors for the plot

    start : str
        Start time

    end : str
        End time
    """
    fig, ax = plt.subplots(figsize=(15, 5))
    _ = im_ex_data.loc[start:end].plot(kind="area", ax=ax, color=country_colors_im_ex)
    _ = ax.set_title("Imports and exports breakdown")
    _ = ax.set_xlabel("Time")
    _ = ax.set_ylabel("Energy in MWh")
    _ = plt.legend(bbox_to_anchor=[1.02, 1.05])
    _ = plt.tight_layout()

    if save:
        _ = plt.savefig(f"{path_plots}{file_name}.png", dpi=300)

    plt.show()


def read_and_reshape_historical_im_ex(
    path="./data/production/", simulation_year=2017, file_name=None
):
    """Read in historical imports and exports from SMARD and reshape data to hourly format

    Parameters
    ----------
    path : str
        path where input file is stored

    simulation_year : int
        year between 2017 and 2021 (inclusive)

    file_name : NoneType or str
        Name of the file to be read in
    """
    if simulation_year in [2018, 2019, 2021]:
        date_cols = {"date": "Datum", "time": "Uhrzeit"}
    else:
        date_cols = {"date": "Date", "time": "Time of day"}
    if file_name is None:
        file_name = f"Kommerzieller_Au_enhandel_{simulation_year}01010000_{simulation_year}12312359.xlsx"

    df = pd.read_excel(
        path + file_name,
        engine="openpyxl",
        skiprows=6,
    )
    df["Datestamp"] = pd.to_datetime(
        df.loc[:, date_cols["date"]] + " " + df.loc[:, date_cols["time"]]
    )
    df["hour_type"] = np.where(~df["Datestamp"].duplicated(), "a", "b")
    grouped_df = df.groupby(
        [
            df["Datestamp"].dt.month,
            df["Datestamp"].dt.day,
            df["Datestamp"].dt.hour,
            df["hour_type"],
        ]
    ).agg(
        {
            date_cols["date"]: "first",
            date_cols["time"]: "first",
            **{
                col: "sum"
                for col in df.columns
                if col not in [date_cols["date"], date_cols["time"], "Datestamp"]
            },
        }
    )
    grouped_df["time"] = pd.date_range(
        start=f"{simulation_year}-01-01 00:00:00", periods=len(grouped_df), freq="H"
    ).astype(str)
    grouped_df = grouped_df.set_index("time").drop(
        columns=[date_cols["date"], date_cols["time"], "hour_type"]
    )
    grouped_df.rename(
        columns={
            "Nettoexport[MWh]": "overall_net_export",
            "Dänemark 1 (Export)[MWh]": "net_export_DK1_pos",
            "Dänemark 1 (Import)[MWh]": "net_export_DK1_neg",
            "Dänemark 2 (Export)[MWh]": "net_export_DK2_pos",
            "Dänemark 2 (Import)[MWh]": "net_export_DK2_neg",
            "Niederlande (Export)[MWh]": "net_export_NL_pos",
            "Niederlande (Import)[MWh]": "net_export_NL_neg",
            "Italien Nord (Export)[MWh]": "net_export_IT_pos",
            "Italien Nord (Import)[MWh]": "net_export_IT_neg",
            "Schweiz (Export)[MWh]": "net_export_CH_pos",
            "Schweiz (Import)[MWh]": "net_export_CH_neg",
            "Tschechien (Export)[MWh]": "net_export_CZ_pos",
            "Tschechien (Import)[MWh]": "net_export_CZ_neg",
            "Frankreich (Export)[MWh]": "net_export_FR_pos",
            "Frankreich (Import)[MWh]": "net_export_FR_neg",
            "Schweden 4 (Export)[MWh]": "net_export_SE4_pos",
            "Schweden 4 (Import)[MWh]": "net_export_SE4_neg",
            "Ungarn (Export)[MWh]": "net_export_HU_pos",
            "Ungarn (Import)[MWh]": "net_export_HU_neg",
            "Slowenien (Export)[MWh]": "net_export_SL_pos",
            "Slowenien (Import)[MWh]": "net_export_SL_neg",
            "Polen (Export)[MWh]": "net_export_PL_pos",
            "Polen (Import)[MWh]": "net_export_PL_neg",
            "Österreich (Export)[MWh]": "net_export_AT_pos",
            "Österreich (Import)[MWh]": "net_export_AT_neg",
            "Norwegen 2 (Export)[MWh]": "net_export_NO2_pos",
            "Norwegen 2 (Import)[MWh]": "net_export_NO2_neg",
            "Belgien (Export)[MWh]": "net_export_BE_pos",
            "Belgien (Import)[MWh]": "net_export_BE_neg",
        },
        inplace=True,
    )

    return grouped_df
