import numpy as np
import pandas as pd
from oemof import solph

from . import carriers, demands

# from . import technologies


class Location:
    def __init__(self, name: str, config: dict, meta_model):
        self._name = name
        self._meta_model = meta_model

        # Initialize energy carriers
        self._carriers = {}
        for carrier_name, carrier_config in config["carriers"].items():
            assert hasattr(
                carriers, carrier_name
            ), f"Energy carrier {carrier_name} not implemented"

            cls = getattr(carriers, carrier_name)
            self._carriers[cls] = cls(location=self, **carrier_config)

        # Initialize demands
        self._demands = {}
        for demand_name, demand_config in config["demands"].items():
            assert hasattr(
                demands, demand_name
            ), f"Demand {demand_name} not implemented"

            cls = getattr(demands, demand_name)
            self._demands[cls] = cls(location=self, **demand_config)

        # self.technologies = {}
        # for tech_name, tech_config in config.get("technologies", {}):
        #     tech = tech_config.get("technology")

        #     assert hasattr(technologies, tech), f"Technology {tech} not implemented"
        #     techcls = getattr(technologies, tech)

        #     cfg = tech_config.get("parameters")
        #     self.technologies[tech_name] = tech_cls(name=tech_name, location=self, energy_system=energy_system, **cfg)

        # # After all technologies have been added to the location we add interconnections
        # # e.g. connect anergy sources to heat pumps
        # for tech in self.technologies:
        #     tech.add_interconnections()

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


class MetaModel:
    """Meta model of the energy system.0"""

    def __init__(self, config):
        # TODO: Read configuration

        self._locations = {}

        # TODO: Proper initialization of the EnergySystem object
        self.timeindex = idx = pd.date_range(start="2020-01-01", freq="H", periods=10)
        self._energy_system = solph.EnergySystem(timeindex=idx)

    #         for location_name, location_config in config["locations"].items():
    #             self._locations[location_name] = Location(config=location_config, meta_model=self)
    @property
    def energy_system(self):
        """Return reference to generated EnergySystem object."""
        return self._energy_system

    def get_timeseries(self, name):
        """Read and cache time series."""
        # TODO
        return pd.Series(
            np.random.randint(0, 100, size=len(self.timeindex)), index=self.timeindex
        )
