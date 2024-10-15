# coding: utf-8
from enum import Enum
from multiants import Parametter

__all__ = ["Category"]


class Category(Parametter):
    class Type(Enum):
        CHURCH = 0
        SCHOOL = 1
        SHOP = 2
        TOILETS = 3
