"""The MTRESS meta model itself."""


from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterable

import pandas as pd
from oemof import solph

if TYPE_CHECKING:
    from ._location import Location
    from ._abstract_component import AbstractSolphComponent, AbstractComponent

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

    def add_location(self, location: Location):
        """Add a new location to the meta model."""
        location.assign_meta_model(self)
        self.locations[location.name] = location

    @property
    def components(self) -> Iterable[AbstractComponent]:
        """Return an iterator over all components of all locations."""
        for _, location in self.locations.items():
            component: AbstractComponent

            # Iterate over carriers, demands and all technologies
            for component in [
                *location.carriers,
                *location.demands,
                *location.technologies,
            ]:
                yield component


class SolphModel:
    """Model adapter for MTRESS meta model."""

    data: DataHandler

    energy_system: solph.EnergySystem
    model: solph.Model

    components: dict = {}

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

        self.data = DataHandler(self.timeindex)

        # Registry of solph components
        self._solph_components = {}
        self.energy_system = solph.EnergySystem(timeindex=self.timeindex)

        # Store a reference to the solph model
        for component in self._meta_model.components:
            component.register_solph_model(self)

    def add_solph_component(
        self,
        mtress_component: AbstractSolphComponent,
        label: str,
        solph_component: Callable,
        **kwargs,
    ):
        """Add a solph component, e.g. a Bus, to the solph energy system."""
        # Generate a unique label
        _full_label = self.get_label(mtress_component, label)

        if (mtress_component, label) in self._solph_components:
            raise KeyError(f"Solph component named {_full_label} already exists")

        _component = solph_component(label=_full_label, **kwargs)
        self._solph_components[(mtress_component, label)] = _component
        self.energy_system.add(_component)

        return _component

    def get_label(self, mtress_component, label):
        """Generate a unique label for a component."""
        return ":".join([*mtress_component.identifier, label])

    def get_solph_component(self, mtress_component: AbstractSolphComponent, label: str):
        """Get a solph component by component and label."""
        return self._solph_components[(mtress_component, label)]

    def build_solph_energy_system(self):
        """Build the `oemof.solph` representation of the energy system."""
        for component in self._meta_model.components:
            component.build_core()

        for component in self._meta_model.components:
            component.establish_interconnections()

        # TODO: Add inter-location connections

    def build_solph_model(self):
        """Build the `oemof.solph` representation of the model."""
        self.model = solph.Model(self.energy_system)

        for component in self._meta_model.components:
            component.add_constraints()

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
