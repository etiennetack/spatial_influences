# coding: utf-8
import random
from math import sqrt
import shapely.affinity as affinity
from shapely.geometry import Polygon

__all__ = ["DwellingFactory", "ImpossibleBuild"]


class ImpossibleBuild(Exception):
    pass


class DwellingFactory:
    """Houses generation in function of environment and agent preferences."""

    def __init__(self, model):
        """Dwelling factory constructor

        Args:
            model (Model): reference to a model instance.
        """
        self._model = model

    def build(self, inhabitant, desired_area, gradient_batches=2, try_n=5):
        """Build new house shapes.

        Returns:
            Polygon: a polygon to be used as a shape for a new house.
        """
        if try_n == 0:
            raise ImpossibleBuild()
        # Generate a random rectangle
        house = self.generate_shape(desired_area)
        # Define it's orientation
        house = self.define_orientation(house)
        # Find the best spot with the help of the influences module`
        context = {
            "agent": inhabitant,
            "shape": house,
        }
        gradient = self._model.influences["HouseBuilding"]
        point = gradient.compute_batches(context, max(gradient_batches - 1, 1))
        # Translate
        house = affinity.translate(house, *point.coords[0])
        # Check if the generated shape is not beyond border
        if not self._model.border.is_valid(house):
            # Retry
            # WARNING: This can cause infinit loops
            return self.build(
                inhabitant,
                desired_area,
                gradient_batches,
                try_n - 1,
            )
        else:
            # Return shape of the new house
            return house

    def random_build(self, inhabitant, desired_area):
        """Generate a random building."""
        house = self.generate_shape(desired_area)
        house = self.define_orientation(house)
        random_position = self._model.border.random_point()
        house = affinity.translate(house, *random_position.coords[0])
        return house

    def generate_shape(self, desired_area, ratio_min=2 / 3, ratio_max=3 / 2):
        """Generate a random rectangular shape.

        Args:
            desired_area (float): desired area in square meters.
            ratio_min (float): minimum ratio of the resulting rectangle.
            ratio_max (float): maximum ratio of the resulting rectangle.

        Raises:
            Exception: if minimum ratio is greater than maximum ratio.

        Returns:
            shapely.geometry.Polygon: a new rectangle to place somewhere.
        """
        # Maybe use this method for the generation for extensions
        assert ratio_min <= ratio_max, "ratio_min is greater than ratio_max"

        ratio = random.uniform(ratio_min, ratio_max)
        width = sqrt(desired_area / ratio)
        height = sqrt(desired_area * ratio)

        return Polygon(
            [
                (-width / 2, +height / 2),
                (+width / 2, +height / 2),
                (+width / 2, -height / 2),
                (-width / 2, -height / 2),
            ]
        )

    def define_orientation(self, geometry):
        # orientation with neighbors?
        # orientation with nearest roads? --> not possible right now
        # random orientation
        return affinity.rotate(geometry, random.randint(1, 360))
