# -*- coding: utf-8 -*-
from typing import Callable

from .utils import InvalidInfluenceFunction, tanh_y


def make_balance(
    l_min: float,
    l_zero: float,
    l_max: float,
) -> Callable[[float], float]:
    """Build a balance function.

    Args:
        l_min: minimum distance where the interest function returns -1.
        l_zero: distance where the interest function returns 1.
        l_max: maximum distance from where the interest function returns -1.

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
            return tanh_y(l)(distance - l_min - l / 2)
        elif distance < l_max:
            l = l_max - l_zero  # noqa: E741
            return -tanh_y(l)(distance - l_zero - l / 2)
        else:
            return -1.0

    return f
