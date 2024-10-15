# -*- coding: utf-8 -*-
from typing import Callable

from .utils import InvalidInfluenceFunction, tanh_y


def make_attraction_repulsion(
    l_min: float,
    l_zero: float,
    l_max: float,
) -> Callable[[float], float]:
    """Build an attraction replusion function.

    Args:
        l_min: minimum distance where the interest function returns -1.
        l_zero: distance where the interest functino returns 1.
        l_max: maximum distance from where the interest function returns 0.

    Raises:
        InvalidInfluenceFunction: if lambda values are not in ascending order.
    """
    if not l_min <= l_zero <= l_max:
        raise InvalidInfluenceFunction("Parameters are not in ascending order.")

    def f(distance: float) -> float:
        if distance <= l_min:
            return -1.0
        elif distance < l_zero:
            l = l_zero - l_min  # noqa: E741
            return tanh_y(l)(distance - l_min) * 2 - 1
        elif distance < l_max:
            l = l_max - l_zero  # noqa: E741
            return -tanh_y(l)(distance - l_zero - l / 2) / 2 + 0.5
        else:
            return 0.0

    return f
