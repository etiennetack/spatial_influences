# coding: utf-8
import random
from multiants import BehaviourRule


class Immigration(BehaviourRule):
    def apply(self, agent, model):
        # Fetch planned new settlements for the current month
        _, _, months = agent.get("annual_settlements")
        for month in filter(lambda m: m == model.time.current.month, months):
            agent.do("create_household")


class ImmigrationBulk(BehaviourRule):
    def apply(self, agent, model):
        desired_areas = [
            random.uniform(*self.options["area_range"])
            for _ in range(self.options["number"])
        ]
        agent.do("create_empty_buildings", desired_areas=desired_areas)


class RandomSimulation(BehaviourRule):
    def apply(self, agent, model):
        desired_areas = [
            random.uniform(*self.options["area_range"])
            for _ in range(self.options["number"])
        ]
        agent.do("create_random_buildings", desired_areas=desired_areas)
