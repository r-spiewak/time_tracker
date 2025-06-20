"""This file contains a function to load a client config."""

import json
from pathlib import Path

from time_tracker.constants import (
    DEFAULT_CLIENT_CONFIG_FILE,
    SAMPLE_CLIENT_CONFIG_FILE,
)

from .client_models import ClientConfig


def load_client_config(
    client_config_file: str | Path | None = None,
) -> ClientConfig:
    """Load a client config file."""
    if (
        not client_config_file
        or not (client_config_file := Path(client_config_file)).exists()
    ):
        client_config_file = (
            DEFAULT_CLIENT_CONFIG_FILE
            if DEFAULT_CLIENT_CONFIG_FILE.exists()
            else SAMPLE_CLIENT_CONFIG_FILE
        )
    with Path(client_config_file).open("r", encoding="utf8") as file:
        client_config = json.load(file)
    return ClientConfig(**client_config)
