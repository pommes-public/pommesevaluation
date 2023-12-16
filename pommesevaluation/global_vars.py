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

STORAGES_TO_GROUP = {
    "PHS": ["PHS", "PHS_new_built"]
}

STORAGES_OTHER = {
    **{f"{stor}_outflow": STORAGES[stor] for stor in STORAGES},
    **{f"{stor}_capacity": STORAGES[stor] for stor in STORAGES},
}
STORAGES_OTHER_RENAMED = {
    "German": {
        **{
            f"{stor}_outflow": STORAGES_RENAMED["German"][stor]
            + " - Ausspeisung"
            for stor in STORAGES
        },
        **{
            f"{stor}_capacity": STORAGES_RENAMED["German"][stor]
            + " - Kapazität"
            for stor in STORAGES
        },
    },
    "English": {
        **{
            f"{stor}_outflow": STORAGES_RENAMED["English"][stor] + " - outflow"
            for stor in STORAGES
        },
        **{
            f"{stor}_capacity": STORAGES_RENAMED["English"][stor]
            + " - capacity"
            for stor in STORAGES
        },
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
    },
}

ELECTROLYZER = {"hydrogen_electrolyzer": "#F0F6FB"}

ELECTROLYZER_RENAMED = {
    "German": {"hydrogen_electrolyzer": "Elektrolyseur"},
    "English": {"hydrogen_electrolyzer": "electrolyzer"},
}

LOAD = {"DE_sink_el_load": "darkblue"}

LOAD_RENAMED = {
    "German": {"DE_sink_el_load": "inflexible Restlast"},
    "English": {"DE_sink_el_load": "inflexible remaining load"},
}

EVS = {
    "storage_ev_cc_bidirectional_inflow": "#7E7B2D",
    "storage_ev_cc_unidirectional_inflow": "#989336",
    "transformer_ev_cc_bidirectional_feedback": "#B1AC3F",
    "transformer_ev_uc": "#D8D59F",
}

EVS_RENAMED = {
    "German": {
        "storage_ev_cc_bidirectional_inflow": "E-Pkw bidirektionales Laden",
        "storage_ev_cc_unidirectional_inflow": "E-Pkw unidirektionales Laden",
        "transformer_ev_cc_bidirectional_feedback": "E-Pkw Rückspeisung",
        "transformer_ev_uc": "E-Pkw ungesteuertes Laden",
    },
    "English": {
        "storage_ev_cc_bidirectional_inflow": "E cars bidirectional charging",
        "storage_ev_cc_unidirectional_inflow": "E cars unidirectional charging",
        "transformer_ev_cc_bidirectional_feedback": "E cars grid feed-in",
        "transformer_ev_uc": "E cars uncontrolled charging",
    },
}

SHORTAGE_EXCESS = {
    "DE_sink_el_excess": "purple",
    "DE_source_el_shortage": "red",
}

SHORTAGE_EXCESS_RENAMED = {
    "German": {
        "DE_sink_el_excess": "EE-Abregelung",
        "DE_source_el_shortage": "unfreiwilliger Lastabwurf",
    },
    "English": {
        "DE_sink_el_excess": "RES curtailment",
        "DE_source_el_shortage": "unvoluntary shedding",
    },
}
