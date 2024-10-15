# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List
import json
from click import Tuple
import pendulum
from enum import Enum
from shapely.geometry import mapping, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from .model import Model
from .agents import Agent, GeoAgent

if TYPE_CHECKING:
    from pyproj import Transformer


__all__ = ["ModelEncoder"]


# TODO implement a partial encoder with memory to send only changes


class ModelEncoder:
    def __init__(self, transformer: Transformer):
        self.transformer = transformer  # model.grid.transformer

    def agent(self, agent: Agent, is_attribute=False) -> Dict | int:
        if is_attribute:
            return agent.unique_id
        else:
            parameters = {
                # Get each parameter ...
                param: agent.get(param)
                # ... but only those to be exported
                for param in agent.EXPORTED_PARAMETTERS
            }
            if not isinstance(agent, GeoAgent):
                return {
                    "type": "Agent",
                    "properties": self.pre_encode(parameters, True),
                }
            else:
                return {
                    "type": "Feature",
                    "geometry": self.geometry(agent.geometry),
                    "properties": self.pre_encode(parameters, True),
                }

    def sequence(
        self,
        sequence: list | tuple | set,
        is_attribute: bool = False,
    ) -> List:
        return [self.pre_encode(elem, is_attribute) for elem in sequence]

    def dictionary(
        self,
        dictionary: Dict[str, Any],
        is_attribute: bool = False,
    ) -> Dict[str, Any]:
        return {
            key: self.pre_encode(value, is_attribute)
            for key, value in dictionary.items()
        }

    def geometry(self, geometry: BaseGeometry):
        # TODO: return type
        return mapping(transform(self.transformer.transform, geometry))

    def point(self, point: Point) -> Dict[str, float]:
        translated_point = self.transformer.transform(point.x, point.y)
        return {"x": translated_point[0], "y": translated_point[1]}

    def bounds(self, bounds: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        return {
            "topLeft": self.point(Point(bounds["west"], bounds["north"])),
            "bottomRight": self.point(Point(bounds["east"], bounds["south"])),
        }

    def enum(self, value) -> str:
        return value.name

    def is_namedtuple(self, value: Any) -> bool:
        return (
            isinstance(value, tuple)
            and hasattr(value, "_asdict")
            and hasattr(value, "_fields")
        )

    def namedtuple(self, value: Tuple, is_attribute: bool = False) -> Dict[str, Any]:
        dict = value._asdict()  # pyright: ignore [reportGeneralTypeIssues]
        return self.dictionary(dict, is_attribute)

    def datetime(self, value: pendulum.DateTime) -> str:
        return value.to_iso8601_string()

    def model(self, model: Model) -> Dict[str, Any]:
        agents_data = {}
        for a_class, agents in model.agents.items():
            is_geoagent = issubclass(a_class, GeoAgent)
            agents_data[a_class.__name__] = {
                "type": "FeatureCollection" if is_geoagent else "AgentCollection",
                "features": self.pre_encode(agents),
                "parametters": a_class.EXPORTED_PARAMETTERS,
                "rules": list(a_class.RULES.keys()),
                "actions": list(a_class.ACTIONS.keys()),
            }
        # model.influences
        return {
            # "timestep": model.schedule.steps,
            "date": self.datetime(model.time.current),
            "agents": agents_data,
            "bounds": self.bounds(model.bounds),
        }

    def pre_encode(
        self,
        value: Any,
        is_attribute: bool = False,
    ) -> Dict[str, Any] | List[Any] | str | int | float:
        if isinstance(value, (Agent, GeoAgent)):
            return self.agent(value, is_attribute)
        elif self.is_namedtuple(value):
            return self.namedtuple(value, is_attribute)
        elif isinstance(value, (list, tuple, set)):
            return self.sequence(value, is_attribute)
        elif isinstance(value, dict):
            return self.dictionary(value, is_attribute)
        elif isinstance(value, BaseGeometry):
            return self.geometry(value)
        elif isinstance(value, Model):
            return self.model(value)
        elif isinstance(value, Point):
            return self.point(value)
        elif isinstance(value, Enum):
            return self.enum(value)
        elif isinstance(value, pendulum.DateTime):
            return self.datetime(value)
        else:
            return value

    def encode(self, value):
        return json.dumps(self.pre_encode(value))

    def pre_encode_changes(self, model: Model):
        # TODO: detect new changes and only parse them
        return {}

    def encode_changes(self, model: Model):
        return json.dumps(self.pre_encode_changes(model))
