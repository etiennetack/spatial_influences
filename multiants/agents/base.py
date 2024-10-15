# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from model import Model

from collections import OrderedDict
from mesa import Agent as MesaAgent

__all__ = ["Agent", "Parametter", "BehaviourRule", "Action"]


class Agent(MesaAgent):
    PARAMETTERS = OrderedDict()
    EXPORTED_PARAMETTERS = []
    RULES = {}
    ACTIONS = {}

    def __init__(self, unique_id: Any, model: Model, **kwargs):
        """Skeleton for all non geographic agents

        Args:
            unique_id: a unique id to identify agents between them.
            model: main model.
            kwargs: any parametter to be used as value for agent's parametters.
        """
        super().__init__(unique_id, model)
        # Cast model to get correct type checking
        self.model: Model = self.model
        # Initialise all parametters
        self._init_parametters(**kwargs)

    def _init_parametters(self, **override_values):
        self.parametters = {}
        for name, param in self.PARAMETTERS.items():
            self.parametters[name] = param.init(
                self, self.model, override_values.get(name)
            )

    def __setattr__(self, name, value):
        """DEPRECATED"""
        if name in self.PARAMETTERS:
            self.set(name, value)
        else:
            super().__setattr__(name, value)

    def get(self, param: str) -> Any:
        return self.parametters[param]

    def set(self, param: str, value: Any):
        new_value = self.PARAMETTERS[param].set(value)
        if new_value is not None:
            self.parametters[param] = new_value

    def do(self, action: str, **kwargs) -> Any:
        self.model.log(f"{self.__class__.__name__} DO {action}")
        return self.ACTIONS[action].apply(self, self.model, **kwargs)

    def step(self):
        for p, v in self.parametters.items():
            # Update dynamic parametters
            updated_param = self.PARAMETTERS[p].update(self, self.model, v)
            if updated_param:
                self.set(p, updated_param)
        for r in self.RULES.values():
            r.apply(self, self.model)


T = TypeVar("T")


class Parametter(Generic[T]):
    def __init__(self, initial_value: T = None, **kwargs):
        self.options = {**kwargs}
        self.initial_value = initial_value

    @abstractmethod
    def init(self, agent: Agent, model: Model, override: Optional[T] = None) -> T:
        if override is not None:
            return override
        else:
            return self.initial_value

    def set(self, value: T) -> T:
        return value

    @abstractmethod
    def update(self, agent: Agent, model: Model, old: T):
        pass


class BehaviourRule:
    def __init__(self, **kwargs):
        self.options = {**kwargs}

    @abstractmethod
    def apply(self, agent: Agent, model: Model, **kwargs):
        pass


class Action:
    def __init__(self, **kwargs):
        self.options = {**kwargs}

    @abstractmethod
    def apply(self, agent: Agent, model: Model, **kwargs):
        pass
