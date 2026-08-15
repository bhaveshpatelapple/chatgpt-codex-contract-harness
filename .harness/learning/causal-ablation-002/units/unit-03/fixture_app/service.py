from .config import DEFAULTS, merge_config


def service_settings(overrides: dict) -> dict:
    merged = merge_config(DEFAULTS, overrides)
    return {
        "bind": f'{merged["http"]["host"]}:{merged["http"]["port"]}',
        "read_timeout": merged["http"]["timeouts"]["read"],
        "log_level": merged["logging"]["level"],
    }
