"""Handle data."""

from enum import IntEnum

import numpy as np
import pandas as pd

TimeseriesSpecifier = str | pd.Series | list | float

class TimeseriesType(IntEnum):
    POINT = 0
    INTERVAL = 1


class DataHandler:
    """Handle data provided in auxiliary files."""

    def __init__(self, timeindex: pd.DatetimeIndex):
        """Initialize data handler."""
        self.timeindex = timeindex
        self._cache: dict[pd.DataFrame] = {}

    def get_timeseries(
            self,
            specifier: TimeseriesSpecifier,
            kind: TimeseriesType
        ):
        """
        Prepare a time series for the usage in MTRESS.

        This method takes a time series specifier and reads a
        time series from a file or checks a provided series for completeness.
        """
        if kind == TimeseriesType.INTERVAL:
            target_index = self.timeindex[:-1]
        else:
            target_index = self.timeindex

        match specifier:
            case str() if specifier.startswith("FILE:"):
                _, file, column = specifier.split(":", maxsplit=2)
                series = self._read_from_file(file, column)

                # Call function again to check series for consistency
                return self.get_timeseries(series, kind=kind)

            case pd.Series() as series:
                if isinstance(series.index, pd.DatetimeIndex):
                    matching_index = target_index.isin(series.index)
                    if not matching_index.all():
                        raise KeyError(
                            "Provided series doesn't cover time index: "
                            + f"{list(self.timeindex[matching_index == False])}"
                        )
                    return series.reindex(target_index)
                else:
                    return pd.Series(
                        data=series.values,
                        index=target_index,
                    )

            case list() | np.ndarray() as values:
                return pd.Series(data=values, index=target_index)

            case float() | int() as value:
                return pd.Series(data=value, index=target_index)

            case _:
                raise ValueError(f"Time series specifier {specifier} not supported")

    def _read_from_file(self, file: str, column: str):
        """Read a column from a file."""
        if file in self._cache and column in self._cache[file]:
            # This column was already read from the file
            return self._cache[file][column]

        if file.lower().endswith(".csv"):
            self._cache[file] = data = pd.read_csv(file, index_col=0, parse_dates=True)
            return data[column]

        if file.lower().endswith(".h5"):
            raise NotImplementedError("HDF5 file support not implemented yet")

        raise NotImplementedError(f"Unsupported file format for file {file}")
