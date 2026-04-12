DIMENSION_HIERARCHY: dict[str, list[str]] = {
    "geography": ["ship_state", "ship_city"],
    "channel":   ["fulfilment", "ship_service_level"],
    "time":      ["date"],
    "category":  ["category", "style"],
    "product":   ["sku", "asin", "category"],
    "size":      ["size"],
    "b2b":       ["is_b2b"],
}

# Maps natural-language terms users might say → actual DB column names
VALID_DIMENSIONS: dict[str, str] = {
    "state":       "ship_state",
    "states":      "ship_state",
    "region":      "ship_state",
    "city":        "ship_city",
    "cities":      "ship_city",
    "category":    "category",
    "categories":  "category",
    "product":     "category",
    "sku":         "sku",
    "channel":     "fulfilment",
    "fulfilment":  "fulfilment",
    "fulfillment": "fulfilment",
    "shipping":    "ship_service_level",
    "style":       "style",
    "size":        "size",
    "b2b":         "is_b2b",
    "business":    "is_b2b",
}


def resolve_dimension(term: str) -> str | None:
    return VALID_DIMENSIONS.get(term.lower())


def get_hierarchy() -> dict[str, list[str]]:
    return DIMENSION_HIERARCHY
