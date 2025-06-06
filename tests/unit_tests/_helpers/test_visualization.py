# -*- coding: utf-8 -*-
"""
Tests for the MTRESS visualization helper module.
"""

import jsonschema

from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows
from mtress._helpers._visualization import (
    generate_graph,
    generate_graph_cytoscape,
)


def test_graph():
    nodes = []
    colors = set()
    meta_model = MetaModel()

    house_1 = Location(name="house_1")
    meta_model.add_location(house_1)

    carrier0 = carriers.ElectricityCarrier()
    nodes.append(("house_1", "ElectricityCarrier"))
    nodes.append(("house_1", "ElectricityCarrier", "distribution"))
    nodes.append(("house_1", "ElectricityCarrier", "feed_in"))

    grid0 = technologies.ElectricityGridConnection(working_rate=32)
    nodes.append(("house_1", "ElectricityGridConnection"))
    nodes.append(("house_1", "ElectricityGridConnection", "grid_import"))
    nodes.append(("house_1", "ElectricityGridConnection", "grid_export"))
    nodes.append(("house_1", "ElectricityGridConnection", "source_import"))

    demand1 = demands.Electricity(name="demand1", time_series=[0, 1, 2])
    nodes.append(("house_1", "demand1"))
    nodes.append(("house_1", "demand1", "input"))
    nodes.append(("house_1", "demand1", "sink"))

    nodes = ["-".join(n) for n in nodes]
    nodes.append("house_1")

    house_1.add(carrier0)
    house_1.add(grid0)
    house_1.add(demand1)

    solph_representation = SolphModel(
        meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60min",
        },
    )

    solph_representation.build_solph_model()

    solved_model = solph_representation.solve(solve_kwargs={"tee": True})
    myresults = results(solved_model)
    flows = get_flows(myresults)

    colorscheme = {
        "ElectricityCarrier": "orange",
        "GasCarrier": "steelblue",
        "HeatCarrier": "maroon",
    }
    colors.add("orange")  # only electricity in the system

    flow_color = {
        ("house_1", "demand1", "input"): {
            ("house_1", "demand1", "sink"): "red"
        },
        ("house_1", "ElectricityGridConnection", "source_import"): {
            ("house_1", "ElectricityGridConnection", "grid_import"): "blue"
        },
    }
    colors.add("red")
    colors.add("blue")

    graph_elements = generate_graph(
        nodes=solph_representation.nodes(),
        flows=flows,
        flow_color=flow_color,
        colorscheme=colorscheme,
    )

    # check all nodes present
    nodes = graph_elements["nodes"]
    assert set(nodes) == set(nodes.keys())

    # check graph colors okay
    edges = graph_elements["edges"]
    graph_colors = set()

    for source, targets in edges.items():
        for target, edge_attributes in targets.items():
            graph_colors.add(edge_attributes["color"])
    assert colors == graph_colors

    # check dict schema
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "generate_graph",
        "title": "graph",
        "description": "simple dict representation of a MTRESS energy system",
        "type": "object",
        "properties": {
            "nodes": {
                "type": "object",
                "additionalProperties": {
                    "label": {
                        "type": "string",
                    },
                    "children": {
                        "type": ["array", "null"],
                    },
                    "parent": {
                        "type": ["string", "null"],
                    },
                    "shape": {
                        "type": "string",
                    },
                    "required": [
                        "label",
                        "children",
                        "parent",
                        "shape",
                    ],
                },
            },
            "edges": {
                "type": "object",  # source
                "additionalProperties": {
                    "type": "object",  # target
                    "additionalProperties": {
                        "color": {
                            "type": "string",
                        },
                        "flow": {
                            "type": "number",
                        },
                        "required": [
                            "color",
                        ],
                    },
                },
            },
        },
    }

    jsonschema.validate(graph_elements, schema)

    # check cytoscape dict schema
    cytoscape_elements = generate_graph_cytoscape(graph_elements, True)

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "generate_graph_cytoscape",
        "title": "graph cytoscape",
        "description": "dash cytoscape ready dict representation",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "parent": {"type": ["string", "null"]},
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                    },
                },
                "classes": {"type": "string"},
                "style": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "text-rotation": {"type": "string"},
                        "text-background-shape": {"type": "string"},
                        "text-background-opacity": {"type": "string"},
                        "color": {"type": "string"},
                    },
                },
            },
        },
    }

    jsonschema.validate(cytoscape_elements["graph"], schema)
    jsonschema.validate(cytoscape_elements["flows"], schema)
