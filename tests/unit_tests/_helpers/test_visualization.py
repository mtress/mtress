# -*- coding: utf-8 -*-
"""
Tests for the MTRESS visualization helper module.
"""

import jsonschema

from oemof.solph import Results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)

from mtress._helpers._visualization import (
    generate_graph,
    generate_graph_cytoscape,
)
from mtress._helpers import get_energy_types


def test_graph():
    nodes = []
    colours = set()
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
    myresults = Results(solved_model)
    flows = myresults["flow"]

    flow_colours = get_energy_types(solph_representation)

    colours.add("orange")  # only electricity in the system

    graph_elements = generate_graph(
        nodes=solph_representation.nodes,
        flows=flows,
        flow_colours=flow_colours,
    )

    # check all nodes present
    graph_nodes = graph_elements["nodes"]
    assert set(nodes) == set(graph_nodes.keys())

    # check graph colours okay
    edges = graph_elements["edges"]
    graph_colours = set()

    for _, targets in edges.items():
        for _, edge_attributes in targets.items():
            graph_colours.add(edge_attributes["colour"])
    assert colours == graph_colours

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
                        "colour": {
                            "type": "string",
                        },
                        "flow": {
                            "type": "number",
                        },
                        "required": [
                            "colour",
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
                        "colour": {"type": "string"},
                    },
                },
            },
        },
    }

    jsonschema.validate(cytoscape_elements["graph"], schema)
    jsonschema.validate(cytoscape_elements["flows"], schema)
