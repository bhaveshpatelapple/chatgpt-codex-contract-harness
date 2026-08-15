from copy import deepcopy


DEFAULTS = {
    "http": {
        "host": "127.0.0.1",
        "port": 8080,
        "timeouts": {"connect": 2, "read": 10},
    },
    "logging": {"level": "INFO", "json": False},
}


def merge_config(defaults: dict, overrides: dict) -> dict:
    merged = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
