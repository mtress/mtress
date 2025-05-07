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

from graphviz import Digraph

# Define shapes for the component types
SHAPES = {
    Source: "source",
    Sink: "sink",
    Bus: "bus",
    Converter: "converter",
    OffsetConverter: "converter",
    GenericStorage: "storage",
}

SHAPES_GRAPHVIZ = {
    "source": "trapezium",
    "sink": "invtrapezium",
    "bus": "ellipse",
    "converter": "octagon",
    "storage": "cylinder",
}


COLORS = {
    "ElectricityCarrier": "orange",
    "GasCarrier": "steelblue",
    "HeatCarrier": "maroon",
}

RAINBOW = """darkslateblue cornflowerblue
            deepskyblue chartreuse
            gold darkorange firebrick"""

RAINBOW_GRAPHVIZ = (
    "firebrick1:darkorange:gold2:"
    + "chartreuse3:deepskyblue:cornflowerblue:"
    + "darkslateblue"
)


SOURCE_SHAPE = "1, 1, 0.75, -1, -0.75, -1, -1, 1"
SINK_SHAPE = "0.75, 1, 1, -1, -1, -1, -0.75, 1"


def graph_graphviz(
    nodes,
    flows,
    flow_color: dict,
    colorscheme: dict,
) -> None:
    if colorscheme is None:
        # set to default
        colorscheme = COLORS

    # get graphviz digraph
    f = flows is not None
    graph = generate_graph_graphviz(
        generate_graph(nodes, flows, flow_color, colorscheme),
        f,
    )

    # render graph and write to file
    graph.render(outfile="model.png", cleanup=True)


def graph_cytoscape(
    nodes,
    flows,
    flow_color: dict,
    colorscheme: dict,
):
    if colorscheme is None:
        # set to default
        colorscheme = COLORS

    # get cytoscape elements
    f = flows is not None
    elements = generate_graph_cytoscape(
        generate_graph(nodes, flows, flow_color, colorscheme),
        f,
    )

    # init dash cytoscape
    cyto.load_extra_layouts()
    app = Dash()

    tabs = [dcc.Tab(label=x, value=x) for x in elements.keys()]

    app.layout = html.Div(
        [
            dcc.Tabs(
                id="view_selector",
                value="graph",
                children=tabs,
            ),
            html.Button(
                html.H3("hide inactive"),
                id="toggle_inactive",
                style={
                    "position": "absolute",
                    "right": 50,
                    "top": 15,
                    "z-index": 10,
                },
                hidden=True,
                n_clicks=0,
            ),
            html.Div(id="graph"),
        ]
    )

    @callback(
        Output("toggle_inactive", "children"),
        Input("toggle_inactive", "n_clicks"),
    )
    def change_button(btn_clicks):
        if btn_clicks % 2:
            return html.H3("show inactive")
        else:
            return html.H3("hide inactive")

    @callback(
        Output("toggle_inactive", "hidden"), Input("view_selector", "value")
    )
    def toggle_inactive(tab):
        if tab == "graph":
            return True
        elif tab == "flows":
            return False

    @callback(
        Output("graph", "children"),
        Input("view_selector", "value"),
        Input("toggle_inactive", "n_clicks"),
    )
    def render_graph(tab, show_inactive):
        e = elements[tab]

        # remove inactive edges
        if show_inactive % 2:
            e = [item for item in e if item["classes"] != "inactive"]

        return html.Div(
            [
                cyto.Cytoscape(
                    id="mtress_model",
                    layout={
                        "name": "cose-bilkent"
                    },  # cose-bilkent | cola | klay
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
                                "target-arrow-shape": "triangle",
                                "line-color": "black",
                                "target-arrow-color": "black",
                                "font-size": "28",
                                "width": "6",
                            },
                        },
                        # Class selectors
                        # coloring
                        {
                            "selector": "." + colorscheme["HeatCarrier"],
                            "style": {
                                "line-color": colorscheme["HeatCarrier"],
                                "target-arrow-color": colorscheme[
                                    "HeatCarrier"
                                ],
                            },
                        },
                        {
                            "selector": "."
                            + colorscheme["ElectricityCarrier"],
                            "style": {
                                "line-color": colorscheme[
                                    "ElectricityCarrier"
                                ],
                                "target-arrow-color": colorscheme[
                                    "ElectricityCarrier"
                                ],
                            },
                        },
                        {
                            "selector": "." + colorscheme["GasCarrier"],
                            "style": {
                                "line-color": colorscheme["GasCarrier"],
                                "target-arrow-color": colorscheme[
                                    "GasCarrier"
                                ],
                            },
                        },
                        {
                            "selector": ".inactive",
                            "style": {
                                "line-color": "lightgrey",
                                "target-arrow-color": "lightgrey",
                                "line-style": "dashed",
                            },
                        },
                        {
                            "selector": ".rainbow",
                            "style": {
                                "line-fill": "linear-gradient",
                                "line-gradient-stop-colors": RAINBOW,
                                "target-arrow-color": "firebrick",
                            },
                        },
                        # node shapes
                        {
                            "selector": ".source",
                            "style": {
                                "shape": "polygon",
                                "shape-polygon-points": SOURCE_SHAPE,
                                "text-valign": "center",
                                "text-halign": "center",
                                "width": "label",
                                "height": "label",
                                "padding": "25px",
                            },
                        },
                        {
                            "selector": ".sink",
                            "style": {
                                "shape": "polygon",
                                "shape-polygon-points": SINK_SHAPE,
                                "text-valign": "center",
                                "text-halign": "center",
                                "width": "label",
                                "height": "label",
                                "padding": "25px",
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
                                "padding": "25px",
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
                                "padding": "25px",
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
                                "padding": "25px",
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
                    elements=e,
                )
            ]
        )

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(debug=False)


