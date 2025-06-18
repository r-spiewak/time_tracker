"""Contains a class with a config loaded from a file."""

from types import SimpleNamespace

import yaml

from python_template.constants import CONFIG_PATH


def dict_to_namespace(d):
    """Turn a dict into a namespace (so its members can be accessed
    with dot notation like for a class)."""
    return SimpleNamespace(
        **{
            k: dict_to_namespace(v) if isinstance(v, dict) else v
            for k, v in d.items()
        }
    )


with open(str(CONFIG_PATH), "r", encoding="utf8") as f:
    config_dict = yaml.safe_load(f)

config = dict_to_namespace(config_dict)
