# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import cast, TYPE_CHECKING
from typing import Any, Dict, List

if TYPE_CHECKING:
    from model import Model
    from geopandas import GeoDataFrame
    from shapely import Geometry

from mesa_geo import (
    GeoAgent as MesaGeoAgent,
    AgentCreator as MesaGeoAgentCreator,
    Cell as MesaCell,
)
from .base import Agent

__all__ = ["GeoAgent", "AgentCreator"]


class GeoAgent(MesaGeoAgent, Agent):
    def __init__(
        self,
        unique_id: Any,
        model: Model,
        geometry: Geometry,
        crs: str,
        **params: Dict[str, Any],
    ):
        """Skeleton for all geographic agents.

        Args:
            unique_id: a unique id to identify agents between them.
            model: model instance of the agent.
            geometry: agent's shape.
            crs: CRS.
            params: any parametter to be used as value for agent's parametters.
        """
        MesaGeoAgent.__init__(self, unique_id, model, geometry, crs)
        Agent._init_parametters(self, **params)

    def __setattr__(self, name: str, value: Any):
        """DEPRECATED"""
        return Agent.__setattr__(self, name, value)

    def get(self, param: str) -> Any:
        return Agent.get(self, param)

    def set(self, param: str, value: Any):
        Agent.set(self, param, value)

    def do(self, action: str, **args) -> Any:
        return Agent.do(self, action, **args)

    def step(self):
        Agent.step(self)


class Cell(MesaCell, Agent):
    def __setattr__(self, name: str, value: Any):
        """DEPRECATED"""
        return Agent.__setattr__(self, name, value)

    def get(self, param: str) -> Any:
        return Agent.get(self, param)

    def set(self, param: str, value: Any):
        Agent.set(self, param, value)

    def do(self, action: str, **args) -> Any:
        return Agent.do(self, action, **args)


class AgentCreator(MesaGeoAgentCreator):
    def from_GeoDataFrame(
        self,
        gdf: GeoDataFrame,
        unique_id: str = "index",
        set_attributes: bool = True,
    ) -> List[GeoAgent]:
        # Use mesa code for agent creation, but don't set attributes
        agents = cast(
            List[GeoAgent],
            super().from_GeoDataFrame(gdf, unique_id, set_attributes=False),
        )
        # Set attributes from the GeoDataFrame using the init method of each
        # parametters
        if set_attributes:
            for index, row in gdf.iterrows():
                for col in row.index:
                    if not col == gdf.geometry.name and not col == unique_id:
                        if col in self.agent_class.PARAMETTERS:
                            agent = agents[cast(int, index)]
                            attribute = (
                                self.agent_class.PARAMETTERS[col]
                                # call the init method of the parametter
                                .init(agent, self.model, override=row[col])
                            )
                            agents[cast(int, index)].set(col, attribute)
        return agents