def get_flow_color(node, flow_color: dict, colorscheme: dict) -> None:
    """
    Function to determine the color of a graphs edges.
    The graph is supposed to be a MTRESS energy system.
    The determined color is dependent on the Energy Carrier
    a node is connected to.
    The algorithm recursivley determines edge colors for neighbouring
    nodes until dead ends are reached.

    :param node: the node of whichs colors should be determined
    :param flow_color: a dictionary of already determined colors for edges
    :param colorscheme: a dictionary which assigns a color
        per MTRESS energy carrier
    """

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

    # tuple with >= 2 entries or str expected
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
) -> dict:
    """
    Function to generate a simple dict representation
    of a MTRESS energy system.

    :param nodes: the oemof.solph.EnergySystem.nodes
    :param flows: [OPTIONAL] the resulting flows of the solved energy system
    :param flow_color: a dictionary of already determined colors for edges
    :param colorscheme: a dictionary which assigns a color
        per MTRESS energy carrier
    """
    if colorscheme is None:
        # set to default
        colorscheme = COLORS

    # determine color of edges
    if flow_color is None:
        flow_color = {}

    for n in nodes:
        get_flow_color(n, flow_color, colorscheme)

    # data structures for storing nodes and edges
    graph_nodes = {}
    graph_nodes_tracker = set()
    graph_edges = {}

    for n in nodes:
        # get nodes
        if type(n.label) == tuple:
            # mtress node
            identifier = list(n.label)

            current_label, current_id = None, None
            is_parent = False
            # go up the hierarchy and build parent - child relationship
            while identifier:  # do until list is empty
                child_id = current_id
                if current_id in graph_nodes_tracker:
                    is_parent = True
                current_id = "-".join(identifier)
                current_label = identifier.pop()  # take element out of list
                parent_id = "-".join(identifier)
                graph_nodes.setdefault(
                    current_id,
                    {
                        "label": current_label,
                        "children": set() if is_parent else None,
                        "parent": parent_id if parent_id != "" else None,
                        "shape": SHAPES.get(type(n), "rectangle"),
                    },
                )
                if is_parent:
                    graph_nodes[current_id]["children"].add(child_id)
                graph_nodes_tracker.add(current_id)
        elif type(n.label) == str:
            # manually added oemof node (floaty boy)
            identifier = n.label
            graph_nodes.setdefault(
                identifier,
                {
                    "label": identifier,
                    "children": None,
                    "parent": None,
                    "shape": SHAPES.get(type(n), "rectangle"),
                },
            )

        # get edges
        for t in n.outputs:
            edge_color = flow_color.get(tuple(n.label), {}).get(
                tuple(t.label), "black"
            )
            source_id = (
                "-".join(n.label) if type(n.label) == tuple else n.label
            )
            target_id = (
                "-".join(t.label) if type(t.label) == tuple else t.label
            )
            graph_edges.setdefault(source_id, {})
            graph_edges[source_id].setdefault(target_id, {})
            graph_edges[source_id][target_id]["color"] = edge_color
            if flows is not None:
                flow = flows[n.label, t.label].mean()  # .sum()
                graph_edges[source_id][target_id]["flow"] = flow

    graph_elements = {
        "nodes": graph_nodes,
        "edges": graph_edges,
    }
    return graph_elements


