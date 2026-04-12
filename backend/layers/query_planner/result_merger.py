def merge_results(
    results: list[list[dict]],
    join_on: list[str],
) -> list[dict]:
    """
    Merges multiple query result sets on shared dimension columns.

    Example:
      results[0] = [{"Channel": "Mobile", "revenue": 12000}, ...]
      results[1] = [{"Channel": "Mobile", "volume": 450}, ...]
      join_on    = ["Channel"]

    Output:
      [{"Channel": "Mobile", "revenue": 12000, "volume": 450}, ...]

    Dimension values present in one set but not the other are kept;
    missing metrics are filled with None — rows are never dropped.
    """
    if not results:
        return []
    if len(results) == 1:
        return results[0]

    merged: dict[tuple, dict] = {}
    for result_set in results:
        for row in result_set:
            key = tuple(row.get(col) for col in join_on)
            if key not in merged:
                merged[key] = {col: row.get(col) for col in join_on}
            merged[key].update({k: v for k, v in row.items() if k not in join_on})

    return list(merged.values())
