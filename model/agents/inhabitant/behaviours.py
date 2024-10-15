# coding: utf-8
import random
from abmlib import BehaviourRule
from .parametters import Status

__all__ = [
    "ExtendHouse",
    "Settle",
]


class ExtendHouse(BehaviourRule):
    """Dummy behavior that randomly ask to build extensions."""

    def apply(self, agent, model):
        min_area_per_inhabitant = self.options["min_area_per_inhabitant"]
        cost_per_m2 = self.options["cost_per_m2"]
        area_range = self.options["area_range"]

        house = agent.get("house")

        if (
            house
            and agent.get("status") == Status.Type.HEAD
            and len(house.get("members")) != 0
            and (
                house.geometry.area / len(house.get("members"))
                <= min_area_per_inhabitant
            )
        ):
            desired_area = random.uniform(*area_range)
            extension_cost = desired_area * cost_per_m2
            if extension_cost <= house.get("construction_savings"):
                house.do("make_extension", desired_area=desired_area)
                house.set(
                    "construction_savings",
                    house.get("construction_savings") - extension_cost,
                )
                model.log(
                    f"House {agent.unique_id}"
                    f"has been extended by {desired_area}"
                    f"square meters, it cost them FJ${extension_cost}"
                )


class Settle(BehaviourRule):
    """Behaviour describing how agents settle"""

    def apply(self, agent, model):
        if agent.get("age").value >= self.options["min_age"]:
            area_range = self.options["area_range"]
            desired_area = random.uniform(*area_range)
            if agent.get("status") == Status.Type.HEAD and not agent.get("house"):
                # This is a newcommer he needs to find a way to get a house
                agent.do("create_building", desired_area=random.uniform(*area_range))
                model.log("House built (external)")
            elif agent.get("status") == Status.Type.MEMBER:
                # This is a young adult of the settlement
                # TODO: add savings
                if model.landowner.ask_permission_to_settle():
                    # Revenus / éconormies + marges à 3 mois`
                    model.log("House built (internal)")
                    agent.do(
                        "create_building", desired_area=random.uniform(*area_range)
                    )
                    agent.set("status", Status.Type.HEAD)
                else:
                    agent.do("leave_settlement")
