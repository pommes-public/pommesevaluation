import pandas as pd


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
