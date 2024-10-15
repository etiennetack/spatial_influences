# coding: utf8
import random
from math import pi, copysign
from shapely.geometry import Polygon
from multiants.geometry import Vector2, shape_index, extract_points

__all__ = ["ExtensionFactory"]


class ExtensionFactory:
    """Extensions generation from a given household."""

    def __init__(self, house):
        """Extension factory constructor.

        Args:
            house (Household): Household agent that need an extension.
        """
        self._house = house

    def is_square_angle(self, angle, error_margin=pi / 8):
        """Check if an angle is square.

        Args:
            angle (float): An angle in radians.
            error_margin (float, optional): Maximum authorized deviation.

        Returns:
            True if the given angle is square, False otherwise.
        """
        # get error_margin from config file
        return (pi / 2 - error_margin) <= angle <= (pi / 2 + error_margin)

    def _extruded_building(self, start, lenght, width):
        """Build an extension from a point and two translation vectors.

        Args:
            start (shapely.geometry.Point): translation starting point.
            lenght (Vector2): translation vector for the length.
            width (Vector2): translation vector for the width.

        Returns:
            shapely.geometry.Polygon: the new extension shape.
        """
        a = start
        b = width.translate_point(start)
        c = lenght.translate_point(width.translate_point(start))
        d = lenght.translate_point(start)
        return Polygon(
            [
                a.coords[0][:2],  # Z axis is useless
                b.coords[0][:2],
                c.coords[0][:2],
                d.coords[0][:2],
            ]
        )

    def build(self, desired_area, min_support_lenght=2.0):
        """Look over the home's shape to build all possible extensions.

        Args:
            desired_area (float): desired extension area constraint.
            min_support_lenght (float, optional): minimum wall length required
                to support a new extension.

        Yields:
            shapely.geometry.Polygon: Possible extensions.
        """
        for a, b, c, d in extract_points(self._house._buildings["main"]):
            ab_vector = Vector2.from_points(a, b)
            bc_vector = Vector2.from_points(b, c)
            cd_vector = Vector2.from_points(c, d)
            abc_angle = ab_vector.angle(bc_vector)
            bcd_angle = bc_vector.angle(cd_vector)

            if self.is_square_angle(abc_angle):
                # filling extensions
                if (
                    self.is_square_angle(bcd_angle)
                    # ab and bc are heading the same direction
                    and copysign(1, ab_vector.dot(cd_vector)) == 1
                ):
                    yield Polygon(
                        [
                            a.coords[0][:2],
                            b.coords[0][:2],
                            c.coords[0][:2],
                            bc_vector.translate_point(a).coords[0][:2],
                        ]
                    )
                    continue
                # extruding extensions
                lenght = random.uniform(
                    min_support_lenght, desired_area / min_support_lenght
                )
                width = desired_area / lenght
                # build extension supported by ab
                if ab_vector.norm() >= min_support_lenght:
                    yield self._extruded_building(
                        b,
                        # translations
                        bc_vector.normalize() * -1 * width,
                        ab_vector.normalize() * -1 * lenght,
                    )
                # build extension supported by bc
                if bc_vector.norm() >= min_support_lenght:
                    yield self._extruded_building(
                        b,
                        # translations
                        bc_vector.normalize() * -1 * width,
                        ab_vector.normalize() * -1 * lenght,
                    )

    def _check_neighbor_distance(self, house_core, old_house_core, min_houses_distance):
        # overlaps with others objects
        neighbors = (
            self._house.model.grid.get_neighbors_within_distance(self._house, 25)
            # TODO: Put this in model parameters (in config)
        )
        for n in neighbors:
            if self._house.shape != n.shape:
                # distances before and after extension
                old_distance = old_house_core.distance(n.shape)
                distance = house_core.distance(n.shape)
                # if neighbor is too near
                if distance < min_houses_distance:
                    # if making the extension decrease the distance
                    if distance < old_distance:
                        return False
                # last check to prevent overlaps
                # because some times the above checks are insuffisants
                if house_core.intersects(n.shape):
                    return False
        return True

    def _check_intersects(self, house_core, extensions):
        return all((not house_core.intersects(ext) for ext in extensions))

    def check(self, extension, min_houses_distance=1.0, max_shape_index=1.4):
        """Check whether an extension is valid or not.

        Args:
            extension (shapely.geometry.Polygon): generated extension.
            min_houses_distance (float): minimum distance between houses.
            max_shape_index (float): maximum shape index allowed for the
                house core.

        Returns:
            dict, None: a dictionary containing extension shape and final
                dwelling shape index. Or None if the extension is not valid.
        """
        old_house_core = self._house.get_house_core()
        house_core = self._house.get_house_core([extension])

        if not house_core.is_valid:
            return
        # check slope
        if not self._house.model.topography.check_slope(house_core, pi / 4):
            return
        # extensions cannot intersects detached extensions
        for ext in self._house._buildings["detached"]:
            if house_core.intersects(ext):
                return
        # extensions must touches the house's core
        for ext in self._house._buildings["extensions"]:
            if not house_core.touches(ext):
                return
        # shape index constraint
        global_shape_index = shape_index(house_core)
        if global_shape_index > max_shape_index:
            return
        # overlaps with others objects
        if self._check_neighbor_distance(
            house_core, old_house_core, min_houses_distance
        ):
            return
        # here it's good
        return {
            "extension": extension,
            "house_core": house_core,
            "shape_index": global_shape_index,
        }

        # Redo
        global_shape_index = shape_index(house_core)
        if (
            house_core.is_valid
            # shape index constraint
            and global_shape_index <= max_shape_index
            # check slope
            and self._house.model.topography.check_slope(house_core, pi / 4)
            # overlaps with others objects
            and self._check_neighbor_distance(
                house_core, old_house_core, min_houses_distance
            )
            # extensions cannot intersects detached extensions
            and all(
                (
                    not house_core.intersects(ext)
                    for ext in self._house._buildings["detached"]
                )
            )
            # extensions must touches the house's core
            and all(
                (
                    house_core.touches(ext)
                    for ext in self._house._buildings["extensions"]
                )
            )
            # overlaps with others objects
            and self._check_neighbor_distance(
                house_core, old_house_core, min_houses_distance
            )
        ):
            return {
                "extension": extension,
                "house_core": house_core,
                "shape_index": global_shape_index,
            }
        else:
            return

    def select_extension(self, desired_area, area_margin_rate=0.15):
        """Build valid extensions sort them by shape index
        and choose the first who fit the desired area constraint.

        Args:
            desired_area (float): Desired extension area constraint.
            area_margin_rate (float): define margins for area.
                For example, if `area_margin_rate=.1` the extension's area
                must be between `desired_area * 0.9` and `desired_area * 1.1`.
        Returns:
            dict, None: The selected valid extension. None if there are any.
        """
        # Generate extensions
        extensions_generator = (
            item
            for item in map(self.check, self.build(desired_area))
            if item is not None
        )
        # Sort extensions by shape index
        valid_extensions = sorted(
            extensions_generator, key=lambda item: item["shape_index"]
        )
        for item in valid_extensions:
            min_area = desired_area * (1.0 - area_margin_rate)
            max_area = desired_area * (1.0 + area_margin_rate)
            if min_area <= item["extension"].area <= max_area:
                return item
