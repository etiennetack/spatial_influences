# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Any, Dict, List, Optional, Sequence, Set, Type
import mesa
import pendulum
from mesa_geo import GeoSpace

if TYPE_CHECKING:
    from shapely.geometry import Point

from .environment import Border, Factor, Raster
from .influences import Gradient, Influence
from .model_time import ModelTime
from .agents import Agent, GeoAgent, AgentCreator
from .logger import Logger
from .utils import random_point_in_bounds


__all__ = ["Model"]


class Model(mesa.Model):
    """Represents a multi-agent model containing agent, environment description,
    time setting, ...

    Args:
        config: TODO.
        logger: TODO.
        random_start_points: TODO.
    """

    # model agent classes by order of execution
    AGENT_CLASSES: Sequence[Type[Agent]] = tuple()

    def __init__(self, config: Dict[str, Any], logger: Logger):
        super().__init__()
        self.config = config
        self.logger = logger
        self.logger.system_log("INITIALISATION START")
        # Time and space
        self.time = ModelTime(
            config["starting_date"],
            {config["timestep"]["unit"]: config["timestep"]["length"]},
            config["timezone"],
        )
        self.scheduled_classes: Set[Type[Agent]] = set()
        self.schedule = mesa.time.RandomActivationByType(self)
        self.schedule.step()  # TODO: Why this first state?!?
        self.grid = GeoSpace(crs=config["crs"])
        self.border = Border(config["border"]["file"], crs=config["crs"])
        # check mesa data collections!!
        # https://mesa.readthedocs.io/en/stable/apis/datacollection.html
        # Influences (init with add influence)
        self.influences: Dict[str, Gradient] = {}
        # Rasters
        self.rasters = self._init_rasters()
        # External factors
        self.factors = self._init_factors()
        # Relationships
        # self.relationships = self._init_relationships()
        # Agents
        self.agents = {}
        self._init_agents()
        self.post_init()

    def _get_nearest_date(self, date, config):
        if date in config:
            return date
        else:
            d = pendulum.parse(date)
            nearest = None
            nearest_dist = None
            for k in config["files"].keys():
                t = pendulum.parse(k)
                if nearest is None or (t - d) < nearest_dist:
                    nearest = k
                    nearest_dist = t - d
            return nearest

    def _init_geoagents(self, agent_class: Type[Agent], config: Dict[str, Any]):
        creator_options = {
            "agent_class": agent_class,
            # "agent_kwargs": agent_config.get("parametters", {}),
            "model": self,
        }
        # if
        if issubclass(agent_class, GeoAgent):
            creator_options["crs"] = self.config["crs"]
        agent_creator = AgentCreator(**creator_options)
        starting_date = self.config["starting_date"]
        nearest_date = self._get_nearest_date(starting_date, config)
        agents = agent_creator.from_file(
            config["files"][nearest_date],
            unique_id=config["unique_id"],
            set_attributes=config["set_attributes"],
        )
        # Add agents to model
        for a in agents:
            self.add_agent(a, config["scheduled"])

    def _init_individuals(self, agent_class: Type[Agent], config: Dict[str, Any]):
        # TODO: Individuals is not a good name find something else
        # (I use it to init the land owner from the configuration file)
        for individual_config in config["individuals"]:
            self.add_agent(
                agent_class(
                    individual_config["unique_id"],
                    self,
                ),  # TODO: add more parametters
                config["scheduled"],
            )

    def _init_agents(self):
        for agent_config in self.config["agents"]:
            # Fetch agent class according to class name
            agent_class: Type[Agent] = next(
                ac
                for ac in self.AGENT_CLASSES
                if ac.__name__ == agent_config["class_name"]
            )
            # GeoAgents
            if "files" in agent_config:
                self._init_geoagents(agent_class, agent_config)
            # Agents
            if "individuals" in agent_config:
                self._init_individuals(agent_class, agent_config)
            self.logger.system_log(f"{agent_class.__name__.upper()} DONE")

    def post_init(self):
        """Override this method for custom initialisations."""
        pass

    def _init_factors(self) -> dict[str, Factor]:
        """Init all factors from the model configuration"""
        factors = {}
        # CSV options
        csv_options = self.config["csv_options"]
        if "skipfooter" in csv_options:
            csv_options["engine"] = "python"
        # Load external factors
        for factor in self.config["factors"]:
            factors[factor["name"]] = Factor(
                factor["files"],
                factor["index_column"],
                factor["probabilities_column"],
                csv_options,
            )
        return factors

    def _init_rasters(self) -> dict[str, Raster]:
        """Init all rasters from the model configuration."""
        rasters = {}
        for raster in self.config["rasters"]:
            r = Raster(raster["file"], raster["undefined_value"], self.grid.crs)
            rasters[raster["name"]] = r
        return rasters

    # def _init_relationships(self) -> dict[str, Relationship]:
    #     """TODO"""
    #     relationships = {}
    #     # name_to_class = {c.__name__: c for c in self.AGENT_CLASSES}
    #     return relationships

    # def add_relationship(self, name: str, relationship: Relationship):
    #     self.relationships[name] = relationship

    def set_influence(self, name: str, infl_functions: Optional[List[Influence]]):
        """Add or change an influence to the model.

        Args:
            name: influence's name.
            infl_functions: influence functions.
        """
        if infl_functions is None:
            self.influences.pop(name)
        else:
            self.influences[name] = Gradient(
                model=self,
                influences=infl_functions,
            )

    def add_agent(self, agent: Agent, schedule: bool = False):
        """Add an agent/object to the model.

        Args:
            agent (mesa.Agent or geo_mesa.GeoAgent): an agent/object.
            schedule (bool or optional): True if agent is updated for
                each time steps.
        """
        # Get agent's set and initialize it if not already done
        self.agents[type(agent)] = self.agents.get(type(agent), set())
        # Add agent to set
        self.agents[type(agent)].add(agent)
        # If agent is a GeoAgent add it to space
        if issubclass(type(agent), GeoAgent):
            self.grid.add_agents([agent])
        # Add agent to model schedule if they need to take actions during model
        # execution
        if schedule:
            self.schedule.add(agent)
            self.scheduled_classes.add(type(agent))

    def remove_agent(self, agent: Agent):
        """Remove an agent/object from the model.

        Args:
            agent (mesa.Agent or geo_mesa.GeoAgent): an agent/object that has
                been previously added to the model.
        """
        self.agents[type(agent)].remove(agent)
        if issubclass(type(agent), GeoAgent):
            self.grid.remove_agent(agent)
        if agent in self.schedule._agents:
            self.schedule.remove(agent)

    @property
    def bounds(self) -> Dict[str, float]:
        """A dictionary containing the model bounds."""
        minx, miny, maxx, maxy = self.border.bounds
        return {
            "west": minx,
            "east": maxx,
            "south": miny,
            "north": maxy,
        }

    def get_random_position(self) -> Point:
        """Generate a random point situated inside the environment's bounds.

        Returns: a random position
        """
        return random_point_in_bounds(self.border.shape)

    def log(self, message: str, error: bool = False):
        self.logger.model_log(message, self, error)

    def reset_influences(self):
        for infl in self.influences.values():
            infl.reset()

    def step(self):
        """Run the model for one step."""
        self.log("IN PROGRESS")
        # Call step methods of all scheduled agents
        for agent_class in self.AGENT_CLASSES:
            if agent_class in self.scheduled_classes:
                self.schedule.step_type(agent_class, True)
                self.log(f"{agent_class.__name__.upper()} DONE")
        self.log("AGENTS DONE")
        # Reset all influences
        self.reset_influences()
        self.log("INFLUENCE RESET DONE")
        # Step forward model's time
        self.time.step()
