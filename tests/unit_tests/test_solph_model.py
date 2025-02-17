# -*- coding: utf-8 -*-
"""
Tests for the MTRESS solph model.
"""

import datetime

import json

import pandas as pd
import pytest

from oemof.solph.processing import results

from mtress import (
    Connection,
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress.technologies.grid_connection import ElectricityGridConnection
from mtress._helpers import get_flows


def test_minimal_initialisation_with_date_range():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 15:15:00"
    frequency = "15T"
    date_range = pd.date_range(
        start=first_index,
        end=last_index,
        freq=frequency,
    )
    solph_model = SolphModel(meta_model=MetaModel(), timeindex=date_range)
    assert solph_model.energy_system.timeindex.freq == frequency
    assert (
        datetime.datetime.strptime(first_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[0]
    )
    assert (
        datetime.datetime.strptime(last_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[-1]
    )


def test_minimal_initialisation_with_time_index_dict():
    first_index = "2021-07-10 00:00:00"
    last_index = "2021-07-10 15:15:00"
    frequency = "15T"
    solph_model = SolphModel(
        meta_model=MetaModel(),
        timeindex={
            "start": first_index,
            "end": last_index,
            "freq": frequency,
        },
    )
    assert solph_model.energy_system.timeindex.freq == frequency
    assert (
        datetime.datetime.strptime(first_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[0]
    )
    assert (
        datetime.datetime.strptime(last_index, "%Y-%m-%d %H:%M:%S")
        == solph_model.energy_system.timeindex[-1]
    )


def test_build_model_with_connected_electricity():
    house_1 = Location(name="house_1")
    house_1.add(carriers.ElectricityCarrier())
    gc1 = ElectricityGridConnection()
    house_1.add(gc1)

    house_2 = Location(name="house_2")
    house_2.add(carriers.ElectricityCarrier())
    gc2 = ElectricityGridConnection()
    house_2.add(gc2)

    meta_model = MetaModel(locations=[house_1, house_2])
    meta_model.add(Connection(house_1, house_2, ElectricityGridConnection))
    solph_model = SolphModel(
        meta_model=meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 15:15:00",
            "freq": "15T",
        },
    )
    solph_model.build_solph_model()

    assert gc2.grid_import in gc1.grid_export.outputs


def test_build_model_with_connected_electricity_missing_connection():
    house_1 = Location(name="house_1")
    house_2 = Location(name="house_2")

    meta_model = MetaModel(locations=[house_1, house_2])
    meta_model.add(Connection(house_1, house_2, ElectricityGridConnection))

    with pytest.raises(KeyError):
        SolphModel(
            meta_model=meta_model,
            timeindex={
                "start": "2021-07-10 00:00:00",
                "end": "2021-07-10 15:15:00",
                "freq": "15T",
            },
        )


def test_graph_simple():
    nodes = []
    meta_model = MetaModel()

    house_1 = Location(name="house_1")
    meta_model.add_location(house_1)

    carrier0 = carriers.ElectricityCarrier()
    nodes.append(("house_1", "ElectricityCarrier"))

    carrier1 = carriers.HeatCarrier(
        temperature_levels=[10, 20, 30]
    )
    nodes.append(
        (
            "house_1",
            "HeatCarrier",
        )
    )

    demand1 = demands.Electricity(name="demand1", time_series=[0, 1, 2])
    nodes.append(("house_1", "demand1"))

    demand2 = demands.FixedTemperatureHeating(
        name="demand2",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[1, 2, 3],
    )
    nodes.append(("house_1", "demand2"))

    house_1.add(carrier0)
    house_1.add(carrier1)
    house_1.add(demand1)
    house_1.add(demand2)

    solph_representation = SolphModel(
        meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60T",
        },
    )

    solph_representation.build_solph_model()

    plot = solph_representation.graph(detail=False)

    plot_json_string = plot.pipe("json").decode()
    plot_json_dict = json.loads(plot_json_string)

    assert plot_json_dict["name"] == "MTRESS model"

    obj_names = [obj["name"] for obj in plot_json_dict["objects"]]
    for n in nodes:
        assert f"['{n[0]}', '{n[1]}']" in obj_names


def test_graph_detail():
    nodes = []
    meta_model = MetaModel()

    house_1 = Location(name="house_1")
    meta_model.add_location(house_1)

    carrier0 = carriers.ElectricityCarrier()
    nodes.append(("house_1", "ElectricityCarrier", "distribution"))
    nodes.append(("house_1", "ElectricityCarrier", "feed_in"))

    carrier1 = carriers.HeatCarrier(
        temperature_levels=[10, 20, 30]
    )
    nodes.append(("house_1", "HeatCarrier", "T_10"))
    nodes.append(("house_1", "HeatCarrier", "T_20"))
    nodes.append(("house_1", "HeatCarrier", "T_30"))

    demand1 = demands.Electricity(name="demand1", time_series=[0, 1, 2])
    nodes.append(("house_1", "demand1", "input"))
    nodes.append(("house_1", "demand1", "sink"))

    demand2 = demands.FixedTemperatureHeating(
        name="demand2",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[1, 2, 3],
    )
    nodes.append(("house_1", "demand2", "output"))
    nodes.append(("house_1", "demand2", "sink"))
    nodes.append(("house_1", "demand2", "heat_exchanger"))

    house_1.add(carrier0)
    house_1.add(carrier1)
    house_1.add(demand1)
    house_1.add(demand2)

    solph_representation = SolphModel(
        meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60T",
        },
    )

    solph_representation.build_solph_model()

    plot = solph_representation.graph(detail=True)

    plot_json_string = plot.pipe("json").decode()
    plot_json_dict = json.loads(plot_json_string)

    print(plot_json_dict)

    assert plot_json_dict["name"] == "MTRESS model"

    obj_names = [obj["name"] for obj in plot_json_dict["objects"]]
    for n in nodes:
        assert (
            f"SolphLabel(location='{n[0]}',"
            + f" mtress_component='{n[1]}', "
            + f"solph_node='{n[2]}')"
            in obj_names
        )


def test_graph_flow():
    nodes = []
    colors = set()
    meta_model = MetaModel()

    house_1 = Location(name="house_1")
    meta_model.add_location(house_1)

    carrier0 = carriers.ElectricityCarrier()
    nodes.append(("house_1", "ElectricityCarrier", "distribution"))
    nodes.append(("house_1", "ElectricityCarrier", "feed_in"))

    grid0 = technologies.ElectricityGridConnection(working_rate=32)
    nodes.append(("house_1", "ElectricityGridConnection", "grid_import"))
    nodes.append(("house_1", "ElectricityGridConnection", "grid_export"))
    nodes.append(("house_1", "ElectricityGridConnection", "source_import"))

    demand1 = demands.Electricity(name="demand1", time_series=[0, 1, 2])
    nodes.append(("house_1", "demand1", "input"))
    nodes.append(("house_1", "demand1", "sink"))

    house_1.add(carrier0)
    house_1.add(grid0)
    house_1.add(demand1)

    solph_representation = SolphModel(
        meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60T",
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
    colors.add("grey")  # no energy will be exported

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

    plot = solph_representation.graph(
        detail=True,
        flow_results=flows,
        flow_color=flow_color,
        colorscheme=colorscheme,
    )

    plot_json_string = plot.pipe("json").decode()
    plot_json_dict = json.loads(plot_json_string)

    assert plot_json_dict["name"] == "MTRESS model"

    obj_names = [obj["name"] for obj in plot_json_dict["objects"]]
    for n in nodes:
        assert (
            f"SolphLabel(location='{n[0]}', "
            + f"mtress_component='{n[1]}', "
            + f"solph_node='{n[2]}')"
            in obj_names
        )

    edge_colors = set([edge["color"] for edge in plot_json_dict["edges"]])
    assert colors == edge_colors


def test_graph_series():
    nodes = []
    meta_model = MetaModel()

    house_1 = Location(name="house_1")
    meta_model.add_location(house_1)

    carrier0 = carriers.ElectricityCarrier()
    nodes.append(("house_1", "ElectricityCarrier", "distribution"))
    nodes.append(("house_1", "ElectricityCarrier", "feed_in"))

    grid0 = technologies.ElectricityGridConnection(working_rate=32)
    nodes.append(("house_1", "ElectricityGridConnection", "grid_import"))
    nodes.append(("house_1", "ElectricityGridConnection", "grid_export"))
    nodes.append(("house_1", "ElectricityGridConnection", "source_import"))

    demand1 = demands.Electricity(name="demand1", time_series=[0, 1, 2])
    nodes.append(("house_1", "demand1", "input"))
    nodes.append(("house_1", "demand1", "sink"))

    house_1.add(carrier0)
    house_1.add(grid0)
    house_1.add(demand1)

    solph_representation = SolphModel(
        meta_model,
        timeindex={
            "start": "2021-07-10 00:00:00",
            "end": "2021-07-10 03:00:00",
            "freq": "60T",
        },
    )

    solph_representation.build_solph_model()

    solved_model = solph_representation.solve(solve_kwargs={"tee": True})
    myresults = results(solved_model)
    flows = get_flows(myresults)

    plots = solph_representation.graph_series(
        flow_results=flows, step=pd.Timedelta("60min")
    )
    for plot in plots:
        plot_json_string = plot.pipe("json").decode()
        plot_json_dict = json.loads(plot_json_string)

        assert plot_json_dict["name"] == "MTRESS model"

        obj_names = [obj["name"] for obj in plot_json_dict["objects"]]
        for n in nodes:
            assert (
                f"SolphLabel(location='{n[0]}',"
                + f" mtress_component='{n[1]}',"
                + f" solph_node='{n[2]}')"
                in obj_names
            )
