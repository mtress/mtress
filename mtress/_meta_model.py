"""The MTRESS meta model itself."""

import pandas as pd
from oemof import solph

from . import Location


class MetaModel:
    """Meta model of the energy system."""

    def __init__(
        self,
        timeindex: dict | list | pd.DatetimeIndex,
        locations=None,
    ):
        """
        Initialize the meta model.

        :param time_index:  time index definition for the soph model
        :param locations: configuration dictionary for locations
        """
        match timeindex:
            case list() as values:
                self.timeindex = pd.DatetimeIndex(values)
            case pd.DatetimeIndex as idx:
                self.timeindex = idx
            case dict() as params:
                self.timeindex = pd.date_range(**params)
            case _:
                raise ValueError("Don't know how to process timeindex specification")

        self._cache: dict[pd.DataFrame] = {}

        self._energy_system = solph.EnergySystem(timeindex=self.timeindex)

        # Initialize locations
        self._locations = {}
        if locations is not None:
            for location_name, location_config in locations.items():
                self._locations[location_name] = Location(
                    name=location_name, meta_model=self, **location_config
                )

    def get_timeseries(self, specifier: str | pd.Series | list):
        """
        Prepare a time series for the usage in MTRESS.

        This method takes a time series specifier and reads a
        time series from a file or checks a provided series for completeness.
        """
        match specifier:
            case str() if specifier.startswith("FILE:"):
                _, file, column = specifier.split(":", maxsplit=2)
                series = self._read_from_file(file, column)

                # Call function again to check series for consistency
                return self.get_timeseries(series)

            case pd.Series() as series:
                if not self.timeindex.isin(series.index).all():
                    raise KeyError("Provided series doesn't cover time index")

                return series.reindex(self.timeindex)

            case list() as values:
                if not len(values) == len(self.timeindex):
                    raise ValueError("Length of list differs from time index length")

                return pd.Series(data=values, index=self.timeindex)

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

    def _add_constraints(self, model):
        """Add constraints to the model."""

    def add_location(self, location):
        self._locations[location.name] = location

    def solve(
        self,
        solver: str = "cbc",
        solve_kwargs: dict = None,
        cmdline_options: dict = None,
    ):
        for location in self._locations.values():
            location.add_interconnections()

        """Solve generated energy system model."""
        model = solph.Model(self.energy_system)
        self._add_constraints(model)

        kwargs = {"solver": solver}
        if solve_kwargs is not None:
            kwargs["solve_kwargs"] = solve_kwargs

        if cmdline_options is not None:
            kwargs["cmdline_options"] = cmdline_options

        model.solve(**kwargs)

        return model

    @property
    def energy_system(self):
        """Return reference to generated EnergySystem object."""
        return self._energy_system
