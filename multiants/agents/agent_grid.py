# -*- coding: utf-8 -*-
import numpy as np
from typing import Any, Dict, Tuple
from .base import Agent

__all__ = ["AgentGrid"]


class AgentGrid(Agent):
    def __init__(self, unique_id, model, size: Tuple[int, int], **kwargs) -> None:
        self.size = size
        super().__init__(unique_id, model, **kwargs)

    def _init_parametters(self, **override_values: Dict[str, Any]):
        self.parametters = {}
        for name, param in self.PARAMETTERS.items():
            param_grid = np.empty(self.size)
            for i, j in param_grid:
                param_grid[i, j] = param.init(
                    self,
                    self.model,
                    override_values.get(name),
                )
            self.parametters[name] = param_grid

    def set(self, param: str, value: Any):
        new_value = self.PARAMETTERS[param].set(value)
        if new_value is not None:
            self.parametters[param] = new_value

    def get(self, param: str, point: Tuple[int, int]):
        return self.parametters[param][point]

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
