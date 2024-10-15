# coding: utf-8
from multiants import GeoAgent
from .parametters import Size

__all__ = ["River"]


class Road(GeoAgent):
    PARAMETTERS = {
        "size": Size(),
    }
    EXPORTED_PARAMETTERS = [
        "size",
    ]
