"""Abstract MTRESS components."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, NamedTuple, Tuple

from graphviz import Digraph
from oemof.solph import Bus
from oemof.solph.components import (
    Converter,
    GenericStorage,
    Sink,
    Source,
    OffsetConverter,
)

from ._interfaces import NamedElement
from ._solph_model import SolphModel

if TYPE_CHECKING:
    from ._location import Location

SOLPH_SHAPES = {
    Source: "trapezium",
    Sink: "invtrapezium",
    Bus: "ellipse",
    Converter: "octagon",
    OffsetConverter: "octagon",
    GenericStorage: "cylinder",
}

test_dict = {}


class AbstractComponent(NamedElement):
    """Abstract MTRESS component."""

    def __init__(self, name: str, autoconnect: bool = True) -> None:
        """Initialize a generic MTRESS component."""
        super().__init__(name)
        self.autoconnect = autoconnect
        self._location = None

    @property
    def location(self):
        """Return location this component belongs to."""
        return self._location

    def register_location(self, location: Location):
        """Register this component to a location."""
        if self._location is not None:
            raise KeyError("Location already registered")

        self._nesting_element = location
        self._location = location

    @abstractmethod
    def graph(self, detail: bool = False) -> Tuple[Digraph, set]:
        """Draw a graph representation of the component."""


class AbstractSolphRepresentation(AbstractComponent):
    """Interface for components which can be represented in `oemof.solph`."""

    def __init__(self, **kwargs) -> None:
        """Initialize component."""
        super().__init__(**kwargs)

        self._solph_nodes: list = []
        self._solph_model: SolphModel = None

    def register_solph_model(self, solph_model: SolphModel) -> None:
        """Store a reference to the solph model."""
        if self._solph_model is not None:
            raise KeyError("SolphModel already registered")

        self._solph_model = solph_model

    def create_solph_node(self, label: str, node_type: Callable, **kwargs):
        """Create a solph node and add it to the solph model."""
        _full_label = tuple(self.create_label(label))

        if label in self._solph_nodes:
            raise KeyError(
                f"Solph component named {_full_label} already exists"
            )

        _node = node_type(label=_full_label, **kwargs)

        # Store a reference to the MTRESS component
        setattr(_node, "mtress_component", self)
        setattr(_node, "short_label", label)

        self._solph_nodes.append(_node)
        self._solph_model.energy_system.add(_node)

        return _node

    @property
    def solph_nodes(self) -> list:
        """Iterate over solph nodes."""
        return self._solph_nodes

    def build_core(self) -> None:
        """Build the core structure of the component."""

    @abstractmethod
    def establish_interconnections(self) -> None:
        """Build interconnections with other nodes."""

    def add_constraints(self) -> None:
        """Add constraints to the model."""

    def get_flow_color(
        self, flow_color: dict, colorscheme: dict = None
    ) -> None:
        def rec(node, color):
            # recursively iterate nodes until all edges covered
            # or node type in [Source, Sink, Converter]
            if type(node) in [Source, Sink, Converter, OffsetConverter]:
                return
            node_id = tuple(node.label)
            for origin in node.inputs:
                origin_id = tuple(origin.label)
                flow_color.setdefault(origin_id, {})
                if node_id not in flow_color[origin_id]:
                    flow_color[origin_id][node_id] = color
                    rec(origin, color)
            for target in node.outputs:
                target_id = tuple(target.label)
                flow_color.setdefault(node_id, {})
                if target_id not in flow_color[node_id]:
                    flow_color[node_id][target_id] = color
                    rec(target, color)
            return

        color = colorscheme.get(self.identifier[-1], None)
        if color is None:  # component not a carrier
            # determine if only connected to ONE carrier
            own_nodes = [tuple(x.label) for x in self.solph_nodes]
            connected_nodes = [
                tuple(y.label) for x in self.solph_nodes for y in x.outputs
            ] + [tuple(y.label) for x in self.solph_nodes for y in x.inputs]
            external_nodes = set(connected_nodes) - set(own_nodes)
            external_nodes = set.intersection(*map(set, external_nodes))
            if external_nodes in [
                set(x.identifier)
                for x in self._solph_model._meta_model.components
            ]:
                color = colorscheme[
                    set.intersection(
                        set(colorscheme.keys()), external_nodes
                    ).pop()
                ]

        if color is not None:  # color nodes
            for solph_node in self.solph_nodes:
                solph_node_id = tuple(solph_node.label)
                for origin in solph_node.inputs:
                    origin_id = tuple(origin.label)
                    flow_color.setdefault(origin_id, {})
                    if solph_node_id not in flow_color[origin_id]:
                        flow_color[origin_id][solph_node_id] = color
                    rec(origin, color)
                for target in solph_node.outputs:
                    target_id = tuple(target.label)
                    flow_color.setdefault(solph_node_id, {})
                    if target_id not in flow_color[solph_node_id]:
                        flow_color[solph_node_id][target_id] = color
                    rec(target, color)

    def graph(
        self,
        detail: bool = False,
        flow_results=None,
        flow_color: dict = None,
        colorscheme: dict = None,
    ) -> Tuple[Digraph, set]:
        self.get_flow_color(flow_color, colorscheme)
        """
        Generate graphviz visualization of the MTRESS component.

        :param detail: Include solph nodes.
        """
        external_edges = set()

        graph = Digraph(name=f"cluster_{self.identifier}")
        graph.attr(
            "graph",
            label=self.name,
            # Draw border of cluster only for detail representation
            style="dashed" if detail else "invis",
            color="black",
        )

        if not detail:
            # TODO: Node shape?
            graph.node(str(self.identifier), label=self.name)

        for solph_node in self.solph_nodes:
            node_flow = 0
            if detail:
                graph.node(
                    name=str(solph_node.label),
                    label=str(solph_node.short_label),
                    shape=SOLPH_SHAPES.get(type(solph_node), "rectangle"),
                )

            for origin in solph_node.inputs:
                edge_color = flow_color.get(tuple(origin.label), {}).get(
                    tuple(solph_node.label), "black"
                )
                if origin in self._solph_nodes:
                    # This is an internal edge and thus only added
                    # if detail is True
                    if detail:
                        flow = 0
                        if flow_results is not None:
                            flow = (
                                flow_results[(origin.label, solph_node.label)]
                            ).sum()
                            node_flow += flow
                            if flow > 0:
                                graph.edge(
                                    str(origin.label),
                                    str(solph_node.label),
                                    label=f"{round(flow, 3)}",
                                    color=edge_color,
                                )
                            else:
                                graph.edge(
                                    str(origin.label),
                                    str(solph_node.label),
                                    color="grey",
                                )
                        else:
                            graph.edge(
                                str(origin.label), str(solph_node.label)
                            )
                else:
                    # This is an external edge
                    if detail:
                        flow = 0
                        if flow_results is not None:
                            flow = (
                                flow_results[(origin.label, solph_node.label)]
                            ).sum()

                            if flow > 0:
                                external_edges.add(
                                    (
                                        str(origin.label),
                                        str(solph_node.label),
                                        f"{round(flow, 3)}",
                                        edge_color,
                                    )
                                )
                            else:
                                external_edges.add(
                                    (
                                        str(origin.label),
                                        str(solph_node.label),
                                        "",
                                        "grey",
                                    )
                                )
                        else:
                            external_edges.add(
                                (
                                    str(origin.label),
                                    str(solph_node.label),
                                    "",
                                    "black",
                                )
                            )
                    else:
                        # Add edge from MTRESS component to MTRESS component
                        external_edges.add(
                            (
                                str(origin.mtress_component.identifier),
                                str(self.identifier),
                                "",
                                "black",
                            )
                        )

        return graph, external_edges

    # TODO: Methods for result analysis


class ModelicaInterface(
    AbstractComponent
):  # pylint: disable=too-few-public-methods
    """Interface for components which can be represented in open modelica."""

    # At the moment, this is just a memory aid
