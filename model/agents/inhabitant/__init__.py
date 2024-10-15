# coding: utf-8
from collections import OrderedDict
from multiants import Agent
from .parametters import Gender, Age, Status, House, Dead, Pregnancy
from .behaviours import ExtendHouse, Settle
from .actions import CreateBuilding, LeaveSettlement, HaveChild


__all__ = [
    "Inhabitant",
]


class Inhabitant(Agent):
    """Represents a human being."""

    PARAMETTERS = OrderedDict(
        {
            "gender": Gender(),
            "age": Age(),
            "status": Status(Status.Type.HEAD),
            "house": House(),
            "dead": Dead(False),
            "pregnancy": Pregnancy(Pregnancy.Type(False, 0), resting_months=3),
        }
    )
    EXPORTED_PARAMETTERS = [
        "gender",
        "age",
        "status",
        "dead",
    ]
    RULES = {
        "extend_house": ExtendHouse(
            min_area_per_inhabitant=2.0,
            cost_per_m2=100.0,
            area_range=(20, 25),
        ),
        "settle": Settle(
            area_range=(25, 75),
            min_age=18,
        ),
    }
    ACTIONS = {
        "create_building": CreateBuilding(),
        "leave_settlement": LeaveSettlement(),
        "have_child": HaveChild(),
    }
