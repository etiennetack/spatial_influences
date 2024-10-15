# coding: utf-8
from enum import Enum
from multiants import Parametter

__all__ = [
    "Category",
]


class Category(Parametter):
    class Type(Enum):
        STEPWAY = 1
        """Stepway (usually in dirt)."""
        PATH = 2
        """A bigger stepway."""
        SMALL_ROAD = 3
        """A road that is praticable with a vehicule."""
        ROAD = 4
        """Regular road."""

    # Widths in meters
    WIDTH = {
        Type.STEPWAY: (0.5, 1.5),
        Type.PATH: (2, 2.5),
        Type.SMALL_ROAD: (3, 4),
        Type.ROAD: (6, 8),
    }

    def init(self, agent, model, override=None):
        if override is not None:
            try:
                return next(
                    (rtype for rtype in self.Type if rtype.value == override)
                )
            except StopIteration:
                return None
        else:
            super().init(agent, model)
