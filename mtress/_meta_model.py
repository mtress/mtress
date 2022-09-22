"""The MTRESS meta model itself."""

import pandas as pd
from oemof import solph

from . import Location


class MetaModel:
    """Meta model of the energy system."""

    def __init__(
            self,
            time_index: dict | pd.DatetimeIndex,
            locations=None,
    ):
        """
        Initialize the meta model.

        :param time_index:  time index definition for the soph model
        :param locations: configuration dictionary for locations
        """
        if locations is None:
            locations = dict()
        self._locations = {}

        if type(time_index) == dict:
            self.time_index = time_index = pd.date_range(**time_index)

        self._energy_system = solph.EnergySystem(timeindex=time_index)

        for location_name, location_config in locations.items():
            self._locations[location_name] = Location(
                name=location_name, config=location_config, meta_model=self
            )

    def add_constraints(self, model):
        """Add constraints to the model."""
        for _, location in self._locations:
            location.add_constraints(model)

    def solve(
        self,
        solver: str = "cbc",
        solve_kwargs: dict = None,
        cmdline_options: dict = None,
    ):
        """Solve generated energy system model."""
        model = solph.Model(self.energy_system)
        self.add_constraints(model)

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

    def get_timeseries(self, specifier) -> pd.Series:
        """
        Read and cache time series.

        :param specifier: Data specifier
        """
        return pd.Series(0, index=self.time_index)

        # if self._cache is None:
        #     _series = read_input_data(specifier)
        #     return _series.reindex()

        # return pd.Series(
        #     self._cache[specifier],
        #     index=self.time_index,
        # )
