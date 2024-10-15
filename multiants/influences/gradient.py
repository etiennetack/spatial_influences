# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Dict, List, Generator

from math import pi, cos, sin
from shapely.geometry import Point

if TYPE_CHECKING:
    from model import Model
    from .base import Influence

__all__ = ["Gradient", "NoValidStartPoint"]


class NoValidStartPoint(Exception):
    pass


class Gradient:
    def __init__(self, model: Model, influences: List[Influence]):
        self.model = model
        self.influences = influences

    def reset(self):
        for influence in self.influences:
            influence.reset()

    def compute_influences(self, obs: Dict, position: Point) -> float:
        weighted_sum = 0
        for value, weight in (
            (influence.get(obs, position), influence.weight)
            for influence in self.influences
        ):
            # If one influence is -1 the whole aggregation is -1
            if value <= -1:
                return -1
            weighted_sum += value * weight
        return weighted_sum

    @staticmethod
    def get_neighbors_positions(
        pos: Point,
        step: float,
        nbnb: int = 8,
    ) -> Generator[Point, None, None]:
        """Generates a number of neighbors positions around a circle.

        Args:
            pos: starting position.
            step: distance between pos and generated positions.
            nbnb: the number of generated neighbors.

        Returns: a generator of Points
        """
        gap = 2 * pi / nbnb
        return (
            Point(
                round(pos.x + step * cos(gap * i), 15),
                round(pos.y + step * sin(gap * i), 15),
                # ^^^ avoid cos(pi/2) != 0
            )
            for i in range(nbnb)
        )

    @staticmethod
    def slope(a, b):
        return (b["value"] - a["value"]) / a["pos"].distance(b["pos"])

    def _get_random_valid_start_point(
        self,
        obs: Dict,
        try_number: int = 100,
    ):  # TODO Return type
        start_point = self.model.get_random_position()
        infl_value = self.compute_influences(obs, start_point)
        if infl_value != -1:
            return {
                "pos": start_point,
                "value": infl_value,
            }
        else:
            if try_number > 0:
                return self._get_random_valid_start_point(obs, try_number - 1)
            else:
                return None

    def _recursive_gradient(
        self,
        obs: Dict,  # TODO Type
        current: Dict,  # TODO Type
        step: float,
        epsilon: float,
        stop_difference: float = 1e-3,
        step_tolerance: float = 0.1,
    ) -> Dict:  # TODO Type
        highest_slope = -float("inf")
        best_neighbor = {"pos": current, "value": -float("inf")}
        # for each positons p around the starting position
        for p in self.get_neighbors_positions(current["pos"], step, 8):
            # get the influence value
            nb = {"pos": p, "value": self.compute_influences(obs, p)}
            # compute the slope between it and the starting position
            # and keep the position that maximize this slope
            if self.slope(current, nb) > highest_slope:
                best_neighbor = nb
        # stop if the best neighbour's values is lower than the current best
        if step < step_tolerance or best_neighbor["value"] < current["value"]:
            return current
        # continue while the difference between values is big enought
        elif abs(current["value"] - best_neighbor["value"]) < stop_difference:
            return best_neighbor
        # reduce the step size
        else:
            return self._recursive_gradient(
                obs,
                best_neighbor,
                step * epsilon,
                epsilon,
                stop_difference,
                step_tolerance,
            )

    def compute(
        self,
        obs: Dict,  # TODO Type
        step: float = 10.0,
        epsilon: float = 0.9,
    ):  # TODO Return type
        start = self._get_random_valid_start_point(obs)
        if start is not None:
            return self._recursive_gradient(obs, start, step, epsilon)["pos"]
        else:
            raise NoValidStartPoint()

    def compute_batches(
        self,
        obs: Dict,  # TODO Type
        batches_n: int = 10,
        step: float = 1.0,
        epsilon: float = 0.95,
    ):  # TODO Return type
        batches = []
        for _ in range(batches_n):
            start = self._get_random_valid_start_point(obs)
            if start is not None:
                batches.append(self._recursive_gradient(obs, start, step, epsilon))
            else:
                raise NoValidStartPoint(batches)

        return max(batches, key=lambda x: x["value"])["pos"]
