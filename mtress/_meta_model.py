"""The MTRESS meta model itself."""

import h5py
import pandas as pd
from oemof import solph

from . import carriers, demands, technologies
from ._helpers import get_from_dict, read_input_data


class Location:
    """Location of a MTRESS meta model."""

    def __init__(self, name: str, config: dict, meta_model):
        """
        Create location instance.

        :param name: User friendly name of the location
        :param config: Configuration dict for this location
        :param meta_model: Reference to the meta model
        """
        self._name = name
        self._meta_model = meta_model

        # Initialize energy carriers
        self._carriers = {}
        for carrier_name, carrier_config in config.get("carriers", {}).items():
            assert hasattr(
                carriers, carrier_name
            ), f"Energy carrier {carrier_name} not implemented"

            cls = getattr(carriers, carrier_name)
            self._carriers[cls] = cls(location=self, **carrier_config)

        # Initialize demands
        self._demands = {}
        for demand_name, demand_config in config.get("demands", {}).items():
            assert hasattr(
                demands, demand_name
            ), f"Demand {demand_name} not implemented"

            cls = getattr(demands, demand_name)
            self._demands[cls] = cls(location=self, **demand_config)

        self._components = {}
        for component_name, component_config in config.get("components", {}).items():
            technology_name = component_config["technology"]
            assert hasattr(
                technologies, technology_name
            ), f"Technology {technology_name} not implemented"

            cls = getattr(technologies, technology_name)
            self._components[component_name] = cls(
                name=component_name, location=self, **component_config["parameters"]
            )

        # After all components have been added, add interconnections
        for _, component in self._components.items():
            component.add_interconnections()

    def add_constraints(self, model: solph.Model):
        """Add constraints to the model."""
        for _, component in self._components.items():
            component.add_constraints(model)

    @property
    def name(self):
        """Return name of the location."""
        return self._name

    @property
    def energy_system(self):
        """Return reference to EnergySystem object of the metamodel."""
        return self._meta_model.energy_system

    @property
    def meta_model(self):
        """Return meta model this location belongs to."""
        return self._meta_model

    def get_carrier(self, carrier: type):
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        return self._carriers[carrier]

    def get_demand(self, demand: type):
        """
        Return demand object.

        :param demand: Demand type
        """
        return self._demands[demand]

    def get_components(self, technology: type):
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [
            obj for _, obj in self._components.items() if isinstance(obj, technology)
        ]


class MetaModel:
    """Meta model of the energy system."""

    def __init__(self, config: dict):
        """
        Initialize the meta model.

        :param config: Configuration dictionary
        """
        self._locations = {}

        if (
            cache_file := get_from_dict(config, "general.cache", default=None)
            is not None
        ):
            self._cache = h5py.File(cache_file, "r")
        else:
            self._cache = None

        # TODO: Proper initialization of the EnergySystem object
        self.timeindex = idx = pd.date_range(start="2020-01-01", freq="H", periods=10)
        self._energy_system = solph.EnergySystem(timeindex=idx)

        for location_name, location_config in config.get("locations", {}).items():
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
        if self._cache is None:
            _series = read_input_data(specifier)
            return _series.reindex()
        else:
            return pd.Series(
                self._cache[specifier],
                index=self.timeindex,
            )
