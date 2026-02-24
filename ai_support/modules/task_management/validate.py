def validate_learning_topic(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("Learning topic must be a dictionary.")

    # --- root ---
    required_root_keys = {"main_topics"}
    if set(data.keys()) != required_root_keys:
        raise ValueError(
            f"Root keys must be exactly {required_root_keys}."
        )

    # --- main_topics ---
    main_topics = data["main_topics"]
    if not isinstance(main_topics, list):
        raise ValueError("main_topics must be list.")

    required_main_keys = {"title", "sub_topics"}
    required_sub_keys = {"title"}

    for main_index, main_topic in enumerate(main_topics):

        if not isinstance(main_topic, dict):
            raise ValueError(f"main_topic[{main_index}] must be a dict.")

        if set(main_topic.keys()) != required_main_keys:
            raise ValueError(
                f"main_topic[{main_index}] keys must be exactly {required_main_keys}."
            )
        
        if not isinstance(main_topic["title"], str) or not main_topic["title"].strip():
            raise ValueError(f"main_topic[{main_index}].title must be non-empty string.")
        

        # --- sub_topics ---
        sub_topics = main_topic["sub_topics"]
        if not isinstance(sub_topics, list):
            raise ValueError(f"main_topic[{main_index}].sub_topics must be list.")

        for sub_index, sub_topic in enumerate(sub_topics):

            if not isinstance(sub_topic, dict):
                raise ValueError(
                    f"sub_topic[{main_index}][{sub_index}] must be dict."
                )

            if set(sub_topic.keys()) != required_sub_keys:
                raise ValueError(
                    f"sub_topic[{main_index}][{sub_index}] keys must be exactly {required_sub_keys}."
                )

            if not isinstance(sub_topic["title"], str) or not sub_topic["title"].strip():
                raise ValueError(
                    f"sub_topic[{main_index}][{sub_index}].title must be non-empty string."
                )


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
