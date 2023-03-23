"""The MTRESS meta model itself."""


from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple

import graphviz
import pandas as pd
from oemof.solph import Bus, EnergySystem, Model
from oemof.solph.components import GenericStorage, Sink, Source, Transformer

from ._data_handler import DataHandler

if TYPE_CHECKING:
    from ._abstract_component import AbstractComponent, AbstractSolphComponent
    from ._location import Location


SOLPH_SHAPES = {
    Source: "trapezium",
    Sink: "invtrapezium",
    Bus: "ellipse",
    Transformer: "octagon",
    GenericStorage: "cylinder",
}


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
        self._locations: List[Location] = []

    @classmethod
    def from_config(cls, config: dict):
        """Generate the meta model from a configuration dict."""
        # TODO: Implement me!
        raise NotImplementedError("Not implemented yet")

    def add_location(self, location: Location):
        """Add a new location to the meta model."""
        location.assign_meta_model(self)
        self._locations.append(location)

    @property
    def locations(self) -> Iterable[Location]:
        """Iterate over all locations."""
        for location in self._locations:
            yield location

    @property
    def components(self) -> Iterable[AbstractComponent]:
        """Iterate over all components of all locations."""
        for location in self.locations:
            for component in location.components:
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

    def generate_graph(self, detail: bool = False) -> graphviz.Digraph:
        """Generate a graph representation of the energy system."""
        dot = graphviz.Digraph()

        for location in self._meta_model.locations:
            with dot.subgraph() as location_subgraph:
                location_subgraph.attr(label=location.name)

                for component in location.components:
                    component: AbstractSolphComponent

                    if detail:
                        component_subgraph = graphviz.Digraph()

                    for solph_component in component.solph_components:
                        if detail:
                            component_subgraph.node(
                                solph_component.label,
                                label=solph_component.short_label,
                                shape=SOLPH_SHAPES.get(
                                    type(solph_component), "rectangle"
                                ),
                            )

                        for output in solph_component.outputs:
                            if detail:
                                dot.edge(solph_component.label, output.label)
                            else:
                                dot.edge(
                                    solph_component.mtress_component.identifier,
                                    output.mtress_component.identifier,
                                )

                    if detail:
                        location_subgraph.subgraph(component_subgraph)
                    else:
                        location_subgraph.node(
                            component.identifier, label=component.name
                        )
        return dot

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
