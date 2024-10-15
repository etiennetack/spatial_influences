# -*- coding: utf-8 -*-
from typing import cast
from typing import Tuple
import random
from enum import Enum
from collections import namedtuple
from abmlib import Parametter
import generation.ages as ages

__all__ = [
    "Gender",
    "Age",
    "Dead",
    "Status",
    "Pregnancy",
    "House",
    "Family",
]


class Gender(Parametter):
    class Type(Enum):
        """Family member's gender enumerator."""

        MALE = 0
        """If agent is a man."""
        FEMALE = 1
        """If agent is a women."""

    def init(self, agent, model, override):
        # TODO:check if, for this, I need to use the demographic data
        # TODO Do it in the other way
        if override is not None:
            return override
        else:
            return Gender.Type.FEMALE if random.random() < 0.5 else Gender.Type.MALE


class Age(Parametter):
    Type = namedtuple("Age", ["value", "group"])
    GROUPS = ages.generate_groups(interval_size=5, max_value=70)

    def init(self, agent, model, override=None):
        # TODO: Décrire dans le document, quel document?
        # Get demographic factor in function of agent's gender
        age_factor = model.factors[
            "age_male" if agent.get("gender") == Gender.Type.MALE else "age_female"
        ]
        # Get gemographic data for current date (year)
        age_data = age_factor.get_data(model.time.current.year)

        # Random pick an age group
        group = int(
            age_factor.roulette_wheel(age_data, index_range=(1, len(Age.GROUPS)))
        )
        # And then randomize the agent's age within this group
        age = ages.random(group, Age.GROUPS)
        return Age.Type(age, group)

    def update(self, agent, model, old):
        """Apply aging and update age group value."""
        (value, _) = old
        value += 1 / 12
        group = ages.to_age_group(value, Age.GROUPS)  # update age group
        return Age.Type(value, group)


class Dead(Parametter):
    pass


class Status(Parametter):
    class Type(Enum):
        """Inhabitant type enumerator."""

        HEAD = 0
        """Inhabitant is household's head."""
        MEMBER = 1
        """Inhabitant is household's member."""


PregnancyType = namedtuple("Pregnancy", ["ongoing", "remaining"])


class Pregnancy(Parametter):
    Type = PregnancyType

    def update(self, agent, model, old: PregnancyType) -> PregnancyType:
        resting_months = cast(int, self.options["resting_months"])
        ongoing, length = old
        if ongoing:
            if length == 9 and agent.get("gender") == Gender.Type.FEMALE:
                # TODO: create child (new agent)
                pass
            elif length == 9 + resting_months:
                # Free mother and father
                return self.initial_value
            return PregnancyType(ongoing, length + 1)
        else:
            return old


class House(Parametter):
    pass


class Family(Parametter):
    # maybe it should be on the household level
    # or as a submodel
    # the idea is to have a graph representing relations between agents
    pass
