"""Visulisation of energy system."""
import re

import graphviz
from oemof.solph import Bus
from oemof.solph.components import GenericStorage, Sink, Source, Converter

from ._util import update_in_dict

# Define shapes for the component types
SHAPES = {
    Source: "trapezium",
    Sink: "invtrapezium",
    Bus: "ellipse",
    Converter: "octagon",
    GenericStorage: "cylinder",
}


def generate_graph(energysystem, label_extractor=None):
    """Generate graphviz graph from energysystem."""
    if label_extractor is None:

        def label_extractor(label):
            return label.split(":")

    dot = graphviz.Digraph(format="png")

    nodes = {}
    locations = {}

    for node in energysystem.nodes:
        # Replace invalid characters
        name = nodes[node] = re.sub(r"[^a-zA-Z0-9_]+", "__", node.label)
        update_in_dict(locations, node.label, (name, type(node)), sep=":")

    for location, components in locations.items():
        with dot.subgraph(name=f"cluster_{location}") as location_subgraph:
            location_subgraph.attr(label=location)

            for component, elements in components.items():
                with location_subgraph.subgraph(
                    name=f"cluster_{location}_{component}"
                ) as component_subgraph:
                    component_subgraph.attr(label=component)

                    for element, (name, node_type) in elements.items():
                        component_subgraph.node(
                            name,
                            label=element,
                            shape=SHAPES.get(node_type, "rectangle"),
                        )

    for node in energysystem.nodes:
        for output in node.outputs:
            dot.edge(nodes[node], nodes[output])

    return dot
