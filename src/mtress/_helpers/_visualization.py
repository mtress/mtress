"""Visulisation of energy system."""

from oemof.solph import Bus
from oemof.solph.components import (
    Converter,
    GenericStorage,
    Sink,
    Source,
    OffsetConverter,
)

import logging
from dash import Dash, html, dcc, Input, Output, callback
import dash_cytoscape as cyto

import networkx as nx

# Define shapes for the component types
SHAPES = {
    Source: "source",
    Sink: "sink",
    Bus: "bus",
    Converter: "converter",
    OffsetConverter: "converter",
    GenericStorage: "storage",
}

COLORS = {
    "ElectricityCarrier": "orange",
    "GasCarrier": "steelblue",
    "HeatCarrier": "maroon",
}


def networkx_graph():
    # TODO: extract networkx representation from cytoscape for static plotting
    # https://networkx.org/documentation/stable/reference/readwrite/generated/networkx.readwrite.json_graph.cytoscape_graph.html
    # cyto.Cytoscape().to_plotly_json()
    pass


def cytoscape_graph(elements: list[dict], colorscheme: dict):
    # init dash cytoscape
    cyto.load_extra_layouts()
    app = Dash()

    graph = cyto.Cytoscape(
        id="mtress_model",
        layout={"name": "cose-bilkent"},  # cose-bilkent | cola | klay
        style={
            "width": "100%",
            "height": "calc(100vh - 120px)",
        },
        wheelSensitivity=0.1,
        stylesheet=[
            # Group selectors
            {
                "selector": "node",
                "style": {
                    "content": "data(label)",
                    "shape": "cut-rectangle",
                    "font-size": "36",
                },
            },
            {
                "selector": "edge",
                "style": {
                    "curve-style": "bezier",
                    "source-arrow-shape": "triangle",
                    "line-color": "black",
                    "source-arrow-color": "black",
                },
            },
            # Class selectors
            # coloring
            {
                "selector": "." + colorscheme["HeatCarrier"],
                "style": {
                    "line-color": colorscheme["HeatCarrier"],
                    "source-arrow-color": colorscheme["HeatCarrier"],
                },
            },
            {
                "selector": "." + colorscheme["ElectricityCarrier"],
                "style": {
                    "line-color": colorscheme["ElectricityCarrier"],
                    "source-arrow-color": colorscheme["ElectricityCarrier"],
                },
            },
            {
                "selector": "." + colorscheme["GasCarrier"],
                "style": {
                    "line-color": colorscheme["GasCarrier"],
                    "source-arrow-color": colorscheme["GasCarrier"],
                },
            },
            {
                "selector": ".inactive",
                "style": {
                    "line-color": "lightgrey",
                    "source-arrow-color": "lightgrey",
                    "line-style": "dashed",
                },
            },
            {
                "selector": ".rainbow",
                "style": {
                    "line-fill": "linear-gradient",
                    "line-gradient-stop-colors": """firebrick darkorange gold
                                                    chartreuse deepskyblue
                                                    cornflowerblue darkslateblue
                                                """,
                    "source-arrow-color": "firebrick",
                },
            },
            # node shapes
            {
                "selector": ".source",
                "style": {
                    "shape": "polygon",
                    "shape-polygon-points": "1, 1, 0.5, -1, -0.5, -1, -1, 1",
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": "label",
                    "height": "label",
                },
            },
            {
                "selector": ".sink",
                "style": {
                    "shape": "polygon",
                    "shape-polygon-points": "0.5, 1, 1, -1, -1, -1, -0.5, 1",
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": "label",
                    "height": "label",
                },
            },
            {
                "selector": ".bus",
                "style": {
                    "shape": "ellipse",
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": "label",
                    "height": "label",
                },
            },
            {
                "selector": ".converter",
                "style": {
                    "shape": "octagon",
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": "label",
                    "height": "label",
                },
            },
            {
                "selector": ".storage",
                "style": {
                    "shape": "barrel",
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": "label",
                    "height": "label",
                },
            },
            {
                "selector": ".parent",
                "style": {
                    "shape": "round-rectangle",
                    "text-valign": "top",
                },
            },
        ],
        elements=elements,
    )

    app.layout = html.Div(
        [
            graph,
        ]
    )

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(debug=False)


