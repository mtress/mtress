"""The MTRESS meta model itself."""


from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Iterable, Tuple

import pandas as pd
from oemof.solph import EnergySystem, Model

from ._data_handler import DataHandler

if TYPE_CHECKING:
    from ._abstract_component import AbstractComponent, AbstractSolphComponent
    from ._location import Location


class MetaModel:
    """
    Meta model of the energy system.

    Functionality: A meta model acts as a container for the model.
    It contains global information, such as the time / a timeseries,
    as well as defaults which can be overwritten for specific
    locations (e.g. weather data). Once the energy system is about
    to be solved, it makes sureevery location has all the needed
    connections and constraints set.

    Procedure: Create a (basic) meta model by doing the following:
        meta_model = MetaModel()

    Further procedure is described in the location class.
    """

    def __init__(self):
        """Initialize the meta model."""
        self.locations: Dict[str, Location] = {}

    @classmethod
    def from_config(cls, config: dict):
        """Generate the meta model from a configuration dict."""
        # TODO: Implement me!
        raise NotImplementedError("Not implemented yet")

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

    def __init__(
        self,
        meta_model: MetaModel,
        timeindex: dict | list | pd.DatetimeIndex,
    ):
        """
        Initialize model.

        :param timeindex:  time index definition for the soph model
        :param locations: configuration dictionary for locations
        """
        self._meta_model = meta_model
        self._solph_components: Dict[Tuple[AbstractSolphComponent, str], object] = {}

        match timeindex:
            case list() as values:
                self.timeindex = pd.DatetimeIndex(values)
            case pd.DatetimeIndex() as idx:
                self.timeindex = idx
            case dict() as params:
                self.timeindex = pd.date_range(**params)
            case _:
                raise ValueError("Don't know how to process timeindex specification")

        self.data = DataHandler(self.timeindex)

        # Registry of solph components
        self._solph_components = {}
        self.energy_system: EnergySystem = EnergySystem(
            timeindex=self.timeindex, infer_last_interval=False
        )
        self.model: Model = None

        # Store a reference to the solph model
        for component in self._meta_model.components:
            component.register_solph_model(self)

    def generate_label(self, mtress_component, label):
        """Generate a unique label for a component."""
        return ":".join([*mtress_component.identifier, label])

    def build_solph_energy_system(self):
        """Build the `oemof.solph` representation of the energy system."""
        for component in self._meta_model.components:
            component.build_core()

        for component in self._meta_model.components:
            component.establish_interconnections()

        # TODO: Add inter-location connections

    def build_solph_model(self):
        """Build the `oemof.solph` representation of the model."""
        self.model = Model(self.energy_system)

        for component in self._meta_model.components:
            component.add_constraints()

    def solve(
        self,
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

        self.model.solve(**kwargs)

        return self.model
