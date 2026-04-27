def validate_mcq_question(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("MCQ question must be a dictionary.")

    required_keys = {"question", "choices", "answer", "explanation"}
    if set(data.keys()) != required_keys:
        raise ValueError(f"MCQ question keys must be exactly {required_keys}.")

    if not isinstance(data["question"], str) or not data["question"].strip():
        raise ValueError("question must be a non-empty string.")

    if not isinstance(data["choices"], dict):
        raise ValueError("choices must be a dictionary.")
    
    required_item_keys = {"A", "B", "C", "D"}
    if set(data["choices"].keys()) != required_item_keys:
        raise ValueError(f"choices keys must be exactly {required_item_keys}.")

    answer = data["answer"].strip()
    if answer not in required_item_keys:
        raise ValueError("answer must be one of A, B, C, D.")
    
    if not data["answer"] in data["choices"]:
        raise ValueError("answer must be one of the choices keys.")
    
    if not isinstance(data["explanation"], str) or not data["explanation"].strip():
        raise ValueError("explanation must be a non-empty string.")

    for key, value in data["choices"].items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Choice '{key}' must be a non-empty string.")
