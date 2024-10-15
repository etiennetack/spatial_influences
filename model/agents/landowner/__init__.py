from abmlib import Agent
from .parametters import AnnualSettlements
from .behaviours import Immigration, ImmigrationBulk
from .actions import (
    CreateHousehold,
    AskPermission,
    CreateEmptyBuildings,
    CreateRandomBuildings,
)

__all__ = ["LandOwner"]


class LandOwner(Agent):
    PARAMETTERS = {
        "annual_settlements": AnnualSettlements(annual_settlements_range=(0, 6)),
    }
    EXPORTED_PARAMETTERS = [
        "annual_settlements",
    ]
    RULES = {
        "immigration_bulk": ImmigrationBulk(
            area_range=(25, 75),
            number=26,
        ),
        # "immigration": Immigration(),
    }
    ACTIONS = {
        "create_empty_buildings": CreateEmptyBuildings(),
        "create_random_buildings": CreateRandomBuildings(),
        "create_household": CreateHousehold(),
        "ask_permission": AskPermission(),
    }
