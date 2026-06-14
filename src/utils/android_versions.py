ANDROID_VERSIONS: dict[int, str] = {
    1: "1.0 (Base)",
    2: "1.1 (Petit Four)",
    3: "1.5 (Cupcake)",
    4: "1.6 (Donut)",
    5: "2.0 (Eclair)",
    6: "2.0.1 (Eclair)",
    7: "2.1 (Eclair)",
    8: "2.2 (Froyo)",
    9: "2.3 (Gingerbread)",
    10: "2.3.3 (Gingerbread)",
    11: "3.0 (Honeycomb)",
    12: "3.1 (Honeycomb)",
    13: "3.2 (Honeycomb)",
    14: "4.0 (Ice Cream Sandwich)",
    15: "4.0.3 (Ice Cream Sandwich)",
    16: "4.1 (Jelly Bean)",
    17: "4.2 (Jelly Bean)",
    18: "4.3 (Jelly Bean)",
    19: "4.4 (KitKat)",
    20: "4.4W (KitKat Wear)",
    21: "5.0 (Lollipop)",
    22: "5.1 (Lollipop)",
    23: "6.0 (Marshmallow)",
    24: "7.0 (Nougat)",
    25: "7.1 (Nougat)",
    26: "8.0 (Oreo)",
    27: "8.1 (Oreo)",
    28: "9 (Pie)",
    29: "10 (Q)",
    30: "11 (R)",
    31: "12 (S)",
    32: "12L",
    33: "13 (Tiramisu)",
    34: "14 (Upside Down Cake)",
    35: "15 (Vanilla Ice Cream)",
}


def sdk_to_version(sdk_level: int) -> str:
    if sdk_level in ANDROID_VERSIONS:
        return f"Android {ANDROID_VERSIONS[sdk_level]}"
    if sdk_level > max(ANDROID_VERSIONS):
        return f"Android API {sdk_level} (Newer)"
    return f"Android API {sdk_level} (Unknown)"


def sdk_to_short_version(sdk_level: int) -> str:
    ver = ANDROID_VERSIONS.get(sdk_level, f"API {sdk_level}")
    # Extract version number like "5.0" or "14"
    parts = ver.split(" (")
    return parts[0] if parts else ver
