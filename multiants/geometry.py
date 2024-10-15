# coding: utf-8
from typing import Generator, List
from typing_extensions import Self
from math import sqrt, acos, pow, pi
from decimal import Decimal
from shapely import Polygon, Point

__all__ = [
    "Vector2",
    "shape_index",
    "extract_points",
]


class Vector2(tuple):
    """Class used to represent vectors in 2D space and provide functions
    to handle them.
    """

    def __new__(cls, x: float, y: float) -> Self:
        return tuple.__new__(cls, (x, y))

    @classmethod
    def from_points(cls, a: Point, b: Point) -> Self:
        """Create a new vector from two points.

        Args:
            a: first point.
            b: second point.
        """
        return cls(b.x - a.x, b.y - a.y)

    @property
    def x(self) -> float:
        """x coordinate."""
        return self[0]

    @property
    def y(self) -> float:
        """y coordinate."""
        return self[1]

    def __add__(self, other: Self) -> Self:
        """Add two vectors.

        Args:
            other: another vector.
        """
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Self) -> Self:
        """Subtract two vectors.

        Args:
            other (Vector2): another vector.
        """
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Self | float) -> float | Self:
        """Multiply this vector by a scalar (cross product) or another vector.

        Args:
            other: another vector or a scalar.
        """
        if isinstance(other, Vector2):
            return self.dot(other)
        elif isinstance(other, (int, float)):
            return Vector2(self.x * other, self.y * other)
        # TODO: else raise Exception

    def norm(self) -> float:
        """Norm of vector."""
        return sqrt(pow(self.x, 2) + pow(self.y, 2))

    def normalize(self) -> Self:
        """Normalize this vector.

        Returns:
            Vector2: this vector normalized.
        """
        norm = self.norm()
        return Vector2(self.x / norm, self.y / norm)

    def dot(self, other: Self) -> float:
        """Cross product of two vectors.

        Args:
            other: another vector.
        """
        return self.x * other.x + self.y * other.y

    def angle(self, other: Self) -> float:
        """Get angle between two vectors.

        Args:
            other: another vector.
        """
        x = Decimal.from_float(self.dot(other))
        x /= Decimal.from_float(self.norm()) * Decimal.from_float(other.norm())
        return acos(round(x, 6))

    def det(self, other: Self) -> float:
        """Determinant of two vectors.

        Args:
            other: another vector.
        """
        return self.x * other.y - self.y * other.x

    def oriented_angle(self, other: Self) -> float:
        """Get oriented angle between two vectors.

        Args:
            other: another vector.
        """
        if self.det(other) > 0:
            return self.angle(other)
        else:
            return -self.angle(other)

    def perpendicular(self, alternative_direction=False) -> Self:
        """Get perpendicular vector from this one.

        Args:
            alternative_direction: get the other perpendicular.

        Returns:
            the perpendicular vector.
        """
        if alternative_direction:
            return Vector2(-self.y, self.x)
        else:
            return Vector2(self.y, self.x)

    def translate_point(self, point: Point) -> Point:
        """Translate a point by this vector.

        Args:
            point: point to translate.
        """
        return Point(point.x + self.x, point.y + self.y)


def shape_index(polygon: Polygon) -> float:
    """Shape Index (SI) measure.

    If SI == 1 then polygon is a circle.
    More SI is away from 1, more the polygon has a complex shape.

    Args:
        polygon: given polygon
    """
    # NOTE: .length is perimeter
    return polygon.length / sqrt(polygon.area * pi) * 0.5


def extract_points(
    polygon: Polygon,
    chunk_size: int = 4,
) -> Generator[List[Point], None, None]:
    """Initialize a generator to extract polygon's points by chunks,
    given a settable chunks_size.

    A chunk is a series of consecutive points, it's usefull for angle
    calculation. For example if a polygon has 4 points (ABCD), calling
    `extract_point((ABCD), chunks_size=3)` will yield the following chunks
    (ABC) (BCD) (CDA) (DAB).

    Args:
        shape (shapely.geometry.Polygon): shape to look around.
        chunk_size (int): number of point in each chunk.
    """
    points = polygon.exterior.coords[:-1]
    # ignore last point, because it's the first deduplicated
    nb_points = len(points)
    for i in range(nb_points):
        yield [Point(*points[(i + j) % nb_points]) for j in range(chunk_size)]
