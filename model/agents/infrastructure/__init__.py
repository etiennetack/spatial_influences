# coding: utf-8
from abmlib import GeoAgent
from .parametters import Category

__all__ = ["Infrastructure"]


class Infrastructure(GeoAgent):
    PARAMETTERS = {"category": Category()}
    EXPORTED_PARAMETTERS = ["category"]
    RULES = {}
    ACTIONS = {}
