from pathlib import Path

import yaml


def load_config(config_path: str) -> dict:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if not path.is_file():
        raise ValueError(f"Config path is not a file: {config_path}")
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if config is None:
        raise ValueError(f"Config file is empty: {config_path}")
    if not isinstance(config, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {config_path}")

    return config