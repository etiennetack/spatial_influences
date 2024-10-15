# -*- coding: utf-8 -*-
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

import pandas as pd
import re
from collections import OrderedDict

__all__ = ["Factor"]


class Factor:
    """This class load factors from CSV files and allow us to make
    extrapolations when there are more than one dataset.
    """

    def __init__(
        self,
        files: Dict[int, str],
        index: str,
        probabilities: str,
        csv_options: Dict[str, Any],
    ):
        """Factor constructor.

        Args:
            files: paths to files in a dictionary
                   (keys are years and values are paths).
            index: name of the column who describe the index values.
            probabilities: name of the column who contain probabilities.
            csv_options: description of how the csv file is coded.
        """
        # load data from CSVs
        self._data = {}
        for year, path in files.items():
            data = pd.read_csv(path, index_col=index, **csv_options)
            self._data[year] = data[probabilities]

        # make extrapolations
        self._lines = {}
        years = list(self._data.keys())
        if len(years) == 1:
            # there is only one dataset
            data_0 = self._data[years[0]]
            time = (-float("inf"), float("inf"))
            self._lines[time] = OrderedDict()
            for i in data_0.index:
                self._lines[time][i] = self._make_constant(data_0[i])
        else:
            # make constant before first year
            data_0 = self._data[years[0]]
            time = (-float("inf"), int(years[0]))
            self._lines[time] = OrderedDict()
            for i in data_0.index:
                self._lines[time][i] = self._make_constant(data_0[i])
            # make lines between intermediates years
            for d in range(len(years) - 1):
                data_d = self._data[years[d]]
                data_next = self._data[years[d + 1]]
                time = (int(years[d]), int(years[d + 1]))
                self._lines[time] = OrderedDict()
                for i in data_d.index:
                    self._lines[time][i] = self._make_line(
                        (time[0], data_d[i]),
                        (time[1], data_next[i]),
                    )
            # make constant after last year
            data_l = self._data[years[-1]]
            time = (int(years[-1]), float("inf"))
            self._lines[time] = OrderedDict()
            for i in data_l.index:
                self._lines[time][i] = self._make_constant(data_l[i])

    def _make_constant(self, value) -> Callable[[float], float]:
        """Create a constant function from a given value.

        Args:
            value: the constant value.
        """
        return lambda _: value

    def _make_line(
        self, point_a: Tuple[float, float], point_b: Tuple[float, float]
    ) -> Callable[[float], float]:
        """Create a linear function between two given points.

        Args:
            point_a: starting point.
            point_b: ending point.
        """
        a = (point_b[1] - point_a[1]) / (point_b[0] - point_a[0])
        b = -(a * point_b[0]) + point_b[1]
        return lambda x: a * x + b

    def get_data(self, year: int) -> pd.Series:
        """Get data for a given year, this function uses the precomputed
        extrapolations function.

        Args:
            year: year of the wanted dataset.
        """
        interval = None
        # Find interval
        for years, lines in self._lines.items():
            inf, sup = years
            if inf <= year <= sup:
                interval = lines
                break
        # Return values
        if interval is not None:
            first_dataset = next(iter(self._data.values()))
            return pd.Series(
                [interval[i](year) for i in first_dataset.index],
                index=first_dataset.index,
                name=first_dataset.name,
                dtype=first_dataset.dtype,
            )
        else:
            # TODO refactor the code to get rid of it.
            raise Exception("This exception should be unreachable.")

    def get_prob(self, year: int, value: Any) -> float:
        """Get the probability for a value at a given date.

        Args:
            year: year for the wanted probability.
            value: value of the index in the dataset.
        """
        interval = None
        for years, lines in self._lines.items():
            inf, sup = years
            if inf <= year <= sup:
                interval = lines
        if interval is not None:
            return interval[value](year)
        else:
            # TODO refactor the code to get rid of it.
            raise Exception("This exception should be unreachable.")

    def roulette_wheel(
        self,
        data: pd.Series,
        result_pattern: str = "NULL",
        index_range: Optional[Tuple[int, int]] = None,
    ) -> Any | Sequence[str]:
        """Make a roulette wheel, that returns a random value among data's values.

        If `result_pattern` (a REGEX) has been set, it returns a sequence that
        contains the matches of the randomly chosen value.

        Args:
            data: a vector of weighted values generated by the
                `get_data` method.
            result_pattern: Regex pattern to parse the result column.
            index_range: A range to limit the inputs.
        """
        if index_range:
            assert index_range[0] <= index_range[1], f"{index_range} not valid"
            data = data.iloc[index_range[0] : index_range[1]]
        res = data.sample(replace=True, weights=list(data), axis=0).index.values[0]
        if result_pattern == "NULL":
            return res
        else:
            pattern = re.compile(result_pattern)
            regex_res = pattern.findall(res)
            if regex_res is not None:
                return regex_res[0]
            raise Exception("`{}` doesnt match `{}`".format(result_pattern, res))
