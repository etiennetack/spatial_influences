# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from typing import Any, List, Dict

from enum import Enum
from random import randint
from shapely.geometry import Polygon, MultiPolygon
from multiants import Parametter
from shapely import unary_union

if TYPE_CHECKING:
    from multiants import Model, GeoAgent, Agent


class Members(Parametter):
    pass


class BuildingShape:
    def __init__(self, geometry: Polygon | MultiPolygon, date: int):
        if isinstance(geometry, Polygon):
            self.main: Polygon = geometry
            self.extensions: Dict[int, List[Polygon]] = {}
            self.detached: Dict[int, List[Polygon]] = {}
        elif isinstance(geometry, MultiPolygon):
            parts: List[Polygon] = list(
                sorted(geometry.geoms, key=lambda p: p.area)
            )
            self.main: Polygon = parts[-1]
            self.extensions: Dict[int, List[Polygon]] = {}
            self.detached: Dict[int, List[Polygon]] = {date: parts[:-1]}
        else:
            raise Exception(
                f"This spatial data type not yet supported: {type(geometry)}"
            )

    def get_extensions(
        self, detached: Optional[bool] = False
    ) -> List[Polygon]:
        def get(shape_dict):
            res = []
            for date in shape_dict.values():
                res += date
            return res

        if detached is None:
            return get(self.extensions) + get(self.detached)
        if detached is True:
            return get(self.detached)
        if detached is False:
            return get(self.extensions)

    def get_house_core(
        self,
        new_extensions: List[Polygon] = [],
    ) -> Polygon:
        """House core is main buildings + attached extensions,
        others buildings can be also added via `new_extensions` parameter.

        Args:
            new_extensions: list of new extensions' shapes to merge with the main building.
        """
        return unary_union(
            [self.main] + self.get_extensions(detached=False) + new_extensions
        )

    def make_geometry(self) -> MultiPolygon | Polygon:
        if self.detached:
            return MultiPolygon(
                [self.get_house_core()] + self.get_extensions(detached=True)
            )
        else:
            return self.get_house_core()

    def add_extension(
        self,
        extension: Polygon,
        date: int,
        detached: bool = False,
    ):
        shape_dict = self.extensions if not detached else self.detached
        if date not in shape_dict:
            shape_dict[date] = []
        shape_dict[date].append(extension)


class Shape(Parametter):
    Type = BuildingShape

    def init(
        self,
        agent: GeoAgent,
        model: Model,
        override: Optional[BuildingShape] = None,
    ):
        if override is None:
            shape = self.Type(agent.geometry, model.time.current.year)
            return super().init(agent, model, shape)
        else:
            return super().init(agent, model, override)


class Employment(Parametter):
    class Type(Enum):
        """Employment type enumerator."""

        INDIE = 0
        """Independent worker."""
        PRIVATE = 1
        """Private employment."""
        PUBLIC = 2
        """Public employment."""
        NOJOB = 3
        """No professional activity."""

    def init(self, agent: GeoAgent, model: Model, override: Any = None):
        # TODO initialise from factors
        return super().init(agent, model, override)


class WeeklyIncome(Parametter):
    def init(
        self,
        agent: Agent,
        model: Model,
        override: Optional[float] = None,
    ):
        if override is None:
            # Make a roulette wheel on weekly income factor
            income_factor = model.factors["weekly_income"]
            year = model.time.current.year
            income_data = income_factor.get_data(year)
            income_range = income_factor.roulette_wheel(
                income_data, r"\$(\d+) \- \$(\d+)"
            )
            # Define weekly income from the randomly drawn income range
            value = randint(int(income_range[0]), int(income_range[1]))
            return super().init(agent, model, value)
        else:
            return super().init(agent, model, override)


class ConstructionSavings(Parametter):
    def update(self, agent: Agent, model: Model, old: float) -> float:
        income = agent.get("weekly_income") * 4 * self.options["savings_rate"]
        return old + income


class StatusType(Enum):
    """Dwelling status enumerator. Describe the relation between the
    household and his house."""

    OWNED = 0
    """House is owned."""
    RENTED = 1
    """House is rented."""
    OTHER = 2
    """House is occupied free of charge."""


class Status(Parametter):
    Type = StatusType
