# coding: utf-8
from uuid import uuid4
from multiants import Action
from generation.dwelling_factory import DwellingFactory

from agents.dwelling import Dwelling
from .parametters import Gender, Pregnancy

# from agents.dwelling2 import Dwelling

__all__ = [
    "CreateBuilding",
    "LeaveSettlement",
    "GetMarried",
    "HaveChild",
]


class CreateBuilding(Action):
    """Creates a new dwelling and find a plot for it using influence module.

    Args:
        desired_area (number): Desired size of the new dwelling, in m²
    """

    def apply(self, agent, model, desired_area):
        dwelling_factory = DwellingFactory(model)
        house_shape = dwelling_factory.build(agent, desired_area)
        dwelling_agent = Dwelling(
            str(uuid4()), model, house_shape, model.config["crs"]
        )
        model.add_agent(dwelling_agent, True)
        agent.set("house", dwelling_agent)
        # TODO: Ajouter dans les membres


class LeaveSettlement(Action):
    """Agent leaves the settlement to find other options outside."""

    def apply(self, agent, model):
        if agent.get("house"):
            agent.get("house").members.remove(agent)
        # TODO: Do not remove the agent, create a new class for outside agent
        model.remove_agent(agent)


class GetMarried(Action):
    """Get married to begin a family.

    Args:
        other (Inhabitant): future spouse or husband.
    """

    def apply(self, agent, model, other):
        # this kind of things must be done at the behaviour level
        # make checks before to avoid two people of the same sex or if
        # someone is already married
        # self.gender != other.gender
        pass
        if agent.gender == Gender.Type.FEMALE:
            # link agent.unique_id with other.unique_id as husband
            # link other.unique_id with agent.unique+id as spouse
            pass
        else:
            # link agent.unique_id with other.unique_id as spouse
            # link other.unique_id with agent.unique+id as husband
            pass


class HaveChild(Action):
    """Have a child.

    Args:
        father (Inhabitant): future father for the child.
    """

    def apply(self, agent, model, father):
        agent.set("pregnancy", Pregnancy.Type(True, 0))
        father.set("pregnancy", Pregnancy.Type(True, 0))
