"""Determine commonly used global variables:

Define color codes and renaming

@author Johannes Kochems
"""

FUELS = {
    "biomass": "#15b01a",
    "uranium": "#e50000",
    "lignite": "#7f2b0a",
    "hardcoal": "#000000",
    "natgas": "#ffd966",
    "hydrogen": "#6fa8dc",
    "mixedfuels": "#a57e52",
    "otherfossil": "#d8dcd6",
    "waste": "#c04e01",
    "oil": "#aaa662",
}

FUELS_RENAMED = {
    "German": {
        "biomass": "Biomasse",
        "uranium": "Kernenergie",
        "lignite": "Braunkohle",
        "hardcoal": "Steinkohle",
        "natgas": "Erdgas",
        "hydrogen": "Wasserstoff",
        "mixedfuels": "gemischte Brennstoffe",
        "otherfossil": "sonstige Konventionelle",
        "waste": "Abfall",
        "oil": "Erdöl",
    },
    "English": {
        "biomass": "biomass",
        "uranium": "uranium",
        "lignite": "lignite",
        "hardcoal": "hard coal",
        "natgas": "natural gas",
        "hydrogen": "hydrogen",
        "mixedfuels": "mixed conventionals",
        "otherfossil": "other conventionals",
        "waste": "waste",
        "oil": "oil",
    },
}

RES = {
    "DE_source_solarPV": "#fcb001",
    "DE_source_windonshore": "#82cafc",
    "DE_source_windoffshore": "#0504aa",
    "DE_source_biomassEEG": "#15b01a",
    "DE_source_ROR": "#c79fef",
    "other RES": "#757575",
    "DE_source_landfillgas": "#06c2ac",
    "DE_source_geothermal": "#ff474c",
    "DE_source_minegas": "#650021",
    "DE_source_larga": "#ad8150",
}

RES_TO_GROUP = {
    "other RES": [
        "DE_source_landfillgas",
        "DE_source_geothermal",
        "DE_source_minegas",
        "DE_source_larga",
    ]
}

RES_RENAMED = {
    "German": {
        "DE_source_solarPV": "Solarenergie",
        "DE_source_windoffshore": "Wind offshore",
        "DE_source_windonshore": "Wind onshore",
        "DE_source_biomassEEG": "Biomasse",
        "DE_source_ROR": "Laufwasser",
        "DE_source_landfillgas": "Deponiegas",
        "DE_source_geothermal": "Geothermie",
        "DE_source_minegas": "Grubengas",
        "DE_source_larga": "Klärgas",
        "other RES": "andere Erneuerbare",
    },
    "English": {
        "DE_source_solarPV": "solar PV",
        "DE_source_windoffshore": "wind offshore",
        "DE_source_windonshore": "wind onshore",
        "DE_source_biomassEEG": "biomass",
        "DE_source_ROR": "run of river",
        "DE_source_landfillgas": "landfillgas",
        "DE_source_geothermal": "geothermal",
        "DE_source_minegas": "minegas",
        "DE_source_larga": "sewage gas",
        "other RES": "other RES",
    },
}

STORAGES = {
    "PHS": "#0c2aac",
    "battery": "#f7e09a",
}

STORAGES_RENAMED = {
    "German": {
        "PHS": "Pumpspeicher",
        "battery": "Batterien",
    },
    "English": {
        "PHS": "pumped hydro",
        "battery": "battery",
    },
}

STORAGES_NEW = {
    "PHS_new_built": "#7c90e7",
    "battery_new_built": "#fff5d5",
}

STORAGES_NEW_RENAMED = {
    "German": {
        "PHS_new_built": "Pumpspeicher",
        "battery_new_built": "Batterien",
    },
    "English": {
        "PHS_new_built": "pumped hydro",
        "battery_new_built": "battery",
    },
}

DEMAND_RESPONSE = {
    "hoho_cluster_shift_only": "#111111",
    "hoho_cluster_shift_shed": "#444444",
    "ind_cluster_shed_only": "#666666",
    "ind_cluster_shift_only": "#aaaaaa",
    "ind_cluster_shift_shed": "#cccccc",
    "tcs+hoho_cluster_shift_only": "#dddddd",
    "tcs_cluster_shift_only": "#eeeeee",
}

DEMAND_RESPONSE_RENAMED = {
    "German": {
        "hoho_cluster_shift_only": "Haushalte - Verschiebung",
        "hoho_cluster_shift_shed": "Haushalte - Verschiebung & Verzicht",
        "ind_cluster_shed_only": "Industrie - Verzicht",
        "ind_cluster_shift_only": "Industrie - Verschiebung",
        "ind_cluster_shift_shed": "Industrie - Verschiebung & Verzicht",
        "tcs+hoho_cluster_shift_only": "GHD & Haushalte - Verschiebung",
        "tcs_cluster_shift_only": "GHD - Verschiebung",
    },
    "English": {
        "hoho_cluster_shift_only": "households - shifting",
        "hoho_cluster_shift_shed": "households - shifting & shedding",
        "ind_cluster_shed_only": "industry - shedding",
        "ind_cluster_shift_only": "industry - shifting",
        "ind_cluster_shift_shed": "industry - shifting & shedding",
        "tcs+hoho_cluster_shift_only": "tcs & households - shifting",
        "tcs_cluster_shift_only": "tcs - shifting",
    }
}
