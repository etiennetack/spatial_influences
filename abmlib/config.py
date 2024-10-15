# coding: utf-8
from typing import Any
import toml
from collections import namedtuple

__all__ = ["load_config", "check_config"]


def dict_to_object(dictionary, class_name):
    values = [
        value
        if not isinstance(value, dict)
        else dict_to_object(value, key.capitalize())
        for key, value in dictionary.items()
    ]
    return namedtuple(class_name, dictionary.keys())(*values)


def load_config(config: str) -> dict[str, Any]:
    """Read TOML config file and load it.

    Args:
        config (str): path to a toml config file.

    Returns:
        Dict: the config as a python dictionary.
    """
    with open(config) as file:
        return toml.loads(file.read())


def check_config(config: dict[str, Any]) -> bool:
    """Returns True if the structure of the config is valid."""
    # TODO: implement this method, use this: https://json-schema.org/
    return True
