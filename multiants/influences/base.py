# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import cast, TYPE_CHECKING
from typing import Callable, Dict, List, Generator

from abc import abstractmethod
from geopandas import GeoDataFrame
from mesa_geo import GeoAgent
from shapely import speedups
from shapely.strtree import STRtree
from shapely.affinity import translate
from shapely.geometry import MultiLineString, MultiPoint, MultiPolygon

if TYPE_CHECKING:
    from model import Model
    from shapely import Geometry, Point

__all__ = [
    "Influence",
    "DistanceInfluence",
    "DistanceInfluenceGPD",
    "SlopeInfluence",
    "SlopeInfluenceE",
]


class Influence:
    def __init__(
        self,
        model: Model,
        function: Callable[[float], float],
        weight: float,
    ):
        self._model = model
        self._function = function
        self._weight = weight

    @property
    def weight(self) -> float:
        """Returns the influence weight used when all influences are summed."""
        return self._weight

    def reset(self):
        """Reset this influence, commonly called at the end of a timestep."""
        pass

    @abstractmethod
    def get(self, obs: Dict, point: Point) -> float:
        pass


class DistanceInfluence(Influence):
    """Defines an influence based on distance within objects."""

    def __init__(
        self,
        model: Model,
        target: Callable[[Model], List[GeoAgent]],
        function: Callable[[float], float],
        weight: float,
    ):
        """Distance influence constructor.

        Args:
            model: a reference to the model.
            target: a function to get the target from the model.
            function: a function that take a distance as input and return a float
                between -1 and 1.
            weight: this influence weight used when all influences are summed.
        """
        super().__init__(model, function, weight)
        self._target = target
        self._strtree = None

    def reset(self):
        """Reset the STR tree."""
        self._strtree = None

    def _get_targets(self) -> Generator[Geometry, None, None]:
        for agent in self._target(self._model):
            if not isinstance(
                agent.geometry, (MultiPolygon, MultiLineString, MultiPoint)
            ):
                yield agent.geometry
            else:
                for geom in agent.geometry.geoms:
                    yield geom

    def _get_strtree(self) -> STRtree:
        # lazy load STR tree
        targets = list(self._get_targets())
        if len(targets) == 0:
            self._model.log.system_log("WARNING: Influence has no targets", True, True)
        return STRtree(targets) if self._strtree is None else self._strtree

    def get(self, obs: Dict, point: Point) -> float:
        """Get the influence value for a given point in the space.

        Args:
            obs: informations about the requester.
            point: position.
        """
        speedups.enable()
        strtree = self._get_strtree()
        object_geometry = translate(obs["shape"], *point.coords[0])
        nearest = strtree.nearest(object_geometry)
        if nearest is not None:
            nearest_obj = strtree.geometries.take(nearest)
            distance = object_geometry.distance(nearest_obj)
            speedups.disable()
            return self._function(distance)
        else:
            speedups.disable()
            return -1


class DistanceInfluenceGPD(Influence):
    # performance is good enough with gradient descent
    # but for minfluence map rendering it's still slow (TODO use numpy better)
    def __init__(
        self,
        model: Model,
        target: Dict,  # TODO Type
        function: Callable[[float], float],
        weight: float,
    ):
        super().__init__(model, function, weight)
        self._target = target
        self._sindex = None

    def reset(self):
        self._sindex = None

    @property
    def sindex(self):
        if self._sindex is None:
            model_grid = self._model.grid
            target_class = self._target["agent_class"]
            target_gdf = model_grid.get_agents_as_GeoDataFrame(target_class)
            target_filter = self._target.get("filter")
            if target_filter is not None:
                target_gdf = cast(
                    GeoDataFrame,
                    target_gdf[target_gdf.parametters.apply(target_filter)],
                )
            self._sindex = target_gdf.sindex
        return self._sindex

    def get(self, obs: Dict, point: Point) -> float:
        shape = translate(obs["shape"], *point.coords[0])
        nearest_obj = self.sindex.geometries[self.sindex.nearest(shape)[1][0]]
        return self._function(shape.distance(nearest_obj))


class SlopeInfluence(Influence):
    """Define an influence based on the topography (slope under the building).
    WARNING: WIP check if OK
    """

    def __init__(
        self,
        model: Model,
        function: Callable[[float], float],
        weight: float,
        raster: str,
    ):
        super().__init__(model, function, weight)
        self._raster = model.rasters[raster]

    def get(self, obs: Dict, point: Point) -> float:
        """Get the influence value for a given point in the space.

        Args:
            obs: informations about the requester (TODO describe type).
            point: position.
        """
        shape = translate(obs["shape"], *point.coords[0])
        slope = self._raster.get_slope(shape)
        # TODO: Fix this bug! An Exception can be passed to the influence
        # function
        if slope is not None and not isinstance(slope, Exception):
            return self._function(slope)
        else:
            return -1


class SlopeInfluenceE(Influence):
    def __init__(
        self,
        model: Model,
        function: Callable[[float], float],
        weight: float,
        raster: str,
    ):
        super().__init__(model, function, weight)
        self._raster = model.rasters[raster]

    def get(self, obs: Dict, point: Point) -> float:
        shape = translate(obs["shape"], *point.coords[0])
        slope = self._raster.get_slope_estimation(shape)
        if slope is not None:
            return self._function(slope)
        else:
            return -1
