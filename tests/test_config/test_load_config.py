"""This file contains tests for the load_config module."""

import types

import yaml

from time_tracker import settings
from time_tracker.config.load_config import Config, dict_to_namespace
from time_tracker.constants import CONFIG_PATH


def test_config_file_exists_and_loadable():
    """Test that the default config file exists and can be loaded."""
    assert CONFIG_PATH.exists(), "Config file is missing"
    with CONFIG_PATH.open("r", encoding="utf8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "Config must be a dictionary"


def test_config_dict_to_namespace_recursive():
    """Test that the namespace returned by load_config goes
    recursively into nested dicts."""
    one = 1
    two = 2
    three = 3
    sample_dict = {
        "a": one,
        "b": {"c": two, "d": {"e": three}},
    }
    ns = dict_to_namespace(sample_dict)
    assert isinstance(ns, types.SimpleNamespace)
    assert ns.a == one
    assert ns.b.c == two
    assert ns.b.d.e == three


# def test_loaded_config_is_namespace():
#     """Tests that load_config returns a namespace."""
#     assert isinstance(config, types.SimpleNamespace)
#     assert hasattr(config, "debug_prints")


def test_loaded_config_is_class():
    """Tests that load_config returns a namespace."""
    assert isinstance(settings, Config)
    assert hasattr(settings, "debug_prints")
