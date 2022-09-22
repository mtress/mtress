"""The MTRESS meta model itself."""

from time import time

import pandas as pd
from oemof import solph

from . import Location


class MetaModel:
    """Meta model of the energy system."""

    def __init__(
        self,
        time_index: dict | list | pd.DatetimeIndex,
        locations=None,
    ):
        """
        Initialize the meta model.

        :param time_index:  time index definition for the soph model
        :param locations: configuration dictionary for locations
        """
        if isinstance(time_index, dict):
            self.time_index = time_index = pd.date_range(**time_index)
        elif isinstance(time_index, list):
            raise NotImplemented("Not implemented yet")
            # TODO: Cast list of times to pd.DatetimeIndex
        else:
            self.time_index = time_index

        self._energy_system = solph.EnergySystem(timeindex=self.time_index)

        # Initialize locations
        self._locations = {}
        if locations is not None:
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
