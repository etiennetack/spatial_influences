# coding: utf-8
from multiants import GeoAgent
from .parametters import Category

__all__ = ["Road"]


class Road(GeoAgent):
    PARAMETTERS = {
        "category": Category(),
    }
    EXPORTED_PARAMETTERS = [
        "category",
    ]
