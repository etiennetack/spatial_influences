# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import cast, TYPE_CHECKING
import pendulum

if TYPE_CHECKING:
    from pendulum.datetime import DateTime
    from pendulum.duration import Duration


class DateTimeFormat:
    def __init__(self, date_format: str, time_format: str):
        self.date = date_format
        self.time = time_format

    def parse_date(self, datetime: DateTime) -> str:
        return datetime.format(self.date)

    def parse_time(self, datetime: DateTime) -> str:
        return datetime.format(self.time)


class ModelTime:
    """
    Time representation for the model.

    Args:
        start: a date string in ISO 8601.
        timestep: the length of timesteps.
        timezone: timezone on the studied area.
        date_format: date format for string representation.
        time_format: time format for string representation.
    """

    def __init__(
        self,
        start: str,
        timestep: dict[str, int],
        timezone: str = "GMT",
        date_format: str = "DD/MM/YYYY",
        time_format: str = "HH:mm:ss",
    ):
        # this is correct see: https://pendulum.eustace.io/docs/#parsing
        self._current: DateTime = cast(
            pendulum.DateTime,
            pendulum.parse(  # pyright: ignore [reportPrivateImportUsage]
                start,
                tz=timezone,
            ),
        )
        self._timestep = pendulum.duration(**timestep)
        self._format = DateTimeFormat(date_format, time_format)

    def step(self):
        self._current += self.timestep

    @property
    def current(self) -> DateTime:
        return self._current

    @property
    def timestep(self) -> Duration:
        return self._timestep

    @timestep.setter
    def timestep(self, new: Duration):
        self._timestep = new

    def __str__(self) -> str:
        return self.current.format(self._format.date + " " + self._format.time)

    def parse_date(self) -> str:
        return self._format.parse_date(self.current)

    def parse_time(self) -> str:
        return self._format.parse_time(self.current)

    @property
    def date(self) -> str:
        # TODO: Remove, but verify where it is used
        return self.parse_date()

    @property
    def time(self) -> str:
        # TODO: Remove, but verify where it is used
        return self.parse_time()


if __name__ == "__main__":
    # time = Time("2019-01-01T12:45:30", {Unit.MINUTES: 45}, "Pacific/Fiji")
    time = ModelTime("2019-01-01", {"minutes": 45}, "Pacific/Fiji")
    print(time.timestep)
    print(time.current)
    print("TEST", time.date, time.time)
    test = time.current
    for _ in range(3):
        time.step()
        print(time)
    print(test)