def get_flow_color(node, flow_color: dict, colorscheme: dict) -> None:
    def rec(n, c):  # node, color
        # recursively iterate nodes until all edges covered
        # or node type in [Source, Sink, Converter]
        if type(n) in [Source, Sink, Converter, OffsetConverter]:
            return
        n_id = tuple(n.label)
        for o in n.inputs:
            o_id = tuple(o.label)
            flow_color.setdefault(o_id, {})
            if n_id not in flow_color[o_id]:
                flow_color[o_id][n_id] = c
                rec(o, c)
        for t in n.outputs:
            t_id = tuple(t.label)
            flow_color.setdefault(n_id, {})
            if t_id not in flow_color[n_id]:
                flow_color[n_id][t_id] = c
                rec(t, c)
        return

    color = colorscheme.get(node.label[-2], None)
    if color is None:  # component not a carrier
        node_id = tuple(node.label)
        input_nodes = [tuple(o.label) for o in node.inputs]
        output_nodes = [tuple(t.label) for t in node.outputs]

        # determine if node only connected to ONE carrier
        connected_nodes = input_nodes + output_nodes
        connected_comp = set([c_n[:-1] for c_n in connected_nodes])
        own_comp = set()
        own_comp.add(node_id[:-1])
        external_comp = connected_comp - own_comp
        if len(external_comp) == 1:
            # only connected to ONE component
            external_comp = external_comp.pop()
            if external_comp[-1] in colorscheme:
                # component IS carrier -> get color
                color = colorscheme[external_comp[-1]]

    if color is not None:  # component is a carrier
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


def generate_graph(
    nodes,
    flows,
    flow_color: dict = None,
    colorscheme: dict = None,
    show: bool = True,
):
    """
    Function to generate nodes and edeges usable for dash cytoscape.
    """
    if colorscheme is None:
        # set to default
        colorscheme = COLORS

    if flow_color is None:
        flow_color = {}

    for n in nodes:
        get_flow_color(n, flow_color, colorscheme)

    graph_nodes = []
    graph_nodes_tracker = set()
    graph_edges = []
    for n in nodes:
        if type(n.label) == tuple:
            # mtress node
            identifier = list(n.label)

            child, child_id = None, None
            is_parent = False
            # go up the hierarchy and build parent - child relationship
            while identifier:
                if child_id in graph_nodes_tracker:
                    is_parent = True
                child_id = "-".join(identifier)
                child = identifier.pop()
                parent_id = "-".join(identifier)
                if child_id not in graph_nodes_tracker:
                    # only add nodes once
                    graph_nodes.append(
                        {
                            "data": {
                                "id": child_id,
                                "label": child,
                                "parent": parent_id,
                            },
                            "classes": (
                                "parent"
                                if is_parent
                                else SHAPES.get(type(n), "rectangle")
                            ),
                        }
                    )
                    graph_nodes_tracker.add(child_id)
        elif type(n.label) == str:
            # manually added oemof node (floaty boy)
            identifier = "-".join(n.label)
            graph_nodes.append(
                {
                    "data": {
                        "id": identifier,
                        "label": n.label,
                    },
                    "classes": SHAPES.get(type(n), "rectangle"),
                }
            )
        for o in n.inputs:
            edge_color = flow_color.get(tuple(o.label), {}).get(
                tuple(n.label), "black"
            )
            edge = {
                "data": {
                    "source": "-".join(n.label),
                    "target": "-".join(o.label),
                }
            }
            if flows is not None:
                flow = flows[o.label, n.label].sum()
                if flow > 0:
                    edge["classes"] = edge_color
                    edge["style"] = {
                        "label": str(round(flow, 3)),
                        "text-rotation": "autorotate",
                        "text-background-shape": "round-rectangle",
                        "text-background-opacity": "1",
                        "color": "white",
                    }
                else:  # TODO: show inactive edges -> toggle on off?
                    edge["classes"] = "inactive"
            else:
                edge["classes"] = edge_color
            graph_edges.append(edge)

    if show:
        cytoscape_graph(graph_nodes + graph_edges, colorscheme)
    else:
        return graph_nodes + graph_edges
