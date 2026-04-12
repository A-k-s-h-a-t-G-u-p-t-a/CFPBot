DIMENSION_HIERARCHY: dict[str, list[str]] = {
    "geography": ["Location"],
    "channel":   ["Channel"],
    "time":      ["TransactionDate"],
    "customer":  ["CustomerOccupation", "CustomerAge"],
    "product":   ["TransactionType", "MerchantID"],
}

# Maps natural-language terms users might say → actual DB column names
VALID_DIMENSIONS: dict[str, str] = {
    "channel":     "Channel",
    "channels":    "Channel",
    "location":    "Location",
    "locations":   "Location",
    "region":      "Location",
    "city":        "Location",
    "type":        "TransactionType",
    "occupation":  "CustomerOccupation",
    "job":         "CustomerOccupation",
    "age":         "CustomerAge",
    "merchant":    "MerchantID",
    "device":      "DeviceID",
}


def resolve_dimension(term: str) -> str | None:
    return VALID_DIMENSIONS.get(term.lower())


def get_hierarchy() -> dict[str, list[str]]:
    return DIMENSION_HIERARCHY
