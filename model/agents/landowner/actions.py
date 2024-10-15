# coding: utf-8
from uuid import uuid4
from agents.inhabitant import Inhabitant
from agents.dwelling import Dwelling
from multiants import Action
from .parametters import AnnualSettlements
from generation.dwelling_factory import DwellingFactory


class CreateEmptyBuildings(Action):
    """Create empty buildings."""

    def apply(self, agent, model, desired_areas):
        # TODO: desired_areas is not a good name for this variable, it can be missleading...
        for desired_area in desired_areas:
            dwelling_factory = DwellingFactory(model)
            house_shape = dwelling_factory.build(agent, desired_area)
            dwelling_agent = Dwelling(
                str(uuid4()), model, house_shape, model.config["crs"]
            )
            model.add_agent(dwelling_agent, True)
            model.reset_influences()
            model.log("RULE create_empty_buildings ADDED 1 building")


class CreateRandomBuildings(Action):
    """Create random buildings."""

    def apply(self, agent, model, desired_areas):
        # TODO: desired_areas is not a good name for this variable, it can be missleading...
        for desired_area in desired_areas:
            dwelling_factory = DwellingFactory(model)
            house_shape = dwelling_factory.random_build(agent, desired_area)
            dwelling_agent = Dwelling(
                str(uuid4()), model, house_shape, model.config["crs"]
            )
            model.add_agent(dwelling_agent, True)
            model.reset_influences()
            model.log("RULE create_random_buildings ADDED 1 building")


class CreateHousehold(Action):
    """Create a new household."""

    def apply(self, agent, model):
        if agent.do("ask_permission"):
            model.add_agent(
                Inhabitant(
                    uuid4(),
                    model,
                    house=None,
                ),
                True,
            )


class AskPermission(Action):
    """Ask permission to settle."""

    def apply(self, agent, model):
        as_number, as_max, as_newcommer_months = agent.get(
            "annual_settlements"
        )
        permission = as_number < as_max
        if permission:
            agent.set(
                "annual_settlements",
                AnnualSettlements.Type(
                    as_number + 1, as_max, as_newcommer_months
                ),
            )
        return permission
