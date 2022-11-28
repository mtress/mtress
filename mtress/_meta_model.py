"""The MTRESS meta model itself."""

from typing import Optional

import pandas as pd
from oemof import solph

from . import Location
from ._abstract_component import AbstractComponent, AbstractSolphComponent
from ._data_handler import DataHandler


class MetaModel:
    """Meta model of the energy system."""

    def __init__(self):
        """Initialize the meta model."""
        self.locations: dict[Location] = {}

    @classmethod
    def from_config(cls, config: dict):
        """Generate the meta model from a configuration dict."""
        # TODO: Implement me!
        raise NotImplementedError("Not implemented yet")

        # def _create_carrier(self, carrier_type: str, carrier_config: dict):
        #     assert hasattr(
        #         mt_carriers, carrier_type
        #     ), f"Energy carrier {carrier_type} not implemented"

        #     cls = getattr(mt_carriers, carrier_type)
        #     self._carriers[cls] = cls(location=self, **carrier_config)

        # def _create_component(self, component_type: str, component_config: dict):
        #     technology_name = component_config["technology"]
        #     assert hasattr(
        #         mt_technologies, technology_name
        #     ), f"Technology {technology_name} not implemented"

        #     cls = getattr(mt_technologies, technology_name)
        #     self._components[component_type] = cls(
        #         name=component_type,
        #         location=self,
        #         **component_config["parameters"],
        #     )

        # def _create_demand(self, demand_type: str, demand_config: dict):
        #     assert hasattr(mt_demands, demand_type), f"Demand {demand_type} not implemented"

        #     cls = getattr(mt_demands, demand_type)
        #     self._demands[cls] = cls(location=self, **demand_config)

    def add_location(self, location):
        """Add a new location to the meta model."""
        self.locations[location.name] = location


class SolphModel:
    """Model adapter for MTRESS meta model."""

    def __init__(
        self,
        meta_model: MetaModel,
        timeindex: dict | list | pd.DatetimeIndex,
    ):
        """Initialize model."""
        self._meta_model = meta_model

        match timeindex:
            case list() as values:
                self.timeindex = pd.DatetimeIndex(values)
            case pd.DatetimeIndex as idx:
                self.timeindex = idx
            case dict() as params:
                self.timeindex = pd.date_range(**params)
            case _:
                raise ValueError("Don't know how to process timeindex specification")

        self._data = DataHandler(self.timeindex)

        self._energy_system = None

    def build_solph_energy_system(self):
        """Build the `oemof.solph` representation of the energy system."""

        self._energy_system = solph.EnergySystem(timeindex=self.timeindex)

        for _, location in self._meta_model.locations.items():
            component: AbstractSolphComponent

            # Build cores of carriers, demands and technologies
            for component in [
                *location.carriers,
                *location.demands,
                *location.technologies,
            ]:
                component.build_core()

            # Build cores of carriers, demands and technologies
            for component in [
                *location.carriers,
                *location.demands,
                *location.technologies,
            ]:
                component.establish_interconnections()

        # TODO: Add inter-location connections

        return self._energy_system

    def build_solph_model(self):
        """Build the `oemof.solph` representation of the model."""
        model = solph.Model(self._energy_system)

        component: AbstractSolphComponent
        for _, location in self._meta_model.locations.items():
            # Add model constraints
            for component in [
                *location.carriers,
                *location.demands,
                *location.technologies,
            ]:
                component.add_constraints(model)

    def solve(
        self,
        model: solph.Model,
        solver: str = "cbc",
        solve_kwargs: dict = None,
        cmdline_options: dict = None,
    ):
        """Solve generated energy system model."""
        kwargs = {"solver": solver}
        if solve_kwargs is not None:
            kwargs["solve_kwargs"] = solve_kwargs

        if cmdline_options is not None:
            kwargs["cmdline_options"] = cmdline_options

        model.solve(**kwargs)

        return model
