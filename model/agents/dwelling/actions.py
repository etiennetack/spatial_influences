# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

from multiants import Action
from generation.extension_factory import ExtensionFactory

if TYPE_CHECKING:
    from multiants import Model, Agent


class MakeExtension(Action):
    def apply(self, agent: Agent, model: Model, desired_area: float):
        """Action to build a new extension attached to the main building.

        args:
            desired_area: desired size of the new extension.
        """
        ef = ExtensionFactory(agent)
        new = ef.select_extension(desired_area)

        if new is not None:
            agent.get("shape").add_extension(new["extension"], model.date)
            agent.geometry = agent.get("shape").make_geometry()
