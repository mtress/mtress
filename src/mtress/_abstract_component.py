"""Abstract MTRESS components."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, NamedTuple, Tuple, List

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
    Source: "source",
    Sink: "sink",
    Bus: "bus",
    Converter: "converter",
    OffsetConverter: "converter",
    GenericStorage: "storage",
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
        flow_results: dict = None,
        flow_color: dict = None,
        colorscheme: dict = None,
    ) -> List:
        self.get_flow_color(flow_color, colorscheme)

        id = "-".join(self.identifier)
        parent = "-".join(self.location.identifier)

        # add component
        nodes_simple = [
            {
                "data": {
                    "id": id,
                    "label": self.name,
                    "parent": parent,
                },
                "classes": "bus",
            }
        ]
        nodes_detail = [
            {
                "data": {
                    "id": id,
                    "label": self.name,
                    "parent": parent,
                },
                "classes": "parent",
            }
        ]
        nodes_result = list(nodes_detail)

        # external edges for simple graph
        external_edges = set()

        # iterate nodes
        for solph_node in self.solph_nodes:
            # add node
            n = {
                "data": {
                    "id": "-".join(solph_node.label),
                    "label": solph_node.short_label,
                    "parent": id,
                },
                "classes": SOLPH_SHAPES.get(type(solph_node), "rectangle"),
            }
            nodes_detail.append(n)
            nodes_result.append(n)

            # iterate edges
            for origin in solph_node.inputs:
                # internal edges
                edge_color = flow_color.get(tuple(origin.label), {}).get(
                    tuple(solph_node.label), "black"
                )
                e_detail = {
                    "data": {
                        "source": "-".join(solph_node.label),
                        "target": "-".join(origin.label),
                    },
                }
                nodes_detail.append(e_detail)

                if flow_results is not None:
                    flow = (
                        flow_results[(origin.label, solph_node.label)]
                    ).sum()
                    e_result = {
                        "data": {
                            "source": "-".join(solph_node.label),
                            "target": "-".join(origin.label),
                        },
                    }
                    if flow > 0:
                        e_result["classes"] = edge_color
                        e_result["style"] = {
                            "label": str(round(flow, 3)),
                            "text-rotation": "autorotate",
                            "text-background-shape": "round-rectangle",
                            "text-background-opacity": "1",
                            "color": "white",
                        }
                        # TODO: show edge only if active?
                        nodes_result.append(e_result)
                    else:
                        e_result["classes"] = "inactive"
                # nodes_result.append(e_result)

                # external edges
                if origin not in self._solph_nodes:
                    e_simple = (
                        id,
                        "-".join(origin.mtress_component.identifier),
                    )
                    external_edges.add(e_simple)

        # add external edges to simple graph
        for s, t in external_edges:
            e_s = {
                "data": {
                    "source": s,
                    "target": t,
                }
            }
            nodes_simple.append(e_s)

        return nodes_simple, nodes_detail, nodes_result


class ModelicaInterface(
    AbstractComponent
):  # pylint: disable=too-few-public-methods
    """Interface for components which can be represented in open modelica."""

    # At the moment, this is just a memory aid
