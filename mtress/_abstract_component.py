"""Abstract MTRESS components."""

from __future__ import annotations
from abc import abstractmethod

from typing import TYPE_CHECKING, Callable, Tuple

from graphviz import Digraph
from oemof.solph import Bus
from oemof.solph.components import Source, Sink, Transformer, GenericStorage

from ._interfaces import NamedElement
from ._meta_model import SolphModel

if TYPE_CHECKING:
    from ._location import Location

SOLPH_SHAPES = {
    Source: "trapezium",
    Sink: "invtrapezium",
    Bus: "ellipse",
    Transformer: "octagon",
    GenericStorage: "cylinder",
}


class AbstractComponent(NamedElement):
    """Abstract MTRESS component."""

    def __init__(self, **kwargs) -> None:
        """Initialize a generic MTRESS component."""
        super().__init__(**kwargs)
        self._location = None

    @property
    def identifier(self) -> str:
        """Return identifier of this component."""
        return f"{self.location.identifier}-{self.slug}"

    def assign_location(self, location):
        """Assign component to a location."""
        self._location = location

    @property
    def location(self):
        """Return location this component belongs to."""
        return self._location

    def register_location(self, location: Location):
        """Register this component to a location."""
        if self._location is not None:
            raise KeyError("Location already registered")

        self._location = location

    @property
    def meta_model(self):
        """Return meta model this component belongs to."""
        return self.location.meta_model

    @abstractmethod
    def graph(self, detail: bool = False) -> Tuple[Digraph, set]:
        """Draw a graph representation of the component."""


class AbstractSolphComponent(AbstractComponent):
    """Interface for components which can be represented in `oemof.solph`."""

    def __init__(self, **kwargs) -> None:
        """Initialize component."""
        super().__init__(**kwargs)

        self._solph_components: list = []
        self._solph_model: SolphModel = None

    def register_solph_model(self, solph_model: SolphModel) -> None:
        """Store a reference to the solph model."""
        if self._solph_model is not None:
            raise KeyError("SolphModel already registered")

        self._solph_model = solph_model

    def create_solph_component(self, label: str, component: Callable, **kwargs):
        """Create a solph component and add it to the solph model."""
        _full_label = f"{self.identifier}-{label}"

        if label in self._solph_components:
            raise KeyError(f"Solph component named {_full_label} already exists")

        _component = component(label=_full_label, **kwargs)

        # Store a reference to the MTRESS component
        setattr(_component, "mtress_component", self)
        setattr(_component, "short_label", label)

        self._solph_components.append(_component)
        self._solph_model.energy_system.add(_component)

        return _component

    @property
    def solph_components(self) -> list:
        """Iterate over solph components."""
        return self._solph_components

    def build_core(self) -> None:
        """Build the core structure of the component."""

    def establish_interconnections(self) -> None:
        """Build interconnections with other components."""

    def add_constraints(self) -> None:
        """Add constraints to the model."""

    def graph(self, detail: bool = False) -> Tuple[Digraph, set]:
        """
        Generate graphviz visualization of the MTRESS component.

        :param detail: Include solph components.
        """
        external_edges = set()

        graph = Digraph(name=f"cluster_{self.identifier}")
        graph.attr(
            "graph",
            label=self.name,
            # Draw border of cluster only for detail representation
            style="dashed" if detail else "invis",
        )

        if not detail:
            # TODO: Node shape?
            graph.node(self.identifier, label=self.name)

        for solph_component in self.solph_components:
            if detail:
                graph.node(
                    name=solph_component.label,
                    label=solph_component.short_label,
                    shape=SOLPH_SHAPES.get(type(solph_component), "rectangle"),
                )

            for origin in solph_component.inputs:
                if origin in self._solph_components:
                    # This is an internal edge and thus only added if detail is True
                    if detail:
                        graph.edge(origin.label, solph_component.label)
                else:
                    # This is an external edge
                    if detail:
                        # Add edge from solph component to solph component
                        external_edges.add((origin.label, solph_component.label))
                    else:
                        # Add edge from MTRESS component to MTRESS component
                        external_edges.add(
                            (origin.mtress_component.identifier, self.identifier)
                        )

        return graph, external_edges

    # TODO: Methods for result analysis


class ModelicaInterface(AbstractComponent):  # pylint: disable=too-few-public-methods
    """Interface for components which can be represented in open modelica."""

    # At the moment, this is just a memory aid
