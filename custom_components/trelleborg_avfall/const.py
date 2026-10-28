"""Konstanter för Trelleborg Kretslopp och Vatten."""

DOMAIN = "trelleborg_avfall"

CONF_ADDRESS = "address"
CONF_BINS = "bins"

CONF_BIN_ID = "id"
CONF_BIN_NAME = "name"
CONF_BIN_TYPE = "bin_type"
CONF_INTERVAL_WEEKS = "interval_weeks"
CONF_REFERENCE_DATE = "reference_date"
CONF_SEASON_START = "season_start_week"
CONF_SEASON_END = "season_end_week"
CONF_EXCLUDE_DATES = "exclude_dates"
CONF_EXTRA_DATES = "extra_dates"

BIN_TYPE_FYRFACK_1 = "fyrfack_1"
BIN_TYPE_FYRFACK_2 = "fyrfack_2"
BIN_TYPE_GARDEN = "garden"
BIN_TYPE_FOOD = "food"
BIN_TYPE_RESIDUAL = "residual"
BIN_TYPE_OTHER = "other"

BIN_TYPES = [
    BIN_TYPE_FYRFACK_1,
    BIN_TYPE_FYRFACK_2,
    BIN_TYPE_GARDEN,
    BIN_TYPE_FOOD,
    BIN_TYPE_RESIDUAL,
    BIN_TYPE_OTHER,
]

# Förifyllda värden enligt Trelleborgs vanliga abonnemang.
PRESETS: dict[str, dict] = {
    BIN_TYPE_FYRFACK_1: {
        CONF_BIN_NAME: "Kärl 1 (fyrfack 370 L)",
        CONF_INTERVAL_WEEKS: 2,
    },
    BIN_TYPE_FYRFACK_2: {
        CONF_BIN_NAME: "Kärl 2 (fyrfack 370 L)",
        CONF_INTERVAL_WEEKS: 4,
    },
    BIN_TYPE_GARDEN: {
        CONF_BIN_NAME: "Trädgårdsavfall (370 L)",
        CONF_INTERVAL_WEEKS: 2,
        CONF_SEASON_START: 12,
        CONF_SEASON_END: 47,
    },
    BIN_TYPE_FOOD: {CONF_BIN_NAME: "Matavfall", CONF_INTERVAL_WEEKS: 2},
    BIN_TYPE_RESIDUAL: {CONF_BIN_NAME: "Restavfall", CONF_INTERVAL_WEEKS: 2},
    BIN_TYPE_OTHER: {CONF_BIN_NAME: "Kärl", CONF_INTERVAL_WEEKS: 2},
}

CONTENTS: dict[str, str] = {
    BIN_TYPE_FYRFACK_1: "Matavfall, restavfall, plastförpackningar, pappersförpackningar",
    BIN_TYPE_FYRFACK_2: "Tidningar, metallförpackningar, ofärgat glas, färgat glas",
    BIN_TYPE_GARDEN: "Trädgårdsavfall",
    BIN_TYPE_FOOD: "Matavfall",
    BIN_TYPE_RESIDUAL: "Restavfall",
    BIN_TYPE_OTHER: "",
}

ICONS: dict[str, str] = {
    BIN_TYPE_FYRFACK_1: "mdi:trash-can",
    BIN_TYPE_FYRFACK_2: "mdi:recycle",
    BIN_TYPE_GARDEN: "mdi:leaf",
    BIN_TYPE_FOOD: "mdi:food-apple",
    BIN_TYPE_RESIDUAL: "mdi:trash-can-outline",
    BIN_TYPE_OTHER: "mdi:delete-variant",
}

UPCOMING_COUNT = 5
