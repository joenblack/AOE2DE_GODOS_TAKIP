# Initial seed data for Reference Tables

CIV_ID_TO_NAME = {
    0: "Random",
    1: "Britons",
    2: "Franks",
    3: "Goths",
    4: "Teutons",
    5: "Japanese",
    6: "Chinese",
    7: "Byzantines",
    8: "Persians",
    9: "Saracens",
    10: "Turks",
    11: "Vikings",
    12: "Mongols",
    13: "Celts",
    14: "Spanish",
    15: "Aztecs",
    16: "Mayans",
    17: "Huns",
    18: "Koreans",
    19: "Italians",
    20: "Hindustanis",
    21: "Incas",
    22: "Magyars",
    23: "Slavs",
    24: "Portuguese",
    25: "Ethiopians",
    26: "Malians",
    27: "Berbers",
    28: "Khmer",
    29: "Malay",
    30: "Burmese",
    31: "Vietnamese",
    32: "Bulgarians",
    33: "Tatars",
    34: "Cumans",
    35: "Lithuanians",
    36: "Burgundians",
    37: "Sicilians",
    38: "Poles",
    39: "Bohemians",
    40: "Dravidians",
    41: "Bengalis",
    42: "Gurjaras",
    43: "Romans",
    44: "Armenians",
    45: "Georgians",
}

# Add some common known maps if desired for initial seeding, 
# otherwise they will be added dynamically as "Unknown Map (123)" or by name if API provides name.
# Since we decided to use the map NAME from API as reference if ID is missing:
# If API gives "Arabia.rms", we will store Map(name="Arabia.rms").
# This dict is mostly if we want to Pre-Seed canonical names.
MAP_ID_TO_NAME = {
    # Examples
    # 9: "Arabia",
    # 12: "Black Forest",
}
