def validate_rubric_schema(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("Rubric schema must be a dictionary.")

    # --- root keys ---
    required_root_keys = {"max_total_score", "criteria"}
    if set(data.keys()) != required_root_keys:
        raise ValueError(
            f"Root keys must be exactly {required_root_keys}."
        )

    # --- max_total_score ---
    if not isinstance(data["max_total_score"], (int, float)):
        raise ValueError("max_total_score must be int or float.")

    # --- criteria ---
    criteria = data["criteria"]
    if not isinstance(criteria, list):
        raise ValueError("criteria must be a list.")

    if len(criteria) == 0:
        raise ValueError("criteria must not be empty.")

    for i, item in enumerate(criteria):
        if not isinstance(item, dict):
            raise ValueError(f"criteria[{i}] must be a dictionary.")

        required_item_keys = {"key", "description", "max_score"}
        if set(item.keys()) != required_item_keys:
            raise ValueError(
                f"criteria[{i}] keys must be exactly {required_item_keys}."
            )

        # key
        if not isinstance(item["key"], str):
            raise ValueError(f"criteria[{i}].key must be string.")
        if not item["key"]:
            raise ValueError(f"criteria[{i}].key must not be empty.")

        # description
        if not isinstance(item["description"], str):
            raise ValueError(f"criteria[{i}].description must be string.")
        if not item["description"].strip():
            raise ValueError(f"criteria[{i}].description must not be empty.")

        # max_score
        if not isinstance(item["max_score"], (int, float)):
            raise ValueError(f"criteria[{i}].max_score must be int or float.")
        if item["max_score"] <= 0:
            raise ValueError(f"criteria[{i}].max_score must be > 0.")
