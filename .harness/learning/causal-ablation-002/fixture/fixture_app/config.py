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
    merged.update(deepcopy(overrides))
    return merged