def generate_graph_graphviz(
    graph_elements: dict,
    flows: bool,
) -> Digraph:
    """
    Function to generate a graphviz Digraph representation
    from the dict representation of the MTRESS graph.

    :param graph_elements: simple dict representation of a MTRESS energy system
    :param flows: flag to toggle flows
    """
    nodes = graph_elements["nodes"]
    edges = graph_elements["edges"]
    graph = Digraph(name="MTRESS model")

    # --- NODES
    # 1. determine LOCATIONS or floaty boys
    # (nodes without parents)
    locations = {k: dict() for k, v in nodes.items() if v["parent"] == None}

    # 2. determine COMPONENTS of LOCATIONS
    # (children of LOCATIONS)
    for l, c in locations.items():
        loc_graph = Digraph(name=f"cluster_{l}")
        loc_graph.attr("graph", label=l)
        components = [k for k, v in nodes.items() if v["parent"] == l]
        for comp in components:
            comp_graph = Digraph(name=f"cluster_{comp}")
            comp_graph.attr(
                "graph",
                label=nodes[comp]["label"],
                style="dashed",  # border of component
                color="black",
            )
            # 3. determine NODES of COMPONENTS
            # (children of COMPONENTS)
            c_n = [k for k, v in nodes.items() if v["parent"] == comp]
            c[comp] = c_n

            # draw nodes
            for n in c_n:
                label = nodes[n]["label"]
                shape = SHAPES_GRAPHVIZ.get(nodes[n]["shape"], "rectangle")
                comp_graph.node(
                    name=n,
                    label=label,
                    shape=shape,
                )
            # draw component
            loc_graph.subgraph(comp_graph)
        # draw location
        graph.subgraph(loc_graph)

    # --- EDGES
    for source, targets in edges.items():
        # one source can have multiple targets
        for target, edge_attributes in targets.items():
            # draw edge for every target
            color = edge_attributes["color"]
            if color == "rainbow":
                color = RAINBOW_GRAPHVIZ
            if flows:
                flow = edge_attributes["flow"]
                if flow > 0:
                    graph.edge(
                        source,
                        target,
                        label=f"{round(flow, 3)}",
                        color=color,
                    )
                else:
                    graph.edge(
                        source,
                        target,
                        label="",
                        color="grey",
                    )
            else:
                graph.edge(
                    source,
                    target,
                    label="",
                    color=color,
                )

    return graph


def generate_graph_cytoscape(graph_elements: dict, flows: bool) -> dict:
    """
    Function to generate a dash cytoscape ready dict representation
    from the dict representation of the MTRESS energy system.

    :param graph_elements: simple dict representation of a MTRESS energy system
    :param flows: flag to toggle flows
    """
    graph_nodes = graph_elements["nodes"]
    graph_edges = graph_elements["edges"]

    cytoscape_nodes = []
    for node, node_attr in graph_nodes.items():
        n = {
            "data": {
                "id": node,
                "label": node_attr["label"],
                "parent": node_attr["parent"],
            },
            "classes": (
                "parent"
                if node_attr["children"] is not None
                else node_attr["shape"]
            ),
        }
        cytoscape_nodes.append(n)

    cytoscape_edges = []
    cytoscape_edges_flows = []
    for source, targets in graph_edges.items():
        for t, edge_attr in targets.items():
            e = {
                "data": {
                    "source": source,
                    "target": t,
                },
                "classes": edge_attr["color"],
            }
            cytoscape_edges.append(e.copy())

            if flows:
                flow = edge_attr["flow"]
                if flow > 0:
                    e["style"] = {
                        "label": str(round(flow, 3)),
                        "text-rotation": "autorotate",
                        "text-background-shape": "round-rectangle",
                        "text-background-opacity": "1",
                        "color": "white",
                    }
                else:
                    e["classes"] = "inactive"
                cytoscape_edges_flows.append(e)

    cytoscape_elements = {}
    cytoscape_elements["graph"] = cytoscape_nodes + cytoscape_edges
    if flows:
        cytoscape_elements["flows"] = cytoscape_nodes + cytoscape_edges_flows

    return cytoscape_elements
