# coding: utf-8
from collections import OrderedDict
from abmlib import GeoAgent
from .parametters import (
    Shape,
    Employment,
    WeeklyIncome,
    ConstructionSavings,
    Status,
    Members,
)
from .actions import MakeExtension


__all__ = ["Dwelling"]


class Dwelling(GeoAgent):
    PARAMETTERS = OrderedDict(
        {
            "shape": Shape(),
            "employment": Employment(),
            "weekly_income": WeeklyIncome(),
            "construction_savings": ConstructionSavings(0, savings_rate=0.08),
            "status": Status(),
            "members": Members([]),
        }
    )
    EXPORTED_PARAMETTERS = [
        "employment",
        "weekly_income",
        "construction_savings",
        "status",
    ]
    RULES = {}
    ACTIONS = {
        "make_extension": MakeExtension(),
    }
