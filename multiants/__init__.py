# coding: utf-8
"""MULTIANTS"""

import datetime
from .model import Model
from .agents import Agent, GeoAgent, Parametter, BehaviourRule, Action

__all__ = [
    "Model",
    "Agent",
    "GeoAgent",
    "Parametter",
    "BehaviourRule",
    "Action",
]

__title__ = "multiants"
__version__ = "0.0.1"
__license__ = "AGPL-3.0-only"
__copyright__ = f"Copyright {datetime.date.today().year} Project MULTIANTS Team"
