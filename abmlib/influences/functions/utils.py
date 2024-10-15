# -*- coding: utf-8 -*-
from typing import Callable

from math import tanh, pi

__all__ = ["InvalidInfluenceFunction", "tanh_y"]


class InvalidInfluenceFunction(Exception):
    pass


def tanh_y(y: float) -> Callable[[float], float]:
    return lambda x: tanh(x * 2 * pi / y)
