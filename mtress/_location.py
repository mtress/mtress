"""Locations in a meta model."""

from __future__ import annotations

from typing import Dict, Iterable, Set, Tuple

from graphviz import Digraph

from ._abstract_component import AbstractComponent
from ._interfaces import NamedElement
from .carriers._abstract_carrier import AbstractCarrier
from .technologies.grid_connection._abstract_grid_connection import AbstractGridConnection


class Location(NamedElement):
    """
    Location in a MTRESS meta model.

    Functionality: A location is able to collect / accomodate energy
        carriers, components and demands.

    Procedure: Create a meta model first (see meta_model class).
        Afterwards create / initialize an (empty) location
        and add it to the meta model by doing the following:

        house_1 = Location(name='house_1')
        meta_model.add_location(house_1)

    Notice: To allow for automatic connections between the components
        and demands, every energy carrier (e.g. electricity or heat) and
        every component (e.g. a heat pump) can only be defined once
        per location (or left out). To define multiple instances of one
        energy carrier with different configurations, multiple locations
        have to be defined.

    Further procedure is described in the carrier and demand classes.
    """

    def __init__(self, name: str) -> None:
        """
        Create location instance.

        :param name: User friendly name of the location
        """
        super().__init__(name)

        self._carriers: Dict[type, AbstractCarrier] = {}
        self._components: Set[AbstractComponent] = set()
        self._grid_connections: Dict[type, AbstractGridConnection] = {}

    @property
    def identifier(self) -> list[str]:
        """As Location is at the highest level, it's name directly identifies it.
        The list is created for consistency.
        """
        return [self.name]

    def add(self, component: AbstractComponent):
        """Add a component to the location."""
        component.register_location(self)

        match component:
            case AbstractCarrier():
                self._carriers[type(component)] = component
            case AbstractGridConnection():
                self._grid_connections[type(component)] = component
            case _:
                self._components.add(component)

    def connect(
        self,
        connection: type,
        destination: Location,
    ):
        self._grid_connections[connection].connect(
            destination._grid_connections[connection]
        )

    def get_carrier(self, carrier: type) -> AbstractCarrier:
        """
        Return the energy carrier object.

        :param carrier: Carrier type to obtain
        """
        return self._carriers[carrier]

    def get_technology(self, technology: type) -> AbstractComponent:
        """
        Get components by technology.

        :param technology: Technology type
        """
        return [obj for obj in self._components if isinstance(obj, technology)]

    @property
    def components(self) -> Iterable[AbstractComponent]:
        """Iterate over all components."""
        for carrier in self._carriers.values():
            yield carrier

        for grid_connection in self._grid_connections.values():
            yield grid_connection

        for component in self._components:
            yield component

    def graph(self, detail: bool = True, flow_results = None) -> Tuple[Digraph, set]:
        """
        Generate graphviz visualization of the MTRESS location.

        :param detail: Include solph nodes.
        """
        graph = Digraph(name=f"cluster_{self.identifier}")
        graph.attr("graph", label=self.name)

        external_edges = set()

        for component in self.components:
            subgraph, edges = component.graph(detail, flow_results)

            external_edges.update(edges)
            graph.subgraph(subgraph)

        return graph, external_edges
